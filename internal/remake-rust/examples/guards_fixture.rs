//! Development-only starting coordinates,seed and explicit combat army.
use eightsword_remake::{
    battle::Stack,
    catalog::{Catalog, UnitId},
    guards,
    journey::Journey,
    world::{Position, WorldData},
};
fn main() -> Result<(), String> {
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 5 {
        return Err("assets real-v13 output empty|army|boss".into());
    }
    let root = std::path::Path::new(&args[1]);
    let d = WorldData::load(root)?;
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&args[2]).map_err(|e| e.to_string())?;
    if raw.len() < 8 || &raw[..8] != b"8SJRN013" {
        return Err("需要真正v13".into());
    }
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" {
        return Err("需要原世界進度".into());
    }
    let i = match args[4].as_str() {
        "empty" | "army" => 0,
        "boss" => 1,
        _ => return Err("fixture模式錯誤".into()),
    };
    let s = guards::sites()[i];
    j.world.area = s.area;
    j.world.position = Position {
        x: s.position.x,
        y: s.position.y + 1,
    };
    if d.tile(s.area, j.world.position)? != 1 {
        return Err("需要原圖草地鄰格".into());
    }
    j.world.rng.seed = 1;
    if args[4] != "empty" {
        j.army = [Stack::default(); 6];
        j.army[0] = Stack {
            unit: Some(UnitId::parse("native:01")?),
            count: 1000,
        };
        j.army[1] = Stack {
            unit: Some(UnitId::parse("native:02")?),
            count: 200,
        };
    }
    let out = std::path::Path::new(&args[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(
        out.join("fixture.tsv"),
        format!(
            "x\t{}\ny\t{}\nsite\t{}\nsteps\t{}\ngold\t{}\ncapacity\t{}\nincome\t{}\n",
            s.position.x,
            s.position.y,
            i,
            j.world.remaining,
            j.resources[3],
            j.resources[5],
            j.resources[2]
        ),
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}
