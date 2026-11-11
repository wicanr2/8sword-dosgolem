//! Explicit month-end starting state; subsequent travel/report/guard input is normal UI.
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
        return Err("assets true-v15 output".into());
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
    let site = guards::sites()[0];
    j.world.area = site.area;
    j.world.position = Position {
        x: site.position.x,
        y: site.position.y + 1,
    };
    if d.tile(site.area, j.world.position)? != 1 {
        return Err("原草地鄰格不符".into());
    }
    j.world.remaining = 1;
    j.world.rng.seed = 1;
    j.army = [Stack::default(); 6];
    j.army[0] = Stack {
        unit: Some(UnitId::parse("native:01")?),
        count: 30,
    };
    j.guards.rows[0] = [Stack::default(); 6];
    for (slot, (kind, count)) in [(11, 20), (16, 5), (21, 1)].into_iter().enumerate() {
        j.guards.rows[0][slot] = Stack {
            unit: Some(UnitId::parse(&format!("native:{kind:02}"))?),
            count,
        };
    }
    if j.guards.rows[1].iter().any(|r| r.count > 0) || !j.guards.swords[0] {
        return Err("來源須保有已擊敗首頭目".into());
    }
    let out = std::path::Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(
        out.join("fixture.tsv"),
        format!(
            "x\t{}\ny\t{}\nresources\t{:?}\nsteps\t1\nseed\t1\nguard0\t20,5,1,0,0,0\n",
            j.world.position.x, j.world.position.y, j.resources
        ),
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}
