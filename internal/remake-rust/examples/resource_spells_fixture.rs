//! Development evidence only. Never linked into the player entrypoint.
use eightsword_remake::{
    catalog::Catalog,
    journey::Journey,
    world::{Position, WorldData, guard},
    world_magic::shops,
};
use std::path::Path;
fn main() -> Result<(), String> {
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 5 {
        return Err("assets input output alchemy|summon".into());
    }
    let d = WorldData::load(Path::new(&args[1]))?;
    let c = Catalog::builtin()?;
    let bytes = std::fs::read(&args[2]).map_err(|e| e.to_string())?;
    let mut j = Journey::decode(&c, &d, &bytes)?;
    if j.phase() != "world" || !j.magic.book {
        return Err("fixture需要前批真正竹簡進度".into());
    }
    let offer = match args[4].as_str() {
        "alchemy" => 1,
        "summon" => 2,
        _ => return Err("fixture種類錯誤".into()),
    };
    let site = *shops()
        .iter()
        .find(|s| s.offer == offer)
        .ok_or("固定商店缺失")?;
    let mut motion = None;
    for (dx, dy, key) in [
        (-1, 0, 0xff53),
        (1, 0, 0xff51),
        (0, -1, 0xff54),
        (0, 1, 0xff52),
    ] {
        let p = Position {
            x: (i32::from(site.x) + dx).rem_euclid(70) as u8,
            y: (i32::from(site.y) + dy).rem_euclid(80) as u8,
        };
        let tile = d.tile(site.area, p)?;
        if tile < 49 && !guard(tile, 0, false, false)?.0 {
            j.world.area = site.area;
            j.world.position = p;
            motion = Some(key);
            break;
        }
    }
    let key = motion.ok_or("商店旁無已接可走地形")?;
    j.resources[4] = 1000;
    let out = Path::new(&args[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"),format!("grade\tcontrolled relocation; original v5 descendant, leadership1000; no natural cross-area claim\narea\t{}\nx\t{}\ny\t{}\nshop_x\t{}\nshop_y\t{}\nkey\t{key}\n",site.area,j.world.position.x,j.world.position.y,site.x,site.y)).map_err(|e|e.to_string())?;
    Ok(())
}
