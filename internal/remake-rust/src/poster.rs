//! Shared presentation shell. The game receives only central logical input.
use crate::media_assets::{Font, Image};
use std::{
    collections::BTreeSet,
    fs,
    io::Write,
    path::{Path, PathBuf},
    time::Instant,
};
pub const WIDTH: usize = 2944;
pub const HEIGHT: usize = 1320;
pub const OFFSET: usize = 512;
const IDS: [&str; 3] = ["wings", "cover", "off"];
const LABELS: [&str; 3] = ["龍虎延展", "經典封面", "關閉"];
const MATTE: [u8; 4] = [8, 36, 23, 255];
fn blank() -> Vec<u8> {
    MATTE.repeat(1024 * 1200)
}
pub struct Shell {
    panels: Vec<Vec<u8>>,
    font: Font,
    from: Vec<u8>,
    started: Instant,
    id: usize,
    menu: Option<usize>,
    pressed: Option<i32>,
    held: BTreeSet<i32>,
    blocked: BTreeSet<i32>,
    preference: Option<PathBuf>,
    assets_bad: bool,
    pub error: String,
}
pub fn preference(bytes: &[u8]) -> Result<usize, String> {
    if bytes.len() > 4096 {
        return Err("海報設定過大".into());
    }
    let input = std::str::from_utf8(bytes).map_err(|_| "海報設定字碼錯誤")?;
    let mut quoted = false;
    let mut s = String::new();
    for c in input.chars() {
        if c == '"' {
            quoted = !quoted;
        }
        if quoted || !c.is_ascii_whitespace() {
            s.push(c);
        }
    }
    for (i, id) in IDS.iter().enumerate() {
        if s == format!("{{\"schema\":1,\"poster\":\"{id}\"}}")
            || s == format!("{{\"poster\":\"{id}\",\"schema\":1}}")
        {
            return Ok(i);
        }
    }
    Err("海報設定無效".into())
}
impl Shell {
    pub fn load(root: &Path, store: Option<&Path>) -> Result<Option<Self>, String> {
        if !root.join("poster-font.bin").exists() {
            return Ok(None);
        }
        let font = Font::load(&root.join("poster-font.bin"))?;
        for ch in "海報龍虎延展經典封面關閉錯誤".chars() {
            if !font.glyphs.contains_key(&ch) {
                return Err("海報工具列缺字".into());
            }
        }
        let mut error = String::new();
        let mut panels = Vec::new();
        for name in ["wings", "cover"] {
            match Image::load(&root.join(format!("poster-{name}.rgba")), 1024, 1200) {
                Ok(im) if im.pixels.chunks_exact(4).all(|p| p[3] == 255) => panels.push(im.pixels),
                _ => {
                    panels.push(blank());
                    error = "海報素材錯誤".into();
                }
            }
        }
        panels.push(blank());
        let assets_bad = !error.is_empty();
        let path = store.map(|p| p.join("poster.json"));
        let mut id = 0;
        if let Some(p) = &path {
            match p.symlink_metadata() {
                Ok(meta) if meta.file_type().is_file() && meta.len() <= 4096 => match fs::read(p)
                    .map_err(|e| e.to_string())
                    .and_then(|b| preference(&b))
                {
                    Ok(i) => id = i,
                    Err(e) => error = e,
                },
                Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
                _ => error = "海報設定錯誤".into(),
            }
        }
        if assets_bad {
            id = 2;
            error = "海報素材錯誤".into();
        }
        Ok(Some(Self {
            from: panels[id].clone(),
            panels,
            font,
            started: Instant::now(),
            id,
            menu: None,
            pressed: None,
            held: BTreeSet::new(),
            blocked: BTreeSet::new(),
            preference: path,
            assets_bad,
            error,
        }))
    }
    fn panel_at(&self, ms: u128) -> Vec<u8> {
        if ms >= 400 {
            return self.panels[self.id].clone();
        }
        let t = ms as u32;
        self.from
            .iter()
            .zip(&self.panels[self.id])
            .map(|(&a, &b)| ((u32::from(a) * (400 - t) + u32::from(b) * t + 200) / 400) as u8)
            .collect()
    }
    fn start_fade(&mut self, id: usize, elapsed: u128) {
        self.from = self.panel_at(elapsed);
        self.id = if self.assets_bad { 2 } else { id };
        self.started = Instant::now();
        self.menu = None;
    }
    fn select(&mut self, id: usize) {
        self.start_fade(id, self.started.elapsed().as_millis());
        if let Err(e) = self.save() {
            self.error = e;
        }
    }
    fn save(&self) -> Result<(), String> {
        let Some(p) = &self.preference else {
            return Ok(());
        };
        if let Ok(meta) = p.symlink_metadata() {
            if !meta.file_type().is_file() {
                return Err("海報設定錯誤".into());
            }
        }
        let temp = p.with_file_name(format!(".poster-{}.tmp", std::process::id()));
        let mut owns_temp = false;
        let result = (|| {
            let mut f = fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&temp)
                .map_err(|e| e.to_string())?;
            owns_temp = true;
            f.write_all(format!("{{\"schema\":1,\"poster\":\"{}\"}}\n", IDS[self.id]).as_bytes())
                .map_err(|e| e.to_string())?;
            f.sync_all().map_err(|e| e.to_string())?;
            fs::rename(&temp, p).map_err(|e| e.to_string())
        })();
        if result.is_err() && owns_temp {
            let _ = fs::remove_file(&temp);
        }
        result
    }
    fn hit(&self, x: i32, y: i32) -> Option<i32> {
        if (2480..2920).contains(&x) && (2..46).contains(&y) {
            return Some(-1);
        }
        if self.menu.is_some() && (2480..2920).contains(&x) && (50..194).contains(&y) {
            return Some((y - 50) / 48);
        }
        None
    }
    /// Return true to consume an outer-shell event; otherwise translate mouse x.
    pub fn event(&mut self, b: &mut [u8; 56]) -> bool {
        let kind = u32::from_ne_bytes(b[..4].try_into().unwrap());
        if kind == 0x200 && b[12] == 13 {
            self.menu = None;
            self.pressed = None;
            self.blocked.extend(self.held.iter().copied());
            return false;
        }
        if kind == 0x300 || kind == 0x301 {
            let key = i32::from_ne_bytes(b[20..24].try_into().unwrap());
            if kind == 0x301 {
                self.held.remove(&key);
                return self.blocked.remove(&key) || self.menu.is_some();
            }
            self.held.insert(key);
            if self.blocked.contains(&key) {
                return true;
            }
            if let Some(i) = self.menu {
                if b[13] == 0 {
                    match key {
                        1073741906 => self.menu = Some((i + 2) % 3),
                        1073741905 => self.menu = Some((i + 1) % 3),
                        13 => self.select(i),
                        27 => self.menu = None,
                        _ => {}
                    }
                }
                self.blocked.insert(key);
                return true;
            }
            return false;
        }
        if matches!(kind, 0x400..=0x402) {
            let x = i32::from_ne_bytes(b[20..24].try_into().unwrap());
            let y = i32::from_ne_bytes(b[24..28].try_into().unwrap());
            let hit = self.hit(x, y);
            if kind == 0x401 {
                if self.menu.is_some() || hit.is_some() || !(512..2432).contains(&x) {
                    self.pressed = Some(hit.unwrap_or(-2));
                    return true;
                }
                self.pressed = None;
            }
            if kind == 0x402 {
                if let Some(pressed) = self.pressed.take() {
                    if hit == Some(pressed) {
                        if pressed == -1 {
                            self.menu = if self.menu.is_some() {
                                None
                            } else {
                                Some(self.id)
                            };
                            self.blocked.extend(self.held.iter().copied());
                        } else if (0..3).contains(&pressed) {
                            self.select(pressed as usize);
                        }
                    } else {
                        self.menu = None;
                    }
                    return true;
                }
                if self.menu.is_some() {
                    self.menu = None;
                    return true;
                }
            }
            if self.menu.is_some() || (kind != 0x402 && !(512..2432).contains(&x)) {
                return true;
            }
            b[20..24].copy_from_slice(&(x - 512).to_ne_bytes());
        }
        false
    }
    pub fn compose(&self, game: &[u8], ms: u128) -> Result<Vec<u8>, String> {
        if game.len() != 1920 * HEIGHT * 4 {
            return Err("海報中央畫布尺寸錯誤".into());
        }
        let mut out = MATTE.repeat(WIDTH * HEIGHT);
        let panel = self.panel_at(ms);
        for y in 0..HEIGHT {
            out[(y * WIDTH + 512) * 4..(y * WIDTH + 2432) * 4]
                .copy_from_slice(&game[y * 1920 * 4..(y + 1) * 1920 * 4]);
        }
        for y in 0..1200 {
            for side in 0..2 {
                let src = (y * 1024 + side * 512) * 4;
                let dst = ((y + 48) * WIDTH + side * 2432) * 4;
                out[dst..dst + 512 * 4].copy_from_slice(&panel[src..src + 512 * 4]);
            }
        }
        self.label(
            &mut out,
            &format!("海報 {}", LABELS[self.id]),
            [2480, 2, 440, 44],
        )?;
        if let Some(selected) = self.menu {
            for (i, name) in LABELS.iter().enumerate() {
                let rect = [2480, 50 + i as i32 * 48, 440, 48];
                self.label(
                    &mut out,
                    &format!("{}{name}", if i == selected { "* " } else { "  " }),
                    rect,
                )?;
            }
        }
        if !self.error.is_empty() {
            self.label(&mut out, "海報錯誤", [24, 2, 440, 44])?;
        }
        Ok(out)
    }
    fn label(&self, out: &mut [u8], s: &str, [x, y, w, h]: [i32; 4]) -> Result<(), String> {
        for yy in y..y + h {
            for xx in x..x + w {
                let at = (yy as usize * WIDTH + xx as usize) * 4;
                out[at..at + 4].copy_from_slice(&[20, 55, 40, 255]);
            }
        }
        let mut atx = x + 12;
        for ch in s.chars() {
            let dw = if ch.is_ascii() { 16 } else { 32 };
            if atx + dw > x + w - 12 {
                return Err("海報工具列文字超界".into());
            }
            let mask = self.font.glyphs.get(&ch).ok_or("海報工具列缺字")?;
            for yy in 0..32 {
                for xx in 0..dw {
                    let a = u32::from(mask[(yy * 2 * 64 + xx * 64 / dw) as usize]);
                    let dst = ((y + 6 + yy) as usize * WIDTH + (atx + xx) as usize) * 4;
                    for (c, color) in [255u32, 241, 181].iter().enumerate() {
                        out[dst + c] =
                            ((color * a + u32::from(out[dst + c]) * (255 - a) + 127) / 255) as u8;
                    }
                }
            }
            atx += dw;
        }
        Ok(())
    }
    pub fn status(&self) -> String {
        format!(
            "poster\t{}\nposter_menu\t{}\nposter_error\t{}\n",
            IDS[self.id],
            self.menu.is_some(),
            self.error
        )
    }
    pub fn elapsed(&self) -> u128 {
        self.started.elapsed().as_millis()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn shell() -> Shell {
        Shell {
            panels: vec![
                [0, 0, 0, 255].repeat(1024 * 1200),
                [200, 100, 50, 255].repeat(1024 * 1200),
                blank(),
            ],
            font: Font {
                glyphs: "海報龍虎延展經典封面關閉錯誤* "
                    .chars()
                    .map(|c| (c, vec![0; 4096]))
                    .collect(),
            },
            from: [0, 0, 0, 255].repeat(1024 * 1200),
            started: Instant::now(),
            id: 1,
            menu: None,
            pressed: None,
            held: BTreeSet::new(),
            blocked: BTreeSet::new(),
            preference: None,
            assets_bad: false,
            error: String::new(),
        }
    }
    fn event(kind: u32, x: i32, y: i32) -> [u8; 56] {
        let mut b = [0; 56];
        b[..4].copy_from_slice(&kind.to_ne_bytes());
        b[20..24].copy_from_slice(&x.to_ne_bytes());
        b[24..28].copy_from_slice(&y.to_ne_bytes());
        b
    }
    #[test]
    fn central_rgba_unchanged_at_fade_boundaries() {
        let s = shell();
        let game = [17, 33, 251, 255].repeat(1920 * HEIGHT);
        for ms in [0, 200, 400, 1000] {
            let out = s.compose(&game, ms).unwrap();
            for y in 0..HEIGHT {
                assert_eq!(
                    &out[(y * WIDTH + 512) * 4..(y * WIDTH + 2432) * 4],
                    &game[y * 1920 * 4..(y + 1) * 1920 * 4]
                );
            }
            assert_eq!(
                &out[(48 * WIDTH) * 4..(48 * WIDTH) * 4 + 4],
                &[
                    (ms.min(400) / 2) as u8,
                    (ms.min(400) / 4) as u8,
                    (ms.min(400) / 8) as u8,
                    255
                ]
            );
        }
    }
    #[test]
    fn shell_owns_menu_and_drag_while_game_receives_translated_click() {
        let mut s = shell();
        assert!(s.event(&mut event(0x401, 2500, 20)));
        assert!(s.event(&mut event(0x402, 2500, 20)));
        assert!(s.menu.is_some());
        let mut key = event(0x300, 1073741905, 0);
        assert!(s.event(&mut key));
        assert_eq!(s.menu, Some(2));
        assert!(s.event(&mut event(0x301, 1073741905, 0)));
        assert!(s.event(&mut event(0x300, 27, 0)));
        assert!(s.menu.is_none());
        assert!(s.event(&mut event(0x301, 27, 0)));
        assert!(s.event(&mut event(0x401, 100, 500)));
        assert!(s.event(&mut event(0x402, 900, 500)));
        let mut b = event(0x401, 900, 500);
        assert!(!s.event(&mut b));
        assert_eq!(i32::from_ne_bytes(b[20..24].try_into().unwrap()), 388);
    }
    #[test]
    fn rapid_reselection_begins_at_current_blend_and_focus_cancels_menu() {
        let mut s = shell();
        let before = s.panel_at(200);
        s.start_fade(2, 200);
        assert_eq!(before, s.panel_at(0));
        s.menu = Some(0);
        s.pressed = Some(1);
        let mut b = event(0x200, 0, 0);
        b[12] = 13;
        assert!(!s.event(&mut b));
        assert!(s.menu.is_none() && s.pressed.is_none());
    }
    #[test]
    fn preference_accepts_go_schema_and_rejects_extra_fields() {
        assert_eq!(
            preference(b"{\"schema\":1, \"poster\":\"cover\"}\n").unwrap(),
            1
        );
        for v in [
            b"{}".as_slice(),
            b"{\"schema\":2,\"poster\":\"off\"}",
            b"{\"schema\":1,\"poster\":\"off\",\"x\":0}",
        ] {
            assert!(preference(v).is_err());
        }
    }
}
