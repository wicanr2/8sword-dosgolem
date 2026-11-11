use super::*;
use crate::{media_assets::checksum, world::Position};
fn before<'a>(d: &WorldData, index: usize) -> Journey<'a> {
    let mut j = Journey::new(d, 1);
    let site = sites()[index];
    j.world.area = site.area;
    j.world.position = Position {
        x: (site.position.x + 69) % 70,
        y: site.position.y,
    };
    j
}
#[test]
fn original_131_text_pointers_and_108_notice_shore_clock_cases() {
    let mut counts = [0; 2];
    let bases = [0x5be, 0x9f6, 0xcc6, 0x10fe, 0x140a, 0x19e6, 0x1da6, 0x21de];
    for line in include_str!("../notice-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let v: Vec<_> = line.split('\t').collect();
        let n = |i: usize| v[i].parse::<u16>().unwrap();
        match v[0] {
            "TEXT" => {
                let s = sites()
                    .iter()
                    .find(|s| u16::from(s.area) == n(1) && u16::from(s.index) == n(2))
                    .unwrap();
                assert_eq!(
                    (
                        u16::from(s.position.x),
                        u16::from(s.position.y),
                        bases[usize::from(s.area)] + 60 * n(2)
                    ),
                    (n(3), n(4), n(5))
                );
                counts[0] += 1;
            }
            "FLOW" => {
                let refuse = n(1) == 2 && n(2) == 0;
                assert_eq!(
                    (n(5), n(6), n(7), n(8), n(9)),
                    (
                        if n(1) == 2 && !refuse { 0 } else { n(1) },
                        n(4) - u16::from(!refuse),
                        u16::from(refuse),
                        1,
                        u16::from(n(1) == 2)
                    ),
                    "{line}"
                );
                counts[1] += 1;
            }
            _ => panic!("unknown reference"),
        }
    }
    assert_eq!(counts, [131, 108]);
}
#[test]
fn all_sites_enter_before_time_cold_confirm_and_space_revisit() {
    let d = WorldData::notice_fixture(false);
    let c = Catalog::builtin().unwrap();
    validate_maps(&d).unwrap();
    for i in 0..sites().len() {
        let mut j = before(&d, i);
        let old = j.clone();
        assert_eq!(j.travel(&d, 0x4d00, &c).unwrap(), None);
        assert_eq!(j.phase(), "map-notice");
        assert_eq!(j.world.position, sites()[i].position);
        assert_eq!(
            (j.world.remaining, j.world.rng, j.world.actions),
            (old.world.remaining, old.world.rng, old.world.actions)
        );
        let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
        assert_eq!(cold, j);
        assert!(j.travel(&d, 0x3920, &c).is_err());
        cold.close_map_notice(&d, &c).unwrap();
        assert_eq!(cold.world.remaining, old.world.remaining - 1);
        assert_eq!(cold.world.actions, old.world.actions + 1);
        assert!(cold.map_notice.is_none());
        if cold.phase() == "prompt" {
            cold.choose(&c, false).unwrap();
            if cold.battle.is_some() {
                continue;
            }
        }
        let steps = cold.world.remaining;
        assert_eq!(cold.travel(&d, 0x3920, &c).unwrap(), None);
        assert_eq!(cold.phase(), "map-notice");
        cold.close_map_notice(&d, &c).unwrap();
        assert_eq!(cold.world.remaining, steps);
    }
}
#[test]
fn notice_on_last_step_precedes_month_report_and_never_replays_on_close() {
    let d = WorldData::notice_fixture(false);
    let c = Catalog::builtin().unwrap();
    let mut j = before(&d, 0);
    j.world.remaining = 1;
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.phase(), "map-notice");
    assert!(j.month.pending.is_none());
    j.close_map_notice(&d, &c).unwrap();
    assert_eq!(j.phase(), "monthly");
    assert_eq!(j.world.remaining, 324);
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    cold.close_month(&d).unwrap();
    assert!(cold.map_notice.is_none());
    assert_eq!(cold.world.remaining, 324);
}
#[test]
fn water_notice_precedes_shore_and_yes_no_keep_correct_tail() {
    let d = WorldData::notice_fixture(true);
    let c = Catalog::builtin().unwrap();
    for yes in [false, true] {
        let mut j = before(&d, 0);
        j.world.boat = 2;
        let old = j.clone();
        j.travel(&d, 0x4d00, &c).unwrap();
        assert_eq!(j.phase(), "map-notice");
        assert_eq!(j.world.position, old.world.position);
        let raw = j.encode(&c, &d).unwrap();
        j = Journey::decode(&c, &d, &raw).unwrap();
        j.close_map_notice(&d, &c).unwrap();
        assert_eq!(j.phase(), "shore");
        j.select_shore(yes).unwrap();
        let raw = j.encode(&c, &d).unwrap();
        j = Journey::decode(&c, &d, &raw).unwrap();
        j.finish_shore(&d, &c).unwrap();
        assert!(j.map_notice.is_none());
        assert_eq!(
            j.world.position,
            if yes {
                sites()[0].position
            } else {
                old.world.position
            }
        );
        assert_eq!(j.world.boat, if yes { 0 } else { 2 });
        assert_eq!(j.world.remaining, old.world.remaining - u16::from(yes));
        assert_eq!(j.world.actions, old.world.actions + 1);
    }
}
#[test]
fn v12_migration_bad_notice_and_bad_text_fail_without_guessing() {
    let d = WorldData::notice_fixture(false);
    let c = Catalog::builtin().unwrap();
    let mut j = before(&d, 0);
    let mut old = j.encode(&c, &d).unwrap();
    old.truncate(old.len() - 16 - 9 - crate::guards::SUFFIX - crate::items::SUFFIX);
    old[..8].copy_from_slice(b"8SJRN012");
    old.extend(checksum(&old).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &old).unwrap(), j);
    j.travel(&d, 0x4d00, &c).unwrap();
    for n in 0..5 {
        let mut b = j.clone();
        match n {
            0 => b.map_notice.as_mut().unwrap().site = 255,
            1 => b.map_notice.as_mut().unwrap().key = 1,
            2 => b.world.position.x = 0,
            3 => b.magic.direction = true,
            _ => b.cue = Some(0),
        }
        assert!(b.encode(&c, &d).is_err());
    }
    let mut raw = j.encode(&c, &d).unwrap();
    let n = raw.len();
    raw[n - 12 - crate::guards::SUFFIX - crate::items::SUFFIX] = 2;
    let sum = checksum(&raw[..n - 8]);
    raw[n - 8..].copy_from_slice(&sum.to_le_bytes());
    assert!(Journey::decode(&c, &d, &raw).is_err());
    for t in ["", "invalid\n", "\t\n"] {
        assert!(parse_texts(t).is_err());
    }
}
#[test]
fn three_fonts_share_bounded_lines_and_original_confirmation_keys() {
    use crate::management_ui::{Manager, Page};
    let d = WorldData::notice_fixture(false);
    let c = Catalog::builtin().unwrap();
    for text in ["中文".repeat(15), "A".repeat(60)] {
        let rows = lines(&text).unwrap();
        assert!(rows.len() <= 3);
        assert_eq!(rows.concat(), text);
        assert!(rows.iter().all(|r| {
            r.chars()
                .map(|c| if c.is_ascii() { 36 } else { 72 })
                .sum::<u32>()
                <= 1248
        }));
    }
    assert!(lines(&"中".repeat(61)).is_err());
    for key in [13, 27] {
        let mut j = before(&d, 0);
        j.travel(&d, 0x4d00, &c).unwrap();
        let mut ui = Manager::default();
        ui.sync(&j);
        assert_eq!(ui.page, Page::MapNotice);
        let old = j.clone();
        for input in [32, 1073741903, 1073741885] {
            ui.key(input, &mut j, &c, &d);
            assert_eq!(j, old);
        }
        ui.key(key, &mut j, &c, &d);
        assert!(j.map_notice.is_none());
        assert!(ui.message.is_empty());
    }
}
