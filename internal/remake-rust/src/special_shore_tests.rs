use super::*;
use crate::{media_assets::checksum, world::Position};
fn at<'a>(d: &WorldData, area: u8, target: Position) -> (Journey<'a>, u16) {
    let mut j = Journey::new(d, 1);
    j.world.area = area;
    j.world.boat = 2;
    j.magic.book = true;
    j.resources[5] = 3;
    for key in crate::jump_spell::DIRECTIONS {
        let p = motion(target, key, 3, true).unwrap().0;
        if water(d.tile(area, p).unwrap()) {
            j.world.position = p;
            return (j, key);
        }
    }
    panic!("fixture requires water");
}
#[test]
fn actual_camps_and_treasures_accept_or_refuse_without_remote_transactions() {
    let d = WorldData::special_shore_fixture();
    let c = Catalog::builtin().unwrap();
    for (area, p, tile) in camps()
        .iter()
        .enumerate()
        .filter(|(_, s)| s.kind > 0)
        .map(|(i, s)| (s.area, Position { x: s.x, y: s.y }, 54 + (i / 24) as u8))
        .chain(
            crate::treasure::sites()
                .iter()
                .map(|s| (s.area, Position { x: s.x, y: s.y }, 59)),
        )
    {
        for yes in [false, true] {
            let (mut j, key) = at(&d, area, p);
            let old = j.clone();
            j.world.remaining = 1;
            j.travel(&d, key, &c).unwrap();
            assert_eq!(j.phase(), "shore");
            j.select_shore(yes).unwrap();
            j = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
            j.finish_shore(&d, &c).unwrap();
            if yes {
                assert_eq!(j.world.position, p);
                assert_eq!(j.world.boat, 0);
                if tile == 59 {
                    assert_eq!(j.phase(), "treasure");
                    j.finish_treasure(&c, &d, true).unwrap();
                } else {
                    assert_eq!(j.phase(), "camp");
                    j.close_camp(&d, &c).unwrap();
                }
                assert_eq!(j.phase(), "monthly");
                assert_eq!(j.month.months, 1);
            } else {
                assert_eq!(j.world.position, old.world.position);
                assert_eq!(j.world.boat, 2);
                assert_eq!(j.world.remaining, 1);
                assert_eq!(j.camps, old.camps);
                assert_eq!(j.treasure, old.treasure);
                assert_eq!(j.resources, old.resources);
                assert_eq!(j.army, old.army);
                assert_eq!(j.month.months, 0);
                assert_eq!(j.world.actions, 1);
            }
            j.encode(&c, &d).unwrap();
        }
    }
}
#[test]
fn declined_shop_defaults_to_bridge_and_cold_purchase_keeps_water_and_clock() {
    let d = WorldData::special_shore_fixture();
    let c = Catalog::builtin().unwrap();
    for site in shops().iter().filter(|s| supported(s.offer)) {
        let (mut j, key) = at(
            &d,
            site.area,
            Position {
                x: site.x,
                y: site.y,
            },
        );
        let old = j.clone();
        j.travel(&d, key, &c).unwrap();
        j.select_shore(false).unwrap();
        j.finish_shore(&d, &c).unwrap();
        assert_eq!(j.phase(), "magic-shop");
        assert_eq!(j.magic_offer().unwrap(), 0);
        assert_eq!(j.world.position, old.world.position);
        assert_eq!(j.world.actions, 0);
        assert_eq!(j.world.remaining, 324);
        j = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
        j.buy_world_spell().unwrap();
        assert_eq!(j.resources[3], old.resources[3] - 10);
        assert_eq!(j.magic.charges[0], 1);
        j.close_magic_shop(&c, &d).unwrap();
        assert_eq!(j.world.boat, 2);
        assert_eq!(j.world.remaining, 324);
        assert_eq!(j.world.actions, 1);
        assert_eq!(j.travel_spell.refused_shop, None);
        j.encode(&c, &d).unwrap();
    }
}
#[test]
fn declined_exits_still_cross_but_do_not_spend_last_step_or_clear_boat() {
    let d = WorldData::special_shore_fixture();
    let c = Catalog::builtin().unwrap();
    for e in exits() {
        for yes in [false, true] {
            let (mut j, key) = at(&d, e.area, e.position);
            j.world.remaining = 1;
            let old = j.clone();
            j.travel(&d, key, &c).unwrap();
            j.select_shore(yes).unwrap();
            j.finish_shore(&d, &c).unwrap();
            assert_eq!(j.world.area, e.destination());
            assert_eq!(j.world.position, d.starts[usize::from(e.destination())]);
            if yes {
                assert_eq!(j.phase(), "monthly");
                assert_eq!(j.world.boat, 0);
            } else {
                assert_eq!(j.world.remaining, 1);
                assert_eq!(j.world.boat, 2);
                assert_eq!(j.month.months, 0);
                assert_eq!(j.resources, old.resources);
            }
            j.encode(&c, &d).unwrap();
        }
    }
}
#[test]
fn refused_shop_rejects_bad_geometry_flags_and_reads_real_v10_shape() {
    let d = WorldData::special_shore_fixture();
    let c = Catalog::builtin().unwrap();
    let s = *shops().iter().find(|s| s.offer == 1).unwrap();
    let (mut j, key) = at(&d, s.area, Position { x: s.x, y: s.y });
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 16 - 10 - 1 - 1 - crate::guards::SUFFIX - crate::items::SUFFIX);
    raw[..8].copy_from_slice(b"8SJRN010");
    raw.extend(checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
    j.travel(&d, key, &c).unwrap();
    j.select_shore(false).unwrap();
    j.finish_shore(&d, &c).unwrap();
    for n in 0..6 {
        let mut bad = j.clone();
        match n {
            0 => bad.world.boat = 0,
            1 => bad.world.position = Position { x: 0, y: 0 },
            2 => bad.magic.shop.as_mut().unwrap().moved = true,
            3 => bad.travel_spell.refused_shop = Some(0x3920),
            4 => bad.travel_spell.shore = Some(crate::travel_spells::Shore { key, yes: true }),
            _ => bad.magic.shop = None,
        };
        assert!(bad.encode(&c, &d).is_err(), "{n}");
    }
    assert!(j.finish_shore(&d, &c).is_err());
}
#[test]
fn ordinary_shop_and_camp_discard_one_original_entry_roll_before_ui() {
    let d = WorldData::special_shore_fixture();
    let c = Catalog::builtin().unwrap();
    let site = *shops().iter().find(|s| s.offer == 1).unwrap();
    let (mut j, key) = at(
        &d,
        site.area,
        Position {
            x: site.x,
            y: site.y,
        },
    );
    j.world.boat = 0;
    let mut rng = j.world.rng;
    rng.next15();
    j.travel(&d, key, &c).unwrap();
    assert_eq!(j.world.rng, rng);
    assert_eq!(j.world.actions, 0);
    let site = camps().iter().find(|s| s.kind > 0).unwrap();
    let (mut j, key) = at(
        &d,
        site.area,
        Position {
            x: site.x,
            y: site.y,
        },
    );
    j.world.boat = 0;
    let mut rng = j.world.rng;
    rng.next15();
    j.travel(&d, key, &c).unwrap();
    assert_eq!(j.world.rng, rng);
    assert_eq!(j.world.actions, 0);
}

#[test]
fn original_288_shore_dispatch_clock_and_28_consumer_lookups_match() {
    let d = WorldData::shore_vectors_fixture();
    let c = Catalog::builtin().unwrap();
    let mut flows = 0;
    let mut lookups = 0;
    for line in include_str!("../special-shore-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<_> = line.split('\t').collect();
        let n = |i: usize| f[i].parse::<u16>().unwrap();
        if f[0] == "LOOK" {
            let expected = if n(1) == 53 && n(3) == 1 {
                u16::from(shops().iter().find(|s| s.area == n(2) as u8).unwrap().offer)
            } else if n(1) == 53 {
                0
            } else {
                n(3)
            };
            assert_eq!(n(4), expected, "{line}");
            lookups += 1;
            continue;
        }
        assert_eq!(f[0], "FLOW");
        let tile = n(1) as u8;
        let key = n(3);
        let (area, target) = match tile {
            49 | 50 => {
                let e = exits()
                    .iter()
                    .find(|e| e.area == 1 && e.tile == tile)
                    .unwrap();
                (e.area, e.position)
            }
            53 => {
                let s = shops().iter().find(|s| s.offer == 0).unwrap();
                (s.area, Position { x: s.x, y: s.y })
            }
            54..=58 => {
                let (_, s) = camps()
                    .iter()
                    .enumerate()
                    .find(|(i, s)| {
                        i / 24 == usize::from(tile - 54)
                            && s.kind > 0
                            && d.tile(s.area, Position { x: s.x, y: s.y }).unwrap() == tile
                            && water(
                                d.tile(
                                    s.area,
                                    motion(Position { x: s.x, y: s.y }, key, 3, true).unwrap().0,
                                )
                                .unwrap(),
                            )
                    })
                    .unwrap();
                (s.area, Position { x: s.x, y: s.y })
            }
            _ => {
                let s = crate::treasure::sites()[0];
                (s.area, Position { x: s.x, y: s.y })
            }
        };
        let source = motion(target, key, 3, true).unwrap().0;
        let mut j = Journey::new(&d, 1);
        j.world.area = area;
        j.world.position = source;
        j.world.boat = 2;
        j.world.remaining = n(4);
        j.magic.book = true;
        j.resources[5] = 3;
        j.travel(&d, key, &c).unwrap();
        assert_eq!(j.phase(), "shore", "{line}");
        j.select_shore(n(2) == 1).unwrap();
        j.finish_shore(&d, &c).unwrap();
        if j.phase() == "magic-shop" {
            j.close_magic_shop(&c, &d).unwrap();
        }
        if j.phase() == "camp" {
            j.close_camp(&d, &c).unwrap();
        }
        if j.phase() == "treasure" {
            j.finish_treasure(&c, &d, true).unwrap();
        }
        assert_eq!(j.world.boat, n(7) as u8, "{line}");
        if n(10) == 0 {
            assert_eq!(j.phase(), "monthly", "{line}");
            assert_eq!(j.world.remaining, 324);
        } else {
            assert_eq!(j.world.remaining, n(10), "{line}");
        }
        if matches!(tile, 49 | 50) {
            assert_eq!(j.world.area, n(9) as u8);
            assert_eq!(
                j.world.position,
                Position {
                    x: n(5) as u8,
                    y: n(6) as u8
                }
            );
        } else {
            assert_eq!(j.world.area, area);
            assert_eq!(j.world.position, if n(2) == 1 { target } else { source });
        }
        assert_eq!(n(8), u16::from(n(2) == 0));
        assert_eq!(n(12), u16::from((53..=58).contains(&tile)));
        j.encode(&c, &d).unwrap();
        flows += 1;
    }
    assert_eq!((flows, lookups), (288, 28));
}
