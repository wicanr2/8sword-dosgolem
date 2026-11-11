use crate::battle::{Modifiers, Outcome, Side, Stack};
use crate::catalog::{Catalog, UnitId};
use crate::checkpoint_store;
use crate::controller::{
    Checkpoint, Controller, EnemyConfig, NAVIGATION, OriginalRng, POSITIONS, ViewState,
};
use crate::media_assets::{Font, MediaPack, checksum};
use crate::sdl::Sdl;
use crate::spells::{Spell, SpellBook, SpellResult};
use std::fs::{self, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

pub(crate) const W: usize = 1920;
pub(crate) const H: usize = 1320;
pub(crate) const TOP: i32 = 48;
pub(crate) const GOLD: [u8; 3] = [255, 241, 181];
pub const UI_TEXT: &str = "字型 隸書 草書 音樂 開 關 再戰 待選敵軍 勝利 全軍覆沒 撤退 出手 略過 方向鍵選敵 Enter Space Esc R F10 損失";

const MAP_SPELLS: [&str; 8] = [
    "造橋術",
    "煉金術",
    "召兵術",
    "跳躍術",
    "停時術",
    "鳥瞰術",
    "涉水術",
    "傳送術",
];
pub(crate) struct SpellView {
    pub(crate) cursor: usize,
    pub(crate) animation: Option<(SpellResult, Instant)>,
    pub(crate) side: Side,
}
fn menu_label(frame: &mut [u8], font: &Font, value: &str, x: i32, y: i32) -> Result<(), String> {
    let mut pos = x;
    for ch in value.chars() {
        let width = if ch.is_ascii() { 24 } else { 48 };
        if pos + width > x + 264 {
            return Err("法術欄位超界".into());
        }
        glyph(frame, font, ch, [pos, y, width, 84], GOLD)?;
        pos += width;
    }
    Ok(())
}
fn spaced_spell(value: &str) -> String {
    format!(
        " {} ",
        value
            .chars()
            .map(|c| c.to_string())
            .collect::<Vec<_>>()
            .join(" ")
    )
}
pub(crate) fn sprite(frame: &mut [u8], image: &crate::media_assets::Image, x: i32, y: i32) {
    for yy in 0..image.height {
        for xx in 0..image.width {
            let dx = x + xx as i32;
            let dy = y + yy as i32;
            if dx < 0 || dy < 0 || dx >= W as i32 || dy >= H as i32 {
                continue;
            }
            let src = (yy * image.width + xx) * 4;
            let a = u32::from(image.pixels[src + 3]);
            let dst = (dy as usize * W + dx as usize) * 4;
            for c in 0..3 {
                frame[dst + c] = ((u32::from(image.pixels[src + c]) * a
                    + u32::from(frame[dst + c]) * (255 - a)
                    + 127)
                    / 255) as u8;
            }
        }
    }
}
fn begin_spell_animation(
    view: &mut SpellView,
    result: SpellResult,
    message: &mut String,
    seen: &mut Option<(u64, usize, usize)>,
    ready: &mut Instant,
    now: Instant,
) {
    *message = result.spell.name().to_owned();
    view.animation = Some((result, now));
    view.side = Side::Player;
    *seen = None;
    *ready = now + Duration::from_millis(480);
}

pub(crate) fn fill(frame: &mut [u8], rect: [i32; 4], color: [u8; 3]) {
    let [x, y, w, h] = rect;
    for yy in y.max(0)..(y + h).min(H as i32) {
        for xx in x.max(0)..(x + w).min(W as i32) {
            let at = (yy as usize * W + xx as usize) * 4;
            frame[at..at + 4].copy_from_slice(&[color[0], color[1], color[2], 255]);
        }
    }
}
pub(crate) fn border(frame: &mut [u8], r: [i32; 4], color: [u8; 3]) {
    let [x, y, w, h] = r;
    for q in [
        [x, y, w, 2],
        [x, y + h - 2, w, 2],
        [x, y, 2, h],
        [x + w - 2, y, 2, h],
    ] {
        fill(frame, q, color)
    }
}
pub(crate) fn glyph(
    frame: &mut [u8],
    font: &Font,
    ch: char,
    rect: [i32; 4],
    color: [u8; 3],
) -> Result<(), String> {
    let mask = font
        .glyphs
        .get(&ch)
        .ok_or_else(|| format!("字型缺字：{ch}"))?;
    let [x, y, w, h] = rect;
    for yy in 0..h {
        for xx in 0..w {
            let dx = x + xx;
            let dy = y + yy;
            if dx < 0 || dy < 0 || dx >= W as i32 || dy >= H as i32 {
                continue;
            }
            let a = u32::from(
                mask[(yy as usize * 64 / h as usize) * 64 + xx as usize * 64 / w as usize],
            );
            if a == 0 {
                continue;
            }
            let at = (dy as usize * W + dx as usize) * 4;
            for c in 0..3 {
                frame[at + c] =
                    ((u32::from(color[c]) * a + u32::from(frame[at + c]) * (255 - a) + 127) / 255)
                        as u8;
            }
        }
    }
    Ok(())
}
pub(crate) fn text(
    frame: &mut [u8],
    font: &Font,
    value: &str,
    x: i32,
    y: i32,
    height: i32,
    max_width: i32,
) -> Result<(), String> {
    let chars: Vec<char> = value.chars().collect();
    let width_of = |ch: char| if ch.is_ascii() { height / 2 } else { height };
    let overflow = chars.iter().copied().map(width_of).sum::<i32>() > max_width;
    let limit = max_width - if overflow { height } else { 0 };
    let mut pos = x;
    for ch in chars {
        let width = if ch.is_ascii() { height / 2 } else { height };
        if pos + width > x + limit {
            break;
        }
        glyph(frame, font, ch, [pos, y, width, height], GOLD)?;
        pos += width;
    }
    if overflow && max_width >= height {
        glyph(frame, font, '…', [pos, y, height, height], GOLD)?;
    }
    Ok(())
}
fn roster(weak: bool, spells: bool, taoist: bool) -> [[Stack; 6]; 2] {
    let mut rows = [[Stack::default(); 6]; 2];
    for (side, raw, name, count) in [
        (0, 0, "openkb:wolf", if weak { 2 } else { 1000 }),
        (0, 1, "openkb:arcr", if weak { 2 } else { 10 }),
        (1, 0, "native:06", 11),
        (1, 1, "native:16", 35),
        (1, 2, "native:11", 29),
    ] {
        rows[side][raw] = Stack {
            unit: Some(UnitId::parse(name).expect("fixed approved ID")),
            count,
        };
    }
    if spells {
        rows[0] = [Stack::default(); 6];
        for (raw, name, count) in [
            (0, "native:01", 74),
            (1, if taoist { "native:10" } else { "native:12" }, 2),
            (2, "openkb:wolf", 1),
            (3, "openkb:arcr", 1),
        ] {
            rows[0][raw] = Stack {
                unit: Some(UnitId::parse(name).expect("fixed spell fixture")),
                count,
            };
        }
    }
    rows
}
fn battle_controller(
    catalog: &Catalog,
    weak: bool,
    spells: bool,
    taoist: bool,
    enemy_spells: bool,
) -> Result<Controller<'_>, String> {
    let mut rows = roster(weak, spells, taoist);
    if enemy_spells {
        if !spells {
            rows[0] = [Stack::default(); 6];
            for (raw, name, count) in [
                (0, "native:01", 74),
                (1, "openkb:wolf", 2),
                (2, "openkb:arcr", 2),
            ] {
                rows[0][raw] = Stack {
                    unit: Some(UnitId::parse(name).map_err(|e| e.to_string())?),
                    count,
                };
            }
        }
        rows[1] = [Stack::default(); 6];
        rows[1][0] = Stack {
            unit: Some(UnitId::parse("native:12")?),
            count: 3,
        };
        rows[1][1] = Stack {
            unit: Some(UnitId::parse("native:16")?),
            count: 10,
        };
    }
    let book = SpellBook {
        enabled: true,
        charges: [3; 8],
        stat_26b0: 2,
        stat_26ae: 4,
    };
    let c = if enemy_spells {
        Controller::with_enemy_spells(
            catalog,
            rows,
            Side::Enemy,
            Modifiers::default(),
            spells.then_some(book),
            EnemyConfig {
                stat_26ae: 4,
                shifted_alias: 0,
            },
        )
    } else if spells {
        Controller::with_spells(catalog, rows, Side::Player, Modifiers::default(), book)
    } else {
        Controller::new(catalog, rows, Side::Player, Modifiers::default())
    };
    c.map_err(|e| format!("{e:?}"))
}
pub(crate) fn compose(
    pack: &MediaPack,
    catalog: &Catalog,
    c: &Controller<'_>,
    font_index: usize,
    music: bool,
    cursor: usize,
    message: &str,
    spell_view: &SpellView,
    now: Instant,
    checkpoint_enabled: bool,
    notice: Option<&str>,
) -> Result<Vec<u8>, String> {
    let mut frame = vec![0u8; W * H * 4];
    fill(&mut frame, [0, 0, W as i32, H as i32], [9, 36, 29]);
    frame[TOP as usize * W * 4..(TOP as usize + 1200) * W * 4]
        .copy_from_slice(&pack.background.pixels);
    let font = &pack.fonts[font_index];
    text(&mut frame, font, "字型", 12, 2, 40, 120)?;
    for (i, name) in ["Noto 900", "隸書", "草書"].iter().enumerate() {
        let rect = [144 + i as i32 * 228, 2, 216, 44];
        fill(
            &mut frame,
            rect,
            if i == font_index {
                [119, 44, 41]
            } else {
                [20, 55, 40]
            },
        );
        border(&mut frame, rect, [206, 170, 74]);
        text(&mut frame, font, name, rect[0] + 12, 4, 38, 192)?;
    }
    for (x, label) in [
        (920, if music { "音樂 開" } else { "音樂 關" }),
        (1200, "再戰"),
    ] {
        border(&mut frame, [x, 2, 232, 44], [206, 170, 74]);
        text(&mut frame, font, label, x + 10, 4, 38, 210)?;
    }
    if checkpoint_enabled {
        border(&mut frame, [1480, 2, 232, 44], [206, 170, 74]);
        text(&mut frame, font, "F7存檔", 1490, 4, 38, 210)?;
    }
    for side in 0..2 {
        for slot in 0..6 {
            let raw = usize::from(c.slots()[side][slot]);
            let stack = c.battle().rows()[side][raw];
            if stack.count == 0 {
                continue;
            }
            let id = stack.unit.ok_or("存活隊伍沒有ID")?;
            let image = pack
                .units
                .get(&id)
                .ok_or_else(|| format!("缺少部隊圖片：{id}"))?;
            let [x, y] = POSITIONS[side * 6 + slot];
            let y = y + TOP;
            for yy in 0..300 {
                for xx in 0..264 {
                    let from = (yy * 264 + xx) * 4;
                    let a = u32::from(image.pixels[from + 3]);
                    if a == 0 {
                        continue;
                    }
                    let at = ((y as usize + yy) * W + x as usize + xx) * 4;
                    for channel in 0..3 {
                        frame[at + channel] = ((u32::from(image.pixels[from + channel]) * a
                            + u32::from(frame[at + channel]) * (255 - a)
                            + 127)
                            / 255) as u8;
                    }
                }
            }
            let digits = stack.count.to_string();
            for (i, ch) in digits.chars().enumerate() {
                glyph(
                    &mut frame,
                    font,
                    ch,
                    [x + 96 + i as i32 * 24, y + 210, 24, 90],
                    GOLD,
                )?;
            }
        }
    }
    if c.battle().outcome().is_none() {
        if let Some(actor) = c.current() {
            let [x, y] = POSITIONS[actor.side.index() * 6 + actor.slot];
            border(&mut frame, [x, y + TOP, 264, 300], [255, 225, 90]);
        }
        if (1..=12).contains(&cursor) {
            let index = if cursor <= 6 {
                6 + cursor - 1
            } else {
                cursor - 7
            };
            let [x, y] = POSITIONS[index];
            border(&mut frame, [x + 3, y + TOP + 3, 258, 294], [255, 101, 70]);
        }
    }
    if let Some((result, start)) = &spell_view.animation {
        let elapsed = now.duration_since(*start).as_millis();
        if elapsed < 480 {
            for effect in &result.effects {
                let [x, y] = POSITIONS[effect.side.index() * 6 + effect.slot];
                if result.spell == Spell::Clone {
                    border(&mut frame, [x, y + TOP, 264, 300], [120, 255, 220]);
                } else if let Some(image) = pack.spell_fx.get((elapsed as usize / 120) % 4) {
                    sprite(&mut frame, image, x, y + TOP);
                }
            }
            if result.spell == Spell::Freeze {
                border(
                    &mut frame,
                    [
                        if spell_view.side == Side::Player {
                            0
                        } else {
                            816
                        },
                        TOP,
                        816,
                        1200,
                    ],
                    [120, 225, 255],
                );
            }
        }
    }
    if c.is_caster() && c.selected_spell().is_none() {
        let book = c.spell_book().ok_or("缺少法術資料")?;
        for (i, spell) in Spell::ALL.iter().enumerate() {
            let y = TOP + 120 + i as i32 * 120;
            fill(&mut frame, [96, y, 1200, 120], [12, 49, 36]);
            if i == spell_view.cursor {
                fill(&mut frame, [240, y + 18, 360, 84], [119, 44, 41]);
            }
            menu_label(&mut frame, font, &spaced_spell(spell.name()), 240, y + 18)?;
            menu_label(&mut frame, font, &book.charges[i].to_string(), 504, y + 18)?;
            menu_label(&mut frame, font, &spaced_spell(MAP_SPELLS[i]), 816, y + 18)?;
            menu_label(&mut frame, font, "0", 1104, y + 18)?;
        }
    }
    let status = if let Some(notice) = notice {
        notice.to_owned()
    } else if let Some(outcome) = c.battle().outcome() {
        match outcome {
            Outcome::Win => "勝利",
            Outcome::Loss => "全軍覆沒",
            Outcome::Retreat => "撤退",
        }
        .to_owned()
    } else if c.is_caster() {
        if let Some(spell) = c.selected_spell() {
            format!(
                "{}  {}",
                spell.name(),
                if spell == Spell::Clone {
                    "選擇同袍"
                } else {
                    "選擇敵軍"
                }
            )
        } else {
            "選擇法術  方向鍵選術 Enter確認 Space略過 Esc撤退".into()
        }
    } else if let Some(actor) = c.current() {
        let row = c.battle().rows()[actor.side.index()][actor.raw];
        let name = &catalog.get(row.unit.ok_or("部隊名稱無效")?).name;
        format!("{name}  待選敵軍")
    } else {
        message.to_owned()
    };
    text(&mut frame, font, &status, 18, 1250, 32, 1860)?;
    text(
        &mut frame,
        font,
        if checkpoint_enabled {
            "方向鍵選敵 Enter出手 Space略過 Esc撤退 R再戰 F10字型 F7存檔"
        } else {
            "方向鍵選敵 Enter出手 Space略過 Esc撤退 R再戰 F10字型"
        },
        18,
        1288,
        28,
        1860,
    )?;
    Ok(frame)
}
pub(crate) fn ppm(path: &Path, pixels: &[u8]) -> Result<(), String> {
    let f = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|e| e.to_string())?;
    let mut f = BufWriter::new(f);
    write!(f, "P6\n{W} {H}\n255\n").map_err(|e| e.to_string())?;
    for row in pixels.chunks_exact(4) {
        f.write_all(&row[..3]).map_err(|e| e.to_string())?;
    }
    f.flush().map_err(|e| e.to_string())
}
fn wav(path: &Path, pcm: &[u8]) -> Result<(), String> {
    let mut f = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|e| e.to_string())?;
    let len: u32 = pcm.len().try_into().map_err(|_| "音訊擷取過大")?;
    let mut header = Vec::new();
    header.extend(b"RIFF");
    header.extend((len + 36).to_le_bytes());
    header.extend(b"WAVEfmt ");
    header.extend(16u32.to_le_bytes());
    header.extend(1u16.to_le_bytes());
    header.extend(2u16.to_le_bytes());
    header.extend(48000u32.to_le_bytes());
    header.extend(192000u32.to_le_bytes());
    header.extend(4u16.to_le_bytes());
    header.extend(16u16.to_le_bytes());
    header.extend(b"data");
    header.extend(len.to_le_bytes());
    f.write_all(&header)
        .and_then(|_| f.write_all(pcm))
        .map_err(|e| e.to_string())
}

pub fn run(args: &[String]) -> Result<(), String> {
    let (mut assets, mut capture) = (None, None);
    let (mut save_dir, mut continuing, mut seed_given) = (None, false, false);
    let (mut mute, mut weak, mut spells, mut taoist) = (false, false, false, false);
    let mut enemy_spells = false;
    let mut scale = 2.0 / 3.0;
    let mut seed = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_nanos() as u32;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--save-dir" => {
                i += 1;
                save_dir = Some(PathBuf::from(args.get(i).ok_or("缺少存檔目錄")?));
            }
            "--continue" => continuing = true,
            "--assets" => {
                i += 1;
                assets = Some(PathBuf::from(args.get(i).ok_or("缺少素材路徑")?));
            }
            "--capture-dir" => {
                i += 1;
                capture = Some(PathBuf::from(args.get(i).ok_or("缺少擷取路徑")?));
            }
            "--scale" => {
                i += 1;
                scale = args
                    .get(i)
                    .ok_or("缺少縮放值")?
                    .parse::<f64>()
                    .map_err(|_| "縮放值無效")?;
            }
            "--seed" => {
                seed_given = true;
                i += 1;
                seed = args
                    .get(i)
                    .ok_or("缺少種子")?
                    .parse::<u32>()
                    .map_err(|_| "種子無效")?;
            }
            "--mute" => mute = true,
            "--weak" => weak = true,
            "--spells" => spells = true,
            "--enemy-spells" => enemy_spells = true,
            "--taoist" => {
                spells = true;
                taoist = true;
            }
            _ => return Err("桌面參數無效".into()),
        }
        i += 1;
    }
    if continuing && (weak || spells || taoist || enemy_spells || seed_given) {
        return Err("續接時使用保存的軍隊與種子，請移除樣本與seed參數".into());
    }
    if let Some(dir) = &save_dir {
        checkpoint_store::check_directory(dir)?;
    }
    if !scale.is_finite() || !(0.5..=1.0).contains(&scale) {
        return Err("縮放值必須介於0.5與1".into());
    }
    if let Some(path) = &capture {
        if scale != 1.0 {
            return Err("擷取比對須使用--scale 1".into());
        }
        if !path.is_dir() {
            return Err("擷取目錄必須存在".into());
        }
    }
    let catalog = Catalog::builtin()?;
    let restored = if continuing {
        Some(checkpoint_store::load(
            save_dir.as_deref().ok_or("續接需要--save-dir")?,
            &catalog,
        )?)
    } else {
        None
    };
    if let Some(s) = &restored {
        weak = s.view.scenario & 1 != 0;
        spells = s.view.scenario & 2 != 0;
        taoist = s.view.scenario & 4 != 0;
        enemy_spells = s.view.scenario & 8 != 0;
    }
    let scenario = u8::from(weak)
        | (u8::from(spells) << 1)
        | (u8::from(taoist) << 2)
        | (u8::from(enemy_spells) << 3);
    let assets = assets.ok_or("請指定--assets素材包")?;
    let mut pack = MediaPack::load(&assets)?;
    if spells || enemy_spells {
        pack.load_spell_assets(&assets)?;
    }
    let (mut c, mut rng, view) = if let Some(s) = restored {
        (s.controller, s.rng, s.view)
    } else {
        (
            battle_controller(&catalog, weak, spells, taoist, enemy_spells)?,
            OriginalRng { seed },
            ViewState::default(),
        )
    };
    for row in c.battle().rows().iter().flatten().filter(|r| r.count > 0) {
        if !row.unit.is_some_and(|id| pack.units.contains_key(&id)) {
            return Err("存活部隊缺少素材".into());
        }
    }
    let mut spell_view = SpellView {
        cursor: usize::from(view.spell_cursor),
        animation: None,
        side: Side::Player,
    };
    let mut sdl = Sdl::open(W, H, scale, mute)?;
    sdl.configure_poster(&assets, save_dir.as_deref(), capture.as_deref(), scale)?;
    let (mut font, mut music, mut cursor) = (
        usize::from(view.font),
        view.music && !mute,
        usize::from(view.cursor),
    );
    sdl.pause_music(!music);
    let mut message = String::new();
    let mut seen = if continuing {
        c.current().map(|a| (c.half_turn(), a.side.index(), a.raw))
    } else {
        None
    };
    let mut ready = Instant::now();
    let mut enemy_ready = Instant::now() + Duration::from_millis(180);
    let (mut save_requested, mut saves, mut last_saved) = (false, 0u64, String::new());
    let mut notice = continuing.then(|| {
        (
            "讀檔 OK".to_owned(),
            Instant::now() + Duration::from_millis(1200),
        )
    });
    let (mut frames, mut captures, mut queued_bytes, mut drains) = (0u64, 0u64, 0u64, 0u64);
    let mut last_queue = 0;
    let (mut audio_position, mut captured_audio) = (0usize, Vec::new());
    let mut capture_next = false;
    let mut readback_equal = true;
    'game: loop {
        let now = Instant::now();
        for event in sdl.events() {
            let b = event.bytes;
            let kind = u32::from_le_bytes(b[0..4].try_into().map_err(|_| "輸入截斷")?);
            if kind == 0x100 {
                break 'game;
            }
            let mut key = 0i32;
            if kind == 0x300 && b[13] == 0 {
                key = i32::from_le_bytes(b[20..24].try_into().map_err(|_| "按鍵截斷")?);
            }
            if kind == 0x401 && b[16] == 1 {
                let x = i32::from_le_bytes(b[20..24].try_into().map_err(|_| "游標截斷")?);
                let y = i32::from_le_bytes(b[24..28].try_into().map_err(|_| "游標截斷")?);
                // SDL_RenderSetLogicalSize already maps mouse events to logical pixels.
                if (2..46).contains(&y) {
                    for n in 0..3 {
                        if (144 + n * 228..360 + n * 228).contains(&x) {
                            font = n as usize;
                        }
                    }
                    if (920..1152).contains(&x) {
                        key = 109;
                    }
                    if (1200..1432).contains(&x) {
                        key = 114;
                    }
                    if save_dir.is_some() && (1480..1712).contains(&x) {
                        key = 1073741888;
                    }
                }
            }
            if key == 1073741891 {
                font = (font + 1) % 3;
            }
            if key == 109 || key == 77 {
                music = !music && !mute;
                sdl.pause_music(!music);
            }
            if key == 1073741893 && capture.is_some() {
                capture_next = true;
            }
            if key == 1073741888 && save_dir.is_some() {
                save_requested = true;
                continue;
            }
            if key == 114 || key == 82 {
                c = battle_controller(&catalog, weak, spells, taoist, enemy_spells)?;
                spell_view.animation = None;
                seen = None;
                ready = now;
                message.clear();
                continue;
            }
            if c.battle().outcome().is_some() {
                if key == 27 {
                    break 'game;
                }
                continue;
            }
            if c.current().is_some_and(|actor| actor.side == Side::Player) && now >= ready {
                if c.is_caster() {
                    if c.selected_spell().is_none() {
                        match key {
                            1073741906 => spell_view.cursor = (spell_view.cursor + 7) % 8,
                            1073741905 => spell_view.cursor = (spell_view.cursor + 1) % 8,
                            13 => match c.select_spell(Spell::ALL[spell_view.cursor]) {
                                Ok(Some(result)) => begin_spell_animation(
                                    &mut spell_view,
                                    result,
                                    &mut message,
                                    &mut seen,
                                    &mut ready,
                                    now,
                                ),
                                Ok(None) => {
                                    cursor = c.current().ok_or("施法者消失")?.slot + 7;
                                }
                                Err(crate::controller::ControlError::NoCharge) => {}
                                Err(e) => return Err(format!("{e:?}")),
                            },
                            32 => {
                                c.skip().map_err(|e| format!("{e:?}"))?;
                                seen = None;
                            }
                            27 => {
                                c.retreat().map_err(|e| format!("{e:?}"))?;
                                seen = None;
                            }
                            _ => {}
                        }
                    } else {
                        match key {
                            1073741906 | 1073741905 | 1073741904 | 1073741903 => {
                                let direction = match key {
                                    1073741906 => 0,
                                    1073741905 => 1,
                                    1073741904 => 2,
                                    _ => 3,
                                };
                                let next = NAVIGATION[cursor][direction];
                                if next != 0 {
                                    cursor = usize::from(next);
                                }
                            }
                            13 => {
                                let clone = c.selected_spell() == Some(Spell::Clone);
                                let target = if clone && (7..=12).contains(&cursor) {
                                    Some(cursor - 7)
                                } else if !clone && (1..=6).contains(&cursor) {
                                    Some(cursor - 1)
                                } else {
                                    None
                                };
                                if let Some(target) = target {
                                    match c.target_spell(target, &mut rng) {
                                        Ok(result) => begin_spell_animation(
                                            &mut spell_view,
                                            result,
                                            &mut message,
                                            &mut seen,
                                            &mut ready,
                                            now,
                                        ),
                                        Err(crate::controller::ControlError::InvalidTarget) => {}
                                        Err(e) => return Err(format!("{e:?}")),
                                    }
                                }
                            }
                            32 | 27 => {
                                c.cancel_spell_target(key == 27)
                                    .map_err(|e| format!("{e:?}"))?;
                                seen = None;
                            }
                            _ => {}
                        }
                    }
                    continue;
                }
                match key {
                    1073741906 | 1073741905 | 1073741904 | 1073741903 => {
                        let direction = match key {
                            1073741906 => 0,
                            1073741905 => 1,
                            1073741904 => 2,
                            _ => 3,
                        };
                        let next = NAVIGATION[cursor][direction];
                        if next != 0 {
                            cursor = usize::from(next);
                        }
                    }
                    13 => {
                        if (1..=6).contains(&cursor) {
                            match c.attack(cursor - 1) {
                                Ok(action) => {
                                    message = format!("損失 {}", action.loss);
                                    seen = None;
                                    ready = now + Duration::from_millis(140);
                                }
                                Err(_) => message = "待選敵軍".into(),
                            }
                        }
                    }
                    32 => {
                        c.skip().map_err(|e| format!("{e:?}"))?;
                        seen = None;
                    }
                    27 => {
                        c.retreat().map_err(|e| format!("{e:?}"))?;
                        seen = None;
                    }
                    _ => {}
                }
            }
        }
        if save_requested && now >= ready {
            let state = Checkpoint {
                controller: c.clone(),
                rng,
                view: ViewState {
                    font: font as u8,
                    music,
                    cursor: cursor as u8,
                    spell_cursor: spell_view.cursor as u8,
                    scenario,
                },
            };
            match checkpoint_store::save(save_dir.as_deref().ok_or("缺少存檔目錄")?, &state) {
                Ok(()) => {
                    saves += 1;
                    last_saved = format!("{:016x}", checksum(&state.encode()?));
                    notice = Some(("存檔 OK".into(), now + Duration::from_millis(1200)));
                }
                Err(e) => {
                    eprintln!("存檔失敗：{e}");
                    notice = Some(("存檔失敗".into(), now + Duration::from_millis(1200)));
                }
            }
            save_requested = false;
        }
        if now >= ready && c.battle().outcome().is_none() {
            if let Some(actor) = c.next_actor().map_err(|e| format!("{e:?}"))? {
                let key = (c.half_turn(), actor.side.index(), actor.raw);
                if seen != Some(key) {
                    seen = Some(key);
                    if actor.side == Side::Player {
                        cursor = actor.slot + 7;
                    }
                    enemy_ready = now + Duration::from_millis(180);
                }
                if actor.side == Side::Enemy && now >= enemy_ready {
                    if c.is_enemy_caster() {
                        let result = c.enemy_cast(&mut rng).map_err(|e| format!("{e:?}"))?;
                        begin_spell_animation(
                            &mut spell_view,
                            result,
                            &mut message,
                            &mut seen,
                            &mut ready,
                            now,
                        );
                        spell_view.side = Side::Enemy;
                    } else {
                        let target = c.enemy_target(&mut rng).map_err(|e| format!("{e:?}"))?;
                        let action = c.attack(target).map_err(|e| format!("{e:?}"))?;
                        message = format!("損失 {}", action.loss);
                        seen = None;
                        ready = now + Duration::from_millis(140);
                    }
                }
            }
        }
        if music {
            let queued = sdl.queued();
            if queued < last_queue {
                drains += 1;
            }
            if queued < 38400 {
                let mut chunk = Vec::with_capacity(38400);
                for _ in 0..9600 {
                    chunk.extend_from_slice(&pack.music.pcm[audio_position..audio_position + 4]);
                    audio_position = (audio_position + 4) % pack.music.pcm.len();
                }
                sdl.queue(&chunk)?;
                queued_bytes += chunk.len() as u64;
                if captured_audio.len() < 960000 {
                    let n = (960000 - captured_audio.len()).min(chunk.len());
                    captured_audio.extend_from_slice(&chunk[..n]);
                }
            }
            last_queue = sdl.queued();
        }
        let frame = compose(
            &pack,
            &catalog,
            &c,
            font,
            music,
            cursor,
            &message,
            &spell_view,
            now,
            save_dir.is_some(),
            notice
                .as_ref()
                .filter(|(_, until)| now < *until)
                .map(|(text, _)| text.as_str()),
        )?;
        let readback = sdl.draw(&frame, capture_next)?;
        if capture_next {
            let path = capture.as_ref().ok_or("擷取路徑消失")?;
            captures += 1;
            ppm(&path.join(format!("frame-{captures:03}.ppm")), &frame)?;
            let pixels = readback.ok_or("缺少紋理讀回")?;
            readback_equal &= pixels == frame;
            ppm(&path.join(format!("readback-{captures:03}.ppm")), &pixels)?;
            wav(
                &path.join(format!("audio-{captures:03}.wav")),
                &captured_audio,
            )?;
            let mut capture_state = format!(
                "frame_hash\t{:016x}\nfont\t{}\nsequence\t{}\nspell_returns\t{}\narmy\t{}\nhp\t{}\ncharges\t{}\nfx\t{}\n",
                checksum(&frame),
                ["noto", "lishu", "caoshu"][font],
                c.battle().sequence(),
                c.spell_returns(),
                c.battle().rows()[0]
                    .iter()
                    .map(|s| s.count.to_string())
                    .collect::<Vec<_>>()
                    .join(","),
                c.battle().hp()[0]
                    .iter()
                    .map(|n| n.to_string())
                    .collect::<Vec<_>>()
                    .join(","),
                c.spell_book()
                    .map(|b| b
                        .charges
                        .iter()
                        .map(|n| n.to_string())
                        .collect::<Vec<_>>()
                        .join(","))
                    .unwrap_or_default(),
                spell_view.animation.as_ref().is_some_and(
                    |(_, start)| now.duration_since(*start) < Duration::from_millis(480)
                )
            );
            capture_state.push_str(&format!(
                "enemy_returns\t{}\nenemy_army\t{}\nspell\t{}\n",
                c.enemy_returns(),
                c.battle().rows()[1]
                    .iter()
                    .map(|s| s.count.to_string())
                    .collect::<Vec<_>>()
                    .join(","),
                spell_view
                    .animation
                    .as_ref()
                    .map(|(r, _)| r.spell.index().to_string())
                    .unwrap_or_default()
            ));
            let state = Checkpoint {
                controller: c.clone(),
                rng,
                view: ViewState {
                    font: font as u8,
                    music,
                    cursor: cursor as u8,
                    spell_cursor: spell_view.cursor as u8,
                    scenario,
                },
            };
            capture_state.push_str(&format!(
                "checkpoint_hash\t{:016x}\nseed\t{}\nsaves\t{saves}\nloaded\t{continuing}\n",
                checksum(&state.encode()?),
                rng.seed
            ));
            fs::write(
                path.join(format!("capture-{captures:03}.tsv")),
                capture_state,
            )
            .map_err(|e| e.to_string())?;
            capture_next = false;
        }
        frames += 1;
        if let Some(path) = &capture {
            if frames % 3 == 0 {
                let (actor_side, slot, raw) = if let Some(a) = c.current() {
                    (
                        if a.side == Side::Player {
                            "player"
                        } else {
                            "enemy"
                        },
                        a.slot as i32,
                        a.raw as i32,
                    )
                } else {
                    ("wait", -1, -1)
                };
                let outcome = match c.battle().outcome() {
                    None => "active",
                    Some(Outcome::Win) => "win",
                    Some(Outcome::Loss) => "loss",
                    Some(Outcome::Retreat) => "retreat",
                };
                let targets = if c.current().is_some() && !c.is_enemy_caster() {
                    c.legal_targets()
                        .map_err(|e| format!("{e:?}"))?
                        .iter()
                        .map(|n| n.to_string())
                        .collect::<Vec<_>>()
                        .join(",")
                } else {
                    String::new()
                };
                let data = format!(
                    "frames\t{frames}\ncaptures\t{captures}\nactor\t{actor_side}\nslot\t{slot}\nraw\t{raw}\ncursor\t{cursor}\nsequence\t{}\nhalf_turn\t{}\noutcome\t{outcome}\nfont\t{}\nmusic\t{}\nqueued_bytes\t{queued_bytes}\ndrains\t{drains}\nreadback_equal\t{readback_equal}\nframe_hash\t{:016x}\nlegal\t{targets}\nmusic_frames\t{}\n",
                    c.battle().sequence(),
                    c.half_turn(),
                    ["noto", "lishu", "caoshu"][font],
                    if music { "on" } else { "off" },
                    checksum(&frame),
                    pack.music.frames
                );
                let data = format!(
                    "{data}phase\t{}\nspell_cursor\t{}\nspell_returns\t{}\ncharges\t{}\n",
                    if c.is_caster() {
                        if c.selected_spell().is_some() {
                            "spell-target"
                        } else {
                            "spell-menu"
                        }
                    } else {
                        "ordinary"
                    },
                    spell_view.cursor,
                    c.spell_returns(),
                    c.spell_book()
                        .map(|b| b
                            .charges
                            .iter()
                            .map(|n| n.to_string())
                            .collect::<Vec<_>>()
                            .join(","))
                        .unwrap_or_default()
                );
                let data = format!(
                    "{data}fx\t{}\n",
                    spell_view
                        .animation
                        .as_ref()
                        .is_some_and(|(_, start)| start.elapsed() < Duration::from_millis(480))
                );
                let data = format!(
                    "{data}enemy_returns\t{}\nenemy_army\t{}\nspell\t{}\n",
                    c.enemy_returns(),
                    c.battle().rows()[1]
                        .iter()
                        .map(|s| s.count.to_string())
                        .collect::<Vec<_>>()
                        .join(","),
                    spell_view
                        .animation
                        .as_ref()
                        .map(|(r, _)| r.spell.index().to_string())
                        .unwrap_or_default()
                );
                let data = format!(
                    "{data}army\t{}\nhp\t{}\nremaining\t{}\n",
                    c.battle().rows()[0]
                        .iter()
                        .map(|s| s.count.to_string())
                        .collect::<Vec<_>>()
                        .join(","),
                    c.battle().hp()[0]
                        .iter()
                        .map(|n| n.to_string())
                        .collect::<Vec<_>>()
                        .join(","),
                    c.remaining()[0]
                        .iter()
                        .map(|n| n.to_string())
                        .collect::<Vec<_>>()
                        .join(",")
                );
                let state = Checkpoint {
                    controller: c.clone(),
                    rng,
                    view: ViewState {
                        font: font as u8,
                        music,
                        cursor: cursor as u8,
                        spell_cursor: spell_view.cursor as u8,
                        scenario,
                    },
                };
                let data = format!(
                    "{data}checkpoint_hash\t{:016x}\nlast_saved\t{last_saved}\nseed\t{}\nsaves\t{saves}\nloaded\t{continuing}\nsave_requested\t{save_requested}\n",
                    checksum(&state.encode()?),
                    rng.seed
                );
                fs::write(path.join("status.tmp"), data)
                    .and_then(|_| fs::rename(path.join("status.tmp"), path.join("status.tsv")))
                    .map_err(|e| e.to_string())?;
            }
        }
        std::thread::sleep(Duration::from_millis(24));
    }
    Ok(())
}
