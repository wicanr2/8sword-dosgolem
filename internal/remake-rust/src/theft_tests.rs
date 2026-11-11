use super::*;
use crate::{
    catalog::{Catalog, UnitId},
    jump_spell::Jump,
    media_assets::checksum,
    world::{Position, WorldData},
};
const SEED: u32 = 0x5578f641; // Inverse LCG, first next15=1000. Fixed before action.
fn before_month_seed() -> u32 {
    // Invert exactly the two independently observed month-end calls, keeping
    // the existing theft comparison point fixed. No search or reroll.
    let previous = |n: u32| n.wrapping_sub(2531011).wrapping_mul(0xb9b33155);
    let seed = previous(previous(SEED));
    let mut rng = crate::controller::OriginalRng { seed };
    rng.next15();
    rng.next15();
    assert_eq!(rng.seed, SEED);
    seed
}
fn empty<'a>(d: &WorldData) -> Journey<'a> {
    let mut j = Journey::new(d, SEED);
    j.army = [Stack::default(); 6];
    j
}
#[test]
fn original_286_losses_and_18_six_slot_scans_match() {
    let (mut amounts, mut scans) = (0, 0);
    for line in include_str!("../theft-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<_> = line.split('\t').collect();
        let n = |i: usize| f[i].parse::<u64>().unwrap();
        match f[0] {
            "LOSS" => {
                let amount = loss(n(2), n(1) as u16).unwrap();
                assert_eq!((n(2) - amount, amount, n(5)), (n(3), n(4), 1), "{line}");
                amounts += 1;
            }
            "ARMY" => {
                let mut a = [Stack::default(); 6];
                if n(2) > 0 {
                    a[n(1) as usize] = Stack {
                        unit: Some(UnitId::parse("native:01").unwrap()),
                        count: n(2) as u32,
                    };
                }
                assert_eq!(has_troops(&a), n(3) == 1, "{line}");
                scans += 1;
            }
            _ => panic!("unknown oracle row"),
        }
    }
    assert_eq!((amounts, scans), (286, 18));
    assert!(loss(30001, 0).is_err());
    assert!(loss(0, 32768).is_err());
}
#[test]
fn empty_encounter_spends_third_roll_once_even_for_zero_gold_and_normal_army_unchanged() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    for gold in [0, 1, 75, 500, 30000] {
        let mut j = empty(&d);
        j.resources[3] = gold;
        let mut rng = j.world.rng;
        assert_eq!(rng.next15(), 1000);
        let cue = (rng.next15() / 2341) as u8;
        let amount = loss(gold, rng.next15()).unwrap();
        assert_eq!(j.travel(&d, 0x3920, &c).unwrap(), None);
        assert_eq!(j.phase(), "theft");
        assert_eq!(j.theft.unwrap().cue, cue);
        assert_eq!(j.theft.unwrap().amount(), amount);
        assert_eq!(j.resources[3], gold - amount);
        assert_eq!(j.world.rng, rng);
        assert_eq!(j.world.actions, 1);
        assert_eq!(j.world.remaining, 324);
        assert!(j.battle.is_none());
        j.encode(&c, &d).unwrap();
    }
    let mut normal = Journey::new(&d, SEED);
    let mut r = normal.world.rng;
    r.next15();
    r.next15();
    normal.travel(&d, 0x3920, &c).unwrap();
    assert_eq!(normal.phase(), "prompt");
    assert!(normal.theft.is_none());
    assert_eq!(normal.world.rng, r);
    assert_eq!(normal.resources[3], 500);
}
#[test]
fn pending_cold_confirm_does_not_charge_or_advance_and_v11_shape_migrates() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = empty(&d);
    let mut old = j.encode(&c, &d).unwrap();
    old.truncate(old.len() - 9 - 1 - crate::guards::SUFFIX - crate::items::SUFFIX);
    old[..8].copy_from_slice(b"8SJRN011");
    old.extend(checksum(&old).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &old).unwrap(), j);
    j.travel(&d, 0x4d00, &c).unwrap();
    let raw = j.encode(&c, &d).unwrap();
    let mut cold = Journey::decode(&c, &d, &raw).unwrap();
    assert_eq!(cold, j);
    let before = j.clone();
    assert!(cold.travel(&d, 0x4b00, &c).is_err());
    assert_eq!(cold, before);
    for s in [&mut j, &mut cold] {
        let world = s.world.clone();
        let resources = s.resources;
        s.close_theft().unwrap();
        assert_eq!(s.world, world);
        assert_eq!(s.resources, resources);
        assert!(s.close_theft().is_err());
        s.encode(&c, &d).unwrap();
    }
    assert_eq!(j, cold);
}
#[test]
fn event_return_routes_share_empty_army_receiver() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::special_shore_fixture();
    for kind in 0..4 {
        let mut j = empty(&d);
        match kind {
            0 => {
                let s = crate::world_magic::shops()[0];
                j.world.area = s.area;
                j.world.position = Position { x: s.x, y: s.y };
                j.magic.shop = Some(crate::world_magic::PendingShop {
                    index: 0,
                    moved: false,
                });
                j.close_magic_shop(&c, &d).unwrap();
            }
            1 => {
                let i = crate::management::camps()
                    .iter()
                    .enumerate()
                    .find(|(i, s)| {
                        s.kind > 0
                            && d.tile(s.area, Position { x: s.x, y: s.y }).unwrap()
                                == 54 + (i / 24) as u8
                    })
                    .unwrap()
                    .0;
                let s = crate::management::camps()[i];
                j.world.area = s.area;
                j.world.position = Position { x: s.x, y: s.y };
                j.camps.pending = Some(i);
                j.close_camp(&d, &c).unwrap();
            }
            2 => {
                let s = crate::treasure::sites()[0];
                j.world.area = s.area;
                j.world.position = Position { x: s.x, y: s.y };
                j.treasure.pending = Some(crate::treasure::Pending {
                    index: 0,
                    choice: 1,
                    moved: false,
                });
                j.finish_treasure(&c, &d, true).unwrap();
            }
            _ => {
                j.world.rng.seed = before_month_seed();
                j.world.remaining = 1;
                j.begin_month(&c, &d, 1).unwrap();
                j.close_month(&d).unwrap();
            }
        }
        // Each selected facing has a plain/water (<47) next tile in this fixture.
        assert_eq!(j.phase(), "theft", "route{kind}");
        j.encode(&c, &d).unwrap();
    }
    let d = WorldData::flat_fixture();
    let mut j = empty(&d);
    j.world.boat = 2;
    j.travel(&d, 0x4d00, &c).unwrap();
    j.select_shore(false).unwrap();
    j.finish_shore(&d, &c).unwrap();
    assert_eq!(j.phase(), "theft");
    let d = WorldData::exits_fixture();
    let mut j = empty(&d);
    j.world.position = Position { x: 2, y: 64 };
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.phase(), "theft");
    assert_eq!(j.world.area, 1);
}
#[test]
fn flying_theft_pauses_then_resumes_old_direction_without_recharge() {
    let d = WorldData::jump_fixture(15);
    let c = Catalog::builtin().unwrap();
    let mut j = empty(&d);
    j.magic.book = true;
    j.resources[5] = 3;
    j.magic.charges[3] = 1;
    j.cast_jump().unwrap();
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.phase(), "theft");
    assert_eq!(j.travel_spell.jump, Jump::Flying { key: 0x4d00 });
    let old = j.clone();
    assert!(j.advance_jump(&d).is_err());
    assert_eq!(j, old);
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    cold.close_theft().unwrap();
    assert_eq!(cold.phase(), "jump-flight");
    cold.advance_jump(&d).unwrap();
    assert_eq!(cold.world.position.x, 42);
    assert_eq!(cold.world.remaining, 324);
    assert_eq!(cold.magic.charges[3], 0);
}
#[test]
fn disbanded_monthly_army_can_be_robbed_after_confirmation() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, before_month_seed());
    j.resources[3] = 0;
    j.resources[2] = 0;
    j.world.remaining = 1;
    j.begin_month(&c, &d, 1).unwrap();
    assert!(!has_troops(&j.army));
    j.close_month(&d).unwrap();
    assert_eq!(j.phase(), "theft");
    assert_eq!(j.theft.unwrap().amount(), 0);
    assert_eq!(j.resources[3], 0);
    assert_eq!(j.world.remaining, 324);
    j.encode(&c, &d).unwrap();
}
#[test]
fn corrupted_notice_seed_army_gold_phase_or_bytes_reject() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = empty(&d);
    j.travel(&d, 0x3920, &c).unwrap();
    for i in 0..7 {
        let mut b = j.clone();
        match i {
            0 => b.theft.as_mut().unwrap().cue = 14,
            1 => b.theft.as_mut().unwrap().seed_before ^= 1,
            2 => b.theft.as_mut().unwrap().gold_before = 0,
            3 => b.army = Journey::new(&d, 1).army,
            4 => b.cue = Some(0),
            5 => b.survey.bird = true,
            _ => b.world.rng.seed ^= 1,
        };
        assert!(b.encode(&c, &d).is_err(), "{i}");
    }
    let mut raw = j.encode(&c, &d).unwrap();
    let at = raw.len() - 17 - crate::guards::SUFFIX - crate::items::SUFFIX;
    raw[at] = 2;
    let end = raw.len() - 8;
    let h = checksum(&raw[..end]);
    raw[end..].copy_from_slice(&h.to_le_bytes());
    assert!(Journey::decode(&c, &d, &raw).is_err());
}
#[cfg(feature = "desktop")]
#[test]
fn original_enter_escape_and_report_buttons_close_theft_without_gameplay_input() {
    use crate::management_ui::{Manager, Page};
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    for end in [13, 27] {
        let mut j = empty(&d);
        j.travel(&d, 0x3920, &c).unwrap();
        let mut ui = Manager::default();
        ui.sync(&j);
        assert_eq!(ui.page, Page::Theft);
        let before = j.clone();
        for key in [32, 1073741903, 1073741882] {
            ui.key(key, &mut j, &c, &d);
            assert_eq!(j, before);
        }
        ui.key(end, &mut j, &c, &d);
        assert_eq!(j.phase(), "world");
        assert_eq!(j.world, before.world);
        assert_eq!(j.resources, before.resources);
    }
}
