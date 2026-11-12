//! Explicit original land-side coordinates and boat2; following GUI uses normal input.
use eightsword_remake::{
    catalog::Catalog,
    journey::Journey,
    world::{self, Position, WorldData},
};
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 5 {
        return Err("assets true-v17 output notice|shop|guard".into());
    }
    let d = WorldData::load(std::path::Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&a[2]).map_err(|e| e.to_string())?;
    if raw.get(..8) != Some(b"8SJRN017") {
        return Err("需要真正v17".into());
    }
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" || !j.magic.book {
        return Err("需要持竹簡的世界檔".into());
    }
    let (area, target) = match a[4].as_str() {
        "notice" => {
            let s = eightsword_remake::map_notice::sites()[0];
            (s.area, s.position)
        }
        "shop" => {
            let s = eightsword_remake::world_magic::shops()[1];
            (s.area, Position { x: s.x, y: s.y })
        }
        "guard" => {
            let s = eightsword_remake::guards::sites()[0];
            (s.area, s.position)
        }
        _ => return Err("模式錯誤".into()),
    };
    let mut entry = None;
    for (key, symbol) in [
        (0x4800, 0xff52),
        (0x5000, 0xff54),
        (0x4b00, 0xff51),
        (0x4d00, 0xff53),
    ] {
        let from = world::motion(target, key, 3, true)?.0;
        let tile = d.tile(area, from)?;
        if tile < 47 && !matches!(tile, 2 | 11..=30 | 46) {
            entry = Some((key, symbol, from, tile));
            break;
        }
    }
    let (key, symbol, from, tile) = entry.ok_or("沒有原圖可站立陸地")?;
    j.world.area = area;
    j.world.position = from;
    j.world.boat = 2;
    j.world.rng.seed = 1;
    j.world.remaining = if a[4] == "notice" { 1 } else { 2 };
    let out = std::path::Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"),format!("mode\t{}\nkey\t{symbol}\ndos_key\t{key}\narea\t{area}\nx\t{}\ny\t{}\norigin_tile\t{tile}\nboat\t2\nsteps\t{}\nseed\t1\nresources\t{:?}\narmy\t{:?}\n",a[4],from.x,from.y,j.world.remaining,j.resources,j.army)).map_err(|e|e.to_string())?;
    Ok(())
}
