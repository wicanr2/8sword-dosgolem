use super::*;
fn row(id: &str, count: u32) -> Stack {
    Stack {
        unit: Some(UnitId::parse(id).unwrap()),
        count,
    }
}
fn fixture(cat: &Catalog, spells: bool, enemy: bool) -> Checkpoint<'_> {
    let mut rows = [[Stack::default(); 6]; 2];
    rows[0][0] = row("native:01", 74);
    rows[0][1] = row("openkb:wolf", 2);
    rows[0][2] = row("openkb:arcr", 2);
    rows[1][0] = row("native:06", 11);
    rows[1][1] = row("native:16", 35);
    rows[1][2] = row("native:11", 29);
    let book = SpellBook {
        enabled: true,
        charges: [3; 8],
        stat_26ae: 4,
        stat_26b0: 2,
    };
    let controller = if enemy {
        rows[1] = [Stack::default(); 6];
        rows[1][0] = row("native:12", 3);
        rows[1][1] = row("native:16", 10);
        Controller::with_enemy_spells(
            cat,
            rows,
            Side::Enemy,
            Modifiers::default(),
            None,
            EnemyConfig {
                stat_26ae: 4,
                shifted_alias: 0,
            },
        )
    } else if spells {
        rows[0][3] = row("native:10", 2);
        Controller::with_spells(cat, rows, Side::Player, Modifiers::default(), book)
    } else {
        Controller::new(cat, rows, Side::Player, Modifiers::default())
    }
    .unwrap();
    Checkpoint {
        controller,
        rng: OriginalRng { seed: 1 },
        view: ViewState {
            scenario: if enemy {
                8
            } else if spells {
                6
            } else {
                0
            },
            ..ViewState::default()
        },
    }
}
fn roundtrip<'a>(a: &Checkpoint<'a>) -> Checkpoint<'a> {
    let raw = a.encode().unwrap();
    assert!(raw.len() < 4096);
    let b = Checkpoint::decode(a.catalog(), &raw).unwrap();
    assert_eq!(&b, a);
    assert_eq!(b.encode().unwrap(), raw);
    b
}
fn ordinary(a: &mut Checkpoint<'_>) {
    let c = &mut a.controller;
    let Some(actor) = c.next_actor().unwrap() else {
        return;
    };
    if c.is_enemy_caster() {
        c.enemy_cast(&mut a.rng).unwrap();
    } else if c.is_caster() {
        c.skip().unwrap();
    } else {
        let target = if actor.side == Side::Enemy {
            c.enemy_target(&mut a.rng).unwrap()
        } else {
            c.legal_targets().unwrap()[0]
        };
        c.attack(target).unwrap();
    }
}
#[test]
fn every_ordinary_boundary_and_terminal_state_resume_with_same_rng() {
    let cat = Catalog::builtin().unwrap();
    for enemy in [false, true] {
        let mut a = fixture(&cat, false, enemy);
        for _ in 0..200 {
            roundtrip(&a);
            a.controller.next_actor().unwrap();
            let mut b = roundtrip(&a);
            if a.controller.battle().outcome().is_some() {
                break;
            }
            ordinary(&mut a);
            ordinary(&mut b);
            assert_eq!(a, b);
        }
        assert!(a.controller.battle().outcome().is_some());
        roundtrip(&a);
    }
    let mut a = fixture(&cat, false, false);
    a.controller.next_actor().unwrap();
    a.controller.retreat().unwrap();
    roundtrip(&a);
    let mut a = fixture(&cat, false, false);
    a.controller
        .battle
        .spell_counts(&[
            (Side::Player, 0, 0),
            (Side::Player, 1, 0),
            (Side::Player, 2, 0),
        ])
        .unwrap();
    assert_eq!(a.controller.battle().outcome(), Some(Outcome::Loss));
    roundtrip(&a);
}
fn caster<'a>(cat: &'a Catalog) -> Checkpoint<'a> {
    let mut a = fixture(cat, true, false);
    for _ in 0..20 {
        a.controller.next_actor().unwrap();
        if a.controller.is_caster() {
            return a;
        }
        a.controller.skip().unwrap();
    }
    panic!("caster not reached")
}
#[test]
fn paid_target_wait_resumes_without_second_charge_and_space_refunds_once() {
    let cat = Catalog::builtin().unwrap();
    let mut a = caster(&cat);
    a.controller.select_spell(Spell::Fireball).unwrap();
    let hp = *a.controller.battle.hp();
    let mut b = roundtrip(&a);
    assert_eq!(b.controller.spell_book().unwrap().charges[0], 2);
    let actor = b.controller.current();
    b.controller.next_actor().unwrap();
    assert_eq!(b.controller.current(), actor);
    a.controller.target_spell(0, &mut a.rng).unwrap();
    b.controller.target_spell(0, &mut b.rng).unwrap();
    assert_eq!(a, b);
    assert_eq!(b.controller.battle.hp(), &hp);
    let mut a = caster(&cat);
    a.controller.select_spell(Spell::Fireball).unwrap();
    let mut b = roundtrip(&a);
    b.controller.cancel_spell_target(false).unwrap();
    assert_eq!(b.controller.spell_book().unwrap().charges[0], 3);
    assert!(b.controller.cancel_spell_target(false).is_err());
    roundtrip(&b);
}
#[test]
fn freeze_aliases_clone_and_spell_results_keep_pending_hp() {
    let cat = Catalog::builtin().unwrap();
    for spell in [Spell::Freeze, Spell::Clone, Spell::Thunder, Spell::Quake] {
        let mut a = caster(&cat);
        let hp = *a.controller.battle.hp();
        let result = a.controller.select_spell(spell).unwrap();
        if result.is_none() {
            a.controller.target_spell(0, &mut a.rng).unwrap();
        }
        assert_eq!(a.controller.battle.hp(), &hp);
        let mut b = roundtrip(&a);
        for _ in 0..3 {
            ordinary(&mut a);
            ordinary(&mut b);
            assert_eq!(a, b);
            if a.controller.battle.outcome().is_some() {
                break;
            }
        }
    }
}
#[test]
fn checked_but_impossible_states_and_malformed_envelopes_are_rejected() {
    let cat = Catalog::builtin().unwrap();
    let a = caster(&cat);
    let raw = a.encode().unwrap();
    for n in 0..raw.len() {
        assert!(Checkpoint::decode(&cat, &raw[..n]).is_err());
    }
    let mut broken = raw.clone();
    broken[20] ^= 1;
    assert!(Checkpoint::decode(&cat, &broken).is_err());
    let mut broken = raw.clone();
    broken[7] = b'2';
    let end = broken.len() - 8;
    let h = checksum(&broken[..end]);
    broken[end..].copy_from_slice(&h.to_le_bytes());
    assert!(Checkpoint::decode(&cat, &broken).is_err());
    let altered =
        Catalog::parse(&include_str!("../unit-catalog.tsv").replacen("民兵", "民兵異版", 1))
            .unwrap();
    assert!(Checkpoint::decode(&altered, &raw).is_err());
    for n in 0..7 {
        let mut b = a.clone();
        match n {
            0 => b.controller.slots[0][0] = 6,
            1 => b.controller.slots[0][1] = b.controller.slots[0][0],
            2 => b.controller.actor.as_mut().unwrap().raw = 6,
            3 => b.controller.scan.rear = 7,
            4 => b.view.font = 3,
            5 => {
                b.controller.battle = Battle::restore_native(
                    &cat,
                    *a.controller.battle.rows(),
                    *a.controller.battle.hp(),
                    0,
                    true,
                )
                .unwrap()
            }
            _ => b.controller.selected_spell = Some(Spell::Quake),
        };
        assert!(b.encode().is_err(), "invalid {n}");
    }
    // Recalculate the envelope checksum after corrupting a slot: semantic guard still rejects.
    let mut w = Reader {
        data: &raw[12..raw.len() - 8],
        at: 0,
    };
    w.q().unwrap();
    for _ in 0..12 {
        let n = usize::from(w.b().unwrap());
        w.bytes(n + 12).unwrap();
    }
    w.q().unwrap();
    w.flag().unwrap();
    let offset = 12 + w.at;
    let mut invalid = raw.clone();
    invalid[offset] = 6;
    let end = invalid.len() - 8;
    let h = checksum(&invalid[..end]);
    invalid[end..].copy_from_slice(&h.to_le_bytes());
    assert!(Checkpoint::decode(&cat, &invalid).is_err());
}
