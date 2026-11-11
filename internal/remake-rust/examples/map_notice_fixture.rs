//! Development fixture. Only original position and pre-action seed are changed.
use eightsword_remake::{
    catalog::Catalog,
    journey::Journey,
    map_notice,
    world::{Position, WorldData},
};
fn main() -> Result<(), String> {
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 4 {
        return Err("assets v12 output".into());
    }
    let root = std::path::Path::new(&args[1]);
    let c = Catalog::builtin()?;
    let d = WorldData::load(root)?;
    let raw = std::fs::read(&args[2]).map_err(|e| e.to_string())?;
    if &raw[..8] != b"8SJRN012" {
        return Err("需要真正v12".into());
    }
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" {
        return Err("需要世界階段".into());
    }
    let s = map_notice::sites()
        .iter()
        .find(|s| {
            s.area == 0
                && s.position.x > 0
                && d.tile(
                    0,
                    Position {
                        x: s.position.x - 1,
                        y: s.position.y,
                    },
                )
                .ok()
                    == Some(1)
        })
        .ok_or("找不到原提示鄰格")?;
    j.world.area = s.area;
    j.world.position = Position {
        x: s.position.x - 1,
        y: s.position.y,
    };
    j.world.rng.seed = 1;
    let out = std::path::Path::new(&args[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(
        out.join("fixture.tsv"),
        format!(
            "x\t{}\ny\t{}\narea\t{}\nsite\t{}\nsteps\t{}\ngold\t{}\nseed\t1\n",
            s.position.x, s.position.y, s.area, s.index, j.world.remaining, j.resources[3]
        ),
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}
