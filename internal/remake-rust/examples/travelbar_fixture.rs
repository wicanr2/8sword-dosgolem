//! Explicit near-month-end setup; subsequent stop spell,walk,report and save use normal UI.
use eightsword_remake::{catalog::Catalog, journey::Journey, world::WorldData};
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 4 {
        return Err("assets true-v16 output".into());
    }
    let d = WorldData::load(std::path::Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&a[2]).map_err(|e| e.to_string())?;
    if raw.get(..8) != Some(b"8SJRN016") {
        return Err("需要真正v16".into());
    }
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" || j.survey.stopped {
        return Err("需要未停時世界".into());
    }
    j.world.remaining = 1;
    j.world.rng.seed = 1;
    j.magic.book = true;
    j.magic.charges[4] = 1;
    j.resources[5] = 3;
    let out = std::path::Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)
}
