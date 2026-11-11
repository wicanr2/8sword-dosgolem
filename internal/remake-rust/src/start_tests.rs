use super::*;
use std::fs;
fn dir(name: &str) -> PathBuf {
    let p = std::env::temp_dir().join(format!("8sword-start-{name}-{}", std::process::id()));
    fs::create_dir(&p).unwrap();
    p
}
#[test]
fn original_92_key_vectors_and_confirm_results() {
    let mut n = 0;
    for l in include_str!("../start-input-reference.tsv")
        .lines()
        .filter(|l| !l.starts_with('#'))
    {
        let v: Vec<_> = l.split('\t').collect();
        let kind: u8 = v[0].parse().unwrap();
        let selected: u8 = v[1].parse().unwrap();
        let expected: u8 = v[3].parse().unwrap();
        let keys: Vec<u16> = v[2].split(',').map(|k| k.parse().unwrap()).collect();
        if kind < 2 {
            assert_eq!(
                navigate(selected, if kind == 0 { 3 } else { 10 }, keys[0]),
                expected,
                "{}",
                l
            );
        } else {
            let mut m = Menu {
                page: Page::Confirm,
                yes: selected != 0,
                ..Menu::default()
            };
            let mut result = false;
            for k in keys {
                result = m.key(k) == Intent::NewGame;
            }
            assert_eq!(u8::from(result), expected, "{l}");
        }
        n += 1;
    }
    assert_eq!(n, 92);
}
#[test]
fn main_defaults_cancel_and_music_return_follow_original_entry() {
    let mut m = Menu::default();
    assert_eq!(m.key(0x1c0d), Intent::Continue);
    m.key(0x5000);
    m.key(0x1c0d);
    assert_eq!(m.page, Page::Confirm);
    assert!(m.yes);
    m.key(0x4d00);
    assert_eq!(m.key(0x1c0d), Intent::None);
    assert_eq!((m.page, m.selected), (Page::Main, 1));
    m.key(0x5000);
    m.key(0x1c0d);
    assert_eq!((m.page, m.selected), (Page::Music, 0));
    m.key(0x4800);
    assert_eq!(m.key(0x1c0d), Intent::Play(10));
    m.key(0x11b);
    assert_eq!((m.page, m.selected, m.playing), (Page::Main, 0, None));
}
#[test]
fn fresh_world_matches_original_initial_fields_and_round_trips() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let p = dir("fresh");
    let j = new_game(&c, &d, &p, 1, 2, false).unwrap();
    assert_eq!(j.resources, [1, 0, 100, 500, 100, 0]);
    assert_eq!(
        (
            j.world.area,
            j.world.position.x,
            j.world.position.y,
            j.world.remaining
        ),
        (0, 40, 40, 324)
    );
    assert_eq!(j.army[0].count, 30);
    assert_eq!(j.army[0].unit.unwrap().native_kind(), Some(1));
    assert!(j.army[1..].iter().all(|s| s.count == 0));
    assert!((0..8).all(|i| !j.has_item(i)));
    assert_eq!((j.world.font, j.world.music), (2, false));
    assert_eq!(Journey::load(&p, &c, &d).unwrap(), j);
    assert_eq!(&fs::read(p.join("journey.chk")).unwrap()[..8], b"8SJRN016");
    fs::remove_dir_all(p).unwrap();
}
#[test]
fn only_confirmed_new_game_replaces_existing_or_corrupt_regular_progress() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let p = dir("reset");
    let mut old = Journey::new(&d, 987);
    old.resources[3] = 12;
    old.world.font = 1;
    old.save(&p, &c, &d).unwrap();
    let raw = fs::read(p.join("journey.chk")).unwrap();
    let mut m = Menu {
        selected: 1,
        ..Menu::default()
    };
    m.key(0x1c0d);
    m.key(0x11b);
    assert_eq!(fs::read(p.join("journey.chk")).unwrap(), raw);
    assert_eq!(Journey::load(&p, &c, &d).unwrap(), old);
    let fresh = new_game(&c, &d, &p, 1, 0, true).unwrap();
    assert_eq!(fresh.resources[3], 500);
    assert_ne!(fs::read(p.join("journey.chk")).unwrap(), raw);
    fs::write(p.join("journey.chk"), b"corrupt").unwrap();
    assert!(Journey::load(&p, &c, &d).is_err());
    assert!(old.save(&p, &c, &d).is_err());
    assert_eq!(fs::read(p.join("journey.chk")).unwrap(), b"corrupt");
    new_game(&c, &d, &p, 2, 1, true).unwrap();
    assert_eq!(Journey::load(&p, &c, &d).unwrap().world.rng.seed, 2);
    assert_eq!(fs::read_dir(&p).unwrap().count(), 1);
    fs::remove_dir_all(p).unwrap();
}
#[test]
fn locked_or_directory_slot_cannot_be_reset() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let p = dir("lock");
    fs::write(p.join("journey.chk"), b"old").unwrap();
    fs::write(p.join(".battle-checkpoint.lock"), b"writer").unwrap();
    assert!(new_game(&c, &d, &p, 1, 0, true).is_err());
    assert_eq!(fs::read(p.join("journey.chk")).unwrap(), b"old");
    fs::remove_file(p.join(".battle-checkpoint.lock")).unwrap();
    fs::remove_file(p.join("journey.chk")).unwrap();
    fs::create_dir(p.join("journey.chk")).unwrap();
    assert!(new_game(&c, &d, &p, 1, 0, true).is_err());
    assert!(p.join("journey.chk").is_dir());
    assert!(!p.join(".battle-checkpoint.lock").exists());
    fs::remove_dir_all(p).unwrap();
}
#[cfg(unix)]
#[test]
fn new_game_does_not_follow_slot_symlink() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let p = dir("link");
    fs::write(p.join("outside"), b"unchanged").unwrap();
    std::os::unix::fs::symlink(p.join("outside"), p.join("journey.chk")).unwrap();
    assert!(new_game(&c, &d, &p, 1, 0, true).is_err());
    assert_eq!(fs::read(p.join("outside")).unwrap(), b"unchanged");
    fs::remove_dir_all(p).unwrap();
}
#[test]
fn source_layout_and_pointer_release_cover_all_rows_and_preserve_save_shortcut() {
    use crate::pointer::{self, Action, Pointer, Screen};
    for l in labels() {
        assert!(l.x + text_width(l.text) <= 1920, "{}", l.text);
        assert!(l.y + 90 <= 1248);
    }
    for count in [3, 10] {
        let s = Screen::Start {
            count,
            confirm: false,
        };
        for i in 0..count {
            let r = row_box(count == 10, usize::from(i));
            let mut p = Pointer::default();
            assert_eq!(p.event(s, 0x401, r.0 + 5, r.1 + 5), None);
            assert_eq!(
                p.event(s, 0x402, r.0 + 5, r.1 + 5),
                Some(Action::StartChoice(i))
            );
            assert_eq!(p.event(s, 0x402, r.0 + 5, r.1 + 5), None);
        }
        assert_eq!(pointer::hit(s, 1500, 20), None);
        assert_eq!(pointer::hit(s, 1500, 1300), None);
    }
    assert_eq!(tracks().len(), 10);
    assert!(
        tracks()
            .iter()
            .enumerate()
            .all(|(i, t)| usize::from(t.id) == i + 1 && !t.title.is_empty())
    );
}
