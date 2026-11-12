use crate::{
    battle::{Side, Stack},
    catalog::{Catalog, UnitId},
    journey::Journey,
    spells::Spell,
    world::{Position, WorldData},
    world_magic::{self, PendingShop},
};
fn army(j: &mut Journey<'_>) {
    j.magic.book = true;
    j.resources[5] = 24;
    j.army[1] = Stack {
        unit: Some(UnitId::parse("native:10").unwrap()),
        count: 2,
    };
}
fn enter<'a>(c: &'a Catalog, d: &WorldData, guard: bool) -> Journey<'a> {
    let mut j = Journey::new(d, 1);
    army(&mut j);
    j.magic.battle_charges = [2; 8];
    if guard {
        let site = crate::guards::sites()[0];
        j.world.area = site.area;
        j.world.position = crate::world::motion(site.position, 0x4800, 3, true)
            .unwrap()
            .0;
        j.travel(d, 0x4800, c).unwrap();
        j.select_guard(true).unwrap();
        j.choose_guard(&d, &c, true).unwrap();
    } else {
        j.cue = Some(1);
        j.choose(c, true).unwrap();
    }
    j
}
fn caster(j: &mut Journey<'_>) {
    let cp = j.battle.as_mut().unwrap();
    for _ in 0..100 {
        let a = cp.controller.next_actor().unwrap().unwrap();
        if cp.controller.is_caster() {
            return;
        }
        if a.side == Side::Player {
            cp.controller.skip().unwrap();
        } else if cp.controller.is_enemy_caster() {
            cp.controller.enemy_cast(&mut cp.rng).unwrap();
        } else {
            let t = cp.controller.enemy_target(&mut cp.rng).unwrap();
            cp.controller.attack(t).unwrap();
        }
    }
    panic!("no caster")
}
#[test]
fn all_46_stores_share_both_columns_capacity_and_fail_atomically() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::magic_fixture(1);
    for (i, site) in world_magic::shops().iter().enumerate() {
        let mut j = Journey::new(&d, 1);
        j.world.area = site.area;
        j.world.position = Position {
            x: site.x,
            y: site.y,
        };
        j.magic.shop = Some(PendingShop {
            index: i as u8,
            moved: false,
        });
        let old = j.clone();
        assert!(j.buy_world_spell().is_err());
        assert_eq!(j, old);
        j.magic.book = true;
        j.resources[5] = 2;
        j.resources[3] = 30000;
        j.magic.charges[0] = 1;
        let price = u64::from(world_magic::offer_data(usize::from(site.offer)).unwrap().1);
        j.buy_world_spell().unwrap();
        assert_eq!(j.resources[3], 30000 - price);
        assert_eq!(j.spell_inventory_used(), 2);
        let old = j.clone();
        assert!(j.buy_world_spell().is_err());
        assert_eq!(j, old);
        assert_eq!(
            Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap(),
            j
        );
        j.resources[5] = 3;
        j.resources[3] = price - 1;
        let old = j.clone();
        assert!(j.buy_world_spell().is_err());
        assert_eq!(j, old);
    }
    // Newly supported battle shops also use the existing water-to-shop consumer.
    let shore = WorldData::special_shore_fixture();
    for (i, site) in world_magic::shops()
        .iter()
        .enumerate()
        .filter(|(_, s)| s.offer >= 8)
    {
        let target = Position {
            x: site.x,
            y: site.y,
        };
        let (from, key) = crate::jump_spell::DIRECTIONS
            .into_iter()
            .find_map(|key| {
                let from = crate::world::motion(target, key, 3, true).unwrap().0;
                matches!(shore.tile(site.area, from).unwrap(), 2 | 11..=14).then_some((from, key))
            })
            .unwrap();
        let mut j = Journey::new(&shore, 1);
        j.world.area = site.area;
        j.world.position = from;
        j.world.boat = 2;
        j.world.remaining = 1;
        j.magic.book = true;
        j.resources[5] = 3;
        j.resources[3] = 30000;
        j.travel(&shore, key, &c).unwrap();
        j.select_shore(true).unwrap();
        j.finish_shore(&shore, &c).unwrap();
        assert_eq!(j.magic.shop.unwrap().index, i as u8);
        assert_eq!(j.world.boat, 0);
        j.buy_world_spell().unwrap();
        assert_eq!(j.battle_charges()[usize::from(site.offer - 8)], 1);
        j.close_magic_shop(&c, &shore).unwrap();
        assert_eq!(j.phase(), "monthly");
        assert_eq!(
            Journey::decode(&c, &shore, &j.encode(&c, &shore).unwrap()).unwrap(),
            j
        );
    }
}
#[test]
fn random_and_guard_all_eight_inventory_transfers_survive_pending_and_finished_cold() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::guards_fixture(false);
    for guard in [false, true] {
        for spell in Spell::ALL {
            let mut j = enter(&c, &d, guard);
            caster(&mut j);
            let cp = j.battle.as_mut().unwrap();
            if cp.controller.select_spell(spell).unwrap().is_none() {
                let raw = j.encode(&c, &d).unwrap();
                j = Journey::decode(&c, &d, &raw).unwrap();
                let cp = j.battle.as_mut().unwrap();
                let t = cp.controller.spell_targets().unwrap()[0];
                cp.controller.target_spell(t, &mut cp.rng).unwrap();
            }
            let charges = j.battle_charges();
            assert!(charges[spell.index()] <= 2);
            assert_eq!(j.magic.battle_charges, [2; 8]);
            let raw = j.encode(&c, &d).unwrap();
            j = Journey::decode(&c, &d, &raw).unwrap();
            if j.battle
                .as_ref()
                .unwrap()
                .controller
                .battle()
                .outcome()
                .is_none()
            {
                j.battle.as_mut().unwrap().controller.retreat().unwrap();
            }
            j.finish(&c, &d, None).unwrap();
            assert_eq!(j.magic.battle_charges, charges);
            assert_eq!(
                Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap(),
                j
            );
            if spell == Spell::Clone {
                assert_eq!(j.army[0].count, 60);
            }
        }
    }
}
#[test]
fn target_space_refunds_esc_does_not_and_old_v16_has_no_new_inventory() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::guards_fixture(false);
    for guard in [false, true] {
        for retreat in [false, true] {
            let mut j = enter(&c, &d, guard);
            caster(&mut j);
            j.battle
                .as_mut()
                .unwrap()
                .controller
                .select_spell(Spell::Fireball)
                .unwrap();
            let raw = j.encode(&c, &d).unwrap();
            j = Journey::decode(&c, &d, &raw).unwrap();
            j.battle
                .as_mut()
                .unwrap()
                .controller
                .cancel_spell_target(retreat)
                .unwrap();
            assert_eq!(j.battle_charges()[0], if retreat { 1 } else { 2 });
            if !retreat {
                j.battle.as_mut().unwrap().controller.retreat().unwrap();
            }
            j.finish(&c, &d, None).unwrap();
            assert_eq!(j.magic.battle_charges[0], if retreat { 1 } else { 2 });
        }
    }
    let j = Journey::new(&d, 1);
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - crate::space_events::SUFFIX - 24);
    raw[..8].copy_from_slice(b"8SJRN016");
    raw.extend(crate::media_assets::checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
    // v16 had a disabled empty caster book even when the world owned the bamboo book.
    let mut old = Journey::new(&d, 1);
    army(&mut old);
    old.magic.book = false;
    old.cue = Some(1);
    old.choose(&c, true).unwrap();
    let mut raw = old.encode(&c, &d).unwrap();
    let tag = world_magic::fingerprint().to_le_bytes();
    let at = raw.windows(8).position(|v| v == tag).unwrap();
    raw[at + 8] = 1;
    raw.truncate(raw.len() - crate::space_events::SUFFIX - 24);
    raw[..8].copy_from_slice(b"8SJRN016");
    raw.extend(crate::media_assets::checksum(&raw).to_le_bytes());
    let upgraded = Journey::decode(&c, &d, &raw).unwrap();
    assert!(
        upgraded.magic.book
            && upgraded
                .battle
                .as_ref()
                .unwrap()
                .controller
                .spell_book()
                .unwrap()
                .enabled
    );
    assert_eq!(upgraded.battle_charges(), [0; 8]);
    assert!(upgraded.encode(&c, &d).is_ok());
}
#[cfg(feature = "desktop")]
#[test]
fn journey_keyboard_and_release_mouse_reach_spell_and_both_target_sides() {
    use crate::{
        journey_desktop::battle_spell_key,
        pointer::{self, Action, Pointer, Screen},
    };
    let c = Catalog::builtin().unwrap();
    let d = WorldData::guards_fixture(false);
    let mut j = enter(&c, &d, false);
    caster(&mut j);
    let cp = j.battle.as_mut().unwrap();
    let mut row = 0;
    let mut cursor = 12;
    battle_spell_key(cp, 13, &mut row, &mut cursor).unwrap();
    assert_eq!(cp.controller.selected_spell(), Some(Spell::Fireball));
    let slot = cp.controller.spell_targets().unwrap()[0];
    cursor = slot + 1;
    assert!(
        battle_spell_key(cp, 13, &mut row, &mut cursor)
            .unwrap()
            .is_some()
    );
    let mut p = Pointer::default();
    let screen = Screen::BattleSpell { target: None };
    assert_eq!(p.event(screen, 0x401, 300, 200), None);
    assert_eq!(
        p.event(screen, 0x402, 300, 200),
        Some(Action::MagicChoice(0))
    );
    for ally in [true, false] {
        let [x, y] = crate::controller::POSITIONS[if ally { 0 } else { 6 }];
        assert_eq!(
            pointer::hit(Screen::BattleSpell { target: Some(ally) }, x + 10, y + 58),
            Some(Action::Target(if ally { 7 } else { 1 }))
        );
    }
}
