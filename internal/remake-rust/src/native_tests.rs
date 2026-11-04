use crate::battle::{Battle, BattleError, Modifiers, Outcome, Side, Stack};
use crate::catalog::{Catalog, UnitId};
use crate::formation::{initial_formation, motion_plan, sort_plan};
use crate::replay::{ModelCount, ReplayCount, check_battles, check_models, parse_rows};

fn id(value: &str) -> UnitId {
    UnitId::parse(value).unwrap()
}
fn army(value: &str) -> [Stack; 6] {
    parse_rows(value).unwrap()
}
fn empty() -> [Stack; 6] {
    [Stack::default(); 6]
}
fn one(value: &str, count: u32) -> [Stack; 6] {
    let mut rows = empty();
    rows[0] = Stack {
        unit: Some(id(value)),
        count,
    };
    rows
}

#[test]
fn all_33_identities_and_source_fields_survive() {
    let c = Catalog::builtin().unwrap();
    assert_eq!(c.profiles().len(), 33);
    let mut native = 0;
    for profile in c.profiles() {
        assert_eq!(id(&profile.id.to_string()), profile.id);
        if profile.id.native_kind().is_some() {
            native += 1;
        } else {
            assert!(profile.id.to_string().starts_with("openkb:"));
        }
    }
    assert_eq!(native, 25);
    assert_eq!(
        (c.get(id("native:01")).attack, c.get(id("native:01")).hp),
        (30, 25)
    );
    assert!(c.get(id("openkb:arcr")).ranged);
    assert!(!c.get(id("openkb:pike")).ranged);
    for invalid in [
        "native:00",
        "native:26",
        "native:1",
        "native:+01",
        "openkb:unknown",
        "",
    ] {
        assert!(UnitId::parse(invalid).is_err(), "{invalid}");
    }
}

#[test]
fn malformed_catalogs_are_refused() {
    let text = include_str!("../unit-catalog.tsv");
    let row = text
        .lines()
        .find(|line| line.starts_with("native:01\t"))
        .unwrap();
    assert!(Catalog::parse("").is_err());
    assert!(Catalog::parse(&format!("{text}{row}\n")).is_err());
    assert!(Catalog::parse(&text.replace(&format!("{row}\n"), "")).is_err());
    assert!(Catalog::parse(&text.replace("native:01\t", "native:26\t")).is_err());
    assert!(Catalog::parse(&text.replace("\t30\t25\t0", "\t30\t0\t0")).is_err());
    assert!(Catalog::parse(&text.replace("\t30\t25\t0", "\t30\t25\t2")).is_err());
}

#[test]
fn setup_sort_and_motion_match_current_go_planners() {
    let c = Catalog::builtin().unwrap();
    assert_eq!(
        check_models(&c, include_str!("../battle-models.tsv")).unwrap(),
        ModelCount {
            setup: 37,
            sort: 128,
            motion: 144
        }
    );
}

#[test]
fn complete_captured_win_loss_and_retreat_actions_match() {
    let c = Catalog::builtin().unwrap();
    assert_eq!(
        check_battles(&c, include_str!("../battle-replay.tsv")).unwrap(),
        ReplayCount {
            battles: 3,
            actions: 40,
            wins: 1,
            losses: 1,
            retreats: 1
        }
    );
    let corrupt = include_str!("../battle-replay.tsv").replacen("\t200\t14\t", "\t201\t14\t", 1);
    assert_ne!(corrupt, include_str!("../battle-replay.tsv"));
    assert!(check_battles(&c, &corrupt).is_err());
}

#[test]
fn enemy_melee_and_ranged_keep_distinct_hp_calls() {
    let c = Catalog::builtin().unwrap();
    for (enemy, calls, pending) in [("native:06", 2, 590), ("native:03", 1, 670)] {
        let mut b = Battle::new(&c, [one("native:01", 30), one(enemy, 10)]).unwrap();
        let result = b.attack(Side::Enemy, 0, 0, Modifiers::default()).unwrap();
        assert_eq!((result.before, result.after, result.loss), (30, 27, 3));
        assert_eq!(result.hits.len(), calls);
        assert_eq!(b.hp()[0][0], pending);
        assert_eq!(b.rows()[0][0].count, 27);
        assert_eq!(b.sequence(), 1);
    }
}

#[test]
fn low_damage_player_and_enemy_have_different_count_rules() {
    let c = Catalog::builtin().unwrap();
    let mut player = Battle::new(&c, [one("native:01", 1), one("native:25", 30)]).unwrap();
    let mut enemy = Battle::new(&c, [one("native:25", 30), one("native:01", 1)]).unwrap();
    let p = player
        .attack(Side::Player, 0, 0, Modifiers::default())
        .unwrap();
    let e = enemy
        .attack(Side::Enemy, 0, 0, Modifiers::default())
        .unwrap();
    assert_eq!(p.after, 29);
    assert_eq!(e.after, 30);
    assert_eq!(p.hits[0].encoded, 1);
    assert_eq!(e.hits[0].encoded, 1);
    assert_eq!(e.hits.len(), 1);
    assert!(e.display.is_empty());
}

#[test]
fn failed_attacks_leave_the_entire_battle_unchanged() {
    let c = Catalog::builtin().unwrap();
    for (source, source_count, target_count, source_raw, target_raw, modifiers) in [
        ("native:01", 30, 30, 6, 0, Modifiers::default()),
        ("native:01", 30, 30, 0, 6, Modifiers::default()),
        ("native:01", 30, 30, 1, 0, Modifiers::default()),
        ("native:10", 30, 30, 0, 0, Modifiers::default()),
        ("native:01", 65536, 30, 0, 0, Modifiers::default()),
        ("native:01", 30, 32768, 0, 0, Modifiers::default()),
        (
            "native:01",
            30,
            30,
            0,
            0,
            Modifiers {
                player_attack: 5,
                ..Modifiers::default()
            },
        ),
        (
            "native:01",
            30,
            30,
            0,
            0,
            Modifiers {
                player_boost: u16::MAX,
                ..Modifiers::default()
            },
        ),
        ("native:05", 65535, 30, 0, 0, Modifiers::default()),
    ] {
        let mut b = Battle::new(
            &c,
            [one(source, source_count), one("native:01", target_count)],
        )
        .unwrap();
        let before = b.clone();
        assert!(
            b.attack(Side::Player, source_raw, target_raw, modifiers)
                .is_err()
        );
        assert_eq!(b, before);
    }
    let mut b = Battle::new(&c, [one("native:01", 30), one("native:06", 10)]).unwrap();
    let before = b.clone();
    assert_eq!(
        b.attack(
            Side::Enemy,
            0,
            0,
            Modifiers {
                enemy_defense: u16::MAX,
                ..Modifiers::default()
            }
        ),
        Err(BattleError::InvalidModifier)
    );
    assert_eq!(b, before);
}

#[test]
fn wide_troops_and_empty_slot_aliases_do_not_truncate() {
    let c = Catalog::builtin().unwrap();
    let rows = [one("openkb:drag", u32::MAX), empty()];
    let p = initial_formation(&c, &rows).unwrap();
    assert_eq!(p.hp[0][0], u64::from(u32::MAX) * 200);
    assert_eq!(p.slots[0], [0, 5, 5, 5, 5, 5]);
    assert_eq!(p.slots[1], [5; 6]);
    let invalid = army("native:01=30,native:01=1,-=0,-=0,-=0,-=0");
    assert_eq!(
        initial_formation(&c, &[invalid, empty()]),
        Err(BattleError::InvalidArmy)
    );
}

#[test]
fn invalid_position_indices_fail_before_indexing() {
    let c = Catalog::builtin().unwrap();
    let rows = one("native:01", 30);
    assert!(motion_plan(&rows, [6, 1, 2, 3, 4, 5], 0, 1).is_err());
    assert!(motion_plan(&rows, [0, 1, 2, 3, 4, 5], 3, 1).is_err());
    assert!(sort_plan(&c, &rows, [0, 1, 2, 3, 4, 5], [[6, 1, 2]; 4], false).is_err());
}

#[test]
fn terminal_battles_reject_further_actions() {
    let c = Catalog::builtin().unwrap();
    let mut b = Battle::new(&c, [one("native:01", 30), one("native:06", 1)]).unwrap();
    b.attack(Side::Player, 0, 0, Modifiers::default()).unwrap();
    assert_eq!(b.outcome(), Some(Outcome::Win));
    let before = b.clone();
    assert!(b.attack(Side::Enemy, 0, 0, Modifiers::default()).is_err());
    assert_eq!(b, before);
    let mut r = Battle::new(&c, [one("native:01", 30), one("native:06", 30)]).unwrap();
    assert_eq!(r.retreat(), Ok(Outcome::Retreat));
    let before = r.clone();
    assert!(r.retreat().is_err());
    assert_eq!(r, before);
}
