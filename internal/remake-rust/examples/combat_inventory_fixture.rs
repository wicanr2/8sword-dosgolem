//! Controlled shop position and caster, from a true v16 progress file. No production shortcut.
use eightsword_remake::{
    battle::Stack,
    catalog::{Catalog, UnitId},
    journey::Journey,
    world::{Position, WorldData},
    world_magic,
};
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 5 {
        return Err("assets true-v16 output shop|guard".into());
    }
    let d = WorldData::load(std::path::Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&a[2]).map_err(|e| e.to_string())?;
    if raw.get(..8) != Some(b"8SJRN016") {
        return Err("需要真正v16".into());
    }
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" {
        return Err("需要世界進度".into());
    }
    let before = format!(
        "resources\t{:?}\narmy\t{:?}\nseed\t{}\n",
        j.resources, j.army, j.world.rng.seed
    );
    if !j.magic.book {
        let item = world_magic::items()[0];
        j.world.area = item[1];
        j.world.position = Position {
            x: item[2],
            y: item[3],
        };
        if j.search_item()? != Some(0) {
            return Err("原竹簡取得失敗".into());
        }
    }
    j.world.rng.seed = 1;
    j.army = [Stack::default(); 6];
    j.army[0] = Stack {
        unit: Some(UnitId::parse("native:01")?),
        count: 30,
    };
    j.army[1] = Stack {
        unit: Some(UnitId::parse("native:10")?),
        count: 2,
    };
    j.world.area = 0;
    match a[4].as_str() {
        "shop" => {
            let s = world_magic::shops()
                .iter()
                .find(|s| s.area == 0 && s.offer == 8)
                .ok_or("缺火球店")?;
            j.world.position = Position { x: s.x, y: s.y - 1 };
            j.world.facing = 2;
        }
        "guard" => {
            let s = eightsword_remake::guards::sites()[0];
            j.world.position = Position {
                x: s.position.x,
                y: s.position.y + 1,
            };
            j.world.facing = 1;
            j.magic.battle_charges = [1, 0, 0, 0, 0, 0, 1, 0];
        }
        _ => return Err("模式錯誤".into()),
    }
    let out = std::path::Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"),format!("mode\t{}\nsource\n{before}controlled\nposition\t{:?}\narmy\t{:?}\nseed\t{}\nbattle_charges\t{:?}\nresources\t{:?}\n",a[4],j.world.position,j.army,j.world.rng.seed,j.magic.battle_charges,j.resources)).map_err(|e|e.to_string())?;
    Ok(())
}
