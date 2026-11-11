use super::*;
use crate::world::Position;
fn entering<'a>(d: &WorldData, i: usize, c: &Catalog) -> Journey<'a> {
    let mut j = Journey::new(d, 1);
    let s = sites()[i];
    j.world.area = s.area;
    j.world.position = Position {
        x: (s.x + 1) % 70,
        y: s.y,
    };
    j.travel(d, 0x4b00, c).unwrap();
    assert_eq!(j.phase(), "treasure");
    j
}
#[test]
fn seven_inherited_go_awards_include_cancel_empty_caps_and_safe_wrap_difference() {
    let mut count = 0;
    for l in include_str!("../treasure-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<_> = l.split('\t').collect();
        let n = |i: usize| f[i].parse::<u64>().unwrap();
        assert_eq!(
            award(n(1), n(2), n(3) as u16, n(4) as u8).unwrap(),
            (n(5), n(6), n(7) == 1),
            "{l}"
        );
        count += 1;
    }
    assert_eq!(count, 7);
    assert!(award(30001, 100, 50, 1).is_err());
    assert!(award(500, 100, 50, 3).is_err());
}
#[test]
fn all_80_identities_consume_only_their_own_value_and_leave_army_and_camps() {
    let d = WorldData::treasure_fixture();
    let c = Catalog::builtin().unwrap();
    validate_maps(&d).unwrap();
    assert!(validate_maps(&WorldData::flat_fixture()).is_err());
    for i in 0..80 {
        let mut j = entering(&d, i, &c);
        assert_eq!(j.treasure.pending.unwrap().index as usize, i);
        let old = j.clone();
        let choice = if i % 2 == 0 { 1 } else { 2 };
        j.select_treasure(choice).unwrap();
        j.finish_treasure(&c, &d, false).unwrap();
        let expected = award(500, 100, sites()[i].amount, choice).unwrap();
        assert_eq!((j.resources[3], j.resources[4]), (expected.0, expected.1));
        for at in 0..80 {
            assert_eq!(
                j.treasure.amounts[at],
                if at == i { 0 } else { old.treasure.amounts[at] }
            );
        }
        assert_eq!(j.army, old.army);
        assert_eq!(j.camps, old.camps);
        assert_eq!(j.world.remaining, 323);
        assert_eq!(j.world.actions, 1);
        assert!(j.encode(&c, &d).is_ok());
    }
}
#[test]
fn cancel_then_space_reopen_pending_cold_choice_and_collected_cold_do_not_reaward() {
    let d = WorldData::treasure_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = entering(&d, 0, &c);
    j.finish_treasure(&c, &d, true).unwrap();
    assert_eq!(
        (j.resources[3], j.resources[4], j.treasure.amounts[0]),
        (500, 100, 50)
    );
    j.travel(&d, 0x3920, &c).unwrap();
    assert!(!j.treasure.pending.unwrap().moved);
    j.select_treasure(2).unwrap();
    let before = j.clone();
    assert!(j.select_treasure(0).is_err());
    assert!(j.dismiss(0).is_err());
    assert_eq!(j, before);
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    assert_eq!(cold, j);
    cold.finish_treasure(&c, &d, false).unwrap();
    j.finish_treasure(&c, &d, false).unwrap();
    assert_eq!(cold, j);
    assert_eq!(
        (
            j.resources[3],
            j.resources[4],
            j.world.remaining,
            j.world.actions
        ),
        (500, 105, 323, 2)
    );
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    let old = cold.clone();
    assert!(cold.finish_treasure(&c, &d, false).is_err());
    assert_eq!(cold, old);
    cold.travel(&d, 0x3920, &c).unwrap();
    assert_eq!(cold.phase(), "world");
    assert_eq!(cold.resources, j.resources);
    assert_eq!(cold.world.remaining, 323);
}
#[test]
fn last_step_award_and_cancel_precede_monthly_and_resume_without_reopening() {
    let d = WorldData::treasure_fixture();
    let c = Catalog::builtin().unwrap();
    for cancel in [false, true] {
        let mut j = entering(&d, 0, &c);
        j.world.remaining = 1;
        j.finish_treasure(&c, &d, cancel).unwrap();
        assert_eq!(j.phase(), "monthly");
        let r = j.month.pending.as_ref().unwrap();
        assert_eq!(r.budget.before, if cancel { 500 } else { 550 });
        assert_eq!(j.resources[3], if cancel { 570 } else { 620 });
        let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
        cold.close_month(&d).unwrap();
        assert_eq!(cold.phase(), "world");
        assert_eq!(cold.world.remaining, 324);
        assert_eq!(cold.world.actions, 1);
        assert!(cold.treasure.pending.is_none());
        assert_eq!(cold.treasure.amounts[0], if cancel { 50 } else { 0 });
    }
}
#[test]
fn v3_migrates_and_bad_pending_bindings_or_partial_values_are_rejected() {
    let d = WorldData::treasure_fixture();
    let c = Catalog::builtin().unwrap();
    let j = Journey::new(&d, 1);
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 8 - 169 - 42 - 2 - 1 - 1 - crate::guards::SUFFIX);
    raw[..8].copy_from_slice(b"8SJRN003");
    raw.extend(checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
    let good = entering(&d, 0, &c);
    for n in 0..5 {
        let mut bad = good.clone();
        match n {
            0 => bad.treasure.pending.as_mut().unwrap().index = 80,
            1 => bad.treasure.pending.as_mut().unwrap().choice = 0,
            2 => bad.treasure.amounts[0] = 49,
            3 => bad.treasure.amounts[0] = 0,
            _ => bad.world.position.x += 1,
        };
        let old = bad.clone();
        assert!(bad.finish_treasure(&c, &d, false).is_err());
        assert_eq!(bad, old);
        assert!(bad.encode(&c, &d).is_err());
    }
}
