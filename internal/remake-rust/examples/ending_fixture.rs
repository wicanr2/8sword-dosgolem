//! Explicit late-game starting state; all following input uses the player UI.
use eightsword_remake::{
    battle::Stack,
    catalog::{Catalog, UnitId},
    guards,
    journey::Journey,
    world::{Position, WorldData},
};
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 4 {
        return Err("assets real-v14 output".into());
    }
    let d = WorldData::load(std::path::Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&a[2]).map_err(|e| e.to_string())?;
    if raw.get(..8) != Some(b"8SJRN014") {
        return Err("需要真正v14".into());
    }
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" {
        return Err("需要世界進度".into());
    }
    let s = guards::sites().iter().find(|s| s.final_guard).unwrap();
    let options = [
        (
            Position {
                x: s.position.x,
                y: s.position.y + 1,
            },
            0xff52u32,
        ),
        (
            Position {
                x: s.position.x + 1,
                y: s.position.y,
            },
            0xff51,
        ),
        (
            Position {
                x: s.position.x + 1,
                y: s.position.y + 1,
            },
            0xff50,
        ),
    ];
    // The final palace is surrounded by blocked decorative terrain. Match the
    // existing controlled original test's east neighbor, without changing map
    // bytes or claiming a naturally reached starting position.
    let (p, key) = options[1];
    if d.tile(s.area, p)? != 27 {
        return Err("原最終守軍東鄰格不符".into());
    }
    j.world.area = s.area;
    j.world.position = p;
    j.world.rng.seed = 1;
    j.guards.swords = [true; 8];
    j.army = std::array::from_fn(|i| Stack {
        unit: Some(UnitId::parse(&format!("native:{:02}", [19, 20, 25, 3, 24, 18][i])).unwrap()),
        count: [1000, 600, 500, 1000, 600, 20][i],
    });
    let out = std::path::Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(
        out.join("fixture.tsv"),
        format!(
            "key\t{key}\nx\t{}\ny\t{}\nresources\t{:?}\nsteps\t{}\n",
            p.x, p.y, j.resources, j.world.remaining
        ),
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}
