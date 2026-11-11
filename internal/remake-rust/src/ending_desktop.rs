//! Native ending playback, sharing the original journey's SDL window and save.
use crate::{
    catalog::Catalog,
    desktop::{H, TOP, W, border, fill, ppm, text},
    ending::{DURATION, Pack},
    journey::Journey,
    media_assets::{Font, Music, checksum},
    pointer::{Action, FOOTER, Pointer, Screen},
    sdl::Sdl,
    world::WorldData,
};
use std::{
    path::Path,
    time::{Duration, Instant},
};
#[allow(clippy::too_many_arguments)]
pub(crate) fn play<'a>(
    sdl: &Sdl,
    root: &Path,
    fonts: &[Font],
    battle_music: &Music,
    j: &mut Journey<'a>,
    c: &'a Catalog,
    d: &WorldData,
    capture: Option<&Path>,
    store: Option<&Path>,
    mute: bool,
    mut captures: u32,
    mut saves: u32,
) -> Result<(), String> {
    let pack = Pack::load(root)?;
    let music = Music::load(&root.join("music-ending.ogg"))?;
    let base = j.guards.ending.ok_or("缺少結局進度")?.elapsed_ms;
    let clock = Instant::now();
    let mut first = true;
    let mut pointer = Pointer::default();
    let mut rendered = None;
    let mut pixels = Vec::new();
    let mut audio = 0;
    let mut cue = 255;
    let mut queued_bytes = 0u64;
    loop {
        let ms = if first {
            base
        } else {
            base.saturating_add(clock.elapsed().as_millis() as u32)
                .min(DURATION)
        };
        let mut snap = first && capture.is_some();
        let mut save = false;
        let mut leave = ms >= DURATION;
        first = false;
        j.guards.ending.as_mut().unwrap().elapsed_ms = ms;
        for e in sdl.events() {
            let b = e.bytes;
            let kind = u32::from_ne_bytes(b[..4].try_into().unwrap());
            if kind == 0x100 {
                leave = true
            }
            if kind == 0x200 && [2, 7, 11, 13].contains(&b[12]) {
                pointer.cancel()
            }
            let mut key = if kind == 0x300 && b[13] == 0 {
                i32::from_ne_bytes(b[20..24].try_into().unwrap())
            } else {
                0
            };
            if matches!(kind, 0x401 | 0x402) && b[16] == 1 {
                if let Some(a) = pointer.event(
                    Screen::Ending,
                    kind,
                    i32::from_ne_bytes(b[20..24].try_into().unwrap()),
                    i32::from_ne_bytes(b[24..28].try_into().unwrap()),
                ) {
                    match a {
                        Action::Key(k) => key = k,
                        Action::Font(n) => j.world.font = n,
                        _ => {}
                    }
                }
            }
            match key {
                27 => leave = true,
                104 => {
                    let p = j.guards.ending.as_mut().unwrap();
                    p.hd = !p.hd
                }
                1073741891 => j.world.font = (j.world.font + 1) % 3,
                109 => j.world.music = !j.world.music,
                1073741888 => save = store.is_some(),
                1073741893 => snap = capture.is_some(),
                _ => {}
            }
        }
        if (save || leave) && store.is_some() {
            j.save(store.unwrap(), c, d)?;
            saves += 1;
            if save {
                snap = capture.is_some()
            }
        }
        let p = j.guards.ending.unwrap();
        let index = pack.frame_index(ms);
        let frame = &pack.frames[index];
        let current_cue = frame.cue.max(1);
        let pcm = if current_cue == 2 {
            &music.pcm
        } else {
            &battle_music.pcm
        };
        if cue != current_cue {
            sdl.clear_music();
            cue = current_cue;
            audio = ((u64::from(ms.saturating_sub(pack.cue_start(index))) * 48 * 4) as usize)
                % pcm.len()
        }
        sdl.pause_music(mute || !j.world.music);
        if !mute && j.world.music && sdl.queued() < 38400 {
            let mut chunk = Vec::with_capacity(38400);
            for _ in 0..9600 {
                chunk.extend_from_slice(&pcm[audio..audio + 4]);
                audio = (audio + 4) % pcm.len()
            }
            sdl.queue(&chunk)?;
            queued_bytes += chunk.len() as u64
        }
        if rendered != Some((index, p.hd, j.world.font)) {
            pixels = pack.render(index, p.hd, usize::from(j.world.font))?;
            rendered = Some((index, p.hd, j.world.font))
        }
        let mut rgba = vec![0; W * H * 4];
        fill(&mut rgba, [0, 0, W as i32, H as i32], [9, 36, 29]);
        rgba[TOP as usize * W * 4..(TOP as usize + crate::ending::HEIGHT) * W * 4]
            .copy_from_slice(&pixels);
        let font = &fonts[usize::from(j.world.font)];
        text(&mut rgba, font, "字型", 12, 2, 40, 120)?;
        for (i, label) in ["Noto 900", "隸書", "草書"].iter().enumerate() {
            let x = 144 + i as i32 * 228;
            fill(
                &mut rgba,
                [x, 2, 216, 44],
                if i == usize::from(j.world.font) {
                    [119, 44, 41]
                } else {
                    [20, 55, 40]
                },
            );
            border(&mut rgba, [x, 2, 216, 44], [206, 170, 74]);
            text(&mut rgba, font, label, x + 12, 4, 38, 192)?;
        }
        for (rect, label) in [
            (
                [920, 2, 232, 44],
                if j.world.music {
                    "音樂 開"
                } else {
                    "音樂 關"
                },
            ),
            ([1200, 2, 232, 44], if p.hd { "HD" } else { "原版" }),
            ([1480, 2, 232, 44], "F7存檔"),
        ] {
            border(&mut rgba, rect, [206, 170, 74]);
            text(&mut rgba, font, label, rect[0] + 12, 4, 38, 210)?;
        }
        text(
            &mut rgba,
            font,
            &format!(
                "結局  {:.1}/{:.1}  H 切換畫面  Esc 離開",
                f64::from(ms) / 1000.0,
                f64::from(DURATION) / 1000.0
            ),
            24,
            1250,
            20,
            1872,
        )?;
        for (i, label) in ["切換畫面", "離開", "F8字型", "F7存檔"].iter().enumerate() {
            let r = FOOTER[i];
            border(&mut rgba, r.array(), [206, 170, 74]);
            text(&mut rgba, font, label, r.0 + 12, r.1 + 6, 32, r.2 - 24)?;
        }
        let back = sdl.draw(&rgba, snap)?;
        let equal = back.as_ref().is_none_or(|b| *b == rgba);
        let status = format!(
            "phase\tending\nelapsed_ms\t{ms}\nending_frame\t{index}\nending_stage\t{}\nending_hd\t{}\nfont\t{}\nmusic\t{}\nending_cue\t{current_cue}\nstate_hash\t{:016x}\nscene_hash\t{:016x}\ncaptures\t{}\nsaves\t{saves}\nreadback_equal\t{equal}\nqueued_bytes\t{queued_bytes}\nresources\t{:?}\nsteps\t{}\n",
            frame.stage,
            p.hd,
            j.world.font,
            j.world.music,
            checksum(&j.encode(c, d)?),
            checksum(&pixels),
            captures + u32::from(snap),
            j.resources,
            j.world.remaining
        );
        if let Some(dir) = capture {
            if snap {
                captures += 1;
                ppm(&dir.join(format!("frame-{captures:03}.ppm")), &rgba)?;
                ppm(
                    &dir.join(format!("readback-{captures:03}.ppm")),
                    back.as_ref().ok_or("缺少結局SDL讀回")?,
                )?;
                std::fs::write(
                    dir.join(format!("capture-{captures:03}.tsv")),
                    format!("{status}frame_hash\t{:016x}\n", checksum(&rgba)),
                )
                .map_err(|e| e.to_string())?;
            }
            std::fs::write(dir.join("status.tmp"), &status)
                .and_then(|_| std::fs::rename(dir.join("status.tmp"), dir.join("status.tsv")))
                .map_err(|e| e.to_string())?;
        }
        if leave {
            return Ok(());
        }
        std::thread::sleep(Duration::from_millis(15));
    }
}
