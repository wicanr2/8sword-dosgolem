//! PAM menu navigation and an explicitly confirmed native new-game transaction.
use crate::{catalog::Catalog, journey::Journey, pointer::Rect, world::WorldData};
use std::path::{Path, PathBuf};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Page {
    Main,
    Confirm,
    Music,
    Message,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Intent {
    None,
    Exit,
    Continue,
    NewGame,
    Play(u8),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Menu {
    pub page: Page,
    pub selected: u8,
    pub yes: bool,
    pub font: u8,
    pub music: bool,
    pub playing: Option<u8>,
    pub message: &'static str,
    back: Page,
}
impl Default for Menu {
    fn default() -> Self {
        Self {
            page: Page::Main,
            selected: 0,
            yes: true,
            font: 0,
            music: true,
            playing: None,
            message: "",
            back: Page::Main,
        }
    }
}
pub fn navigate(selected: u8, count: u8, key: u16) -> u8 {
    match key {
        0x4800 => (selected + count - 1) % count,
        0x5000 => (selected + 1) % count,
        _ => selected,
    }
}
impl Menu {
    pub fn fail(&mut self, message: &'static str) {
        self.back = self.page;
        self.page = Page::Message;
        self.message = message;
    }
    pub fn select(&mut self, index: u8) {
        let count = match self.page {
            Page::Main => 3,
            Page::Music => 10,
            _ => 0,
        };
        if index < count {
            self.selected = index;
        }
    }
    pub fn key(&mut self, key: u16) -> Intent {
        match self.page {
            Page::Main => {
                self.selected = navigate(self.selected, 3, key);
                match key {
                    0x11b => return Intent::Exit,
                    0x1c0d => match self.selected {
                        0 => return Intent::Continue,
                        1 => {
                            self.page = Page::Confirm;
                            self.yes = true;
                        }
                        _ => {
                            self.page = Page::Music;
                            self.selected = 0;
                            self.playing = None;
                        }
                    },
                    _ => {}
                }
            }
            Page::Confirm => match key {
                0x4b00 | 0x4d00 => self.yes = !self.yes,
                0x11b => {
                    self.page = Page::Main;
                    self.selected = 1;
                }
                0x1c0d => {
                    if self.yes {
                        return Intent::NewGame;
                    }
                    self.page = Page::Main;
                    self.selected = 1;
                }
                _ => {}
            },
            Page::Music => {
                self.selected = navigate(self.selected, 10, key);
                match key {
                    0x11b => {
                        self.page = Page::Main;
                        self.selected = 0;
                        self.playing = None;
                    }
                    0x1c0d => {
                        self.playing = Some(self.selected + 1);
                        return Intent::Play(self.selected + 1);
                    }
                    _ => {}
                }
            }
            Page::Message => {
                if matches!(key, 0x11b | 0x1c0d) {
                    self.page = self.back;
                    self.message = "";
                }
            }
        }
        Intent::None
    }
}
pub struct Label {
    pub kind: &'static str,
    pub index: u8,
    pub x: i32,
    pub y: i32,
    pub text: &'static str,
}
pub fn labels() -> &'static Vec<Label> {
    static L: std::sync::OnceLock<Vec<Label>> = std::sync::OnceLock::new();
    L.get_or_init(|| {
        include_str!("../start-layout.tsv")
            .lines()
            .filter(|l| !l.starts_with('#'))
            .map(|l| {
                let v: Vec<_> = l.splitn(5, '\t').collect();
                assert_eq!(v.len(), 5);
                Label {
                    kind: v[0],
                    index: v[1].parse().expect("fixed menu index"),
                    x: v[2].parse::<i32>().expect("fixed x") * 24,
                    y: v[3].parse::<i32>().expect("fixed y") * 6 + 48,
                    text: v[4],
                }
            })
            .collect()
    })
}
pub fn row_box(music: bool, index: usize) -> Rect {
    Rect(
        336,
        48 + if music {
            index as i32 * 120
        } else {
            360 + index as i32 * 120
        },
        1224,
        120,
    )
}
pub fn choice_box(yes: bool) -> Rect {
    Rect(if yes { 1152 } else { 1296 }, 954, 96, 114)
}
pub fn text_width(s: &str) -> i32 {
    s.chars().map(|c| if c.is_ascii() { 24 } else { 48 }).sum()
}
pub struct Track {
    pub id: u8,
    pub title: &'static str,
    pub file: &'static str,
    pub fnv: u64,
}
pub fn tracks() -> &'static Vec<Track> {
    static T: std::sync::OnceLock<Vec<Track>> = std::sync::OnceLock::new();
    T.get_or_init(|| {
        include_str!("../start-music.tsv")
            .lines()
            .filter(|l| !l.starts_with('#'))
            .map(|l| {
                let v: Vec<_> = l.split('\t').collect();
                assert_eq!(v.len(), 4);
                Track {
                    id: v[0].parse().expect("track id"),
                    title: v[1],
                    file: v[2],
                    fnv: u64::from_str_radix(v[3], 16).expect("track FNV"),
                }
            })
            .collect()
    })
}
pub fn default_save_root() -> Result<PathBuf, String> {
    if let Some(p) = std::env::var_os("XDG_DATA_HOME").filter(|p| !p.is_empty()) {
        return Ok(PathBuf::from(p).join("8sword-remake"));
    }
    std::env::var_os("HOME")
        .filter(|p| !p.is_empty())
        .map(|p| PathBuf::from(p).join(".local/share/8sword-remake"))
        .ok_or_else(|| "請用--save-dir指定存檔目錄".into())
}
pub fn new_game<'a>(
    c: &'a Catalog,
    d: &WorldData,
    dir: &Path,
    seed: u32,
    font: u8,
    music: bool,
) -> Result<Journey<'a>, String> {
    new_game_rules(c, d, dir, seed, font, music, crate::rules::Mode::Native)
}
pub fn new_game_rules<'a>(
    c: &'a Catalog,
    d: &WorldData,
    dir: &Path,
    seed: u32,
    font: u8,
    music: bool,
    rules: crate::rules::Mode,
) -> Result<Journey<'a>, String> {
    let mut j = Journey::new(d, seed);
    j.rules = rules;
    j.world.font = font;
    j.world.music = music;
    let raw = j.encode(c, d)?;
    crate::checkpoint_store::reset_journey(dir, &raw, |b| Journey::decode(c, d, b).map(|_| ()))?;
    crate::rules::write_marker(dir, "journey.chk", &raw, rules)?;
    Ok(j)
}
#[cfg(test)]
#[path = "start_tests.rs"]
mod tests;
