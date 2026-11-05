use super::*;
#[test]
fn existing_bridge_survives_empty_chest_and_monthly_event_continuations() {
    let d = WorldData::bridge_and_treasure_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = learned(&d);
    j.world.position = Position { x: 40, y: 40 };
    j.magic.charges[0] = 1;
    j.begin_bridge().unwrap();
    j.finish_bridge(&d, 0x4d00).unwrap();
    j.world.remaining = 1;
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.month.pending.as_ref().unwrap().tile, 52);
    j.close_month(&d).unwrap();
    assert_eq!(j.world.position, Position { x: 41, y: 40 });
    assert!(j.encode(&c, &d).is_ok());
    let s = crate::treasure::sites()[0];
    j.world.position = Position {
        x: (s.x + 69) % 70,
        y: s.y,
    };
    j.treasure.amounts[0] = 0;
    j.cue = None;
    j.travel(&d, 0x4d00, &c).unwrap();
    assert!(j.treasure.pending.is_none());
    assert_eq!(j.magic.bridges, vec![2841, 2842]);
    assert!(j.encode(&c, &d).is_ok());
    j.world.remaining = 0;
    assert!(j.encode(&c, &d).is_err());
}
#[test]
fn inherited_original_right_cast_matches_entire_local_map_and_cold_state() {
    let d = WorldData::bridge_reference_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = learned(&d);
    j.world.position = Position { x: 40, y: 40 };
    j.magic.charges[0] = 2;
    j.begin_bridge().unwrap();
    j.finish_bridge(&d, 0x4d00).unwrap();
    let view = j.magic.view(&d).unwrap();
    let mut cells = 0;
    for row in include_str!("../magic-bridge-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<u8> = row.split('\t').map(|s| s.parse().unwrap()).collect();
        assert_eq!(view.tile(0, Position { x: f[0], y: f[1] }).unwrap(), f[3]);
        cells += 1;
    }
    assert_eq!(cells, 25);
    assert_eq!(j.magic.bridges, vec![2841, 2842]);
    assert_eq!(
        (j.world.position, j.world.remaining, j.magic.charges[0]),
        (Position { x: 40, y: 40 }, 324, 1)
    );
    assert_eq!(
        Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap(),
        j
    );
    let d = WorldData::bridge_wrap_fixture();
    let mut j = learned(&d);
    j.world.position = Position { x: 0, y: 0 };
    j.magic.charges[0] = 1;
    j.begin_bridge().unwrap();
    j.finish_bridge(&d, 0x4800).unwrap();
    assert_eq!(j.magic.bridges, vec![5460, 5530]);
}
#[cfg(feature = "desktop")]
#[test]
fn original_menu_wraps_without_spending_and_pointer_uses_same_direction_and_confirmation() {
    use crate::management_ui::{Manager, Page};
    use crate::pointer::{self, Action, Screen};
    let d = WorldData::magic_fixture(1);
    let c = Catalog::builtin().unwrap();
    let mut j = learned(&d);
    j.magic.charges[0] = 1;
    let mut ui = Manager::default();
    let before = j.clone();
    ui.key(1073741885, &mut j, &c, &d);
    assert_eq!(ui.page, Page::Magic);
    ui.key(1073741906, &mut j, &c, &d);
    assert_eq!(ui.selected, 7);
    ui.key(13, &mut j, &c, &d);
    assert_eq!(j, before);
    ui.key(1073741905, &mut j, &c, &d);
    ui.key(13, &mut j, &c, &d);
    assert_eq!(ui.page, Page::Bridge);
    assert_eq!(j.magic.charges[0], 0);
    let before = j.clone();
    ui.key(27, &mut j, &c, &d);
    assert_eq!(j, before);
    assert_eq!(
        pointer::hit(Screen::Bridge, 700, 1290),
        Some(Action::Key(32))
    );
    assert_eq!(
        pointer::hit(Screen::Bridge, 700, 300),
        Some(Action::Key(1073741906))
    );
    assert_eq!(
        pointer::hit(Screen::Magic, 900, 200),
        Some(Action::MagicChoice(0))
    );
    ui.key(32, &mut j, &c, &d);
    assert_eq!(ui.page, Page::World);
    assert_eq!(j.world.remaining, 325);
}
fn learned<'a>(d: &WorldData) -> Journey<'a> {
    let mut j = Journey::new(d, 1);
    j.world.position = Position { x: 50, y: 60 };
    assert!(j.search_book().unwrap());
    j
}
#[test]
fn book_is_found_once_at_original_location_and_does_not_spend_time_or_rng() {
    let d = WorldData::magic_fixture(1);
    let mut j = Journey::new(&d, 1);
    assert!(!j.search_book().unwrap());
    assert!(j.begin_bridge().is_err());
    j.world.position = Position { x: 50, y: 60 };
    let w = j.world.clone();
    assert!(j.search_book().unwrap());
    assert_eq!(j.resources[5], 3);
    assert_eq!(j.world, w);
    j.resources[5] = 12;
    assert!(!j.search_book().unwrap());
    assert_eq!(j.resources[5], 12);
    for [i, a, x, y] in items() {
        if i > 0 {
            j.world.area = a;
            j.world.position = Position { x, y };
            assert!(j.search_book().is_err());
        }
    }
}
#[test]
fn shop_buys_one_at_ten_gold_and_capacity_or_money_fail_atomically() {
    let d = WorldData::magic_fixture(1);
    let c = Catalog::builtin().unwrap();
    validate_maps(&d).unwrap();
    assert_eq!(shops().len(), 46);
    let mut j = Journey::new(&d, 1);
    j.world.position = Position { x: 30, y: 6 };
    assert_eq!(j.travel(&d, 0x5000, &c).unwrap(), None);
    assert_eq!(j.phase(), "magic-shop");
    let old = j.clone();
    assert!(j.buy_bridge().is_err());
    assert_eq!(j, old);
    j.magic.book = true;
    j.resources[5] = 3;
    for n in 1..=3 {
        j.buy_bridge().unwrap();
        assert_eq!(j.magic.charges[0], n);
        assert_eq!(j.resources[3], 500 - 10 * u64::from(n));
    }
    let old = j.clone();
    assert!(j.buy_bridge().is_err());
    assert_eq!(j, old);
    j.magic.charges[0] = 0;
    j.resources[3] = 9;
    let old = j.clone();
    assert!(j.buy_bridge().is_err());
    assert_eq!(j, old);
    j.close_magic_shop(&c, &d).unwrap();
    assert_eq!(j.world.remaining, 323);
    assert_eq!(j.world.actions, 1);
    assert!(j.close_magic_shop(&c, &d).is_err());
}
#[test]
fn all_cardinals_change_two_water_cells_or_shore_center_and_allow_walking() {
    let c = Catalog::builtin().unwrap();
    for center in [1, 3, 10, 15] {
        for (key, dx, dy) in [
            (0x4800, 0, -1),
            (0x5000, 0, 1),
            (0x4b00, -1, 0),
            (0x4d00, 1, 0),
        ] {
            let d = WorldData::magic_fixture(center);
            let mut j = learned(&d);
            j.world.position = Position { x: 40, y: 40 };
            j.magic.charges[0] = 1;
            let old = j.world.clone();
            j.begin_bridge().unwrap();
            j.finish_bridge(&d, key).unwrap();
            assert_eq!(j.world, old);
            assert_eq!(j.magic.bridges.len(), 2);
            assert_eq!(j.magic.charges[0], 0);
            let view = j.magic.view(&d).unwrap();
            assert_eq!(view.fingerprint, d.fingerprint);
            for n in [1, if (3..=10).contains(&center) { 0 } else { 2 }] {
                let p = Position {
                    x: (40 + dx * n) as u8,
                    y: (40 + dy * n) as u8,
                };
                assert_eq!(view.tile(0, p).unwrap(), 52);
            }
            j.travel(&d, key, &c).unwrap();
            assert_eq!(
                j.world.position,
                Position {
                    x: (40 + dx) as u8,
                    y: (40 + dy) as u8
                }
            );
        }
    }
}
#[test]
fn diagonal_spends_charge_escape_waits_space_credits_one_step_and_overflow_is_atomic() {
    let d = WorldData::magic_fixture(1);
    for key in [0x4700, 0x4900, 0x4f00, 0x5100, 0x3920] {
        let mut j = learned(&d);
        j.magic.charges[0] = 1;
        let old = j.world.clone();
        j.begin_bridge().unwrap();
        let pending = j.clone();
        assert!(j.finish_bridge(&d, 0x011b).is_err());
        assert_eq!(j, pending);
        j.finish_bridge(&d, key).unwrap();
        assert!(j.magic.bridges.is_empty());
        assert_eq!(j.world.remaining, old.remaining + u16::from(key == 0x3920));
        assert_eq!(j.world.rng, old.rng);
        assert_eq!(j.world.actions, old.actions);
    }
    let mut j = learned(&d);
    j.magic.charges[0] = 1;
    j.world.remaining = u16::MAX;
    j.begin_bridge().unwrap();
    let old = j.clone();
    assert!(j.finish_bridge(&d, 0x3920).is_err());
    assert_eq!(j, old);
}
#[test]
fn pending_direction_cold_completion_does_not_double_spend_and_v4_migrates() {
    let d = WorldData::magic_fixture(1);
    let c = Catalog::builtin().unwrap();
    let mut j = learned(&d);
    j.world.position = Position { x: 40, y: 40 };
    j.magic.charges[0] = 2;
    j.begin_bridge().unwrap();
    let raw = j.encode(&c, &d).unwrap();
    let mut cold = Journey::decode(&c, &d, &raw).unwrap();
    assert_eq!(cold, j);
    cold.finish_bridge(&d, 0x4d00).unwrap();
    j.finish_bridge(&d, 0x4d00).unwrap();
    assert_eq!(cold, j);
    assert_eq!(cold.magic.charges[0], 1);
    let cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    assert_eq!(cold, j);
    let old = Journey::new(&d, 1);
    let mut raw = old.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 8 - 42);
    raw[..8].copy_from_slice(b"8SJRN004");
    raw.extend(checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), old);
}
#[test]
fn malformed_patches_phases_and_charges_are_rejected() {
    let d = WorldData::magic_fixture(1);
    let c = Catalog::builtin().unwrap();
    let j = learned(&d);
    for n in 0..7 {
        let mut bad = j.clone();
        match n {
            0 => bad.magic.bridges = vec![44800],
            1 => bad.magic.bridges = vec![0],
            2 => bad.magic.bridges = vec![2839, 2839],
            3 => bad.magic.charges[3] = 4,
            4 => bad.magic.charges[0] = 4,
            5 => {
                bad.magic.direction = true;
                bad.cue = Some(0)
            }
            _ => {
                bad.magic.shop = Some(PendingShop {
                    index: 255,
                    moved: false,
                })
            }
        };
        assert!(bad.encode(&c, &d).is_err());
    }
}
#[test]
fn shop_last_step_monthly_and_cold_return_only_run_one_event_tail() {
    let d = WorldData::magic_fixture(1);
    let c = Catalog::builtin().unwrap();
    let mut j = learned(&d);
    j.world.position = Position { x: 30, y: 6 };
    j.world.remaining = 1;
    j.travel(&d, 0x5000, &c).unwrap();
    j.buy_bridge().unwrap();
    let mut j = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    j.close_magic_shop(&c, &d).unwrap();
    assert_eq!(j.phase(), "monthly");
    assert_eq!(j.resources[3], 560);
    assert_eq!(j.world.actions, 0);
    let mut j = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    j.close_month(&d).unwrap();
    assert_eq!(j.world.actions, 1);
    assert_eq!(j.world.remaining, 324);
    assert_eq!(j.magic.charges[0], 1);
}
