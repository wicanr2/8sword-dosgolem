use crate::battle::{Modifiers, Outcome, Side, Stack};
use crate::catalog::{Catalog, UnitId};
use crate::controller::{ControlError, Controller, NAVIGATION, OriginalRng};

fn one(id: &str, count: u32) -> [Stack; 6] {
    let mut out = [Stack::default(); 6];
    out[0] = Stack {
        unit: Some(UnitId::parse(id).unwrap()),
        count,
    };
    out
}

#[test]
fn waiting_and_rejected_input_do_not_consume_twice() {
    let catalog = Catalog::builtin().unwrap();
    let mut c = Controller::new(
        &catalog,
        [one("native:01", 30), one("native:06", 30)],
        Side::Player,
        Modifiers::default(),
    )
    .unwrap();
    let actor = c.next_actor().unwrap().unwrap();
    let before = c.clone();
    assert_eq!(c.next_actor().unwrap(), Some(actor));
    assert_eq!(c, before);
    assert_eq!(c.attack(5), Err(ControlError::InvalidTarget));
    assert_eq!(c, before);
    c.skip().unwrap();
    let next = c.next_actor().unwrap().unwrap();
    assert_eq!(next.side, Side::Enemy);
    let before = c.clone();
    assert!(c.skip().is_err());
    assert_eq!(c, before);
}

#[test]
fn autonomous_ordinary_battle_runs_to_a_result() {
    let catalog = Catalog::builtin().unwrap();
    for first in [Side::Player, Side::Enemy] {
        let mut c = Controller::new(
            &catalog,
            [one("native:01", 74), one("native:06", 30)],
            first,
            Modifiers::default(),
        )
        .unwrap();
        let mut rng = OriginalRng { seed: 0x12345678 };
        for _ in 0..200 {
            let Some(actor) = c.next_actor().unwrap() else {
                break;
            };
            let target = if actor.side == Side::Enemy {
                c.enemy_target(&mut rng).unwrap()
            } else {
                c.legal_targets().unwrap()[0]
            };
            c.attack(target).unwrap();
        }
        assert!(matches!(
            c.battle().outcome(),
            Some(Outcome::Win | Outcome::Loss)
        ));
        assert!(c.battle().sequence() > 0);
    }
}

#[test]
fn cursor_graph_never_indexes_outside_the_twelve_original_nodes() {
    assert!(NAVIGATION.iter().flatten().all(|node| *node <= 12));
}

#[test]
fn original_controller_reference() {
    let c = Catalog::builtin().unwrap();
    let result = crate::replay::check_controller(&c, include_str!("../controller-reference.tsv"));
    assert!(result.is_ok(), "{result:?}");
    assert_eq!(result.unwrap().battles, 4);
}

#[test]
fn native_target_selection_replays_the_same_seed() {
    let catalog = Catalog::builtin().unwrap();
    let run = || {
        let mut rows = [one("native:03", 100), one("native:03", 100)];
        rows[0][1] = one("openkb:wolf", 20)[0];
        rows[1][1] = one("native:06", 20)[0];
        let mut c = Controller::new(&catalog, rows, Side::Enemy, Modifiers::default()).unwrap();
        let mut rng = OriginalRng { seed: 0x12345678 };
        let mut targets = Vec::new();
        for _ in 0..200 {
            let Some(actor) = c.next_actor().unwrap() else {
                break;
            };
            let target = if actor.side == Side::Enemy {
                let t = c.enemy_target(&mut rng).unwrap();
                assert!(c.legal_targets().unwrap().contains(&t));
                targets.push(t);
                t
            } else {
                c.legal_targets().unwrap()[0]
            };
            c.attack(target).unwrap();
        }
        assert!(c.battle().outcome().is_some());
        (targets, c.battle().rows().to_owned(), rng.seed)
    };
    assert_eq!(run(), run());
}
