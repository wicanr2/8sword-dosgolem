//! Original PAM menu, rendered and operated directly by the native player.
use crate::{
    catalog::Catalog,
    desktop::{H, W, border, fill, glyph, ppm, text},
    journey::Journey,
    media_assets::{Font, Music, checksum},
    pointer::{Action, FOOTER, Pointer, Screen},
    sdl::Sdl,
    start::{self, Intent, Menu, Page},
    world::WorldData,
};
use std::{path::Path, time::Duration};
pub const _UI_TEXT: &str = "無法讀取進度 請檢查存檔或開始新遊戲 無法建立新遊戲 請檢查存檔目錄 無法播放曲目 請檢查素材 確認 返回 離開 音樂欣賞";
pub(crate) struct Launch<'a> {
    pub journey: Journey<'a>,
    pub loaded: bool,
    pub captures: u32,
    pub saves: u32,
}
const GOLD: [u8; 3] = [206, 170, 74];
fn label(frame: &mut [u8], font: &Font, l: &start::Label, color: [u8; 3]) -> Result<(), String> {
    if l.x < 0 || l.x + start::text_width(l.text) > W as i32 || l.y + 90 > 1248 {
        return Err("開始選單文字超出畫面".into());
    }
    let mut x = l.x;
    for ch in l.text.chars() {
        let w = if ch.is_ascii() { 24 } else { 48 };
        glyph(frame, font, ch, [x, l.y, w, 90], color)?;
        x += w;
    }
    Ok(())
}
pub(crate) fn render(m: &Menu, fonts: &[Font]) -> Result<Vec<u8>, String> {
    let mut f = vec![0; W * H * 4];
    fill(&mut f, [0, 0, W as i32, H as i32], [9, 36, 29]);
    fill(&mut f, [0, 48, W as i32, 1200], [0, 0, 0]);
    let font = &fonts[usize::from(m.font)];
    text(&mut f, font, "字型", 12, 2, 40, 120)?;
    for (i, t) in ["Noto 900", "隸書", "草書"].iter().enumerate() {
        let x = 144 + i as i32 * 228;
        fill(
            &mut f,
            [x, 2, 216, 44],
            if i == usize::from(m.font) {
                [119, 44, 41]
            } else {
                [20, 55, 40]
            },
        );
        border(&mut f, [x, 2, 216, 44], GOLD);
        text(&mut f, font, t, x + 12, 4, 38, 192)?;
    }
    border(&mut f, [920, 2, 232, 44], GOLD);
    text(
        &mut f,
        font,
        if m.music { "音樂 開" } else { "音樂 關" },
        932,
        4,
        38,
        210,
    )?;
    let music = m.page == Page::Music;
    let count = if music { 10 } else { 3 };
    for i in 0..count {
        let r = start::row_box(music, i);
        fill(
            &mut f,
            r.array(),
            if i == usize::from(m.selected) {
                [119, 44, 41]
            } else {
                [20, 55, 40]
            },
        );
        border(
            &mut f,
            r.array(),
            if music && m.playing == Some(i as u8 + 1) {
                [90, 220, 200]
            } else {
                GOLD
            },
        );
    }
    for l in start::labels() {
        if l.kind == if music { "MUSIC" } else { "MAIN" } {
            label(&mut f, font, l, GOLD)?;
        }
    }
    if m.page == Page::Confirm {
        for l in start::labels()
            .iter()
            .filter(|l| matches!(l.kind, "WARN" | "ASK"))
        {
            label(&mut f, font, l, GOLD)?;
        }
        for yes in [true, false] {
            let r = start::choice_box(yes);
            fill(
                &mut f,
                r.array(),
                if m.yes == yes {
                    [119, 44, 41]
                } else {
                    [0, 0, 0]
                },
            );
            border(&mut f, r.array(), GOLD);
            let l = start::labels()
                .iter()
                .find(|l| l.kind == if yes { "YES" } else { "NO" })
                .ok_or("缺少確認文字")?;
            label(&mut f, font, l, GOLD)?;
        }
    }
    if m.page == Page::Message {
        fill(&mut f, [240, 780, 1440, 336], [9, 36, 29]);
        border(&mut f, [240, 780, 1440, 336], GOLD);
        for (i, s) in m.message.split(' ').enumerate() {
            text(&mut f, font, s, 288, 822 + i as i32 * 90, 48, 1344)?;
        }
    }
    for (i, t) in [
        "確認",
        if m.page == Page::Main {
            "離開"
        } else {
            "返回"
        },
    ]
    .iter()
    .enumerate()
    {
        let r = FOOTER[i];
        border(&mut f, r.array(), GOLD);
        text(&mut f, font, t, r.0 + 12, r.1 + 6, 32, r.2 - 24)?;
    }
    Ok(f)
}
#[allow(clippy::too_many_arguments)]
pub(crate) fn play<'a>(
    sdl: &Sdl,
    root: &Path,
    fonts: &[Font],
    c: &'a Catalog,
    d: &WorldData,
    store: &Path,
    capture: Option<&Path>,
    mute: bool,
    seed: u32,
) -> Result<Option<Launch<'a>>, String> {
    let mut m = Menu::default();
    let mut pointer = Pointer::default();
    let (mut captures, mut queued_bytes) = (0u32, 0u64);
    let mut audio: Option<Music> = None;
    let mut pos = 0usize;
    let mut first = true;
    loop {
        let mut snap = first && capture.is_some();
        first = false;
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
                let screen = Screen::Start {
                    count: match m.page {
                        Page::Main => 3,
                        Page::Music => 10,
                        _ => 0,
                    },
                    confirm: m.page == Page::Confirm,
                };
                if let Some(a) = pointer.event(
                    screen,
                    kind,
                    i32::from_ne_bytes(b[20..24].try_into().unwrap()),
                    i32::from_ne_bytes(b[24..28].try_into().unwrap()),
                ) {
                    match a {
                        Action::Key(v) => k = v,
                        Action::Font(v) => m.font = v,
                        Action::StartChoice(i) => m.select(i),
                        Action::Choice(v) => m.yes = v,
                        _ => {}
                    }
                }
            }
            if kind == 0x300 && k != 0 {
                pointer.cancel();
            }
            match k {
                1073741891 => {
                    m.font = (m.font + 1) % 3;
                    continue;
                }
                109 => {
                    m.music = !m.music;
                    continue;
                }
                1073741893 => {
                    snap = capture.is_some();
                    continue;
                }
                _ => {}
            }
            let key = match k {
                13 => 0x1c0d,
                27 => 0x11b,
                1073741906 => 0x4800,
                1073741905 => 0x5000,
                1073741904 => 0x4b00,
                1073741903 => 0x4d00,
                _ => 0,
            };
            let before = m.page;
            let intent = m.key(key);
            if m.page != before {
                pointer.cancel();
            }
            if before == Page::Music && m.page == Page::Main {
                sdl.clear_music();
                audio = None;
            }
            match intent {
                Intent::Exit => {
                    sdl.clear_music();
                    return Ok(None);
                }
                Intent::Continue => match Journey::load(store, c, d) {
                    Ok(j) => {
                        sdl.clear_music();
                        return Ok(Some(Launch {
                            journey: j,
                            loaded: true,
                            captures,
                            saves: 0,
                        }));
                    }
                    Err(_) => m.fail("無法讀取進度 請檢查存檔或開始新遊戲"),
                },
                Intent::NewGame => match start::new_game(c, d, store, seed, m.font, m.music) {
                    Ok(j) => {
                        sdl.clear_music();
                        return Ok(Some(Launch {
                            journey: j,
                            loaded: false,
                            captures,
                            saves: 1,
                        }));
                    }
                    Err(_) => m.fail("無法建立新遊戲 請檢查存檔目錄"),
                },
                Intent::Play(id) => {
                    let t = &start::tracks()[usize::from(id - 1)];
                    let path = root.join(t.file);
                    let result = std::fs::read(&path)
                        .map_err(|e| e.to_string())
                        .and_then(|b| {
                            if checksum(&b) == t.fnv {
                                Music::load(&path)
                            } else {
                                Err("曲目雜湊不符".into())
                            }
                        });
                    sdl.clear_music();
                    pos = 0;
                    match result {
                        Ok(v) => audio = Some(v),
                        Err(_) => {
                            audio = None;
                            m.playing = None;
                            m.fail("無法播放曲目 請檢查素材");
                        }
                    }
                }
                Intent::None => {}
            }
        }
        sdl.pause_music(mute || !m.music);
        if !mute && m.music && sdl.queued() < 38400 {
            if let Some(a) = &audio {
                let mut chunk = Vec::with_capacity(38400);
                for _ in 0..9600 {
                    chunk.extend_from_slice(&a.pcm[pos..pos + 4]);
                    pos = (pos + 4) % a.pcm.len();
                }
                sdl.queue(&chunk)?;
                queued_bytes += chunk.len() as u64;
            }
        }
        let rgba = render(&m, fonts)?;
        let back = sdl.draw(&rgba, snap)?;
        let equal = back.as_ref().is_none_or(|b| *b == rgba);
        let phase = match m.page {
            Page::Main => "start",
            Page::Confirm => "new-confirm",
            Page::Music => "music",
            Page::Message => "start-message",
        };
        let status = format!(
            "phase\t{phase}\nselected\t{}\nyes\t{}\nfont\t{}\nmusic\t{}\nplaying\t{:?}\nstate_hash\t{:016x}\ncaptures\t{}\nsaves\t0\nreadback_equal\t{equal}\nqueued_bytes\t{queued_bytes}\n",
            m.selected,
            m.yes,
            m.font,
            m.music,
            m.playing,
            checksum(format!("{m:?}").as_bytes()),
            captures + u32::from(snap)
        );
        if let Some(dir) = capture {
            if snap {
                captures += 1;
                ppm(&dir.join(format!("frame-{captures:03}.ppm")), &rgba)?;
                ppm(
                    &dir.join(format!("readback-{captures:03}.ppm")),
                    back.as_ref().ok_or("缺少選單SDL讀回")?,
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
        std::thread::sleep(Duration::from_millis(15));
    }
}
