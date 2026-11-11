use super::*;
use crate::{
    controller::OriginalRng,
    jump_spell::Jump,
    world::{WorldState, motion},
};
#[test]
fn actual_map_validation_rejects_missing_exits_and_unsafe_starts() {
    assert!(validate(&WorldData::jump_fixture(1)).is_err());
    let mut d = WorldData::exits_fixture();
    d.starts[1] = Position { x: 0, y: 0 };
    assert!(validate(&d).is_err());
    validate(&WorldData::exits_fixture()).unwrap();
}
#[test]
fn all_468_original_exit_clock_vectors_follow_normal_travel_and_save() {
    let d = WorldData::exits_fixture();
    let c = Catalog::builtin().unwrap();
    validate(&d).unwrap();
    let mut count = 0;
    for line in include_str!("../exits-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<u16> = line.split('\t').map(|s| s.parse().unwrap()).collect();
        let mut j = Journey::new(&d, 1);
        j.world.area = f[0] as u8;
        j.world.position = motion(
            Position {
                x: f[1] as u8,
                y: f[2] as u8,
            },
            f[4],
            3,
            true,
        )
        .unwrap()
        .0;
        j.world.remaining = f[5];
        j.world.boat = f[6] as u8;
        let before = j.clone();
        assert_eq!(j.travel(&d, f[4], &c).unwrap(), None);
        assert_eq!(
            (
                j.world.area,
                j.world.position.x,
                j.world.position.y,
                j.world.facing,
                j.world.boat
            ),
            (f[7] as u8, f[8] as u8, f[9] as u8, f[10] as u8, f[12] as u8),
            "{line}"
        );
        if f[11] == 0 {
            assert_eq!(j.phase(), "monthly");
            assert_eq!(j.world.remaining, 324);
            // Local exit vectors stopped at the month boundary. The separately
            // observed month body consumes two calls before the report.
            let mut rng = before.world.rng;
            rng.next15();
            rng.next15();
            assert_eq!(j.world.rng, rng);
            j = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
            j.close_month(&d).unwrap();
        } else {
            assert_eq!(j.world.remaining, f[11]);
        }
        assert_eq!(j.world.actions, before.world.actions + 1);
        assert_eq!(j.army, before.army);
        assert_eq!(
            Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap(),
            j
        );
        count += 1;
    }
    assert_eq!(count, 468);
}
#[test]
fn original_540_encounter_prefixes_ignore_jump_flag_and_match_rng_consumption() {
    let mut count = 0;
    for line in include_str!("../jump-encounter-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<u32> = line.split('\t').map(|s| s.parse().unwrap()).collect();
        let d = WorldData::jump_fixture(f[2] as u8);
        let mut s = WorldState::new(&d, f[3]);
        s.rank = f[1] as u8;
        s.facing = 4;
        let mut rng = s.rng;
        assert_eq!(rng.next15(), f[4] as u16);
        let cue = rng.next15() / 2341;
        let result = s.encounter_tail(&d, false).unwrap();
        let mut expected = OriginalRng { seed: f[3] };
        for _ in 0..f[8] {
            expected.next15();
        }
        assert_eq!(s.rng, expected, "{line}");
        assert_eq!(s.actions, 1);
        if f[6] == 1 {
            assert_eq!(result, WalkResult::Boundary(Boundary::Encounter(cue as u8)));
            assert_eq!(cue, f[7] as u16);
        } else {
            assert_eq!(result, WalkResult::Committed { blocked: false });
        }
        count += 1;
    }
    assert_eq!(count, 540);
}
#[test]
fn exits_preserve_exploration_and_boat_but_clear_only_reloaded_bridges() {
    let d = WorldData::exits_fixture();
    let c = Catalog::builtin().unwrap();
    for e in exits() {
        let mut j = Journey::new(&d, 1);
        j.magic.book = true;
        j.resources[5] = 3;
        j.magic.bridges = vec![0, 5600, 11200, 16800, 22400, 28000, 33600, 39200];
        j.world.area = e.area;
        j.world.position = e.position;
        j.world.boat = 1;
        j.world.explored.iter_mut().for_each(|s| s.fill(0));
        j.travel(&d, 0x3920, &c).unwrap();
        assert_eq!(j.world.remaining, 324);
        assert_eq!(j.world.boat, 1);
        assert_eq!(j.world.facing, 3);
        assert_eq!(j.magic.bridges.len(), 6);
        assert!(
            j.magic
                .bridges
                .iter()
                .all(|i| *i / 5600 != u16::from(e.area) && *i / 5600 != u16::from(e.destination()))
        );
        let bits = |a: u8| {
            j.world.explored[usize::from(a)]
                .iter()
                .map(|v| v.count_ones())
                .sum::<u32>()
        };
        assert_eq!(bits(e.area), if e.tile == 49 { 9 } else { 0 });
        assert_eq!(bits(e.destination()), 9);
        j.encode(&c, &d).unwrap();
        let mut water = Journey::new(&d, 1);
        water.world.area = e.area;
        water.world.position = e.position;
        water.world.boat = 2;
        let old = water.clone();
        assert_eq!(
            water.travel(&d, 0x3920, &c).unwrap(),
            Some(Boundary::BoatExit)
        );
        assert_eq!(water, old);
    }
}
#[test]
fn flying_encounter_cold_prompt_and_battle_pause_then_resume_old_direction() {
    let d = WorldData::jump_fixture(15);
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 0x5578f641);
    j.magic.book = true;
    j.magic.charges[3] = 1;
    j.resources[5] = 3;
    j.cast_jump().unwrap();
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.phase(), "prompt");
    assert_eq!(j.world.position, Position { x: 41, y: 40 });
    assert_eq!(j.world.remaining, 324);
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    assert_eq!(cold, j);
    assert!(cold.advance_jump(&d).is_err());
    assert_eq!(cold, j);
    for s in [&mut j, &mut cold] {
        s.choose(&c, true).unwrap();
        assert_eq!(s.phase(), "battle");
        let raw = s.encode(&c, &d).unwrap();
        *s = Journey::decode(&c, &d, &raw).unwrap();
        assert!(s.advance_jump(&d).is_err());
        s.battle.as_mut().unwrap().controller.next_actor().unwrap();
        s.battle.as_mut().unwrap().controller.retreat().unwrap();
        s.finish(&c, &d, None).unwrap();
        assert_eq!(s.phase(), "jump-flight");
        s.advance_jump(&d).unwrap();
        assert_eq!(s.world.position, Position { x: 42, y: 40 });
        assert_eq!(s.travel_spell.jump, Jump::Flying { key: 0x4d00 });
        assert_eq!(s.world.actions, 2);
    }
    assert_eq!(j, cold);
}

#[test]
fn flying_loss_origin_lands_and_refusal_resumes_without_spending_a_step() {
    use crate::battle::{Outcome, Side};
    let d = WorldData::magic_fixture(5);
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 0x5578f641);
    j.magic.book = true;
    j.magic.charges[3] = 1;
    j.resources[5] = 3;
    j.army[0].count = 1;
    j.cast_jump().unwrap();
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.phase(), "prompt");
    let mut refusal = j.clone();
    refusal.choose(&c, false).unwrap();
    assert_eq!(refusal.phase(), "jump-flight");
    assert_eq!(refusal.world.remaining, 324);
    j.choose(&c, true).unwrap();
    for _ in 0..100 {
        let cp = j.battle.as_mut().unwrap();
        if cp.controller.battle().outcome().is_some() {
            break;
        }
        if let Some(a) = cp.controller.next_actor().unwrap() {
            if a.side == Side::Player {
                cp.controller.skip().unwrap();
            } else if cp.controller.is_enemy_caster() {
                cp.controller.enemy_cast(&mut cp.rng).unwrap();
            } else {
                let t = cp.controller.enemy_target(&mut cp.rng).unwrap();
                cp.controller.attack(t).unwrap();
            }
        }
    }
    assert_eq!(j.finish(&c, &d, Some(true)).unwrap(), Outcome::Loss);
    assert_eq!(j.phase(), "world");
    assert_eq!(j.travel_spell.jump, Jump::Idle);
    assert_eq!(j.world.position, d.starts[0]);
    j.encode(&c, &d).unwrap();
}

#[cfg(feature = "desktop")]
#[test]
fn flying_ui_yields_to_prompt_and_battle_then_reopens_flight() {
    use crate::management_ui::{Manager, Page};
    let d = WorldData::jump_fixture(15);
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 0x5578f641);
    j.magic.book = true;
    j.magic.charges[3] = 1;
    j.resources[5] = 3;
    j.cast_jump().unwrap();
    let mut ui = Manager::default();
    j.travel(&d, 0x4d00, &c).unwrap();
    ui.page = Page::Flight;
    ui.sync(&j);
    assert_eq!(ui.page, Page::World);
    j.choose(&c, true).unwrap();
    ui.sync(&j);
    assert_eq!(ui.page, Page::World);
    j.battle.as_mut().unwrap().controller.next_actor().unwrap();
    j.battle.as_mut().unwrap().controller.retreat().unwrap();
    j.finish(&c, &d, None).unwrap();
    ui.sync(&j);
    assert_eq!(ui.page, Page::Flight);
}
