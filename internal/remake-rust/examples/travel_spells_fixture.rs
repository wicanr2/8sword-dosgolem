//! Development evidence only. Does not add player shortcuts.
use eightsword_remake::{
    catalog::Catalog,
    journey::Journey,
    world::{Position, WorldData, guard},
    world_magic::shops,
};
use std::path::Path;
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() < 3 {
        return Err("assets oracle | assets input output teleport".into());
    }
    let d = WorldData::load(Path::new(&a[1]))?;
    if a[2] == "oracle" {
        for (i, p) in d.starts.iter().enumerate() {
            println!(
                "TELEPORT\t{i}\t{}\t{}\t{}",
                p.x,
                p.y,
                eightsword_remake::travel_spells::regions()[i]
            );
        }
        return Ok(());
    }
    if a.len() != 5 {
        return Err("fixture參數錯誤".into());
    }
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&a[2]).map_err(|e| e.to_string())?;
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" || !j.magic.book {
        return Err("fixture需要前批竹簡進度".into());
    }
    let offer = match a[4].as_str() {
        "teleport" => 7,
        _ => return Err("fixture種類錯誤".into()),
    };
    let site = *shops()
        .iter()
        .find(|s| s.offer == offer)
        .ok_or("商店缺失")?;
    let mut key = None;
    for (dx, dy, k) in [
        (-1, 0, 0xff53),
        (1, 0, 0xff51),
        (0, -1, 0xff54),
        (0, 1, 0xff52),
    ] {
        let p = Position {
            x: (i32::from(site.x) + dx).rem_euclid(70) as u8,
            y: (i32::from(site.y) + dy).rem_euclid(80) as u8,
        };
        let tile = d.tile(site.area, p)?;
        if tile < 49 && !guard(tile, 0, false, false)?.0 {
            j.world.area = site.area;
            j.world.position = p;
            key = Some(k);
            break;
        }
    }
    // The sole original teleport shop is enclosed by mountain tiles. The
    // mountain item is outside this slice. Relocate onto the actual shop and
    // use its ordinary Space interaction; retain every non-position field.
    let key = key.unwrap_or_else(|| {
        j.world.area = site.area;
        j.world.position = Position {
            x: site.x,
            y: site.y,
        };
        0x20
    });
    let out = Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"),format!("grade\tcontrolled relocation only; source RNG/resources/army retained; no natural cross-area claim\narea\t{}\nx\t{}\ny\t{}\nshop_x\t{}\nshop_y\t{}\nkey\t{key}\n",site.area,j.world.position.x,j.world.position.y,site.x,site.y)).map_err(|e|e.to_string())?;
    Ok(())
}
