use super::*;
fn before<'a>(d: &WorldData, i: usize, facing: u8) -> (Journey<'a>, u16) {
    let s = sites()[i];
    let key = [0x4800, 0x5000, 0x4b00, 0x4d00][usize::from(facing - 1)];
    let mut j = Journey::new(d, 1);
    j.world.area = s.area;
    j.world.position = motion(s.position, key, 3, true).unwrap().0;
    (j, key)
}
fn strong(j: &mut Journey<'_>) {
    j.army[0].count = 1000;
    j.army[1] = Stack {
        unit: Some(UnitId::parse("native:02").unwrap()),
        count: 200,
    };
}
fn play(j: &mut Journey<'_>) {
    for _ in 0..1000 {
        let cp = j.battle.as_mut().unwrap();
        if cp.controller.battle().outcome().is_some() {
            return;
        }
        if let Some(a) = cp.controller.next_actor().unwrap() {
            if cp.controller.is_enemy_caster() {
                cp.controller.enemy_cast(&mut cp.rng).unwrap();
            } else {
                let target = if a.side == Side::Enemy {
                    cp.controller.enemy_target(&mut cp.rng).unwrap()
                } else {
                    cp.controller.legal_targets().unwrap()[0]
                };
                cp.controller.attack(target).unwrap();
            }
        }
    }
    panic!("battle budget")
}
#[test]
fn original_1176_entries_32_gains_and_20_retreats_match_scoped_rules() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::guards_fixture(false);
    let mut n = [0; 3];
    for line in include_str!("../guard-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<_> = line.split('\t').collect();
        let v = |i: usize| f[i].parse::<u16>().unwrap();
        match f[0] {
            "ENTER" => {
                let i = usize::from(v(1));
                let face = v(2) as u8;
                let mode = v(3);
                let phase = v(4);
                let eligible = matches!(face, 1 | 3);
                let site = sites()[i];
                if mode == 6 {
                    assert_eq!(phase, if eligible { 1 } else { 0 });
                    n[0] += 1;
                    continue;
                }
                let (mut j, key) = before(&d, i, face);
                if mode == 2 || mode == 5 {
                    j.army = [Stack::default(); 6];
                }
                if mode >= 4 {
                    j.guards.swords = [true; 8];
                }
                if mode == 3 {
                    j.guards.rows[i] = [Stack::default(); 6];
                }
                j.travel(&d, key, &c).unwrap();
                if !eligible {
                    assert_eq!(phase, 0);
                    assert!(j.guards.pending.is_none());
                } else if mode == 3 {
                    assert_eq!(phase, 1);
                    assert_eq!(j.guards.pending.unwrap().stage, Stage::Cleared);
                } else {
                    assert_eq!(j.guards.pending.unwrap().stage, Stage::Prompt);
                    assert_eq!(v(5), 1);
                    let result = j.choose_guard(&d, &c, mode != 0);
                    if site.final_guard && mode == 4 {
                        assert_eq!(phase, 4);
                        result.unwrap();
                        assert_eq!(j.guards.pending.unwrap().stage, Stage::Battle);
                    } else {
                        result.unwrap();
                        match phase {
                            0 => assert!(j.guards.pending.is_none()),
                            2 => assert_eq!(j.guards.pending.unwrap().stage, Stage::NoArmy),
                            3 => assert_eq!(j.guards.pending.unwrap().stage, Stage::Missing),
                            4 => assert!(j.battle.is_some()),
                            _ => panic!("phase"),
                        }
                    }
                }
                n[0] += 1;
            }
            "GAIN" => {
                let mut rng = OriginalRng { seed: 1 };
                let out = reward(
                    [1, 10000, u64::from(v(3)), 500, 100, 100],
                    v(1) as u8,
                    v(2) == 1,
                    Outcome::Win,
                    &mut rng,
                )
                .unwrap();
                assert_eq!((out[2], out[5]), (u64::from(v(4)), u64::from(v(6))));
                assert_eq!(rng.seed, 1);
                assert_eq!(out[0], 1);
                n[1] += 1;
            }
            "RETREAT" => {
                assert_eq!(
                    u64::from(v(2)) - retreat_loss(u64::from(v(2)), v(1)),
                    u64::from(v(3))
                );
                n[2] += 1;
            }
            _ => panic!("row"),
        }
    }
    assert_eq!(n, [1176, 32, 20]);
}
#[test]
fn forty_two_records_native_tables_caps_and_map_identity() {
    let d = WorldData::guards_fixture(false);
    validate_maps(&d).unwrap();
    assert_eq!(sites().iter().filter(|s| s.boss).count(), 8);
    assert_eq!(sites().iter().filter(|s| s.final_guard).count(), 1);
    for s in sites() {
        assert!(army_ok(&s.initial, true));
        assert!(s.initial[0].count > 0);
        assert!(!s.initial.iter().any(|v| v.count > 32767));
    }
    let mut rng = OriginalRng { seed: 1 };
    assert_eq!(
        reward(
            [1, 10000, 29999, 30000, 30000, 29999],
            7,
            true,
            Outcome::Win,
            &mut rng
        )
        .unwrap(),
        [1, 10000, 30000, 30000, 30000, 30000]
    );
}
#[test]
fn prompt_cancel_sideways_and_space_are_single_world_actions_after_confirmation() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    let (mut j, key) = before(&d, 0, 1);
    let steps = j.world.remaining;
    let rng = j.world.rng;
    j.travel(&d, key, &c).unwrap();
    assert_eq!((j.world.remaining, j.world.rng), (steps, rng));
    let raw = j.encode(&c, &d).unwrap();
    j = Journey::decode(&c, &d, &raw).unwrap();
    j.choose_guard(&d, &c, false).unwrap();
    assert_eq!(j.world.remaining, steps - 1);
    assert!(j.guards.pending.is_none());
    assert_eq!(j.guards.rows[0], sites()[0].initial);
    j.world.facing = 3;
    j.travel(&d, 0x3920, &c).unwrap();
    j.choose_guard(&d, &c, false).unwrap();
    assert_eq!(j.world.remaining, steps - 1);
}
#[test]
fn retreat_keeps_damaged_guard_cold_report_charges_once_and_reopens_latest_rows() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    let (mut j, key) = before(&d, 0, 1);
    strong(&mut j);
    j.travel(&d, key, &c).unwrap();
    j.choose_guard(&d, &c, true).unwrap();
    let cp = j.battle.as_mut().unwrap();
    cp.controller.next_actor().unwrap();
    let target = cp.controller.legal_targets().unwrap()[0];
    cp.controller.attack(target).unwrap();
    cp.controller.retreat().unwrap();
    let mid = j.encode(&c, &d).unwrap();
    let mut cold = Journey::decode(&c, &d, &mid).unwrap();
    j.finish(&c, &d, None).unwrap();
    cold.finish(&c, &d, None).unwrap();
    assert_eq!(j, cold);
    assert_ne!(j.guards.rows[0], sites()[0].initial);
    let remaining = j.guards.rows[0];
    let resources = j.resources;
    let seed = j.world.rng;
    let report = j.encode(&c, &d).unwrap();
    j = Journey::decode(&c, &d, &report).unwrap();
    assert_eq!(j.resources, resources);
    assert_eq!(j.world.rng, seed);
    j.close_guard(&d, &c).unwrap();
    j.world.facing = 1;
    j.travel(&d, 0x3920, &c).unwrap();
    j.choose_guard(&d, &c, true).unwrap();
    assert_eq!(j.enemy, remaining);
}
#[test]
fn boss_victory_uses_real_rounds_persists_sword_without_random_rewards_or_promotion() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    let (mut j, key) = before(&d, 1, 1);
    strong(&mut j);
    j.resources[1] = 10000;
    j.magic.book = true;
    j.resources[5] = 3;
    j.travel(&d, key, &c).unwrap();
    j.choose_guard(&d, &c, true).unwrap();
    play(&mut j);
    assert_eq!(j.finish(&c, &d, None).unwrap(), Outcome::Win);
    assert_eq!(j.resources, [1, 10000, 120, 500, 100, 4]);
    assert!(j.guards.swords[0]);
    assert_eq!(j.guards.rows[1], [Stack::default(); 6]);
    let raw = j.encode(&c, &d).unwrap();
    let mut cold = Journey::decode(&c, &d, &raw).unwrap();
    cold.close_guard(&d, &c).unwrap();
    cold.world.facing = 1;
    cold.travel(&d, 0x3920, &c).unwrap();
    assert_eq!(cold.guards.pending.unwrap().stage, Stage::Cleared);
    cold.close_guard(&d, &c).unwrap();
    assert_eq!(cold.resources, j.resources);
    assert!(cold.guards.swords[0]);
}
#[test]
fn loss_roam_or_origin_preserves_enemy_survivors_and_resets_origin_boat() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    for origin in [false, true] {
        let (mut j, key) = before(&d, 0, 1);
        j.army[0].count = 1;
        j.travel(&d, key, &c).unwrap();
        j.choose_guard(&d, &c, true).unwrap();
        play(&mut j);
        assert_eq!(
            j.battle.as_ref().unwrap().controller.battle().outcome(),
            Some(Outcome::Loss)
        );
        let enemy = compact(j.battle.as_ref().unwrap().controller.battle().rows()[1]);
        j.finish(&c, &d, Some(origin)).unwrap();
        assert_eq!(j.guards.rows[0], enemy);
        assert_eq!(j.army, [Stack::default(); 6]);
        assert_eq!(
            j.world.position,
            if origin {
                d.starts[0]
            } else {
                sites()[0].position
            }
        );
        if origin {
            assert_eq!((j.world.facing, j.world.boat), (3, 0));
        }
        assert_eq!(
            Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap(),
            j
        );
    }
}
#[test]
fn last_step_waits_for_guard_before_month_and_revisit_never_double_rewards() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    let (mut j, key) = before(&d, 0, 1);
    j.world.remaining = 1;
    j.travel(&d, key, &c).unwrap();
    assert!(j.month.pending.is_none());
    j.choose_guard(&d, &c, false).unwrap();
    assert!(j.month.pending.is_some());
    let raw = j.encode(&c, &d).unwrap();
    j = Journey::decode(&c, &d, &raw).unwrap();
    j.close_month(&d).unwrap();
    assert!(j.guards.pending.is_none());
    assert_eq!(j.world.remaining, 324);
}
#[test]
fn v13_migrates_and_guard_bad_source_rows_phases_flags_are_rejected() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    let (mut j, key) = before(&d, 0, 1);
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 16 - 8 - SUFFIX - crate::items::SUFFIX);
    raw[..8].copy_from_slice(b"8SJRN013");
    raw.extend(checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
    j.travel(&d, key, &c).unwrap();
    for n in 0..7 {
        let mut b = j.clone();
        match n {
            0 => b.guards.pending.as_mut().unwrap().site = 255,
            1 => b.guards.rows[0][0].count = 32768,
            2 => b.guards.rows[0][0].unit = Some(UnitId::parse("openkb:wolf").unwrap()),
            3 => b.world.position.x = 0,
            4 => b.guards.pending.as_mut().unwrap().stage = Stage::Battle,
            5 => b.guards.pending.as_mut().unwrap().before[3] += 1,
            _ => b.cue = Some(0),
        }
        assert!(b.encode(&c, &d).is_err(), "{n}");
    }
    let mut raw = j.encode(&c, &d).unwrap();
    let end = raw.len() - 8;
    raw[end - 57] = 42;
    let sum = checksum(&raw[..end]);
    raw[end..].copy_from_slice(&sum.to_le_bytes());
    assert!(Journey::decode(&c, &d, &raw).is_err());
}
#[test]
fn shore_yes_enters_guard_no_uses_original_missing_coordinate_empty_city_path() {
    let d = WorldData::guards_fixture(true);
    let c = Catalog::builtin().unwrap();
    for yes in [false, true] {
        let (mut j, key) = before(&d, 0, 1);
        j.world.boat = 2;
        let old = j.world.clone();
        j.travel(&d, key, &c).unwrap();
        assert_eq!(j.phase(), "shore");
        j.select_shore(yes).unwrap();
        j.finish_shore(&d, &c).unwrap();
        assert_eq!(
            j.guards.pending.unwrap().stage,
            if yes { Stage::Prompt } else { Stage::Refused }
        );
        let raw = j.encode(&c, &d).unwrap();
        j = Journey::decode(&c, &d, &raw).unwrap();
        j.close_guard(&d, &c).unwrap();
        assert_eq!(
            j.world.position,
            if yes {
                sites()[0].position
            } else {
                old.position
            }
        );
        assert_eq!(j.world.remaining, old.remaining - u16::from(yes));
        assert_eq!(j.world.boat, if yes { 0 } else { 2 });
        assert_eq!(j.guards.rows[0], sites()[0].initial);
    }
}
#[cfg(feature = "desktop")]
#[test]
fn keyboard_mouse_prompt_share_choice_and_reports_ignore_gameplay() {
    use crate::management_ui::{Manager, Page};
    use crate::pointer::{Action, Screen, hit};
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    let (mut j, key) = before(&d, 0, 1);
    j.army = [Stack::default(); 6];
    j.travel(&d, key, &c).unwrap();
    let mut ui = Manager::default();
    ui.sync(&j);
    assert_eq!(ui.page, Page::Guard);
    assert_eq!(ui.screen(), Some(Screen::Prompt));
    assert_eq!(hit(Screen::Prompt, 700, 900), Some(Action::Choice(true)));
    ui.key(13, &mut j, &c, &d);
    ui.sync(&j);
    assert_eq!(j.guards.pending.unwrap().stage, Stage::NoArmy);
    let before = j.clone();
    ui.key(32, &mut j, &c, &d);
    assert_eq!(j, before);
    ui.key(27, &mut j, &c, &d);
    assert!(j.guards.pending.is_none());
}

fn final_army(j: &mut Journey<'_>) {
    j.army = std::array::from_fn(|i| Stack {
        unit: Some(UnitId::parse(&format!("native:{:02}", [19, 20, 25, 3, 24, 18][i])).unwrap()),
        count: [1000, 600, 500, 1000, 600, 20][i],
    });
    j.guards.swords = [true; 8];
}
#[test]
fn final_win_enters_ending_before_reward_month_and_world_tail() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    let (mut j, key) = before(&d, 4, 1);
    final_army(&mut j);
    j.world.remaining = 1;
    let resources = j.resources;
    let initial_npc = j.guards.rows[4];
    j.travel(&d, key, &c).unwrap();
    j.choose_guard(&d, &c, true).unwrap();
    assert_eq!(j.enemy, initial_npc);
    let checkpoint = j.encode(&c, &d).unwrap();
    j = Journey::decode(&c, &d, &checkpoint).unwrap();
    play(&mut j);
    assert_eq!(
        j.battle.as_ref().unwrap().controller.battle().outcome(),
        Some(Outcome::Win)
    );
    let rng = j.battle.as_ref().unwrap().rng;
    j.finish(&c, &d, None).unwrap();
    assert_eq!(j.phase(), "ending");
    assert_eq!(j.resources, resources);
    assert_eq!(j.world.remaining, 1);
    assert_eq!(j.month.months, 0);
    assert_eq!(j.world.rng, rng);
    assert_eq!(j.battles, 1);
    assert_eq!(j.guards.rows[4], [Stack::default(); 6]);
    assert!(j.battle.is_none() && j.guards.pending.is_none());
    assert!(j.travel(&d, key, &c).is_err());
    assert!(j.finish(&c, &d, None).is_err());
    j.guards.ending = Some(crate::ending::Progress {
        elapsed_ms: 23945,
        hd: false,
    });
    j.world.font = 1;
    let raw = j.encode(&c, &d).unwrap();
    assert_eq!(&raw[..8], b"8SJRN017");
    let cold = Journey::decode(&c, &d, &raw).unwrap();
    assert_eq!(cold, j);
    for mode in 0..6 {
        let mut bad = j.clone();
        match mode {
            0 => bad.guards.ending.as_mut().unwrap().elapsed_ms = crate::ending::DURATION + 1,
            1 => bad.guards.swords[0] = false,
            2 => bad.guards.rows[4] = initial_npc,
            3 => bad.world.position.x = 1,
            4 => bad.enemy[0] = initial_npc[0],
            _ => {
                bad.guards.pending = Some(Pending {
                    site: 4,
                    key,
                    stage: Stage::Cleared,
                    yes: true,
                    before: resources,
                    reward_seed: bad.world.rng.seed,
                })
            }
        };
        assert!(bad.encode(&c, &d).is_err(), "{mode}");
    }
    let mut bad = raw.clone();
    let n = bad.len();
    bad[n - 9 - crate::items::SUFFIX] = 2;
    let h = checksum(&bad[..n - 8]);
    bad[n - 8..].copy_from_slice(&h.to_le_bytes());
    assert!(Journey::decode(&c, &d, &bad).is_err());
    j.guards.ending.as_mut().unwrap().elapsed_ms = crate::ending::DURATION;
    assert!(j.encode(&c, &d).is_ok());
}
#[test]
fn final_retreat_and_loss_keep_guard_rules_and_do_not_start_ending() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    for retreat in [true, false] {
        let (mut j, key) = before(&d, 4, 1);
        j.guards.swords = [true; 8];
        let original = j.guards.rows[4];
        j.travel(&d, key, &c).unwrap();
        j.choose_guard(&d, &c, true).unwrap();
        if retreat {
            j.battle.as_mut().unwrap().controller.retreat().unwrap();
        } else {
            play(&mut j)
        }
        let outcome = j
            .battle
            .as_ref()
            .unwrap()
            .controller
            .battle()
            .outcome()
            .unwrap();
        assert_eq!(
            outcome,
            if retreat {
                Outcome::Retreat
            } else {
                Outcome::Loss
            }
        );
        j.finish(&c, &d, (!retreat).then_some(true)).unwrap();
        assert!(j.guards.ending.is_none());
        assert!(j.encode(&c, &d).is_ok());
        if retreat {
            assert_eq!(j.guards.rows[4], original);
            assert_eq!(j.guards.pending.unwrap().stage, Stage::Retreat);
            assert!(j.resources[3] < 500);
        } else {
            assert_eq!(j.army, [Stack::default(); 6]);
        }
    }
}
#[test]
fn real_v14_layout_migrates_without_starting_an_ending() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    let j = Journey::new(&d, 1);
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 16 - 8 - 9 - crate::items::SUFFIX);
    raw[..8].copy_from_slice(b"8SJRN014");
    raw.extend(checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
}
