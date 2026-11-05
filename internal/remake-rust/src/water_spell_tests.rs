use crate::{
    catalog::Catalog,
    journey::Journey,
    travel_spells::Shore,
    world::{Position, WorldData},
};
fn ready<'a>(d: &WorldData) -> Journey<'a> {
    let mut j = Journey::new(d, 1);
    j.magic.book = true;
    j.magic.charges[6] = 2;
    j.resources[5] = 3;
    j
}
#[test]
fn special_shore_sites_remain_an_uncommitted_boundary() {
    let c = Catalog::builtin().unwrap();
    for tile in [49, 50, 51, 53, 54, 55, 56, 57, 58, 59, 65] {
        let d = WorldData::water_event_fixture(tile);
        let mut j = ready(&d);
        j.world.position.x = 42;
        j.world.boat = 2;
        let before = j.clone();
        assert_eq!(
            j.travel(&d, 0x4d00, &c).unwrap(),
            Some(crate::world::Boundary::BoatExit)
        );
        assert_eq!(j, before);
    }
}
#[test]
fn ninety_original_result_and_rollback_cases_match_native_rules() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut count = 0;
    for l in include_str!("../shore-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let fields: Vec<_> = l.split('\t').collect();
        let f: Vec<u16> = fields[..9].iter().map(|s| s.parse().unwrap()).collect();
        let mut j = ready(&d);
        j.world.position = Position {
            x: f[2] as u8,
            y: f[3] as u8,
        };
        j.world.boat = 2;
        j.world.explored[0].fill(0);
        j.world.reveal();
        j.travel(&d, f[1], &c).unwrap();
        assert_eq!(j.phase(), "shore");
        j.select_shore(f[0] == 1).unwrap();
        j.finish_shore(&d, &c).unwrap();
        assert_eq!(
            (
                j.world.position.x,
                j.world.position.y,
                j.world.facing,
                j.world.boat
            ),
            (f[4] as u8, f[5] as u8, f[6] as u8, f[7] as u8),
            "{l}"
        );
        assert_eq!(f[8], u16::from(f[0] == 0));
        assert_eq!(j.world.actions, 1);
        assert_eq!(
            j.world.remaining,
            if f[0] == 1 && f[1] != 0x3920 {
                323
            } else {
                324
            }
        );
        assert_eq!(
            format!(
                "{:016x}",
                crate::media_assets::checksum(&j.world.explored[0])
            ),
            fields[9],
            "{l}"
        );
        count += 1;
    }
    assert_eq!(count, 90);
}
#[test]
fn cast_water_cross_two_water_types_repeat_and_cold_shore_do_not_double_spend() {
    let d = WorldData::water_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    let old = j.clone();
    j.cast_water().unwrap();
    assert_eq!(j.world.boat, 1);
    assert_eq!(j.magic.charges[6], 1);
    assert_eq!(j.resources, old.resources);
    assert_eq!(j.world.rng, old.world.rng);
    assert_eq!(j.world.remaining, old.world.remaining);
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.world.boat, 2);
    assert_eq!(j.world.position.x, 41);
    j.cast_water().unwrap();
    assert_eq!(j.world.boat, 1);
    assert_eq!(j.magic.charges[6], 0);
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.world.boat, 2);
    assert_eq!(j.world.position.x, 42);
    let before = j.clone();
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.world.position, before.world.position);
    assert_eq!(j.world.rng, before.world.rng);
    assert_eq!(j.world.actions, before.world.actions);
    assert_eq!(j.world.remaining, before.world.remaining);
    assert_eq!(
        j.travel_spell.shore,
        Some(Shore {
            key: 0x4d00,
            yes: true
        })
    );
    j.select_shore(false).unwrap();
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    let old = cold.clone();
    assert!(cold.cast_water().is_err());
    assert!(cold.begin_teleport().is_err());
    assert!(cold.begin_bird_view().is_err());
    assert!(cold.dismiss(0).is_err());
    assert!(cold.travel(&d, 0x5000, &c).is_err());
    assert_eq!(cold, old);
    cold.finish_shore(&d, &c).unwrap();
    assert_eq!(cold.world.position, before.world.position);
    assert_eq!(cold.world.remaining, before.world.remaining);
    assert_eq!(cold.world.boat, 2);
    assert_eq!(cold.world.actions, before.world.actions + 1);
    let mut rng = before.world.rng;
    rng.next15();
    assert_eq!(cold.world.rng, rng);
    cold.travel(&d, 0x4d00, &c).unwrap();
    let raw = cold.encode(&c, &d).unwrap();
    let mut cold = Journey::decode(&c, &d, &raw).unwrap();
    cold.finish_shore(&d, &c).unwrap();
    assert_eq!(cold.world.position.x, 43);
    assert_eq!(cold.world.remaining, before.world.remaining - 1);
    assert_eq!(cold.world.boat, 0);
    assert_eq!(cold.magic.charges[6], 0);
    let old = cold.clone();
    assert!(cold.finish_shore(&d, &c).is_err());
    assert_eq!(cold, old);
}
#[test]
fn refusal_can_encounter_while_yes_last_step_enters_month_once() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    j.world.boat = 2;
    j.world.rng.seed = 0x5578f641;
    let old = j.world.clone();
    j.travel(&d, 0x4d00, &c).unwrap();
    j.select_shore(false).unwrap();
    j.finish_shore(&d, &c).unwrap();
    assert_eq!(j.phase(), "prompt");
    assert_eq!(j.world.position, old.position);
    assert_eq!(j.world.remaining, old.remaining);
    assert_eq!(j.world.actions, old.actions + 1);
    let mut j = ready(&d);
    j.world.boat = 2;
    j.world.remaining = 1;
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.phase(), "shore");
    j.finish_shore(&d, &c).unwrap();
    assert_eq!(j.phase(), "monthly");
    assert_eq!(j.world.position.x, 41);
    assert_eq!(j.world.boat, 0);
    assert_eq!(j.month.months, 1);
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    cold.close_month(&d).unwrap();
    assert_eq!(cold.month.months, 1);
    assert_eq!(cold.world.actions, 1);
}
#[test]
fn invalid_shore_bindings_and_bytes_reject_and_v8_migrates() {
    let d = WorldData::water_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    j.magic.charges[6] = 0;
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 14);
    raw[..8].copy_from_slice(b"8SJRN008");
    raw.extend(crate::media_assets::checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
    j.world.position.x = 42;
    j.world.boat = 2;
    j.travel(&d, 0x4d00, &c).unwrap();
    for n in 0..7 {
        let mut b = j.clone();
        match n {
            0 => b.world.boat = 1,
            1 => b.travel_spell.shore.as_mut().unwrap().key = 0x1c0d,
            2 => b.travel_spell.teleport = Some(0),
            3 => b.cue = Some(0),
            4 => b.survey.bird = true,
            5 => b.world.position.x = 41,
            _ => b.magic.direction = true,
        };
        assert!(b.encode(&c, &d).is_err(), "{n}");
    }
    let mut raw = j.encode(&c, &d).unwrap();
    let at = raw.len() - 12;
    raw[at] = 2;
    let end = raw.len() - 8;
    let sum = crate::media_assets::checksum(&raw[..end]);
    raw[end..].copy_from_slice(&sum.to_le_bytes());
    assert!(Journey::decode(&c, &d, &raw).is_err());
}
#[cfg(feature = "desktop")]
#[test]
fn original_left_right_enter_and_escape_share_mouse_confirmation() {
    use crate::{
        management_ui::{Manager, Page},
        pointer::{Action, SHORE_CHOICES, Screen, hit},
    };
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    let mut ui = Manager::default();
    ui.key(1073741885, &mut j, &c, &d);
    ui.selected = 6;
    ui.key(13, &mut j, &c, &d);
    assert_eq!(ui.page, Page::World);
    assert_eq!(j.world.boat, 1);
    j.world.boat = 2;
    j.travel(&d, 0x4d00, &c).unwrap();
    ui.sync(&j);
    assert_eq!(ui.page, Page::Shore);
    let old = j.clone();
    for k in [32, 1073741906, 1073741905] {
        ui.key(k, &mut j, &c, &d);
        assert_eq!(j, old);
    }
    ui.key(1073741903, &mut j, &c, &d);
    assert!(!j.travel_spell.shore.unwrap().yes);
    ui.key(1073741904, &mut j, &c, &d);
    assert!(j.travel_spell.shore.unwrap().yes);
    for (i, r) in SHORE_CHOICES.iter().enumerate() {
        assert_eq!(
            hit(Screen::Shore, r.0 + r.2 / 2, r.1 + r.3 / 2),
            Some(Action::ShoreChoice(i == 0))
        );
    }
    ui.key(27, &mut j, &c, &d);
    assert_eq!(ui.page, Page::World);
    assert_eq!(j.world.position.x, 40);
    assert_eq!(j.world.boat, 2);
    assert_eq!(j.world.remaining, 324);
}
