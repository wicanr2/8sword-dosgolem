use crate::{
    battle::{Modifiers, Side, Stack},
    catalog::{Catalog, UnitId},
    controller::{Checkpoint, Controller, EnemyConfig, OriginalRng, ViewState},
    rules::Mode,
};
fn archer_front<'a>(catalog: &'a Catalog, side: Side, mode: Mode) -> Controller<'a> {
    let mut rows = [[Stack::default(); 6]; 2];
    for (raw, id) in ["native:21", "native:06", "native:01"].iter().enumerate() {
        rows[1 - side.index()][raw] = Stack {
            unit: Some(UnitId::parse(id).unwrap()),
            count: 100,
        };
    }
    for (raw, id) in [
        "native:10",
        "native:12",
        "native:24",
        "native:03",
        "native:21",
        "native:06",
    ]
    .iter()
    .enumerate()
    {
        rows[side.index()][raw] = Stack {
            unit: Some(UnitId::parse(id).unwrap()),
            count: if raw == 3 { 50 } else { 1 },
        };
    }
    let book = crate::spells::SpellBook {
        enabled: true,
        charges: [10; 8],
        stat_26ae: 0,
        stat_26b0: 0,
    };
    Controller::with_enemy_spells(
        catalog,
        rows,
        side,
        Modifiers::default(),
        Some(book),
        EnemyConfig {
            stat_26ae: 0,
            shifted_alias: 0,
        },
    )
    .unwrap()
    .with_rule_mode(mode)
    .unwrap()
}
#[test]
fn both_sides_scale_before_hp_commit_and_lock_after_actor() {
    let catalog = Catalog::builtin().unwrap();
    for side in [Side::Player, Side::Enemy] {
        for mode in [Mode::Native, Mode::Formation, Mode::Tactics] {
            let mut c = archer_front(&catalog, side, mode);
            loop {
                let a = c.next_actor().unwrap().unwrap();
                if a.raw == 3 {
                    assert_eq!(a.slot, 2);
                    break;
                }
                if side == Side::Player {
                    c.skip().unwrap();
                } else {
                    let target = c.legal_targets().unwrap()[0];
                    c.attack(target).unwrap();
                }
            }
            assert!(
                c.clone()
                    .with_rule_mode(if mode == Mode::Native {
                        Mode::Tactics
                    } else {
                        Mode::Native
                    })
                    .is_err()
            );
            let before = c.battle().hp()[1 - side.index()][2];
            c.attack(2).unwrap();
            let amount = [400, 320, 240][mode.index()];
            assert_eq!(before - c.battle().hp()[1 - side.index()][2], amount);
            let expected = 100 - amount / 25 - u64::from(side == Side::Player);
            assert_eq!(
                u64::from(c.battle().rows()[1 - side.index()][2].count),
                expected
            );
        }
    }
}
#[test]
fn enemy_spells_do_not_acquire_ordinary_damage_scaling() {
    let catalog = Catalog::builtin().unwrap();
    for seed in 1..=64 {
        let mut expected = None;
        for mode in [Mode::Native, Mode::Formation, Mode::Tactics] {
            let mut rows = [[Stack::default(); 6]; 2];
            for (side, raw, id, count) in [
                (0, 0, "native:01", 100),
                (0, 1, "native:21", 100),
                (1, 0, "native:12", 3),
            ] {
                rows[side][raw] = Stack {
                    unit: Some(UnitId::parse(id).unwrap()),
                    count,
                };
            }
            let mut c = Controller::with_enemy_spells(
                &catalog,
                rows,
                Side::Enemy,
                Modifiers::default(),
                None,
                EnemyConfig {
                    stat_26ae: 0,
                    shifted_alias: 0,
                },
            )
            .unwrap()
            .with_rule_mode(mode)
            .unwrap();
            c.next_actor().unwrap();
            assert!(c.is_enemy_caster());
            let mut rng = OriginalRng { seed };
            let action = c.enemy_cast(&mut rng).unwrap();
            let actual = (action, rng, c.battle().clone(), *c.remaining());
            if let Some(e) = &expected {
                assert_eq!(&actual, e);
            } else {
                expected = Some(actual);
            }
        }
    }
}
#[test]
fn non_native_names_do_not_inherit_traits_and_each_rounding_is_visible() {
    let f = [2, 1, 0];
    assert_eq!(
        crate::rules::scale(Mode::Tactics, 0, 3, 10, 0, 1, 2, f).apply(9),
        4
    );
    assert_eq!(
        crate::rules::scale(Mode::Tactics, 0, 0, 10, 0, 0, 2, f).apply(9),
        9
    );
    assert_eq!(
        crate::rules::scale(Mode::Tactics, 3, 3, 10, 3, 1, 2, f).apply(9),
        9
    );
}
#[test]
fn battle_file_restores_locked_mode_and_raw_legacy_remains_native() {
    let catalog = Catalog::builtin().unwrap();
    let dir = std::env::temp_dir().join(format!("8s-rules-battle-{}", std::process::id()));
    std::fs::create_dir(&dir).unwrap();
    let mut c = archer_front(&catalog, Side::Enemy, Mode::Tactics);
    c.next_actor().unwrap();
    let cp = Checkpoint {
        controller: c,
        rng: OriginalRng { seed: 1 },
        view: ViewState {
            scenario: 10,
            ..ViewState::default()
        },
    };
    crate::checkpoint_store::save(&dir, &cp).unwrap();
    let cold = crate::checkpoint_store::load(&dir, &catalog).unwrap();
    assert_eq!(cold, cp);
    assert_eq!(
        Checkpoint::decode(&catalog, &cp.encode().unwrap())
            .unwrap()
            .controller
            .rules(),
        Mode::Native
    );
    std::fs::write(dir.join("battle.chk.rules.json"), b"{}").unwrap();
    assert!(crate::checkpoint_store::load(&dir, &catalog).is_err());
    std::fs::remove_dir_all(dir).unwrap();
}
#[test]
fn world_mode_survives_cold_and_confirmed_new_game_replaces_marker() {
    let c = Catalog::builtin().unwrap();
    let d = crate::world::WorldData::flat_fixture();
    let dir = std::env::temp_dir().join(format!("8s-rules-world-{}", std::process::id()));
    std::fs::create_dir(&dir).unwrap();
    let mut j = crate::journey::Journey::new(&d, 1);
    j.set_rules(Mode::Formation).unwrap();
    j.save(&dir, &c, &d).unwrap();
    assert_eq!(crate::journey::Journey::load(&dir, &c, &d).unwrap(), j);
    let raw = std::fs::read(dir.join("journey.chk")).unwrap();
    assert_eq!(
        crate::journey::Journey::decode(&c, &d, &raw).unwrap().rules,
        Mode::Native
    );
    let reset = crate::start::new_game_rules(&c, &d, &dir, 2, 0, true, Mode::Native).unwrap();
    assert_eq!(crate::journey::Journey::load(&dir, &c, &d).unwrap(), reset);
    std::fs::remove_file(dir.join("journey.chk.rules.json")).unwrap();
    assert_eq!(
        crate::journey::Journey::load(&dir, &c, &d).unwrap().rules,
        Mode::Native
    );
    std::fs::remove_dir_all(dir).unwrap();
}

#[test]
fn skipped_first_actor_does_not_unlock_rules() {
    let catalog = Catalog::builtin().unwrap();
    let mut c = archer_front(&catalog, Side::Player, Mode::Formation);
    c.next_actor().unwrap();
    c.skip().unwrap();
    assert!(c.with_rule_mode(Mode::Native).is_err());
}
