//! Spec031 READY: source-owned cinematic data; no CPU, DOS or RGB movie.
use crate::media_assets::{checksum, read_checked};
use std::path::Path;
pub const WIDTH: usize = 1920;
pub const HEIGHT: usize = 1200;
struct Reader<'a> {
    b: &'a [u8],
    at: usize,
}
impl<'a> Reader<'a> {
    fn take(&mut self, n: usize) -> Result<&'a [u8], String> {
        let z = self.at.checked_add(n).ok_or("開場長度超界")?;
        let b = self.b.get(self.at..z).ok_or("開場資料截斷")?;
        self.at = z;
        Ok(b)
    }
    fn byte(&mut self) -> Result<u8, String> {
        Ok(self.take(1)?[0])
    }
    fn word(&mut self) -> Result<usize, String> {
        Ok(u16::from_le_bytes(self.take(2)?.try_into().unwrap()) as usize)
    }
    fn dword(&mut self) -> Result<usize, String> {
        Ok(u32::from_le_bytes(self.take(4)?.try_into().unwrap()) as usize)
    }
    fn count(&mut self, max: usize) -> Result<usize, String> {
        let n = self.dword()?;
        if n > max {
            Err("開場筆數超界".into())
        } else {
            Ok(n)
        }
    }
}
struct Texture {
    w: usize,
    h: usize,
    kind: u8,
    raw: Vec<u8>,
}
enum Op {
    Blit {
        ids: [usize; 3],
        x: usize,
        y: usize,
        source: bool,
        clear: bool,
    },
    Erase(usize),
    Glyph {
        ids: [usize; 3],
        x: usize,
        y: usize,
        color: [u8; 3],
        mask: usize,
    },
    Actor {
        id: usize,
        rows: Vec<usize>,
        tint: Option<[u8; 3]>,
    },
    Ink {
        id: usize,
        x: usize,
        y: usize,
    },
}
pub struct Frame {
    pub ms: u32,
    pub stage: String,
    pub cue: u8,
    mode: u8,
    native: usize,
    clean: usize,
    palette: usize,
    pub revealed: usize,
    ops: Vec<usize>,
}
pub struct Pack {
    pub duration: u32,
    pub frames: Vec<Frame>,
    textures: Vec<Texture>,
    blobs: Vec<Vec<u8>>,
    ops: Vec<Op>,
    order: Vec<usize>,
    prelude: usize,
}
impl Pack {
    pub fn load(root: &Path) -> Result<Self, String> {
        let b = read_checked(&root.join("intro.bin"), b"8SINTRO2", 256 << 20)?;
        let m: Vec<_> = include_str!("../intro-plan.tsv")
            .split_whitespace()
            .collect();
        if m.len() != 3
            || checksum(&b) != u64::from_str_radix(m[1], 16).map_err(|_| "開場資料版本錯誤")?
        {
            return Err("開場資料版本不符".into());
        }
        let p = Self::parse(&b)?;
        if p.duration.to_string() != m[0] || p.frames.len().to_string() != m[2] {
            return Err("開場時長／節點不符".into());
        }
        Ok(p)
    }
    fn parse(b: &[u8]) -> Result<Self, String> {
        let mut r = Reader { b, at: 0 };
        if r.take(8)? != b"8SINTRO2" {
            return Err("開場標頭不符".into());
        }
        let duration = r.count(180000)? as u32;
        let prelude = r.dword()?;
        if r.dword()? != 64000 {
            return Err("開場揭圖筆數錯誤".into());
        }
        let mut order = Vec::new();
        let mut seen = vec![false; 64000];
        for _ in 0..64000 {
            let n = r.word()?;
            if n >= 64000 || seen[n] {
                return Err("開場揭圖順序錯誤".into());
            }
            seen[n] = true;
            order.push(n);
        }
        let mut textures = Vec::new();
        let mut total = 0;
        for _ in 0..r.count(4096)? {
            let (w, h, kind) = (r.word()?, r.word()?, r.byte()?);
            if w == 0 || w > WIDTH || h == 0 || h > HEIGHT || kind > 1 {
                return Err("開場材質形狀錯誤".into());
            }
            let n = w * h * if kind == 0 { 8 } else { 4 };
            total += n;
            if total > 512 << 20 {
                return Err("開場材質總量超界".into());
            }
            let (x, y, cw, ch) = (r.word()?, r.word()?, r.word()?, r.word()?);
            if cw == 0 || ch == 0 || x + cw > w || y + ch > h {
                return Err("開場透明邊界超界".into());
            }
            let stride = if kind == 0 { 8 } else { 4 };
            let cropped = r.take(cw * ch * stride)?;
            let mut raw = vec![0; n];
            for yy in 0..ch {
                let at = ((y + yy) * w + x) * stride;
                raw[at..at + cw * stride]
                    .copy_from_slice(&cropped[yy * cw * stride..(yy + 1) * cw * stride]);
            }
            if kind == 0
                && raw.chunks_exact(8).any(|p| {
                    let a = u16::from_le_bytes([p[6], p[7]]);
                    (0..3).any(|k| u16::from_le_bytes([p[k * 2], p[k * 2 + 1]]) > a)
                })
            {
                return Err("開場預乘色錯誤".into());
            }
            textures.push(Texture { w, h, kind, raw });
        }
        if textures
            .get(prelude)
            .is_none_or(|t| (t.w, t.h, t.kind) != (WIDTH, HEIGHT, 0))
        {
            return Err("開場前導材質錯誤".into());
        }
        let mut blobs = Vec::new();
        let mut total = 0;
        for _ in 0..r.count(12000)? {
            let n = r.count(128000)?;
            total += n;
            if total > 256 << 20 {
                return Err("開場索引總量超界".into());
            }
            let z = r.count(n.saturating_mul(3))?;
            let mut rr = Reader {
                b: r.take(z)?,
                at: 0,
            };
            let mut raw = Vec::with_capacity(n);
            while rr.at < rr.b.len() {
                let (c, v) = (rr.word()?, rr.byte()?);
                if c == 0 || raw.len() + c > n {
                    return Err("開場索引壓縮錯誤".into());
                }
                raw.resize(raw.len() + c, v);
            }
            if raw.len() != n {
                return Err("開場索引長度錯誤".into());
            }
            blobs.push(raw);
        }
        let texture = |id: usize| {
            textures
                .get(id)
                .ok_or_else(|| "開場材質索引超界".to_string())
        };
        let mut ops = Vec::new();
        for _ in 0..r.count(20000)? {
            let n = r.word()?;
            let mut o = Reader {
                b: r.take(n)?,
                at: 0,
            };
            let k = o.byte()?;
            let op = match k {
                0 | 1 | 7 | 8 => {
                    let mut ids = [0; 3];
                    if k < 2 {
                        ids.fill(o.dword()?);
                    } else {
                        for id in &mut ids {
                            *id = o.dword()?;
                        }
                    }
                    let (x, y) = (o.word()?, o.word()?);
                    let t = texture(ids[0])?;
                    for id in ids {
                        let a = texture(id)?;
                        if (a.w, a.h, a.kind) != (t.w, t.h, 0) {
                            return Err("開場字型材質形狀不符".into());
                        }
                    }
                    if x + t.w > WIDTH || y + t.h > HEIGHT {
                        return Err("開場圖層位置超界".into());
                    }
                    Op::Blit {
                        ids,
                        x,
                        y,
                        source: k == 1,
                        clear: k == 8,
                    }
                }
                2 => {
                    let id = o.dword()?;
                    let t = texture(id)?;
                    if (t.w, t.h, t.kind) != (WIDTH, HEIGHT, 0) {
                        return Err("開場抹字遮罩錯誤".into());
                    }
                    Op::Erase(id)
                }
                3 => {
                    let mut ids = [0; 3];
                    for id in &mut ids {
                        *id = o.dword()?;
                    }
                    let (x, y) = (o.word()?, o.word()?);
                    let color = o.take(3)?.try_into().unwrap();
                    let mask = o.dword()?;
                    let t = texture(ids[0])?;
                    for id in ids {
                        let a = texture(id)?;
                        if (a.w, a.h, a.kind) != (t.w, 90, 0) || ![24, 48].contains(&a.w) {
                            return Err("開場字模形狀錯誤".into());
                        }
                    }
                    if x % 3 != 0
                        || y % 6 != 0
                        || x + t.w > WIDTH
                        || y + 90 > HEIGHT
                        || blobs
                            .get(mask)
                            .is_none_or(|b| b.len() != t.w / 3 * 15 || b.iter().any(|v| *v > 1))
                    {
                        return Err("開場文字所有權錯誤".into());
                    }
                    Op::Glyph {
                        ids,
                        x,
                        y,
                        color,
                        mask,
                    }
                }
                4 | 5 => {
                    let id = o.dword()?;
                    let n = usize::from(o.byte()?);
                    let t = texture(id)?;
                    let want = if k == 4 {
                        (240, 276, 46)
                    } else {
                        (576, 300, 50)
                    };
                    if (t.w, t.h, n) != want || t.kind != 1 {
                        return Err("開場角色形狀錯誤".into());
                    }
                    let mut rows = Vec::new();
                    for _ in 0..n {
                        let row = o.word()?;
                        if row < 1600 || row + want.0 / 24 > 12000 {
                            return Err("開場角色列超界".into());
                        }
                        rows.push(row);
                    }
                    let tint = if k == 5 {
                        Some(o.take(3)?.try_into().unwrap())
                    } else {
                        None
                    };
                    Op::Actor { id, rows, tint }
                }
                6 => {
                    let id = o.dword()?;
                    let t = texture(id)?;
                    let (x, y) = (o.word()?, o.word()?);
                    if t.kind != 0 || x + t.w > 640 || y + t.h > 200 {
                        return Err("開場來源墨層錯誤".into());
                    }
                    Op::Ink { id, x, y }
                }
                _ => return Err("開場命令類型錯誤".into()),
            };
            if o.at != o.b.len() {
                return Err("開場命令尾端錯誤".into());
            }
            ops.push(op);
        }
        let mut frames = Vec::new();
        for _ in 0..r.count(12000)? {
            let ms = r.dword()? as u32;
            let n = usize::from(r.byte()?);
            let stage = std::str::from_utf8(r.take(n)?)
                .map_err(|_| "開場標籤錯誤")?
                .to_string();
            let (mode, cue) = (r.byte()?, r.byte()?);
            let (native, clean, palette, revealed) =
                (r.dword()?, r.dword()?, r.dword()?, r.dword()?);
            let len = if mode == 0xe {
                128000
            } else if mode == 0x13 {
                64000
            } else {
                return Err("開場繪圖模式錯誤".into());
            };
            if ms > duration
                || frames.last().is_some_and(|f: &Frame| f.ms >= ms)
                || cue > 1
                || revealed > 64000
                || [native, clean]
                    .iter()
                    .any(|id| blobs.get(*id).is_none_or(|b| b.len() != len))
                || blobs.get(palette).is_none_or(|b| b.len() != 768)
            {
                return Err("開場節點錯誤".into());
            }
            let n = r.word()?;
            if n > 2048 {
                return Err("開場圖層太多".into());
            }
            let mut list = Vec::new();
            for _ in 0..n {
                let id = r.dword()?;
                if id >= ops.len() {
                    return Err("開場圖層索引超界".into());
                }
                list.push(id);
            }
            frames.push(Frame {
                ms,
                stage,
                mode,
                cue,
                native,
                clean,
                palette,
                revealed,
                ops: list,
            });
        }
        if r.at != b.len()
            || frames.first().is_none_or(|f| f.ms != 0)
            || !frames.iter().any(|f| f.stage == "story-5-text")
            || !frames.iter().any(|f| f.revealed == 64000)
        {
            return Err("開場資料不完整".into());
        }
        Ok(Self {
            duration,
            frames,
            textures,
            blobs,
            ops,
            order,
            prelude,
        })
    }
    pub fn frame_index(&self, ms: u32) -> usize {
        self.frames
            .partition_point(|f| f.ms <= ms)
            .saturating_sub(1)
    }
    pub fn skip_waits_for_reveal(&self, index: usize) -> bool {
        let f = &self.frames[index];
        f.stage == "prelude-reveal" && f.revealed < 64000
    }
    pub fn render(&self, index: usize, hd: bool, font: usize) -> Result<Vec<u8>, String> {
        let f = self.frames.get(index).ok_or("開場節點超界")?;
        if font >= 3 {
            return Err("開場字型錯誤".into());
        }
        let mut out = vec![0; WIDTH * HEIGHT * 4];
        let src = &self.blobs[if hd { f.clean } else { f.native }];
        let pal = &self.blobs[f.palette];
        let width = if f.mode == 0xe { 640 } else { 320 };
        let sx = WIDTH / width;
        for (y, row) in src.chunks_exact(width).enumerate() {
            for (x, v) in row.iter().enumerate() {
                let c = &pal[usize::from(*v) * 3..usize::from(*v) * 3 + 3];
                for yy in y * 6..y * 6 + 6 {
                    for xx in x * sx..x * sx + sx {
                        let at = (yy * WIDTH + xx) * 4;
                        out[at..at + 3].copy_from_slice(c);
                        out[at + 3] = 255;
                    }
                }
            }
        }
        if !hd {
            return Ok(out);
        }
        if f.revealed > 0 {
            let t = &self.textures[self.prelude];
            for p in &self.order[..f.revealed] {
                for y in p / 320 * 6..p / 320 * 6 + 6 {
                    for x in p % 320 * 6..p % 320 * 6 + 6 {
                        let at = y * WIDTH + x;
                        let c = &t.raw[at * 8..at * 8 + 8];
                        for k in 0..4 {
                            out[at * 4 + k] = c[k * 2 + 1];
                        }
                    }
                }
            }
            return Ok(out);
        }
        for id in &f.ops {
            match &self.ops[*id] {
                Op::Blit {
                    ids,
                    x,
                    y,
                    source,
                    clear,
                } => {
                    let t = &self.textures[ids[font]];
                    for yy in 0..t.h {
                        for xx in 0..t.w {
                            let at = ((y + yy) * WIDTH + x + xx) * 4;
                            let c = &t.raw[(yy * t.w + xx) * 8..(yy * t.w + xx + 1) * 8];
                            if *clear {
                                out[at..at + 3].fill(0);
                            }
                            over16(&mut out[at..at + 4], c, *source);
                        }
                    }
                }
                Op::Erase(id) => {
                    let t = &self.textures[*id];
                    for (at, c) in t.raw.chunks_exact(8).enumerate() {
                        let a = u32::from(u16::from_le_bytes([c[6], c[7]]));
                        for k in 0..3 {
                            out[at * 4 + k] = ((u32::from(out[at * 4 + k]) * (65535 - a) * 257
                                / 65535)
                                >> 8) as u8;
                        }
                    }
                }
                Op::Glyph {
                    ids,
                    x,
                    y,
                    color,
                    mask,
                } => {
                    let t = &self.textures[ids[font]];
                    for yy in 0..90 {
                        for xx in 0..t.w {
                            if self.blobs[*mask][(yy / 6) * (t.w / 3) + xx / 3] == 0 {
                                continue;
                            }
                            let a = t.raw[(yy * t.w + xx) * 8 + 7];
                            let at = ((y + yy) * WIDTH + x + xx) * 4;
                            for k in 0..3 {
                                out[at + k] = ((u32::from(color[k]) * u32::from(a)
                                    + u32::from(out[at + k]) * u32::from(255 - a)
                                    + 127)
                                    / 255) as u8;
                            }
                        }
                    }
                }
                Op::Actor { id, rows, tint } => {
                    let t = &self.textures[*id];
                    for y in 0..t.h {
                        for x in 0..t.w {
                            let c = &t.raw[(y * t.w + x) * 4..(y * t.w + x + 1) * 4];
                            let address = rows[y / 6] + x / 24;
                            let (dx, dy) = (address % 80 * 24 + x % 24, address / 80 * 6 + y % 6);
                            let at = (dy * WIDTH + dx) * 4;
                            let a = u32::from(c[3]);
                            for k in 0..3 {
                                let v = if let Some(tint) = tint {
                                    (u32::from(*c[..3].iter().max().unwrap()) * u32::from(tint[k])
                                        + 127)
                                        / 255
                                } else {
                                    u32::from(c[k])
                                };
                                out[at + k] = ((v * a + u32::from(out[at + k]) * (255 - a) + 127)
                                    / 255) as u8;
                            }
                        }
                    }
                }
                Op::Ink { id, x, y } => {
                    let t = &self.textures[*id];
                    for sy in 0..t.h {
                        for sx in 0..t.w {
                            let c = &t.raw[(sy * t.w + sx) * 8..(sy * t.w + sx + 1) * 8];
                            let (y, x) = (y + sy, x + sx);
                            if c[7] == 0 {
                                continue;
                            }
                            for yy in y * 6..y * 6 + 6 {
                                for xx in x * 3..x * 3 + 3 {
                                    let at = (yy * WIDTH + xx) * 4;
                                    for k in 0..4 {
                                        out[at + k] = c[k * 2 + 1];
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        Ok(out)
    }
}
fn over16(d: &mut [u8], s: &[u8], source: bool) {
    let a = u32::from(u16::from_le_bytes([s[6], s[7]]));
    let inv = if source { 0 } else { (65535 - a) * 257 };
    for k in 0..4 {
        let v = u32::from(u16::from_le_bytes([s[k * 2], s[k * 2 + 1]]));
        d[k] = ((u32::from(d[k]) * inv / 65535 + v) >> 8) as u8;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn skipping_reveal_waits_for_completion_and_clock_uses_last_committed_node() {
        let frame = |ms, stage: &str, revealed| Frame {
            ms,
            stage: stage.into(),
            cue: 0,
            mode: 0x13,
            native: 0,
            clean: 0,
            palette: 0,
            revealed,
            ops: vec![],
        };
        let p = Pack {
            duration: 30,
            frames: vec![
                frame(0, "museum-portrait", 0),
                frame(10, "prelude-reveal", 32000),
                frame(20, "prelude-complete", 64000),
            ],
            textures: vec![],
            blobs: vec![],
            ops: vec![],
            order: vec![],
            prelude: 0,
        };
        assert!(!p.skip_waits_for_reveal(0));
        assert!(p.skip_waits_for_reveal(1));
        assert!(!p.skip_waits_for_reveal(2));
        assert_eq!(p.frame_index(19), 1);
        assert_eq!(p.frame_index(20), 2);
        assert_eq!(p.frame_index(u32::MAX), 2);
    }
    #[test]
    fn malformed_packets_and_oversized_counts_are_rejected() {
        for n in 0..128 {
            assert!(Pack::parse(&vec![0; n]).is_err());
        }
        let mut b = b"8SINTRO2".to_vec();
        b.extend(200000u32.to_le_bytes());
        assert!(Pack::parse(&b).is_err());
        let mut b = b"8SINTRO2".to_vec();
        b.extend(100u32.to_le_bytes());
        b.extend(0u32.to_le_bytes());
        b.extend(64000u32.to_le_bytes());
        b.extend(vec![0; 128000]);
        assert!(Pack::parse(&b).is_err());
    }
    #[test]
    fn source_reference_covers_all_five_pages_and_both_original_and_hd() {
        let rows: Vec<_> = include_str!("../intro-reference.tsv")
            .lines()
            .filter(|l| !l.starts_with('#'))
            .collect();
        assert_eq!(rows.len(), 18);
        for i in 1..=5 {
            assert!(rows.iter().any(|l| l.contains(&format!("story-{i}-text"))));
        }
        for l in rows {
            let v: Vec<_> = l.split('\t').collect();
            assert_eq!(v.len(), 7);
            for h in &v[3..] {
                assert!(u64::from_str_radix(h, 16).is_ok());
            }
        }
    }
    #[test]
    fn original_byte_rows_wrap_and_pointer_cannot_save_in_opening() {
        use crate::pointer::{Action, Screen, hit};
        assert_eq!(hit(Screen::Intro, 220, 1296), Some(Action::Key(27)));
        assert_eq!(hit(Screen::Intro, 700, 1296), Some(Action::Key(113)));
        assert_eq!(hit(Screen::Intro, 1500, 20), None);
        let row = 79usize;
        let x = 30usize;
        assert_eq!(
            ((row + x / 24) % 80 * 24 + x % 24, (row + x / 24) / 80 * 6),
            (6, 6)
        );
    }
}
