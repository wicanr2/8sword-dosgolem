//! Native opening playback in the same window as the menu and journey.
use crate::{
    desktop::{H, TOP, W, border, fill, ppm, text},
    intro::Pack,
    media_assets::{Font, Music, checksum},
    pointer::{Action, FOOTER, Pointer, Screen},
    sdl::Sdl,
};
use std::{
    path::Path,
    time::{Duration, Instant},
};
pub(crate) fn play(
    sdl: &Sdl,
    root: &Path,
    fonts: &[Font],
    capture: Option<&Path>,
    mute: bool,
) -> Result<Option<(u8, bool, u32)>, String> {
    let pack = Pack::load(root)?;
    let music = Music::load(&root.join("start-music-1.ogg"))?;
    let (mut font, mut enabled, mut hd) = (0u8, true, true);
    let mut pointer = Pointer::default();
    let clock = Instant::now();
    let (mut first, mut pending) = (true, false);
    let (mut captures, mut queued_bytes) = (0u32, 0u64);
    let (mut audio, mut old_cue) = (0usize, 0u8);
    let mut rendered = None;
    let mut pixels = Vec::new();
    let mut portrait_captured = false;
    loop {
        let ms = (clock.elapsed().as_millis() as u32).min(pack.duration);
        let index = pack.frame_index(ms);
        let f = &pack.frames[index];
        let mut snap = first && capture.is_some();
        first = false;
        if capture.is_some() && f.stage == "museum-portrait" && !portrait_captured {
            snap = true;
            portrait_captured = true;
        }
        if pending && f.revealed == 64000 {
            snap = capture.is_some();
        }
        let mut skip = false;
        for e in sdl.events() {
            let b = e.bytes;
            let kind = u32::from_ne_bytes(b[..4].try_into().unwrap());
            if kind == 0x100 {
                sdl.clear_music();
                return Ok(None);
            }
            if kind == 0x200 && [2, 7, 11, 13].contains(&b[12]) {
                pointer.cancel();
            }
            let mut k = if kind == 0x300 && b[13] == 0 {
                i32::from_ne_bytes(b[20..24].try_into().unwrap())
            } else {
                0
            };
            if matches!(kind, 0x401 | 0x402) && b[16] == 1 {
                if let Some(a) = pointer.event(
                    Screen::Intro,
                    kind,
                    i32::from_ne_bytes(b[20..24].try_into().unwrap()),
                    i32::from_ne_bytes(b[24..28].try_into().unwrap()),
                ) {
                    match a {
                        Action::Key(v) => k = v,
                        Action::Font(v) => font = v,
                        _ => {}
                    }
                }
            }
            match k {
                27 | 13 => skip = true,
                113 => {
                    sdl.clear_music();
                    return Ok(None);
                }
                104 => hd = !hd,
                109 => enabled = !enabled,
                1073741891 => font = (font + 1) % 3,
                1073741893 => snap = capture.is_some(),
                _ => {}
            }
        }
        if skip {
            if pack.skip_waits_for_reveal(index) {
                pending = true;
            } else {
                sdl.clear_music();
                return Ok(Some((font, enabled, captures)));
            }
        }
        if f.cue != old_cue {
            sdl.clear_music();
            audio = 0;
            old_cue = f.cue;
        }
        sdl.pause_music(mute || !enabled || f.cue == 0);
        if !mute && enabled && f.cue != 0 && sdl.queued() < 38400 {
            let mut chunk = Vec::with_capacity(38400);
            for _ in 0..9600 {
                chunk.extend_from_slice(&music.pcm[audio..audio + 4]);
                audio = (audio + 4) % music.pcm.len();
            }
            sdl.queue(&chunk)?;
            queued_bytes += chunk.len() as u64;
        }
        if rendered != Some((index, hd, font)) {
            pixels = pack.render(index, hd, usize::from(font))?;
            rendered = Some((index, hd, font));
        }
        let mut rgba = vec![0; W * H * 4];
        fill(&mut rgba, [0, 0, W as i32, H as i32], [9, 36, 29]);
        rgba[TOP as usize * W * 4..(TOP as usize + 1200) * W * 4].copy_from_slice(&pixels);
        let face = &fonts[usize::from(font)];
        text(&mut rgba, face, "字型", 12, 2, 40, 120)?;
        for (i, t) in ["Noto 900", "隸書", "草書"].iter().enumerate() {
            let x = 144 + i as i32 * 228;
            fill(
                &mut rgba,
                [x, 2, 216, 44],
                if i == usize::from(font) {
                    [119, 44, 41]
                } else {
                    [20, 55, 40]
                },
            );
            border(&mut rgba, [x, 2, 216, 44], [206, 170, 74]);
            text(&mut rgba, face, t, x + 12, 4, 38, 192)?;
        }
        for (rect, t) in [
            (
                [920, 2, 232, 44],
                if enabled { "音樂 開" } else { "音樂 關" },
            ),
            ([1200, 2, 232, 44], if hd { "HD" } else { "原版" }),
        ] {
            border(&mut rgba, rect, [206, 170, 74]);
            text(&mut rgba, face, t, rect[0] + 12, 4, 38, 210)?;
        }
        for (i, t) in [
            if pending {
                "完成揭圖後略過"
            } else {
                "略過開場"
            },
            "結束遊戲",
        ]
        .iter()
        .enumerate()
        {
            let r = FOOTER[i];
            border(&mut rgba, r.array(), [206, 170, 74]);
            text(&mut rgba, face, t, r.0 + 12, r.1 + 6, 32, r.2 - 24)?;
        }
        let back = sdl.draw(&rgba, snap)?;
        let equal = back.as_ref().is_none_or(|b| *b == rgba);
        let status = format!(
            "phase\tintro\nstage\t{}\nelapsed_ms\t{ms}\nintro_frame\t{index}\nrevealed\t{}\nskip_pending\t{pending}\nhd\t{hd}\nfont\t{font}\nmusic\t{enabled}\nstate_hash\t{:016x}\nscene_hash\t{:016x}\ncaptures\t{}\nsaves\t0\nreadback_equal\t{equal}\nqueued_bytes\t{queued_bytes}\n",
            f.stage,
            f.revealed,
            checksum(format!("{index}/{font}/{hd}/{enabled}/{pending}").as_bytes()),
            checksum(&pixels),
            captures + u32::from(snap)
        );
        if let Some(dir) = capture {
            if snap {
                captures += 1;
                ppm(&dir.join(format!("frame-{captures:03}.ppm")), &rgba)?;
                ppm(
                    &dir.join(format!("readback-{captures:03}.ppm")),
                    back.as_ref().ok_or("缺少開場SDL讀回")?,
                )?;
                std::fs::write(
                    dir.join(format!("capture-{captures:03}.tsv")),
                    format!("{status}frame_hash\t{:016x}\n", checksum(&rgba)),
                )
                .map_err(|e| e.to_string())?;
            }
            std::fs::write(dir.join("status.tmp"), status)
                .and_then(|_| std::fs::rename(dir.join("status.tmp"), dir.join("status.tsv")))
                .map_err(|e| e.to_string())?;
        }
        if ms >= pack.duration || pending && f.revealed == 64000 {
            sdl.clear_music();
            return Ok(Some((font, enabled, captures)));
        }
        std::thread::sleep(Duration::from_millis(15));
    }
}
