//! Development initial position/seed only. Troops are dismissed through F3.
use eightsword_remake::{catalog::Catalog, journey::Journey, theft::loss, world::WorldData};
use std::path::Path;
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 4 {
        return Err("assets real-v11 new-store".into());
    }
    let d = WorldData::load(Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let mut j = Journey::decode(&c, &d, &std::fs::read(&a[2]).map_err(|e| e.to_string())?)?;
    if j.phase() != "world" || j.army[0].count != 30 || j.army[1..].iter().any(|s| s.count != 0) {
        return Err("需要既有30民兵進度".into());
    }
    j.world.area = 0;
    j.world.position = d.starts[0];
    j.world.rng.seed = 0x5578f641;
    let mut r = j.world.rng;
    let first = r.next15();
    let cue = r.next15() / 2341;
    let third = r.next15();
    let amount = loss(j.resources[3], third)?;
    let out = Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"),format!("grade\tactual v11 resources/army/magic retained; only original start position and fixed seed changed; empty army obtained by normal F3\nseed\t{}\nfirst_roll\t{}\ncue\t{}\nthird_roll\t{}\nexpected_loss\t{}\ngold_before\t{}\ngold_after\t{}\nseed_after\t{}\nsteps\t{}\n",j.world.rng.seed,first,cue,third,amount,j.resources[3],j.resources[3]-amount,r.seed,j.world.remaining)).map_err(|e|e.to_string())?;
    Ok(())
}
