//! Spec031 READY: source-owned linear cinematic commands. No guest runtime.
use crate::media_assets::read_checked;
use std::path::Path;
pub const PLAN_HASH: u64 = 0x13b0f4ebc624c905;
pub const DURATION: u32 = 46825;
pub const WIDTH: usize = 1920;
pub const HEIGHT: usize = 1200;
const PALETTE: [[u8; 3]; 16] = [
    [0, 0, 0],
    [0, 0, 170],
    [0, 170, 0],
    [0, 170, 170],
    [170, 0, 0],
    [170, 0, 170],
    [170, 85, 0],
    [170, 170, 170],
    [85, 85, 85],
    [85, 85, 255],
    [85, 255, 85],
    [85, 255, 255],
    [255, 85, 85],
    [255, 85, 255],
    [255, 255, 85],
    [255, 255, 255],
];
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Progress {
    pub elapsed_ms: u32,
    pub hd: bool,
}
impl Default for Progress {
    fn default() -> Self {
        Self {
            elapsed_ms: 0,
            hd: true,
        }
    }
}
struct Bitmap {
    w: usize,
    h: usize,
    mode: u8,
    repeat: bool,
    textures: [u32; 3],
    pixels: Vec<u8>,
    mask: Vec<u8>,
}
struct Texture {
    width: usize,
    height: usize,
    pixels: Vec<u16>,
}
struct Glyph {
    w: usize,
    mask: Vec<u8>,
    alpha: [Vec<u8>; 3],
}
#[derive(Clone, Copy)]
struct Op {
    kind: u8,
    id: usize,
    x: usize,
    y: usize,
    fg: u8,
    bg: u8,
}
pub struct Frame {
    pub ms: u32,
    pub stage: u8,
    pub cue: u8,
    ops: Vec<usize>,
}
pub struct Pack {
    textures: Vec<Texture>,
    bitmaps: Vec<Bitmap>,
    glyphs: Vec<Glyph>,
    ops: Vec<Op>,
    pub frames: Vec<Frame>,
}
struct Reader<'a> {
    b: &'a [u8],
    at: usize,
}
impl<'a> Reader<'a> {
    fn take(&mut self, n: usize) -> Result<&'a [u8], String> {
        let end = self.at.checked_add(n).ok_or("結局長度超界")?;
        let v = self.b.get(self.at..end).ok_or("結局資料截斷")?;
        self.at = end;
        Ok(v)
    }
    fn byte(&mut self) -> Result<u8, String> {
        Ok(self.take(1)?[0])
    }
    fn word(&mut self) -> Result<usize, String> {
        Ok(u16::from_le_bytes(self.take(2)?.try_into().unwrap()) as usize)
    }
    fn dword(&mut self) -> Result<u32, String> {
        Ok(u32::from_le_bytes(self.take(4)?.try_into().unwrap()))
    }
    fn count(&mut self, max: u32) -> Result<usize, String> {
        let n = self.dword()?;
        if n > max {
            return Err("結局筆數超界".into());
        }
        Ok(n as usize)
    }
}
impl Pack {
    pub fn load(root: &Path) -> Result<Self, String> {
        let raw = read_checked(&root.join("ending.bin"), b"8SEND003", 128 << 20)?;
        if crate::media_assets::checksum(&raw) != PLAN_HASH {
            return Err("結局命令版本不符".into());
        }
        Self::parse(&raw)
    }
    fn parse(raw: &[u8]) -> Result<Self, String> {
        let mut r = Reader { b: raw, at: 8 };
        if raw.get(..8) != Some(b"8SEND003") || r.dword()? != DURATION {
            return Err("結局時長或標頭錯誤".into());
        }
        let mut textures = Vec::new();
        for _ in 0..r.count(128)? {
            let (w, h) = (r.word()?, r.word()?);
            if w == 0 || w > WIDTH || h == 0 || h > HEIGHT {
                return Err("結局材質尺寸錯誤".into());
            }
            let pixels: Vec<u16> = r
                .take(w * h * 8)?
                .chunks_exact(2)
                .map(|p| u16::from_le_bytes([p[0], p[1]]))
                .collect();
            if pixels
                .chunks_exact(4)
                .any(|p| p[..3].iter().any(|c| *c > p[3]))
            {
                return Err("結局預乘色錯誤".into());
            }
            textures.push(Texture {
                width: w,
                height: h,
                pixels,
            });
        }
        let mut bitmaps = Vec::new();
        let count = r.word()?;
        if count == 0 || count > 128 {
            return Err("結局原圖筆數錯誤".into());
        }
        for _ in 0..count {
            let (w, h, mode, rep) = (r.word()?, r.word()?, r.byte()?, r.byte()?);
            if w == 0 || w > 640 || w % 8 != 0 || h == 0 || h > 200 || mode > 4 || rep > 1 {
                return Err("結局原圖形狀錯誤".into());
            }
            let mut ids = [0; 3];
            for id in &mut ids {
                *id = r.dword()?;
                if mode == 0 {
                    if *id != u32::MAX {
                        return Err("結局來源材質錯誤".into());
                    }
                } else {
                    let im = textures.get(*id as usize).ok_or("結局材質索引錯誤")?;
                    if (im.width, im.height) != (w * 3, h * 6) {
                        return Err("結局材質幾何不符".into());
                    }
                }
            }
            let pixels = r.take(w * h)?.to_vec();
            let mask = r.take(w * h)?.to_vec();
            if pixels.iter().any(|v| *v > 15) || mask.iter().any(|v| *v > 1) {
                return Err("結局像素或遮罩錯誤".into());
            }
            bitmaps.push(Bitmap {
                w,
                h,
                mode,
                repeat: rep == 1,
                textures: ids,
                pixels,
                mask,
            });
        }
        let mut glyphs = Vec::new();
        let count = r.word()?;
        if count == 0 || count > 512 {
            return Err("結局字模筆數錯誤".into());
        }
        for _ in 0..count {
            let w = usize::from(r.byte()?);
            if ![8, 16].contains(&w) {
                return Err("結局字模寬度錯誤".into());
            }
            let mask = r.take(w * 15)?.to_vec();
            if mask.iter().any(|v| *v > 1) {
                return Err("結局字模遮罩錯誤".into());
            }
            let mut alpha: [Vec<u8>; 3] = std::array::from_fn(|_| Vec::new());
            for a in &mut alpha {
                *a = r.take(w * 3 * 90)?.to_vec()
            }
            glyphs.push(Glyph { w, mask, alpha });
        }
        let mut ops = Vec::new();
        for _ in 0..r.count(100000)? {
            let o = Op {
                kind: r.byte()?,
                id: r.word()?,
                x: r.word()?,
                y: r.word()?,
                fg: r.byte()?,
                bg: r.byte()?,
            };
            let (w, h) = match o.kind {
                0 => {
                    let b = bitmaps.get(o.id).ok_or("結局圖形索引錯誤")?;
                    (b.w, b.h)
                }
                1 => {
                    let g = glyphs.get(o.id).ok_or("結局字模索引錯誤")?;
                    if o.fg > 15 || o.bg != 255 && o.bg > 15 {
                        return Err("結局字模色號錯誤".into());
                    }
                    (g.w, 15)
                }
                _ => return Err("結局命令類型錯誤".into()),
            };
            if o.x + w > 640 || o.y + h > 200 {
                return Err("結局命令位置錯誤".into());
            }
            ops.push(o);
        }
        let mut frames = Vec::new();
        for _ in 0..r.count(20000)? {
            let (ms, stage, cue, n) = (r.dword()?, r.byte()?, r.byte()?, r.word()?);
            if ms > DURATION
                || frames.last().is_some_and(|f: &Frame| f.ms > ms)
                || stage > 9
                || cue > 2
                || n > 4096
            {
                return Err("結局節點錯誤".into());
            }
            let mut ids = Vec::new();
            for _ in 0..n {
                let id = r.dword()? as usize;
                if id >= ops.len() {
                    return Err("結局命令索引錯誤".into());
                }
                ids.push(id)
            }
            frames.push(Frame {
                ms,
                stage,
                cue,
                ops: ids,
            });
        }
        if r.at != raw.len()
            || frames.first().is_none_or(|f| f.ms != 0)
            || !(1..=9).all(|s| frames.iter().any(|f| f.stage == s))
        {
            return Err("結局尾端或階段不完整".into());
        }
        Ok(Self {
            textures,
            bitmaps,
            glyphs,
            ops,
            frames,
        })
    }
    pub fn frame_index(&self, ms: u32) -> usize {
        self.frames
            .partition_point(|f| f.ms <= ms)
            .saturating_sub(1)
    }
    pub fn cue_start(&self, index: usize) -> u32 {
        let cue = self.frames[index].cue;
        let mut i = index;
        while i > 0 && self.frames[i - 1].cue == cue {
            i -= 1
        }
        self.frames[i].ms
    }
    fn dimensions(&self, o: Op) -> (usize, usize) {
        if o.kind == 0 {
            let b = &self.bitmaps[o.id];
            (b.w, b.h)
        } else {
            (self.glyphs[o.id].w, 15)
        }
    }
    fn repeated(&self, frame: &Frame, i: usize) -> bool {
        let o = self.ops[frame.ops[i]];
        let (w, h) = self.dimensions(o);
        for id in frame.ops[..i].iter().rev() {
            let p = self.ops[*id];
            let (pw, ph) = self.dimensions(p);
            if o.x < p.x + pw && p.x < o.x + w && o.y < p.y + ph && p.y < o.y + h {
                return p.kind == o.kind && p.id == o.id && p.x == o.x && p.y == o.y;
            }
        }
        false
    }
    pub fn render(&self, index: usize, hd: bool, font: usize) -> Result<Vec<u8>, String> {
        let frame = self.frames.get(index).ok_or("結局節點超界")?;
        if font >= 3 {
            return Err("結局字型錯誤".into());
        }
        let mut out = vec![0; WIDTH * HEIGHT * 4];
        for c in out.chunks_exact_mut(4) {
            c[3] = 255
        }
        for (i, id) in frame.ops.iter().enumerate() {
            let o = self.ops[*id];
            if o.kind == 0 {
                let b = &self.bitmaps[o.id];
                if hd && b.mode != 0 {
                    if b.repeat && self.repeated(frame, i) {
                        continue;
                    }
                    if b.mode == 3 {
                        for at in 0..b.pixels.len() {
                            if b.mask[at] != 0 && b.pixels[at] == 0 {
                                block(&mut out, o.x + at % b.w, o.y + at / b.w, PALETTE[0])
                            }
                        }
                    }
                    if b.mode == 4 {
                        rect(&mut out, o.x * 3, o.y * 6, b.w * 3, b.h * 6, PALETTE[0])
                    }
                    texture(
                        &mut out,
                        &self.textures[b.textures[font] as usize],
                        o.x * 3,
                        o.y * 6,
                        b.mode == 1,
                    );
                } else {
                    for at in 0..b.pixels.len() {
                        if b.mask[at] != 0 {
                            block(
                                &mut out,
                                o.x + at % b.w,
                                o.y + at / b.w,
                                PALETTE[usize::from(b.pixels[at])],
                            )
                        }
                    }
                }
            } else {
                let g = &self.glyphs[o.id];
                if o.bg != 255 {
                    rect(
                        &mut out,
                        o.x * 3,
                        o.y * 6,
                        g.w * 3,
                        90,
                        PALETTE[usize::from(o.bg)],
                    )
                }
                if hd {
                    let fg = PALETTE[usize::from(o.fg)];
                    for (y, row) in g.alpha[font].chunks_exact(g.w * 3).enumerate() {
                        for (x, a) in row.iter().enumerate() {
                            if *a == 0 {
                                continue;
                            }
                            let at = ((o.y * 6 + y) * WIDTH + o.x * 3 + x) * 4;
                            for k in 0..3 {
                                out[at + k] = ((u32::from(fg[k]) * u32::from(*a)
                                    + u32::from(out[at + k]) * u32::from(255 - *a)
                                    + 127)
                                    / 255) as u8
                            }
                        }
                    }
                } else {
                    for at in 0..g.mask.len() {
                        if g.mask[at] != 0 {
                            block(
                                &mut out,
                                o.x + at % g.w,
                                o.y + at / g.w,
                                PALETTE[usize::from(o.fg)],
                            )
                        }
                    }
                }
            }
        }
        Ok(out)
    }
}
fn rect(out: &mut [u8], x: usize, y: usize, w: usize, h: usize, c: [u8; 3]) {
    for row in y..y + h {
        for col in x..x + w {
            let at = (row * WIDTH + col) * 4;
            out[at..at + 3].copy_from_slice(&c);
            out[at + 3] = 255
        }
    }
}
fn block(out: &mut [u8], x: usize, y: usize, c: [u8; 3]) {
    rect(out, x * 3, y * 6, 3, 6, c)
}
fn texture(out: &mut [u8], im: &Texture, x: usize, y: usize, src: bool) {
    for row in 0..im.height {
        let at = ((y + row) * WIDTH + x) * 4;
        let s = &im.pixels[row * im.width * 4..(row + 1) * im.width * 4];
        let d = &mut out[at..at + im.width * 4];
        for (d, s) in d.chunks_exact_mut(4).zip(s.chunks_exact(4)) {
            // Color.RGBA supplies full 16-bit premultiplied components.
            let sa = u32::from(s[3]);
            let a = if src { 0 } else { (65535 - sa) * 257 };
            for k in 0..4 {
                let value = u32::from(s[k]);
                d[k] = ((u32::from(d[k]) * a / 65535 + value) >> 8) as u8;
            }
        }
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn malformed_packet_is_rejected_without_panics() {
        for n in 0..64 {
            assert!(Pack::parse(&vec![0; n]).is_err())
        }
        let mut b = b"8SEND003".to_vec();
        b.extend(DURATION.to_le_bytes());
        b.extend(u32::MAX.to_le_bytes());
        assert!(Pack::parse(&b).is_err());
    }
}
