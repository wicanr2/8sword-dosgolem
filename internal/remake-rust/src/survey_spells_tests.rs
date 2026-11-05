use super::*;
use crate::{catalog::Catalog, world::WorldData};
fn ready<'a>(d: &WorldData) -> Journey<'a> {
    let mut j = Journey::new(d, 1);
    j.magic.book = true;
    j.resources[5] = 6;
    j.magic.charges = [0, 0, 0, 0, 2, 2, 0, 0];
    j
}
#[test]
fn original_stop_receipt_and_all_rank_truncation_boundaries_match() {
    for line in include_str!("../survey-stop-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let f: Vec<u16> = line.split('\t').map(|s| s.parse().unwrap()).collect();
        assert_eq!(extension(f[0] as u8, f[1]).unwrap(), (f[5], f[6] as u8));
        assert_eq!((f[3], f[7], f[4] - f[8]), (0, 1, 1));
    }
    for (rank, factor) in [(1, 8), (2, 10), (3, 12), (4, 15), (5, 18)] {
        for before in [1, 5, 7, 111, 324, 32767 / factor] {
            assert_eq!(
                extension(rank, before).unwrap(),
                (before * factor / 6, factor as u8)
            );
        }
        assert!(extension(rank, 32767 / factor + 1).is_err());
    }
    assert!(extension(0, 1).is_err());
    assert!(extension(6, 1).is_err());
    assert!(extension(1, 0).is_err());
}
#[test]
fn repeated_stop_spends_charge_without_reextending_and_cold_state_remembers_tempo() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    let before = j.clone();
    j.cast_stop_time().unwrap();
    assert_eq!(
        (j.world.remaining, j.survey.tempo, j.magic.charges[4]),
        (432, 8, 1)
    );
    assert!(j.survey.stopped);
    assert_eq!(j.world.rng, before.world.rng);
    assert_eq!(j.world.position, before.world.position);
    assert_eq!(j.world.actions, before.world.actions);
    assert_eq!(j.world.explored, before.world.explored);
    assert_eq!(j.resources, before.resources);
    assert_eq!(j.army, before.army);
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    cold.cast_stop_time().unwrap();
    assert_eq!(
        (
            cold.world.remaining,
            cold.survey.tempo,
            cold.magic.charges[4]
        ),
        (432, 8, 0)
    );
    let old = cold.clone();
    assert!(cold.cast_stop_time().is_err());
    assert_eq!(cold, old);
    j.world.remaining = u16::MAX;
    j.survey = Survey::default();
    let old = j.clone();
    assert!(j.cast_stop_time().is_err());
    assert_eq!(j, old);
}
#[test]
fn monthly_resets_stop_and_cold_confirmation_does_not_restore_old_flag() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    j.cast_stop_time().unwrap();
    j.world.remaining = 1;
    j.travel(&d, 0x5000, &c).unwrap();
    assert_eq!(j.phase(), "monthly");
    assert_eq!(j.survey, Survey::default());
    let mut j = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    j.close_month(&d).unwrap();
    j.cast_stop_time().unwrap();
    assert_eq!(j.world.remaining, 432);
    assert_eq!(j.survey.tempo, 8);
}
#[test]
fn bird_projects_full_region_without_touching_exploration_or_spending_on_resume() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    let before = j.world.clone();
    j.begin_bird_view().unwrap();
    assert_eq!(j.world, before);
    assert_eq!(j.magic.charges[5], 1);
    assert_eq!(j.phase(), "birdseye");
    assert_eq!(
        crate::minimap::all_cells(&d, &j.world)
            .unwrap()
            .iter()
            .filter(|n| **n != 0)
            .count(),
        5600
    );
    assert_eq!(
        crate::minimap::cells(&d, &j.world)
            .unwrap()
            .iter()
            .filter(|n| **n != 0)
            .count(),
        9
    );
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    let old = cold.clone();
    assert!(cold.begin_bird_view().is_err());
    assert!(cold.cast_stop_time().is_err());
    assert!(cold.travel(&d, 0x5000, &c).is_err());
    assert!(cold.dismiss(0).is_err());
    assert_eq!(cold, old);
    cold.close_bird_view().unwrap();
    assert_eq!(cold.world, before);
    assert_eq!(cold.magic.charges[5], 1);
    let old = cold.clone();
    assert!(cold.close_bird_view().is_err());
    assert_eq!(cold, old);
}
#[test]
fn malformed_flags_and_real_v6_shape_are_checked_at_save_boundary() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let j = ready(&d);
    for n in 0..5 {
        let mut bad = j.clone();
        match n {
            0 => bad.survey.tempo = 8,
            1 => bad.survey.stopped = true,
            2 => {
                bad.survey.bird = true;
                bad.magic.selected = 5;
                bad.cue = Some(0)
            }
            3 => bad.survey.bird = true,
            _ => {
                bad.survey.stopped = true;
                bad.survey.tempo = 7
            }
        };
        assert!(bad.encode(&c, &d).is_err());
    }
    let mut j = j;
    j.magic.charges[4] = 0;
    j.magic.charges[5] = 0;
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 18);
    raw[..8].copy_from_slice(b"8SJRN006");
    raw.extend(crate::media_assets::checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
}
#[cfg(feature = "desktop")]
#[test]
fn original_keys_and_mouse_bird_map_only_close_with_enter_or_escape() {
    use crate::management_ui::{Manager, Page};
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    let mut ui = Manager::default();
    ui.key(1073741885, &mut j, &c, &d);
    ui.selected = 4;
    ui.key(13, &mut j, &c, &d);
    assert_eq!(ui.page, Page::World);
    assert_eq!(j.world.remaining, 432);
    ui.key(1073741885, &mut j, &c, &d);
    ui.selected = 5;
    ui.key(13, &mut j, &c, &d);
    assert_eq!(ui.page, Page::Bird);
    let old = j.clone();
    for key in [32, 1073741903, 1073741886] {
        ui.key(key, &mut j, &c, &d);
        assert_eq!(ui.page, Page::Bird);
        assert_eq!(j, old);
    }
    ui.key(13, &mut j, &c, &d);
    assert_eq!(ui.page, Page::World);
    assert!(!j.survey.bird);
}
