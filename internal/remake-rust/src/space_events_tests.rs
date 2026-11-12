use super::*;
use crate::{
    battle::Side, controller::OriginalRng, land_shore_tests::site, media_assets::checksum,
    world::Position,
};
fn cold<'a>(j: &Journey<'a>, c: &'a Catalog, d: &WorldData) -> Journey<'a> {
    let out = Journey::decode(c, d, &j.encode(c, d).unwrap()).unwrap();
    assert_eq!(&out, j);
    out
}
fn start<'a>(d: &WorldData, tile: u8, boat: u8, remaining: u16) -> Journey<'a> {
    let (area, position) = site(tile);
    let mut j = Journey::new(d, 1);
    j.world.area = area;
    j.world.position = position;
    j.world.boat = boat;
    j.world.remaining = remaining;
    j.magic.book = true;
    j.resources[5] = 3;
    j
}
fn settle<'a>(j: &mut Journey<'a>, c: &'a Catalog, d: &WorldData) {
    for _ in 0..6 {
        *j = cold(j, c, d);
        match j.phase() {
            "magic-shop" => j.close_magic_shop(c, d).unwrap(),
            "camp" => {
                j.close_camp(d, c).unwrap();
            }
            "treasure" => j.finish_treasure(c, d, true).unwrap(),
            "guard" => j.close_guard(d, c).unwrap(),
            _ => break,
        }
    }
}
#[test]
fn original_132_space_clocks_and_boats_survive_all_native_modal_cold_returns() {
    let d = WorldData::land_shore_fixture();
    let c = Catalog::builtin().unwrap();
    let mut count = 0;
    for line in include_str!("../space-events-reference.tsv")
        .lines()
        .filter(|l| l.starts_with("SPACE\t"))
    {
        let v: Vec<u16> = line
            .split('\t')
            .skip(1)
            .map(|s| s.parse().unwrap())
            .collect();
        let mut j = start(&d, v[0] as u8, v[1] as u8, v[3]);
        j.travel(&d, 0x3920, &c).unwrap();
        if j.phase() == "map-notice" {
            j = cold(&j, &c, &d);
            j.close_map_notice(&d, &c).unwrap();
        }
        if v[1] == 2 {
            assert_eq!(j.phase(), "shore");
            assert_eq!(j.world.remaining, v[3] + 1);
            j.select_shore(v[2] == 1).unwrap();
            j = cold(&j, &c, &d);
            j.finish_shore(&d, &c).unwrap();
        }
        settle(&mut j, &c, &d);
        assert_eq!(
            (j.world.remaining, j.world.boat),
            (v[4], v[5] as u8),
            "{line}"
        );
        assert!(j.wait_event.is_none());
        assert!(j.month.pending.is_none());
        cold(&j, &c, &d);
        count += 1;
    }
    assert_eq!(count, 132);
}
#[test]
fn declined_space_shop_uses_actual_offer_and_each_current_camp_can_recruit_then_return() {
    let d = WorldData::land_shore_fixture();
    let c = Catalog::builtin().unwrap();
    for s in crate::world_magic::shops() {
        let mut j = Journey::new(&d, 1);
        j.world.area = s.area;
        j.world.position = Position { x: s.x, y: s.y };
        j.world.boat = 2;
        j.world.remaining = 1;
        j.magic.book = true;
        j.resources[5] = 3;
        j.resources[3] = 30000;
        j.travel(&d, 0x3920, &c).unwrap();
        j.select_shore(false).unwrap();
        j.finish_shore(&d, &c).unwrap();
        assert_eq!(j.magic_offer().unwrap(), usize::from(s.offer));
        j = cold(&j, &c, &d);
        j.buy_world_spell().unwrap();
        let price = crate::world_magic::offer_data(usize::from(s.offer))
            .unwrap()
            .1;
        assert_eq!(j.resources[3], 30000 - u64::from(price));
        j.close_magic_shop(&c, &d).unwrap();
        assert_eq!((j.world.remaining, j.world.boat), (2, 2));
        assert!(j.wait_event.is_none());
        cold(&j, &c, &d);
    }
    for (i, s) in crate::management::camps()
        .iter()
        .enumerate()
        .filter(|(_, s)| s.kind > 0)
    {
        let mut j = Journey::new(&d, 1);
        j.world.area = s.area;
        j.world.position = Position { x: s.x, y: s.y };
        j.world.boat = 2;
        j.world.remaining = 1;
        j.resources[0] = 5;
        j.world.rank = 5;
        j.resources[3] = 30000;
        j.resources[4] = 30000;
        j.travel(&d, 0x3920, &c).unwrap();
        j.select_shore(false).unwrap();
        j.finish_shore(&d, &c).unwrap();
        assert_eq!(j.camps.pending, Some(i));
        j = cold(&j, &c, &d);
        if j.camps.stock[i] > 0 {
            j.recruit(&c, None, 1).unwrap();
        }
        j.close_camp(&d, &c).unwrap();
        assert_eq!((j.world.remaining, j.world.boat), (2, 2));
        cold(&j, &c, &d);
    }
}
#[test]
fn same_guard_confirmation_matches_original_boat_independence_and_retreat_cold_once() {
    let d = WorldData::land_shore_fixture();
    let c = Catalog::builtin().unwrap();
    let mut checked = 0;
    for line in include_str!("../space-events-reference.tsv")
        .lines()
        .filter(|l| l.starts_with("GUARD\t"))
    {
        let v: Vec<u16> = line
            .split('\t')
            .skip(1)
            .map(|s| s.parse().unwrap())
            .collect();
        assert_eq!(v[3], u16::from(v[0] == 1 && matches!(v[2], 1 | 3)));
        checked += 1;
        if v[0] == 0 {
            continue;
        }
        let mut j = start(&d, 65, v[1] as u8, 1);
        j.world.facing = v[2] as u8;
        j.travel(&d, 0x3920, &c).unwrap();
        if v[1] == 2 {
            j.select_shore(false).unwrap();
            j.finish_shore(&d, &c).unwrap();
        }
        assert_eq!(j.guards.pending.is_some(), v[3] == 1);
        settle(&mut j, &c, &d);
        assert_eq!(j.world.remaining, if v[1] == 2 { 2 } else { 1 });
    }
    assert_eq!(checked, 16);
    for yes in [false, true] {
        let mut j = start(&d, 65, 2, 1);
        j.travel(&d, 0x3920, &c).unwrap();
        j.select_shore(yes).unwrap();
        j.finish_shore(&d, &c).unwrap();
        j.choose_guard(&d, &c, true).unwrap();
        j = cold(&j, &c, &d);
        j.battle.as_mut().unwrap().controller.retreat().unwrap();
        j.finish(&c, &d, None).unwrap();
        j = cold(&j, &c, &d);
        j.close_guard(&d, &c).unwrap();
        assert!(j.wait_event.is_none());
        assert_eq!(j.world.remaining, if yes { 1 } else { 2 });
        cold(&j, &c, &d);
    }
}
#[test]
fn final_guard_space_keeps_credited_step_without_a_returning_caller() {
    let d = WorldData::land_shore_fixture();
    let c = Catalog::builtin().unwrap();
    let (i, site) = crate::guards::sites()
        .iter()
        .enumerate()
        .find(|(_, s)| s.final_guard)
        .unwrap();
    let mut j = Journey::new(&d, 1);
    j.world.area = site.area;
    j.world.position = site.position;
    j.world.boat = 2;
    j.world.remaining = 1;
    j.army[0].count = 1000;
    j.guards.swords = [true; 8];
    for row in &mut j.guards.rows[i] {
        if row.count > 0 {
            row.count = 1;
        }
    }
    j.travel(&d, 0x3920, &c).unwrap();
    j.finish_shore(&d, &c).unwrap();
    j.choose_guard(&d, &c, true).unwrap();
    for _ in 0..300 {
        let cp = j.battle.as_mut().unwrap();
        if cp.controller.battle().outcome().is_some() {
            break;
        }
        if let Some(a) = cp.controller.next_actor().unwrap() {
            if cp.controller.is_enemy_caster() {
                cp.controller.enemy_cast(&mut cp.rng).unwrap();
            } else {
                let t = if a.side == Side::Player {
                    cp.controller.legal_targets().unwrap()[0]
                } else {
                    cp.controller.enemy_target(&mut cp.rng).unwrap()
                };
                cp.controller.attack(t).unwrap();
            }
        }
    }
    j.finish(&c, &d, None).unwrap();
    assert_eq!(j.phase(), "ending");
    assert_eq!(j.world.remaining, 2);
    assert!(j.wait_event.is_none());
    cold(&j, &c, &d);
}
#[test]
fn v17_migrates_without_credit_and_malformed_flags_or_overflow_do_not_commit() {
    let d = WorldData::land_shore_fixture();
    let c = Catalog::builtin().unwrap();
    let j = Journey::new(&d, 1);
    let mut old = j.encode(&c, &d).unwrap();
    old.truncate(old.len() - 9);
    old[..8].copy_from_slice(b"8SJRN017");
    old.extend(checksum(&old).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &old).unwrap(), j);
    let mut bad = j.encode(&c, &d).unwrap();
    let n = bad.len();
    bad[n - 9] = 3;
    let h = checksum(&bad[..n - 8]);
    bad[n - 8..].copy_from_slice(&h.to_le_bytes());
    assert!(Journey::decode(&c, &d, &bad).is_err());
    let mut overflow = j.clone();
    overflow.world.remaining = u16::MAX;
    let before = overflow.clone();
    assert!(overflow.travel(&d, 0x3920, &c).is_err());
    assert_eq!(overflow, before);
    let mut wait = j.clone();
    wait.wait_event = Some(Wait { blocked: false });
    assert!(wait.encode(&c, &d).is_err());
    let mut plain = j;
    plain.world.rng = OriginalRng { seed: 1 };
    plain.travel(&d, 0x3920, &c).unwrap();
    assert_eq!(plain.world.remaining, 324);
    assert!(plain.wait_event.is_none());
}
