//! Explicit late-game item/guard coordinates; normal UI follows each fixture.
use eightsword_remake::{
    battle::Stack,
    catalog::{Catalog, UnitId},
    guards,
    journey::Journey,
    world::{Position, WorldData},
};
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 5 {
        return Err("assets true-v15 output gold|battle".into());
    }
    let d = WorldData::load(std::path::Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&a[2]).map_err(|e| e.to_string())?;
    if raw.get(..8) != Some(b"8SJRN015") {
        return Err("需要真正v15".into());
    }
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" {
        return Err("需要世界進度".into());
    }
    // Six earlier items explicitly granted, book remains the real source book.
    j.artifacts = 0x1e;
    j.world.bamboo = true;
    j.world.mountain = true;
    j.world.rng.seed = 1;
    if !j.magic.book {
        return Err("來源須有竹簡".into());
    }
    match a[4].as_str() {
        "gold" => {
            j.world.area = 4;
            j.world.position = Position { x: 23, y: 37 };
            if d.tile(4, j.world.position)? != 16 {
                return Err("原令牌位置地形不符".into());
            }
        }
        "battle" => {
            j.artifacts |= 0x80;
            let s = guards::sites()[0];
            j.world.area = s.area;
            j.world.position = Position {
                x: s.position.x,
                y: s.position.y + 1,
            };
            j.army = [Stack::default(); 6];
            j.army[0] = Stack {
                unit: Some(UnitId::parse("native:01")?),
                count: 1000,
            };
        }
        _ => return Err("模式錯誤".into()),
    }
    let out = std::path::Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(
        out.join("fixture.tsv"),
        format!(
            "mode\t{}\nresources\t{:?}\nsteps\t{}\nitems\t{:?}\n",
            a[4],
            j.resources,
            j.world.remaining,
            j.item_flags()
        ),
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}
