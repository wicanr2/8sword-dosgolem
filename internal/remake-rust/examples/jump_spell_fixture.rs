//! Development evidence only: actual merchant position; no grants or RNG writes.
use eightsword_remake::{
    catalog::Catalog,
    journey::Journey,
    jump_spell::{Jump, landable},
    media_assets::checksum,
    world::{Position, WorldData, guard},
    world_magic::shops,
};
use std::path::Path;
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 4 {
        return Err("assets input output|inspect".into());
    }
    let d = WorldData::load(Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&a[2]).map_err(|e| e.to_string())?;
    let mut j = Journey::decode(&c, &d, &raw)?;
    if a[3] == "inspect" {
        println!(
            "phase\t{}\njump\t{:?}\nx\t{}\ny\t{}\nsteps\t{}\nseed\t{}\nactions\t{}\nstate_hash\t{:016x}",
            j.phase(),
            j.travel_spell.jump,
            j.world.position.x,
            j.world.position.y,
            j.world.remaining,
            j.world.rng.seed,
            j.world.actions,
            checksum(&j.encode(&c, &d)?)
        );
        return Ok(());
    }
    if j.phase() != "world" || !j.magic.book || j.travel_spell.jump != Jump::Idle {
        return Err("需要既有未跳躍的竹簡進度".into());
    }
    let site = shops()
        .into_iter()
        .find(|s| s.offer == 3)
        .ok_or("缺少跳躍原店")?;
    j.world.area = site.area;
    j.world.position = Position {
        x: site.x,
        y: site.y,
    };
    let view = j.magic.view(&d)?;
    let mut land = None;
    for n in 1..=70 {
        let p = Position {
            x: (i32::from(site.x) - n).rem_euclid(70) as u8,
            y: site.y,
        };
        if landable(view.tile(site.area, p)?) {
            land = Some((p, n));
            break;
        }
    }
    let (p, n) = land.ok_or("西向無落地點")?;
    if n != 3 {
        return Err("原商店西向三格契約改變".into());
    }
    let mut walk = None;
    for (dx, dy, key) in [
        (-1, 0, 0xff51),
        (0, -1, 0xff52),
        (0, 1, 0xff54),
        (1, 0, 0xff53),
    ] {
        let q = Position {
            x: (i32::from(p.x) + dx).rem_euclid(70) as u8,
            y: (i32::from(p.y) + dy).rem_euclid(80) as u8,
        };
        let tile = view.tile(site.area, q)?;
        if tile < 49 && !guard(tile, 0, false, false)?.0 {
            walk = Some(key);
            break;
        }
    }
    let out = Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"),format!("grade\tcontrolled actual merchant position only; source resources/army/RNG/clock retained\narea\t{}\nx\t{}\ny\t{}\nkey\t65361\nland_x\t{}\nland_y\t{}\nwalk\t{}\n",site.area,site.x,site.y,p.x,p.y,walk.ok_or("落地旁無普通地面")?)).map_err(|e|e.to_string())?;
    Ok(())
}
