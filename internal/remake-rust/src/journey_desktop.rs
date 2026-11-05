use crate::battle::{Outcome, Side};
use crate::catalog::Catalog;
use crate::controller::NAVIGATION;
use crate::desktop::{self, H, SpellView, W, border, fill, ppm, text};
use crate::journey::Journey;
use crate::media_assets::{MediaPack, checksum};
use crate::sdl::Sdl;
use crate::world::WorldData;
use crate::world_desktop::{self, Pack, key_motion};
use std::path::PathBuf;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
pub const UI_TEXT: &str =
    "遭遇敵軍 迎戰 避戰 返回地圖 戰鬥 金錢 戰績 回到起點 浪跡江湖 方向鍵選擇 Enter確認 已回場";
pub fn run(args: &[String]) -> Result<(), String> {
    let (mut assets, mut capture, mut store): (Option<PathBuf>, Option<PathBuf>, Option<PathBuf>) =
        (None, None, None);
    let (mut continuing, mut mute, mut fixed) = (false, false, false);
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
                    _ => store = p,
                }
            }
            "--continue" => continuing = true,
            "--mute" => mute = true,
            "--seed" => {
                i += 1;
                seed = args
                    .get(i)
                    .ok_or("缺少seed")?
                    .parse()
                    .map_err(|_| "seed錯誤")?;
                fixed = true
            }
            "--scale" => {
                i += 1;
                scale = args
                    .get(i)
                    .ok_or("缺少縮放值")?
                    .parse::<f64>()
                    .map_err(|_| "縮放錯誤")?
            }
            _ => return Err("旅程參數錯誤".into()),
        }
        i += 1;
    }
    if continuing && fixed {
        return Err("冷讀使用保存的seed".into());
    }
    if !scale.is_finite() || !(0.5..=1.0).contains(&scale) {
        return Err("縮放範圍錯誤".into());
    }
    if let Some(p) = &store {
        crate::checkpoint_store::check_directory(p)?;
    }
    if let Some(p) = &capture {
        if scale != 1.0 || !p.is_dir() {
            return Err("擷取需要既有目錄與--scale 1".into());
        }
    }
    let assets = assets.ok_or("缺少素材目錄")?;
    let data = WorldData::load(&assets)?;
    let catalog = Catalog::builtin()?;
    let mut journey = if continuing {
        Journey::load(
            store.as_deref().ok_or("冷讀需要--save-dir")?,
            &catalog,
            &data,
        )?
    } else {
        Journey::new(&data, seed)
    };
    let map = Pack::load(&assets)?;
    let mut battle_pack = MediaPack::load(&assets)?;
    battle_pack.load_spell_assets(&assets)?;
    battle_pack.load_native_units(&assets)?;
    let sdl = Sdl::open_named(W, H, scale, mute, "神州八劍・Rust 原生旅程")?;
    let (mut boundary, mut choose, mut cursor, mut captures, mut saves) =
        (None, false, 7usize, 0u32, 0u32);
    if let Some(cp) = &journey.battle {
        cursor = usize::from(cp.view.cursor);
    }
    let mut spell_view = SpellView {
        cursor: 0,
        animation: None,
        side: Side::Enemy,
    };
    let mut seen = None;
    let (mut ready, mut enemy_ready) = (Instant::now(), Instant::now());
    let (mut audio, mut audio_battle) = (0, false);
    let (mut drains, mut last_queue, mut queued_bytes) = (0u64, 0u32, 0u64);
    let mut save_requested = false;
    'game: loop {
        let now = Instant::now();
        let mut snap = false;
        for e in sdl.events() {
            let b = e.bytes;
            let kind = u32::from_ne_bytes(b[..4].try_into().unwrap());
            if kind == 0x100 {
                break 'game;
            }
            let mut key = if kind == 0x300 && b[13] == 0 {
                i32::from_ne_bytes(b[20..24].try_into().unwrap())
            } else {
                0
            };
            if kind == 0x401 && b[16] == 1 {
                let x = i32::from_ne_bytes(b[20..24].try_into().unwrap());
                let y = i32::from_ne_bytes(b[24..28].try_into().unwrap());
                if (2..46).contains(&y) {
                    for n in 0..3 {
                        if (144 + n * 228..360 + n * 228).contains(&x) {
                            journey.world.font = n as u8;
                        }
                    }
                    if (920..1152).contains(&x) {
                        key = 109;
                    }
                    if (1480..1712).contains(&x) {
                        key = 1073741888;
                    }
                    if (1200..1432).contains(&x)
                        && journey
                            .battle
                            .as_ref()
                            .is_some_and(|c| c.controller.battle().outcome().is_some())
                    {
                        key = 13;
                    }
                }
            }
            match key {
                1073741891 => {
                    journey.world.font = (journey.world.font + 1) % 3;
                    continue;
                }
                109 => {
                    journey.world.music = !journey.world.music;
                    continue;
                }
                1073741893 => {
                    snap = capture.is_some();
                    continue;
                }
                1073741888 => {
                    save_requested = store.is_some();
                    continue;
                }
                _ => {}
            }
            if let Some(cp) = &mut journey.battle {
                if let Some(outcome) = cp.controller.battle().outcome() {
                    if outcome == Outcome::Loss && [1073741904, 1073741903].contains(&key) {
                        choose = !choose;
                    }
                    if key == 13 && now >= ready {
                        journey.finish(
                            &catalog,
                            &data,
                            (outcome == Outcome::Loss).then_some(!choose),
                        )?;
                        choose = false;
                        seen = None;
                        spell_view.animation = None;
                    }
                    continue;
                }
                if now < ready {
                    continue;
                }
                if key == 27 {
                    cp.controller.retreat().map_err(|e| format!("{e:?}"))?;
                    seen = None;
                    continue;
                }
                if cp
                    .controller
                    .current()
                    .is_some_and(|a| a.side == Side::Player)
                {
                    match key {
                        1073741906 | 1073741905 | 1073741904 | 1073741903 => {
                            let direction = match key {
                                1073741906 => 0,
                                1073741905 => 1,
                                1073741904 => 2,
                                _ => 3,
                            };
                            let n = NAVIGATION[cursor][direction];
                            if n != 0 {
                                cursor = usize::from(n);
                            }
                        }
                        13 => {
                            if (1..=6).contains(&cursor)
                                && cp
                                    .controller
                                    .legal_targets()
                                    .map_err(|e| format!("{e:?}"))?
                                    .contains(&(cursor - 1))
                            {
                                cp.controller
                                    .attack(cursor - 1)
                                    .map_err(|e| format!("{e:?}"))?;
                                seen = None;
                                ready = now + Duration::from_millis(140);
                            }
                        }
                        32 => {
                            cp.controller.skip().map_err(|e| format!("{e:?}"))?;
                            seen = None;
                        }
                        _ => {}
                    }
                }
            } else if journey.cue.is_some() {
                if [1073741904, 1073741903, 1073741906, 1073741905].contains(&key) {
                    choose = !choose;
                }
                if key == 13 {
                    journey.choose(&catalog, !choose)?;
                    choose = false;
                    seen = None;
                    ready = now;
                }
            } else {
                if key == 27 {
                    break 'game;
                }
                if boundary.is_none() {
                    if let Some(k) = key_motion(key) {
                        boundary = journey.walk(&data, k)?;
                    }
                }
            }
        }
        if let Some(cp) = &mut journey.battle {
            cp.view.font = journey.world.font;
            cp.view.music = journey.world.music;
            cp.view.cursor = cursor as u8;
        }
        if save_requested && now >= ready {
            if boundary.is_none() {
                journey.save(store.as_deref().ok_or("缺少保存目錄")?, &catalog, &data)?;
                saves += 1;
            }
            save_requested = false;
        }
        if let Some(cp) = &mut journey.battle {
            if now >= ready && cp.controller.battle().outcome().is_none() {
                if let Some(a) = cp.controller.next_actor().map_err(|e| format!("{e:?}"))? {
                    let tag = (cp.controller.half_turn(), a.side.index(), a.raw);
                    if seen != Some(tag) {
                        seen = Some(tag);
                        enemy_ready = now + Duration::from_millis(180);
                        if a.side == Side::Player {
                            cursor = a.slot + 7;
                        }
                    }
                    if a.side == Side::Enemy && now >= enemy_ready {
                        if cp.controller.is_enemy_caster() {
                            let result = cp
                                .controller
                                .enemy_cast(&mut cp.rng)
                                .map_err(|e| format!("{e:?}"))?;
                            spell_view.animation = Some((result, now));
                            ready = now + Duration::from_millis(480);
                        } else {
                            let target = cp
                                .controller
                                .enemy_target(&mut cp.rng)
                                .map_err(|e| format!("{e:?}"))?;
                            cp.controller.attack(target).map_err(|e| format!("{e:?}"))?;
                            ready = now + Duration::from_millis(140);
                        }
                        seen = None;
                    }
                }
            }
            cp.view.cursor = cursor as u8;
        }
        let active = journey.battle.is_some();
        if active != audio_battle {
            sdl.clear_music();
            audio = 0;
            last_queue = 0;
            audio_battle = active;
        }
        sdl.pause_music(mute || !journey.world.music);
        if !mute && journey.world.music {
            let n = sdl.queued();
            if n < last_queue {
                drains += 1;
            }
            if n < 38400 {
                let pcm = if active {
                    &battle_pack.music.pcm
                } else {
                    &map.music.pcm
                };
                let mut chunk = Vec::with_capacity(38400);
                for _ in 0..9600 {
                    chunk.extend_from_slice(&pcm[audio..audio + 4]);
                    audio = (audio + 4) % pcm.len();
                }
                sdl.queue(&chunk)?;
                queued_bytes += chunk.len() as u64;
            }
            last_queue = sdl.queued();
        }
        let font = &map.fonts[usize::from(journey.world.font)];
        let mut frame = if let Some(cp) = &journey.battle {
            desktop::compose(
                &battle_pack,
                &catalog,
                &cp.controller,
                usize::from(cp.view.font),
                cp.view.music,
                cursor,
                "",
                &spell_view,
                now,
                store.is_some(),
                None,
            )?
        } else {
            world_desktop::compose(&map, &data, &journey.world, boundary, store.is_some())?
        };
        if let Some(cp) = &journey.battle {
            fill(&mut frame, [1200, 2, 240, 44], [9, 36, 29]);
            border(&mut frame, [1200, 2, 232, 44], [206, 170, 74]);
            text(
                &mut frame,
                font,
                if cp.controller.battle().outcome().is_some() {
                    "返回地圖"
                } else {
                    "戰鬥"
                },
                1210,
                4,
                38,
                210,
            )?;
            if cp.controller.battle().outcome() == Some(Outcome::Loss) {
                fill(&mut frame, [0, 1288, 1920, 32], [9, 36, 29]);
                text(
                    &mut frame,
                    font,
                    if choose {
                        "回到起點  [浪跡江湖]  方向鍵選擇 Enter確認"
                    } else {
                        "[回到起點]  浪跡江湖  方向鍵選擇 Enter確認"
                    },
                    18,
                    1288,
                    28,
                    1860,
                )?;
            } else if cp.controller.battle().outcome().is_some() {
                fill(&mut frame, [0, 1288, 1920, 32], [9, 36, 29]);
                text(&mut frame, font, "Enter 返回地圖", 18, 1288, 28, 1860)?;
            }
        } else if journey.cue.is_some() {
            fill(&mut frame, [96, 770, 1200, 264], [12, 49, 36]);
            border(&mut frame, [96, 770, 1200, 264], [206, 170, 74]);
            text(&mut frame, font, "遭遇敵軍", 144, 794, 48, 1056)?;
            text(
                &mut frame,
                font,
                if choose {
                    "迎戰   [避戰]"
                } else {
                    "[迎戰]   避戰"
                },
                144,
                870,
                48,
                1056,
            )?;
            text(
                &mut frame,
                font,
                "方向鍵選擇  Enter確認",
                144,
                950,
                36,
                1056,
            )?;
        }
        if !active && journey.cue.is_none() {
            fill(&mut frame, [0, 1250, 1920, 36], [9, 36, 29]);
            text(
                &mut frame,
                font,
                &format!(
                    "金錢 {}  戰績 {}  民兵 {}",
                    journey.resources[3], journey.resources[1], journey.army[0].count
                ),
                18,
                1250,
                32,
                1860,
            )?;
        }
        let back = sdl.draw(&frame, snap)?;
        let equal = back.as_ref().is_none_or(|p| *p == frame);
        let (actor, raw, targets, outcome, sequence) = if let Some(cp) = &journey.battle {
            let a = cp.controller.current();
            let targets = if a.is_some() && !cp.controller.is_enemy_caster() {
                cp.controller
                    .legal_targets()
                    .unwrap_or_default()
                    .iter()
                    .map(|n| n.to_string())
                    .collect::<Vec<_>>()
                    .join(",")
            } else {
                String::new()
            };
            (
                a.map(|a| {
                    if a.side == Side::Player {
                        "player"
                    } else {
                        "enemy"
                    }
                })
                .unwrap_or("wait"),
                a.map(|a| a.raw as i32).unwrap_or(-1),
                targets,
                format!("{:?}", cp.controller.battle().outcome()),
                cp.controller.battle().sequence(),
            )
        } else {
            ("wait", -1, String::new(), "None".into(), 0)
        };
        let status = format!(
            "phase\t{}\nactions\t{}\nx\t{}\ny\t{}\nsteps\t{}\ngold\t{}\nmerit\t{}\narmy\t{}\nenemy\t{}\nseed\t{}\nactor\t{actor}\nraw\t{raw}\ntargets\t{targets}\ncursor\t{cursor}\noutcome\t{outcome}\nsequence\t{sequence}\nbattles\t{}\nfont\t{}\nmusic\t{}\nstate_hash\t{:016x}\nsaves\t{saves}\nloaded\t{continuing}\ncaptures\t{}\nreadback_equal\t{equal}\nqueued_bytes\t{queued_bytes}\ndrains\t{drains}\npending\t{:?}\n",
            journey.phase(),
            journey.world.actions,
            journey.world.position.x,
            journey.world.position.y,
            journey.world.remaining,
            journey.resources[3],
            journey.resources[1],
            journey
                .army
                .iter()
                .map(|s| s.count.to_string())
                .collect::<Vec<_>>()
                .join(","),
            journey
                .enemy
                .iter()
                .map(|s| format!(
                    "{}={}",
                    s.unit.map(|u| u.to_string()).unwrap_or_default(),
                    s.count
                ))
                .collect::<Vec<_>>()
                .join(","),
            journey
                .battle
                .as_ref()
                .map(|c| c.rng.seed)
                .unwrap_or(journey.world.rng.seed),
            journey.battles,
            journey.world.font,
            journey.world.music,
            checksum(&journey.encode(&catalog, &data)?),
            captures + u32::from(snap),
            boundary
        );
        if let Some(d) = &capture {
            if snap {
                captures += 1;
                ppm(&d.join(format!("frame-{captures:03}.ppm")), &frame)?;
                ppm(
                    &d.join(format!("readback-{captures:03}.ppm")),
                    back.as_ref().ok_or("缺讀回")?,
                )?;
                std::fs::write(
                    d.join(format!("capture-{captures:03}.tsv")),
                    format!("{status}frame_hash\t{:016x}\n", checksum(&frame)),
                )
                .map_err(|e| e.to_string())?;
            }
            std::fs::write(d.join("status.tmp"), status)
                .and_then(|_| std::fs::rename(d.join("status.tmp"), d.join("status.tsv")))
                .map_err(|e| e.to_string())?;
        }
        std::thread::sleep(Duration::from_millis(30));
    }
    Ok(())
}
