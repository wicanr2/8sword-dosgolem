use super::*;
use crate::{catalog::Catalog, media_assets::checksum, world::Position};
fn ready<'a>(d: &WorldData) -> Journey<'a> {
    let mut j = Journey::new(d, 1);
    j.magic.book = true;
    j.magic.charges[7] = 2;
    j.resources[5] = 3;
    j
}
#[test]
fn all_original_region_starts_preserve_clock_rng_fog_army_and_resources() {
    let mut d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    for area in 0..8 {
        d.starts[area] = Position {
            x: area as u8 + 5,
            y: area as u8 + 10,
        };
    }
    assert_eq!(regions().len(), 8);
    assert!(
        regions()
            .iter()
            .all(|n| n.replace(' ', "").chars().count() == 3)
    );
    for area in 0..8 {
        let mut j = ready(&d);
        j.world.area = 7;
        j.world.boat = 2;
        let before = j.clone();
        j.begin_teleport().unwrap();
        assert_eq!(j.travel_spell.teleport, Some(7));
        j.select_teleport(area).unwrap();
        let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
        assert_eq!(cold, j);
        cold.finish_teleport(&d, true).unwrap();
        assert_eq!(cold.world.area, area);
        assert_eq!(cold.world.position, d.starts[usize::from(area)]);
        assert_eq!(cold.world.boat, 0);
        assert_eq!(cold.world.facing, before.world.facing);
        assert_eq!(cold.world.rng, before.world.rng);
        assert_eq!(cold.world.actions, before.world.actions);
        assert_eq!(cold.world.remaining, before.world.remaining);
        assert_eq!(cold.world.explored, before.world.explored);
        assert_eq!(cold.resources, before.resources);
        assert_eq!(cold.army, before.army);
        assert_eq!(cold.magic.charges[7], 1);
        assert_eq!(
            Journey::decode(&c, &d, &cold.encode(&c, &d).unwrap()).unwrap(),
            cold
        );
    }
}
#[test]
fn cancel_spends_once_cold_modal_blocks_gameplay_and_invalid_calls_are_atomic() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    let world = j.world.clone();
    j.begin_teleport().unwrap();
    j.select_teleport(5).unwrap();
    let old = j.clone();
    assert!(j.begin_teleport().is_err());
    assert!(j.select_teleport(8).is_err());
    assert!(j.travel(&d, 0x5000, &c).is_err());
    assert!(j.cast_stop_time().is_err());
    assert!(j.begin_bird_view().is_err());
    assert!(j.dismiss(0).is_err());
    assert_eq!(old, j);
    let mut j = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    j.finish_teleport(&d, false).unwrap();
    assert_eq!(j.world, world);
    assert_eq!(j.magic.charges[7], 1);
    j.begin_teleport().unwrap();
    j.finish_teleport(&d, false).unwrap();
    let old = j.clone();
    assert!(j.begin_teleport().is_err());
    assert!(j.finish_teleport(&d, true).is_err());
    assert!(j.select_teleport(0).is_err());
    assert_eq!(j, old);
}
#[test]
fn map_reload_drops_departure_and_destination_bridges_but_cancel_keeps_them() {
    let d = WorldData::magic_fixture(2);
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    j.magic.bridges = vec![40 * 70 + 40];
    let fog = j.world.explored.clone();
    j.begin_teleport().unwrap();
    j.finish_teleport(&d, false).unwrap();
    assert_eq!(
        j.magic
            .view(&d)
            .unwrap()
            .tile(0, Position { x: 40, y: 40 })
            .unwrap(),
        52
    );
    j.begin_teleport().unwrap();
    j.finish_teleport(&d, true).unwrap();
    assert!(j.magic.bridges.is_empty());
    assert_eq!(j.world.explored, fog);
    assert_eq!(
        j.magic
            .view(&d)
            .unwrap()
            .tile(0, Position { x: 40, y: 40 })
            .unwrap(),
        2
    );
    j.encode(&c, &d).unwrap();
}
#[test]
fn malformed_pending_fields_reject_and_real_v7_layout_migrates() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    j.magic.charges[7] = 0;
    let mut v7 = j.encode(&c, &d).unwrap();
    v7.truncate(v7.len() - 17 - 1);
    v7[..8].copy_from_slice(b"8SJRN007");
    v7.extend(checksum(&v7).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &v7).unwrap(), j);
    j.magic.charges[7] = 1;
    j.begin_teleport().unwrap();
    for n in 0..8 {
        let mut bad = j.clone();
        match n {
            0 => bad.travel_spell.teleport = Some(8),
            1 => bad.magic.book = false,
            2 => bad.magic.selected = 5,
            3 => bad.survey.bird = true,
            4 => bad.cue = Some(0),
            5 => bad.magic.direction = true,
            6 => {
                bad.magic.shop = Some(crate::world_magic::PendingShop {
                    index: 0,
                    moved: false,
                })
            }
            _ => bad.magic.charges[3] = 4,
        }
        assert!(bad.encode(&c, &d).is_err(), "{n}");
    }
    let mut raw = j.encode(&c, &d).unwrap();
    let at = raw.len() - 15;
    raw[at] = 254;
    let end = raw.len() - 8;
    let hash = checksum(&raw[..end]);
    raw[end..].copy_from_slice(&hash.to_le_bytes());
    assert!(Journey::decode(&c, &d, &raw).is_err());
}
#[cfg(feature = "desktop")]
#[test]
fn keyboard_wrap_mouse_destination_and_cancel_keep_original_selection_flow() {
    use crate::{
        management_ui::{Manager, Page},
        pointer::{Action, Screen, hit},
    };
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    let mut ui = Manager::default();
    ui.key(1073741885, &mut j, &c, &d);
    ui.selected = 7;
    ui.key(13, &mut j, &c, &d);
    assert_eq!(ui.page, Page::Teleport);
    ui.key(1073741906, &mut j, &c, &d);
    assert_eq!(j.travel_spell.teleport, Some(7));
    ui.key(1073741905, &mut j, &c, &d);
    assert_eq!(j.travel_spell.teleport, Some(0));
    for i in 0..8 {
        assert_eq!(
            hit(Screen::Teleport, 600, 210 + i * 120),
            Some(Action::TeleportChoice(i as usize))
        );
    }
    let old = j.clone();
    ui.key(32, &mut j, &c, &d);
    assert_eq!(old, j);
    ui.key(27, &mut j, &c, &d);
    assert_eq!(ui.page, Page::World);
    assert_eq!(j.magic.charges[7], 1);
}
