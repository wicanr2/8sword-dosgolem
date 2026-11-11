use super::*;
use crate::world::{Position, WorldData};
fn shop<'a>(d: &WorldData) -> Journey<'a> {
    let mut j = Journey::new(d, 1);
    j.world.position = Position { x: 39, y: 38 };
    j.camps.pending = Some(1);
    j
}
#[test]
fn native_and_independent_extra_stocks_buy_merge_and_dismiss_without_refund() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = shop(&d);
    assert_eq!(camps().len(), 120);
    assert_eq!((camps()[1].kind, camps()[1].stock), (1, 3000));
    j.open_extra(&c).unwrap();
    assert_eq!(j.offer(Some(2)).unwrap().1, 75);
    j.recruit(&c, Some(2), 1).unwrap();
    assert_eq!(
        (j.resources[3], j.army[1].count, j.used(&c).unwrap()),
        (460, 1, 33)
    );
    assert_eq!(j.camps.stock[1], 3000);
    assert_eq!(j.camps.extras[1].unwrap()[2], 74);
    j.recruit(&c, None, 1).unwrap();
    assert_eq!(
        (j.resources[3], j.army[0].count, j.camps.stock[1]),
        (459, 31, 2999)
    );
    let saved = j.encode(&c, &d).unwrap();
    let mut cold = Journey::decode(&c, &d, &saved).unwrap();
    assert_eq!(cold, j);
    cold.close_camp(&d, &c).unwrap();
    let gold = cold.resources[3];
    cold.dismiss(1).unwrap();
    assert_eq!(cold.resources[3], gold);
    assert_eq!(cold.army[1], Stack::default());
    assert_eq!(cold.camps.extras[1].unwrap()[2], 74);
}
#[test]
fn lazy_extra_binding_uses_current_stock_once_and_never_replenishes() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = shop(&d);
    j.recruit(&c, None, 1).unwrap();
    j.open_extra(&c).unwrap();
    assert_eq!(j.offer(Some(2)).unwrap().1, 74);
    j.recruit(&c, Some(2), 1).unwrap();
    j.open_extra(&c).unwrap();
    assert_eq!(j.offer(Some(2)).unwrap().1, 73);
    let old = j.clone();
    assert!(j.recruit(&c, Some(2), 9999).is_err());
    assert_eq!(j, old);
    assert!(j.recruit(&c, None, 0).is_err());
    assert_eq!(j, old);
}
#[test]
fn every_extra_id_rank_and_full_army_limit_is_checked_before_mutation() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    for n in 0..8 {
        let mut j = shop(&d);
        j.resources = [5, 0, 100, 30000, 30000, 0];
        j.world.rank = 5;
        j.world.position = Position { x: 37, y: 38 };
        j.camps.pending = Some(0);
        j.open_extra(&c).unwrap();
        assert!(j.offer(Some(n)).unwrap().1 > 0);
        j.recruit(&c, Some(n), 1).unwrap();
        assert_eq!(j.army[1].unit, Some(UnitId::parse(EXTRA[n]).unwrap()));
    }
    let mut j = shop(&d);
    j.open_extra(&c).unwrap();
    let before = j.clone();
    assert!(j.recruit(&c, Some(1), 1).is_err());
    assert_eq!(j, before);
    for (i, s) in j.army.iter_mut().enumerate() {
        *s = Stack {
            unit: Some(UnitId::parse(&format!("native:{:02}", i + 1)).unwrap()),
            count: 1,
        };
    }
    assert!(j.recruit(&c, Some(2), 1).is_err());
    j.camps.pending = Some(120);
    assert!(j.offer(None).is_err());
}
#[test]
fn old_no_camp_v1_migrates_but_new_bad_camp_bindings_are_refused() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let j = Journey::new(&d, 1);
    let mut raw = j.encode(&c, &d).unwrap();
    assert_eq!(&raw[..8], b"8SJRN015");
    raw.truncate(raw.len() - 8 - 609 - 17 - 169 - 42 - 2 - 1 - 1 - crate::guards::SUFFIX);
    raw[..8].copy_from_slice(b"8SJRN001");
    raw.extend(checksum(&raw).to_le_bytes());
    let migrated = Journey::decode(&c, &d, &raw).unwrap();
    assert_eq!(migrated, j);
    let mut bad = j.clone();
    bad.camps.stock[1] = 3001;
    assert!(bad.encode(&c, &d).is_err());
    bad.camps.stock[1] = 3000;
    bad.camps.pending = Some(1);
    assert!(bad.encode(&c, &d).is_err());
}
#[test]
fn unlearned_native_casters_are_admitted_and_use_the_existing_zero_charge_controller() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 1);
    j.army[0] = Stack {
        unit: Some(UnitId::parse("native:12").unwrap()),
        count: 2,
    };
    j.cue = Some(0);
    j.choose(&c, true).unwrap();
    let cp = j.battle.as_mut().unwrap();
    assert!(!cp.controller.spell_book().unwrap().enabled);
    assert!(cp.controller.next_actor().is_ok());
    assert!(j.encode(&c, &d).is_ok());
}
