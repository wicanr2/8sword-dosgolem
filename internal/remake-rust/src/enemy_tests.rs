use super::*;
use crate::battle::Stack;
use crate::catalog::UnitId;
fn row(id: &str, count: u32) -> Stack {
    Stack {
        unit: Some(UnitId::parse(id).unwrap()),
        count,
    }
}
fn setup(c: &Catalog, kind: u8) -> Controller<'_> {
    let mut rows = [[Stack::default(); 6]; 2];
    rows[0][0] = row("native:01", 70);
    rows[0][1] = row("native:06", 30);
    rows[1][0] = row(&format!("native:{kind:02}"), 50);
    rows[1][1] = row("native:16", 10);
    let mut ctl = Controller::with_enemy_spells(
        c,
        rows,
        Side::Enemy,
        Modifiers::default(),
        None,
        EnemyConfig {
            stat_26ae: 4,
            shifted_alias: 0,
        },
    )
    .unwrap();
    ctl.next_actor().unwrap();
    ctl.attack(0).unwrap();
    ctl.next_actor().unwrap();
    assert!(ctl.is_enemy_caster());
    ctl
}
#[test]
fn matches_go_models_and_thirteen_original_pairs() {
    assert_eq!(
        crate::replay::check_enemy(
            &Catalog::builtin().unwrap(),
            include_str!("../enemy-reference.tsv")
        ),
        Ok((384, 13))
    );
}
#[test]
fn dispatch_distribution_preserves_unreachable_eighth_and_fallback() {
    let mut n = [0; 8];
    for roll in 0..340 {
        n[enemy_selector(roll).index()] += 1;
    }
    assert_eq!(n, [110, 50, 70, 50, 30, 10, 20, 0]);
    for roll in 0..32768 {
        assert_ne!(enemy_selector(roll), Spell::Quake);
    }
}
#[test]
fn freeze_aliases_and_clone_return_to_scheduler_without_charges() {
    let cat = Catalog::builtin().unwrap();
    let mut c = setup(&cat, 10);
    let hp = *c.battle().hp();
    c.enemy_cast_choice(Spell::Freeze, None, None).unwrap();
    assert_eq!(c.remaining()[1], [1, 1, 1, 1, 1, 5]);
    assert_eq!(c.battle().hp(), &hp);
    let actor = c.next_actor().unwrap().unwrap();
    assert_eq!(actor.raw, 1);
    c.attack(0).unwrap();
    c.next_actor().unwrap();
    assert!(c.is_enemy_caster());
    c.enemy_cast_choice(Spell::Clone, Some(5), None).unwrap();
    assert_eq!(c.battle().rows()[1][0].count, 70);
    assert!(c.spell_book().is_none());
    assert_eq!(c.enemy_returns(), 2);
    assert_eq!(c.spell_returns(), 0);
}
#[test]
fn shifted_guard_admits_empty_target_and_uses_explicit_combined_alias() {
    let cat = Catalog::builtin().unwrap();
    let mut c = setup(&cat, 12);
    assert_eq!(c.enemy_spell_targets(Spell::Halve).unwrap(), vec![0, 1, 2]);
    let hp = *c.battle().hp();
    let r = c.enemy_cast_choice(Spell::Halve, Some(2), None).unwrap();
    assert_eq!(r.effects[0].before, 0);
    assert_eq!(r.effects[0].after, 0);
    assert_eq!(r.effects[0].amount, 1);
    assert_eq!(r.effects[0].display, vec![0]);
    assert_eq!(c.battle().hp(), &hp);
    for alias in 0..12 {
        let mut c = setup(&cat, 10);
        c.enemy_config.as_mut().unwrap().shifted_alias = alias;
        assert_eq!(
            c.enemy_spell_targets(Spell::Halve).unwrap().contains(&0),
            c.battle().rows()[usize::from(alias / 6)][usize::from(alias % 6)].count > 0
        );
    }
}
#[test]
fn invalid_phase_target_gate_and_overflow_do_not_partially_commit() {
    let cat = Catalog::builtin().unwrap();
    let mut c = setup(&cat, 10);
    for (s, t, g) in [
        (Spell::Fireball, Some(6), None),
        (Spell::Assassination, Some(0), None),
        (Spell::Assassination, Some(0), Some(50)),
        (Spell::Thunder, Some(0), None),
        (Spell::Clone, Some(4), None),
    ] {
        let old = c.clone();
        assert!(c.enemy_cast_choice(s, t, g).is_err());
        assert_eq!(c, old);
    }
    let old = c.clone();
    assert!(c.attack(0).is_err());
    assert_eq!(c, old);
    c.remaining[1][5] = 65534;
    let old = c.clone();
    assert!(c.enemy_cast_choice(Spell::Freeze, None, None).is_err());
    assert_eq!(c, old);
    let mut c = setup(&cat, 10);
    c.battle.spell_counts(&[(Side::Player, 0, 10923)]).unwrap();
    let old = c.clone();
    assert!(c.enemy_cast_choice(Spell::Quake, None, None).is_err());
    assert_eq!(c, old);
}
#[test]
fn natural_enemy_new_units_death_and_three_ordinary_actions_win() {
    let cat = Catalog::builtin().unwrap();
    let mut rows = [[Stack::default(); 6]; 2];
    rows[0][0] = row("native:01", 74);
    rows[0][1] = row("openkb:wolf", 2);
    rows[0][2] = row("openkb:arcr", 2);
    rows[1][0] = row("native:12", 3);
    rows[1][1] = row("native:16", 10);
    let mut c = Controller::with_enemy_spells(
        &cat,
        rows,
        Side::Enemy,
        Modifiers::default(),
        None,
        EnemyConfig {
            stat_26ae: 4,
            shifted_alias: 0,
        },
    )
    .unwrap();
    let mut rng = OriginalRng { seed: 1 };
    for _ in 0..20 {
        let Some(a) = c.next_actor().unwrap() else {
            break;
        };
        if c.is_enemy_caster() {
            let old = c.clone();
            let seed = rng;
            let r = c.enemy_cast(&mut rng).unwrap();
            let mut replay = old;
            let mut rr = seed;
            assert_eq!(replay.enemy_cast(&mut rr).unwrap(), r);
            assert_eq!(rr, rng);
            assert_eq!(replay, c);
            if c.enemy_returns() == 1 {
                assert_eq!(r.spell, Spell::Thunder);
                assert_eq!(r.effects.len(), 3);
            } else {
                assert_eq!(r.spell, Spell::Exorcism);
                assert!(r.effects.is_empty());
            }
        } else {
            let target = if a.side == Side::Enemy {
                c.enemy_target(&mut rng).unwrap()
            } else {
                c.legal_targets().unwrap()[0]
            };
            c.attack(target).unwrap();
        }
    }
    assert_eq!(c.battle().outcome(), Some(Outcome::Win));
    assert_eq!(c.battle().sequence(), 3);
    assert_eq!(
        c.battle().rows()[0]
            .iter()
            .map(|s| s.count)
            .collect::<Vec<_>>(),
        vec![71, 0, 0, 0, 0, 0]
    );
    assert_eq!(c.enemy_returns(), 2);
}
