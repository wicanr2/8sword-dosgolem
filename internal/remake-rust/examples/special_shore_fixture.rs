//! Development evidence: actual water/special tile adjacency, no runtime hook.
use eightsword_remake::{
    catalog::Catalog,
    journey::Journey,
    jump_spell::Jump,
    world::{Position, WorldData},
};
use std::path::Path;
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 5 {
        return Err("assets real-v10 output treasure|shop|exit|camp".into());
    }
    let d = WorldData::load(Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let mut j = Journey::decode(&c, &d, &std::fs::read(&a[2]).map_err(|e| e.to_string())?)?;
    if j.phase() != "world" || !j.magic.book || j.travel_spell.jump != Jump::Idle {
        return Err("需要既有竹簡世界進度".into());
    }
    let (area, x, y, tx, ty, key, tile) = match a[4].as_str() {
        "treasure" => (0, 63, 24, 62, 24, 0xff51, 59),
        "shop" => (5, 7, 3, 8, 4, 0xff56, 53),
        "exit" => (1, 9, 31, 10, 31, 0xff53, 50),
        "camp" => (1, 51, 10, 51, 11, 0xff54, 54),
        _ => return Err("未知樣本".into()),
    };
    let p = Position { x, y };
    let t = Position { x: tx, y: ty };
    if !matches!(d.tile(area, p)?, 2 | 11..=14) || d.tile(area, t)? != tile {
        return Err("原水岸錨點不符".into());
    }
    j.world.area = area;
    j.world.position = p;
    j.world.boat = 2;
    j.world.rng.seed = 1;
    let amount = if tile == 59 {
        eightsword_remake::treasure::sites()
            .iter()
            .find(|s| s.area == area && s.x == tx && s.y == ty)
            .ok_or("缺少寶箱")?
            .amount
    } else {
        0
    };
    let out = Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"),format!("mode\t{}\nkey\t{}\narea\t{}\nx\t{}\ny\t{}\ntarget_x\t{}\ntarget_y\t{}\namount\t{}\ngrade\tcontrolled actual water position,boat2,seed1; real v10 resources/army/magic retained\n",a[4],key,area,x,y,tx,ty,amount)).map_err(|e|e.to_string())?;
    Ok(())
}
