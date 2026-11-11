//! Bounded native world preview. Unimplemented events never commit a move.
use crate::desktop::{GOLD, H, TOP, W, border, fill, glyph, ppm, sprite, text};
use crate::media_assets::{Font, Image, Music, checksum};
use crate::sdl::Sdl;
use crate::world::{Boundary, Position, WalkResult, WorldData, WorldState};
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

pub const UI_TEXT: &str =
    "字型 隸書 草書 音樂 開 關 F7存檔 存檔失敗 地圖 移動 方向鍵 Space Esc 遇見怪物 月報 船 STOP";
pub(crate) struct Pack {
    frame: Image,
    tiles: Vec<Image>,
    heroes: Vec<Image>,
    pub(crate) fonts: Vec<Font>,
    pub(crate) music: Music,
}
impl Pack {
    pub(crate) fn spell_cue(
        &self,
        f: &mut [u8],
        s: &WorldState,
        elapsed: Duration,
        color: [u8; 3],
    ) {
        let progress = (elapsed.as_secs_f32() / 1.2).clamp(0.0, 1.0);
        if progress >= 1.0 {
            return;
        }
        let radius = 50.0 + 100.0 * progress;
        for y in 540..751i32 {
            for x in 520..873i32 {
                let dx = (x - 696) as f32;
                let dy = (y - 645) as f32 * 1.55;
                let distance = (dx * dx + dy * dy).sqrt();
                let edge = (1.0 - ((distance - radius) / 9.0).abs()).max(0.0);
                let alpha = edge * (1.0 - progress) * 0.85;
                if alpha > 0.0 {
                    let at = (y as usize * W + x as usize) * 4;
                    for (i, c) in color.iter().enumerate() {
                        f[at + i] =
                            (f[at + i] as f32 * (1.0 - alpha) + f32::from(*c) * alpha) as u8;
                    }
                }
            }
        }
        sprite(
            f,
            &self.heroes[usize::from(s.facing - 1) * 3],
            600,
            TOP + 522,
        );
    }
    pub(crate) fn load(root: &Path) -> Result<Self, String> {
        Ok(Self {
            frame: Image::load(&root.join("world-frame.rgba"), 1920, 1200)?,
            tiles: (0..65)
                .map(|i| Image::load(&root.join(format!("map-tile-{i:02}.rgba")), 192, 150))
                .collect::<Result<_, _>>()?,
            heroes: (0..12)
                .map(|i| Image::load(&root.join(format!("map-hero-{i:02}.rgba")), 192, 150))
                .collect::<Result<_, _>>()?,
            fonts: ["noto", "lishu", "caoshu"]
                .iter()
                .map(|n| Font::load(&root.join(format!("font-{n}.bin"))))
                .collect::<Result<_, _>>()?,
            music: Music::load(&root.join("world-music.ogg"))?,
        })
    }
}
pub(crate) fn compose(
    pack: &Pack,
    data: &WorldData,
    s: &WorldState,
    pending: Option<Boundary>,
    save: bool,
    tempo: u8,
    stopped: bool,
) -> Result<Vec<u8>, String> {
    let mut f = vec![0; W * H * 4];
    fill(&mut f, [0, 0, W as i32, H as i32], [9, 36, 29]);
    sprite(&mut f, &pack.frame, 0, TOP);
    for row in 0..7 {
        for col in 0..7 {
            let p = Position {
                x: (i32::from(s.position.x) + col - 3).rem_euclid(70) as u8,
                y: (i32::from(s.position.y) + row - 3).rem_euclid(80) as u8,
            };
            let tile = data.tile(s.area, p)?;
            sprite(
                &mut f,
                &pack.tiles[usize::from(tile - 1)],
                24 + col * 192,
                TOP + 72 + row * 150,
            );
        }
    }
    sprite(
        &mut f,
        &pack.heroes[usize::from(s.facing - 1) * 3],
        600,
        TOP + 522,
    );
    let font = &pack.fonts[usize::from(s.font)];
    for m in &data.menu {
        let mut x = i32::from(m.x) * 24;
        for ch in m.text.chars() {
            let w = if ch.is_ascii() { 24 } else { 48 };
            glyph(&mut f, font, ch, [x, TOP + i32::from(m.y) * 6, w, 96], GOLD)?;
            x += w;
        }
    }
    text(&mut f, font, "字型", 12, 2, 40, 120)?;
    for (i, n) in ["Noto 900", "隸書", "草書"].iter().enumerate() {
        let x = 144 + i as i32 * 228;
        fill(
            &mut f,
            [x, 2, 216, 44],
            if i == usize::from(s.font) {
                [119, 44, 41]
            } else {
                [20, 55, 40]
            },
        );
        border(&mut f, [x, 2, 216, 44], [206, 170, 74]);
        text(&mut f, font, n, x + 12, 4, 38, 192)?;
    }
    border(&mut f, [920, 2, 232, 44], [206, 170, 74]);
    text(
        &mut f,
        font,
        if s.music { "音樂 開" } else { "音樂 關" },
        930,
        4,
        38,
        210,
    )?;
    if save {
        border(&mut f, [1480, 2, 232, 44], [206, 170, 74]);
        text(&mut f, font, "F7存檔", 1490, 4, 38, 210)?;
    }
    crate::travelbar::draw(&mut f, s.remaining, tempo, stopped)?;
    let status = match pending {
        Some(Boundary::Terrain(t)) => format!("STOP {t}"),
        Some(Boundary::BoatExit) => "STOP 船".into(),
        Some(Boundary::Monthly) => "STOP 月報".into(),
        Some(Boundary::Encounter(_)) => "STOP 遇見怪物".into(),
        None => format!("地圖 {}   {} {}", s.area + 1, s.position.x, s.position.y),
    };
    text(&mut f, font, &status, 18, 1250, 32, 1860)?;
    text(
        &mut f,
        font,
        "方向鍵 移動  Space  Esc  F7存檔",
        18,
        1288,
        28,
        1860,
    )?;
    Ok(f)
}
pub(crate) fn key_motion(key: i32) -> Option<u16> {
    Some(match key {
        1073741898 | 1073741919 => 0x4700, // Home / keypad7
        1073741906 | 1073741920 => 0x4800,
        1073741899 | 1073741921 => 0x4900,
        1073741904 | 1073741916 => 0x4b00,
        1073741903 | 1073741918 => 0x4d00,
        1073741901 | 1073741913 => 0x4f00,
        1073741905 | 1073741914 => 0x5000,
        1073741902 | 1073741915 => 0x5100,
        32 => 0x3920,
        _ => return None,
    })
}
pub fn run(args: &[String]) -> Result<(), String> {
    let (mut assets, mut capture, mut saves): (Option<PathBuf>, Option<PathBuf>, Option<PathBuf>) =
        (None, None, None);
    let (mut continuing, mut mute, mut seed_given) = (false, false, false);
    let mut check_only = false;
    let mut scale = 2.0 / 3.0;
    let mut seed = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_nanos() as u32;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--assets" | "--capture-dir" | "--save-dir" => {
                let k = args[i].as_str();
                i += 1;
                let p = Some(PathBuf::from(args.get(i).ok_or("缺少目錄")?));
                match k {
                    "--assets" => assets = p,
                    "--capture-dir" => capture = p,
                    _ => saves = p,
                }
            }
            "--continue" => continuing = true,
            "--check-only" => check_only = true,
            "--mute" => mute = true,
            "--seed" => {
                i += 1;
                seed = args
                    .get(i)
                    .ok_or("缺少seed")?
                    .parse()
                    .map_err(|_| "seed錯誤")?;
                seed_given = true
            }
            "--scale" => {
                i += 1;
                scale = args
                    .get(i)
                    .ok_or("缺少縮放值")?
                    .parse::<f64>()
                    .map_err(|_| "縮放值錯誤")?
            }
            _ => return Err("地圖預覽參數無效".into()),
        }
        i += 1;
    }
    if continuing && seed_given {
        return Err("續接使用保存的seed".into());
    }
    if !scale.is_finite() || !(0.5..=1.0).contains(&scale) {
        return Err("縮放值必須介於0.5與1".into());
    }
    if let Some(d) = &saves {
        crate::checkpoint_store::check_directory(d)?;
    }
    if let Some(d) = &capture {
        if scale != 1.0 || !d.is_dir() {
            return Err("擷取需要既有目錄及--scale 1".into());
        }
    }
    let assets = assets.ok_or("請指定--assets素材包")?;
    let data = WorldData::load(&assets)?;
    let mut state = if continuing {
        WorldState::load(saves.as_deref().ok_or("續接需要--save-dir")?, &data)?
    } else {
        WorldState::new(&data, seed)
    };
    let pack = Pack::load(&assets)?;
    // Check every displayed glyph before opening the window.
    for font in &pack.fonts {
        for ch in UI_TEXT
            .chars()
            .chain(data.menu.iter().flat_map(|m| m.text.chars()))
            .chain("Noto 9000123456789".chars())
        {
            if !font.glyphs.contains_key(&ch) {
                return Err(format!("地圖字型缺字：{ch}"));
            }
        }
    }
    if check_only {
        for area in 0..8 {
            let mut cells = Vec::new();
            for y in 0..80 {
                for x in 0..70 {
                    cells.push(data.tile(area, Position { x, y })?);
                }
            }
            println!("MAP\t{}\t{:016x}", area + 1, checksum(&cells));
        }
        println!("MEDIA\t65\t12\t3\t{}", pack.music.frames);
        return Ok(());
    }
    let mut sdl = Sdl::open_named(W, H, scale, mute, "神州八劍・Rust 世界移動預覽")?;
    sdl.configure_poster(&assets, saves.as_deref(), capture.as_deref(), scale)?;
    let (mut pending, mut audio, mut captures, mut saved, mut readback_equal) =
        (None, 0, 0, 0, true);
    let (mut queued_bytes, mut drains, mut last_queue) = (0u64, 0u64, 0u32);
    'app: loop {
        let (mut snap, mut save) = (false, false);
        for e in sdl.events() {
            let kind = u32::from_ne_bytes(e.bytes[..4].try_into().unwrap());
            if kind == 0x100 {
                break 'app;
            }
            if kind == 0x300 && e.bytes[13] == 0 {
                let key = i32::from_ne_bytes(e.bytes[20..24].try_into().unwrap());
                match key {
                    27 => break 'app,
                    1073741891 => state.font = (state.font + 1) % 3, // F10
                    109 => state.music = !state.music,
                    1073741888 => save = true,
                    1073741893 => snap = capture.is_some(),
                    _ => {
                        if pending.is_none() {
                            if let Some(k) = key_motion(key) {
                                if let WalkResult::Boundary(b) = state.walk(&data, k)? {
                                    pending = Some(b);
                                }
                            }
                        }
                    }
                }
            }
            if kind == 0x401 && e.bytes[16] == 1 {
                let x = i32::from_ne_bytes(e.bytes[20..24].try_into().unwrap());
                let y = i32::from_ne_bytes(e.bytes[24..28].try_into().unwrap());
                if (2..46).contains(&y) {
                    if (144..828).contains(&x) {
                        state.font = ((x - 144) / 228) as u8;
                    } else if (920..1152).contains(&x) {
                        state.music = !state.music;
                    } else if (1480..1712).contains(&x) {
                        save = true;
                    }
                }
            }
        }
        if save {
            if pending.is_some() {
                eprintln!("事件邊界不保存；保留上一次完整檢查點");
            } else if let Some(d) = &saves {
                state.save(d, &data)?;
                saved += 1;
            }
        }
        sdl.pause_music(mute || !state.music);
        if !mute && state.music {
            let n = sdl.queued();
            if n < last_queue {
                drains += 1;
            }
            if n < 38400 {
                let mut b = Vec::with_capacity(38400);
                for _ in 0..9600 {
                    b.extend_from_slice(&pack.music.pcm[audio..audio + 4]);
                    audio = (audio + 4) % pack.music.pcm.len();
                }
                sdl.queue(&b)?;
                queued_bytes += b.len() as u64;
            }
            last_queue = sdl.queued();
        }
        let frame = compose(&pack, &data, &state, pending, saves.is_some(), 6, false)?;
        let back = sdl.draw(&frame, snap)?;
        if let Some(pixels) = &back {
            readback_equal &= *pixels == frame;
        }
        let status = format!(
            "actions\t{}\nx\t{}\ny\t{}\nremaining\t{}\nseed\t{}\nstate_hash\t{:016x}\nfont\t{}\nmusic\t{}\npending\t{:?}\nsaves\t{saved}\nloaded\t{continuing}\ncaptures\t{}\nreadback_equal\t{readback_equal}\nqueued_bytes\t{queued_bytes}\ndrains\t{drains}\nmusic_frames\t{}\n",
            state.actions,
            state.position.x,
            state.position.y,
            state.remaining,
            state.rng.seed,
            checksum(&state.encode(&data)?),
            state.font,
            state.music,
            pending,
            captures + u32::from(snap),
            pack.music.frames
        );
        if let Some(d) = &capture {
            if snap {
                captures += 1;
                let back = back.ok_or("缺少SDL讀回")?;
                readback_equal &= back == frame;
                ppm(&d.join(format!("frame-{captures:03}.ppm")), &frame)?;
                ppm(&d.join(format!("readback-{captures:03}.ppm")), &back)?;
                std::fs::write(
                    d.join(format!("capture-{captures:03}.tsv")),
                    format!("{status}frame_hash\t{:016x}\n", checksum(&frame)),
                )
                .map_err(|e| e.to_string())?;
            }
            std::fs::write(d.join("status.tmp"), &status).map_err(|e| e.to_string())?;
            std::fs::rename(d.join("status.tmp"), d.join("status.tsv"))
                .map_err(|e| e.to_string())?;
        }
        std::thread::sleep(Duration::from_millis(30));
    }
    Ok(())
}
