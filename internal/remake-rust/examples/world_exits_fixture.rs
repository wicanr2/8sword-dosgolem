//! Development initial-state fixtures only. Never linked into the player.
use eightsword_remake::{
    catalog::Catalog,
    journey::Journey,
    jump_spell::Jump,
    media_assets::checksum,
    world::{Position, WorldData, guard, motion},
    world_exits::exits,
};
use std::path::Path;
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 5 {
        return Err("assets input output inspect|forward|back|month|jump".into());
    }
    let d = WorldData::load(Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let mut j = Journey::decode(&c, &d, &std::fs::read(&a[2]).map_err(|e| e.to_string())?)?;
    if a[4] == "inspect" {
        println!(
            "phase\t{}\narea\t{}\nx\t{}\ny\t{}\nsteps\t{}\nseed\t{}\nactions\t{}\nstate_hash\t{:016x}",
            j.phase(),
            j.world.area,
            j.world.position.x,
            j.world.position.y,
            j.world.remaining,
            j.world.rng.seed,
            j.world.actions,
            checksum(&j.encode(&c, &d)?)
        );
        return Ok(());
    }
    if j.phase() != "world" || j.travel_spell.jump != Jump::Idle {
        return Err("需要已完成事件的既有進度".into());
    }
    let key;
    if a[4] == "jump" {
        j.world.area = 3;
        j.world.position = Position { x: 67, y: 70 };
        j.travel_spell.jump = Jump::Ready;
        j.world.rng.seed = 0x5578f641;
        key = 0xff51;
    } else {
        let e = exits()
            .iter()
            .find(|e| {
                e.area == if a[4] == "back" { 1 } else { 0 }
                    && e.tile == if a[4] == "back" { 49 } else { 50 }
            })
            .ok_or("找不到出口")?;
        j.world.area = e.area;
        let (p, k) = [
            (0x5000, 0xff54),
            (0x4d00, 0xff53),
            (0x4b00, 0xff51),
            (0x4800, 0xff52),
        ]
        .into_iter()
        .filter_map(|(k, s)| {
            let p = motion(e.position, k, 3, true).ok()?.0;
            let t = d.tile(e.area, p).ok()?;
            (!guard(t, 0, false, false).ok()?.0 && t < 49).then_some((p, s))
        })
        .next()
        .ok_or("出口沒有普通鄰格")?;
        j.world.position = p;
        key = k;
        if a[4] == "month" {
            j.world.remaining = 1;
        }
    }
    let out = Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"),format!("mode\t{}\nkey\t{}\narea\t{}\nx\t{}\ny\t{}\nseed\t{}\nsteps\t{}\ngrade\tcontrolled initial position; month additionally remaining1; jump additionally Ready and inverse-LCG seed for firstroll1000; source army/resources unchanged\n",a[4],key,j.world.area,j.world.position.x,j.world.position.y,j.world.rng.seed,j.world.remaining)).map_err(|e|e.to_string())?;
    Ok(())
}
