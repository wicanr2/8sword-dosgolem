use super::*;
use crate::world::Position;
#[test]
fn last_step_camp_purchase_precedes_finances_then_returns_once() {
    let d = WorldData::camp_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 1);
    j.world.position = Position { x: 40, y: 38 };
    j.world.remaining = 1;
    j.travel(&d, 0x4b00, &c).unwrap();
    assert_eq!(j.phase(), "camp");
    j.recruit(&c, None, 1).unwrap();
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    cold.close_camp(&d, &c).unwrap();
    assert_eq!(cold.phase(), "monthly");
    assert_eq!(cold.resources[3], 568);
    assert_eq!(cold.month.pending.as_ref().unwrap().budget.due, 31);
    assert_eq!(cold.world.actions, 0);
    cold.close_month(&d).unwrap();
    assert_eq!(cold.world.actions, 1);
    assert_eq!(cold.world.remaining, 324);
    assert_eq!(cold.army[0].count, 31);
    assert!(cold.encode(&c, &d).is_ok());
}
fn stack(id: &str, n: u32) -> Stack {
    Stack {
        unit: Some(UnitId::parse(id).unwrap()),
        count: n,
    }
}
#[test]
fn six_inherited_go_budgets_and_720_source_stock_transitions_match() {
    let c = Catalog::builtin().unwrap();
    let mut count = 0;
    for line in include_str!("../monthly-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<_> = line.split('\t').collect();
        let n = |i: usize| f[i].parse::<u64>().unwrap();
        let mut army = [Stack::default(); 6];
        for (i, s) in f[3].split(',').enumerate() {
            let (id, num) = s.split_once('=').unwrap();
            army[i] = stack(id, num.parse().unwrap());
        }
        let b = plan(&c, army, n(1), n(2)).unwrap();
        assert_eq!(
            (b.due, b.charged, b.after, b.disbanded),
            (n(4), n(5), n(6), n(7) == 1),
            "{line}"
        );
        count += 1;
    }
    assert_eq!(count, 6);
    count = 0;
    for line in include_str!("../monthly-stock.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<_> = line.split('\t').collect();
        let n = |i: usize| f[i].parse::<u32>().unwrap();
        assert_eq!(caps()[n(1) as usize], n(4));
        assert_eq!(
            if n(2) > 0 {
                refill(n(3), n(4), true).unwrap()
            } else {
                n(3)
            },
            n(5),
            "{line}"
        );
        count += 1;
    }
    assert_eq!(count, 720);
}
#[test]
fn last_step_report_cold_resume_and_confirm_commit_exactly_once() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 1);
    j.world.remaining = 1;
    let rng = j.world.rng;
    assert_eq!(j.travel(&d, 0x5000, &c).unwrap(), None);
    assert_eq!(
        (j.phase(), j.resources[3], j.world.remaining, j.month.months),
        ("monthly", 570, 324, 1)
    );
    assert_eq!(j.world.position, Position { x: 40, y: 41 });
    assert_eq!(j.world.actions, 0);
    assert_eq!(j.world.rng, rng);
    let old = j.clone();
    assert!(j.travel(&d, 0x5000, &c).is_err());
    assert!(j.dismiss(0).is_err());
    assert_eq!(j, old);
    let raw = j.encode(&c, &d).unwrap();
    let mut cold = Journey::decode(&c, &d, &raw).unwrap();
    assert_eq!(cold, j);
    cold.close_month(&d).unwrap();
    j.close_month(&d).unwrap();
    assert_eq!(cold, j);
    assert_eq!(j.world.actions, 1);
    assert_eq!(j.resources[3], 570);
    let old = j.clone();
    assert!(j.close_month(&d).is_err());
    assert_eq!(j, old);
}
#[test]
fn equality_bankruptcy_extra_refill_and_changed_caps_keep_source_semantics() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let mut army = [Stack::default(); 6];
    army[0] = stack("native:01", 30);
    let b = plan(&c, army, 0, 30).unwrap();
    assert!(!b.disbanded);
    assert_eq!(b.after, 0);
    let mut j = Journey::new(&d, 1);
    j.army[1] = stack("openkb:wolf", 2500);
    j.world.remaining = 1;
    j.camps.pending = Some(1);
    j.open_extra(&c).unwrap();
    j.camps.pending = None;
    j.camps.stock[1] = 2999;
    j.camps.extras[1].as_mut().unwrap()[2] = 74;
    j.travel(&d, 0x5000, &c).unwrap();
    assert_eq!(j.army, [Stack::default(); 6]);
    let r = j.month.pending.as_ref().unwrap();
    assert_eq!(
        (r.budget.due, r.budget.charged, r.budget.after),
        (100030, 0, 600)
    );
    assert_eq!(j.camps.stock[1], 3000);
    assert_eq!(j.camps.extras[1].unwrap()[2], 75);
    assert!(j.camps.extras[0].is_none());
    assert_eq!(j.camps.stock[51], 800);
    assert_eq!(j.camps.stock[54], 660);
    assert_eq!(j.camps.stock[66], 660);
    assert!(j.encode(&c, &d).is_ok());
    assert!(refill(32767, 3000, true).is_err());
    assert_eq!(refill(u32::MAX, u32::MAX, false).unwrap(), u32::MAX);
}
#[test]
fn v2_migrates_and_checked_impossible_reports_or_overflow_leave_state_intact() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let mut j = Journey::new(&d, 1);
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 8 - 17 - 169 - 42 - 2 - 1 - 1);
    raw[..8].copy_from_slice(b"8SJRN002");
    raw.extend(checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
    j.world.remaining = 1;
    j.month.months = u64::MAX;
    let old = j.clone();
    assert!(j.travel(&d, 0x5000, &c).is_err());
    assert_eq!(j, old);
    j.month.months = 0;
    j.travel(&d, 0x5000, &c).unwrap();
    j.month.pending.as_mut().unwrap().budget.due += 1;
    assert!(j.encode(&c, &d).is_err());
}
