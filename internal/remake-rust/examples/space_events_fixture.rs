//! Controlled original-site fixtures; subsequent UI input uses normal player commands.
use eightsword_remake::{
    catalog::Catalog,
    journey::Journey,
    world::{Position, WorldData},
};
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 5 {
        return Err("assets true-v17 output shop|camp|guard".into());
    }
    let d = WorldData::load(std::path::Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&a[2]).map_err(|e| e.to_string())?;
    if raw.get(..8) != Some(b"8SJRN017") {
        return Err("需要真正v17".into());
    }
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" || !j.magic.book {
        return Err("需要持竹簡世界檔".into());
    }
    let (area, position) = match a[4].as_str() {
        "shop" => {
            let s = eightsword_remake::world_magic::shops()[1];
            (s.area, Position { x: s.x, y: s.y })
        }
        "camp" => {
            let s = eightsword_remake::management::camps()
                .iter()
                .find(|s| s.kind == 1)
                .ok_or("無民兵營")?;
            (s.area, Position { x: s.x, y: s.y })
        }
        "guard" => {
            let s = eightsword_remake::guards::sites()[0];
            (s.area, s.position)
        }
        _ => return Err("模式錯誤".into()),
    };
    j.world.area = area;
    j.world.position = position;
    j.world.facing = 3;
    j.world.boat = 2;
    j.world.remaining = 1;
    j.world.rng.seed = 1;
    let out = std::path::Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"),format!("mode\t{}\narea\t{area}\nx\t{}\ny\t{}\nboat\t2\nsteps\t1\nseed\t1\nresources\t{:?}\narmy\t{:?}\n",a[4],position.x,position.y,j.resources,j.army)).map_err(|e|e.to_string())?;
    Ok(())
}
