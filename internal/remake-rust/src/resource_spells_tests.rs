use super::*;
use crate::world::{Position, WorldData};
fn ready<'a>(d: &WorldData) -> Journey<'a> {
    let mut j = Journey::new(d, 0x12345678);
    j.magic.book = true;
    j.resources[5] = 10;
    j.resources[4] = 1000;
    j.magic.charges = [0, 2, 2, 0, 0, 0, 0, 0];
    j
}
#[test]
fn five_original_receipts_cover_alchemy_caps_and_all_summon_shapes() {
    let c = Catalog::builtin().unwrap();
    let mut count = 0;
    for row in include_str!("../resource-spells-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<_> = row.split('\t').collect();
        let n = |i: usize| f[i].parse::<u16>().unwrap();
        if f[0] == "A" {
            let amount = alchemy_amount(n(2), n(3) == 1).unwrap();
            assert_eq!(amount, n(4));
            assert_eq!(
                (u64::from(n(1)) + u64::from(amount)).min(30000),
                u64::from(n(5))
            );
        } else {
            assert_eq!(
                summon_payload(n(1) as u8, n(2), n(3) == 1).unwrap(),
                (n(4) as u8, n(5))
            );
            let id = UnitId::parse(&format!("native:{:02}", n(4))).unwrap();
            let mut army = [Stack::default(); 6];
            if f[6] == "full" {
                for (i, s) in army.iter_mut().enumerate() {
                    *s = Stack {
                        unit: Some(UnitId::parse(&format!("native:{:02}", i + 1)).unwrap()),
                        count: 10,
                    };
                }
            } else {
                army[0] = Stack {
                    unit: Some(if f[6] == "merge" {
                        id
                    } else {
                        UnitId::parse("native:01").unwrap()
                    }),
                    count: 30,
                };
                army[1] = Stack {
                    unit: Some(UnitId::parse("openkb:wolf").unwrap()),
                    count: 5,
                };
            }
            let out = plan(&c, army, n(1) as u8, 500, 1000, 2, n(2), n(3) == 1).unwrap();
            match f[6] {
                "merge" => assert_eq!(out.army[0].count, 50),
                "new-bonus" => assert_eq!(
                    out.army[2],
                    Stack {
                        unit: Some(id),
                        count: 6
                    }
                ),
                "full" => {
                    assert!(!out.joined);
                    assert_eq!(out.army, army);
                }
                _ => panic!("receipt case"),
            }
        }
        count += 1;
    }
    assert_eq!(count, 5);
}
#[test]
fn ranks_and_roll_division_boundaries_keep_original_integer_order() {
    for rank in 1..=5 {
        for roll in [
            0, 259, 260, 6599, 6600, 13199, 13200, 19799, 19800, 26399, 26400, 32767,
        ] {
            let (kind, count) = summon_payload(rank, roll, false).unwrap();
            assert_eq!(kind, (roll / 6600 * 5) as u8 + rank);
            assert_eq!(count, [20, 16, 12, 8, 4][usize::from(rank - 1)]);
            assert_eq!(summon_payload(rank, roll, true).unwrap().1, count * 3 / 2);
            assert_eq!(alchemy_amount(roll, true).unwrap(), roll / 260 + 40);
        }
    }
    assert!(summon_payload(0, 1, false).is_err());
    assert!(summon_payload(6, 1, false).is_err());
    assert!(summon_payload(1, 32768, false).is_err());
    assert!(alchemy_amount(u16::MAX, false).is_err());
}
#[test]
fn result_commits_seed_charge_and_army_once_then_cold_acknowledges_without_recast() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    for spell in [1, 2] {
        let mut j = ready(&d);
        let before = j.clone();
        j.cast_resource(&c, spell).unwrap();
        assert_eq!(j.phase(), "resource-result");
        assert_eq!(j.magic.charges[usize::from(spell)], 1);
        assert_eq!(j.world.remaining, before.world.remaining);
        assert_eq!(j.world.position, before.world.position);
        assert_eq!(j.world.actions, before.world.actions);
        assert_eq!(j.world.explored, before.world.explored);
        assert_eq!(j.camps, before.camps);
        // One rule RNG call; the inherited whole-UI receipt also has ambient calls.
        assert_eq!(j.world.rng.seed, 0xb3e97b5b);
        let raw = j.encode(&c, &d).unwrap();
        let mut cold = Journey::decode(&c, &d, &raw).unwrap();
        assert_eq!(cold, j);
        assert!(cold.cast_resource(&c, spell).is_err());
        cold.close_resource_notice(&c).unwrap();
        j.close_resource_notice(&c).unwrap();
        assert_eq!(cold, j);
        let old = cold.clone();
        assert!(cold.close_resource_notice(&c).is_err());
        assert_eq!(cold, old);
    }
}
#[test]
fn full_army_still_pays_and_failed_leadership_or_stack_limits_leave_rng_untouched() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    for (i, s) in j.army.iter_mut().enumerate() {
        *s = Stack {
            unit: Some(UnitId::parse(&format!("native:{:02}", i + 1)).unwrap()),
            count: 10,
        };
    }
    let army = j.army;
    j.cast_resource(&c, 2).unwrap();
    assert_eq!(j.army, army);
    assert_eq!(j.magic.charges[2], 1);
    assert!(
        !j.resource_notice
            .as_ref()
            .unwrap()
            .effect(&j, &c)
            .unwrap()
            .joined
    );
    let mut j = ready(&d);
    j.resources[4] = 30;
    let old = j.clone();
    assert!(j.cast_resource(&c, 2).is_err());
    assert_eq!(j, old);
    j.resources[4] = 30000;
    j.army[0] = Stack {
        unit: Some(UnitId::parse("native:16").unwrap()),
        count: 32760,
    };
    let old = j.clone();
    assert!(j.cast_resource(&c, 2).is_err());
    assert_eq!(j, old);
}
#[test]
fn all_three_shop_charges_share_capacity_and_unlearned_unfunded_or_unknown_spells_refuse() {
    let d = WorldData::magic_fixture(1);
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    j.magic.charges = [2, 0, 0, 0, 0, 0, 0, 0];
    j.resources[5] = 3;
    for offer in [1, 2] {
        let i = crate::world_magic::shops()
            .iter()
            .position(|s| s.offer == offer)
            .unwrap();
        let site = crate::world_magic::shops()[i];
        j.world.area = site.area;
        j.world.position = Position {
            x: site.x,
            y: site.y,
        };
        j.magic.shop = Some(crate::world_magic::PendingShop {
            index: i as u8,
            moved: false,
        });
        let old = j.resources[3];
        j.buy_world_spell().unwrap();
        assert_eq!(j.resources[3], old - 100);
        assert_eq!(j.magic.charges[usize::from(offer)], 1);
        let old = j.clone();
        assert!(j.buy_world_spell().is_err());
        assert_eq!(j, old);
        j.magic.charges[usize::from(offer)] = 0;
    }
    j.magic.shop = None;
    for spell in [0, 3, 255] {
        let old = j.clone();
        assert!(j.cast_resource(&c, spell).is_err());
        assert_eq!(j, old);
    }
}
#[test]
fn corrupt_notices_and_other_event_overlap_cannot_be_saved_or_acknowledged() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut good = ready(&d);
    good.cast_resource(&c, 1).unwrap();
    for n in 0..7 {
        let mut bad = good.clone();
        match n {
            0 => bad.resource_notice.as_mut().unwrap().spell = 0,
            1 => bad.resource_notice.as_mut().unwrap().seed_before ^= 1,
            2 => bad.resource_notice.as_mut().unwrap().gold_before += 1,
            3 => bad.resource_notice.as_mut().unwrap().uses_before = 0,
            4 => bad.world.rng.seed ^= 1,
            5 => bad.magic.charges[1] += 1,
            _ => bad.cue = Some(0),
        };
        let old = bad.clone();
        assert!(bad.encode(&c, &d).is_err());
        assert!(bad.close_resource_notice(&c).is_err());
        assert_eq!(bad, old);
    }
}
#[test]
fn v5_progress_migrates_with_real_bridge_and_charges_while_new_result_is_separate() {
    let d = WorldData::magic_fixture(1);
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 1);
    j.magic.book = true;
    j.resources[5] = 3;
    j.magic.charges[0] = 1;
    j.begin_bridge().unwrap();
    j.finish_bridge(&d, 0x4d00).unwrap();
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 12);
    raw[..8].copy_from_slice(b"8SJRN005");
    raw.extend(crate::media_assets::checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
}
