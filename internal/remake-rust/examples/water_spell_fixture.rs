//! Development evidence only: two explicit positions, never grants a spell.
use eightsword_remake::{
    catalog::Catalog,
    journey::Journey,
    world::{Position, WorldData, guard},
    world_magic::shops,
};
use std::path::Path;
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 5 {
        return Err("assets input output shop|bank".into());
    }
    let d = WorldData::load(Path::new(&a[1]))?;
    let c = Catalog::builtin()?;
    let raw = std::fs::read(&a[2]).map_err(|e| e.to_string())?;
    let mut j = Journey::decode(&c, &d, &raw)?;
    if j.phase() != "world" || !j.magic.book {
        return Err("需要既有竹簡進度".into());
    }
    let mut metadata =
        String::from("grade\tcontrolled position only; source resources/army/RNG/clock retained\n");
    if a[4] == "shop" {
        if j.world.boat != 0 {
            return Err("商店樣本須在施法前".into());
        }
        let shop = shops()
            .into_iter()
            .find(|s| s.offer == 6)
            .ok_or("缺少涉水原店")?;
        j.world.area = shop.area;
        j.world.position = Position {
            x: shop.x,
            y: shop.y,
        };
    } else if a[4] == "bank" {
        if j.world.boat != 1 || j.magic.charges[6] != 0 {
            return Err("水岸樣本須沿實購後已施法進度".into());
        }
        let view = j.magic.view(&d)?;
        let old = j.world.position;
        let mut candidates = Vec::new();
        for y in 0..80u8 {
            for x in 0..70u8 {
                let p = Position { x, y };
                let tile = view.tile(j.world.area, p)?;
                if guard(tile, 0, false, false)?.0 || matches!(tile,49..=51|53..=59|65) {
                    continue;
                }
                for (dx, dy, key, back) in [
                    (-1, 0, 0xff51, 0xff53),
                    (1, 0, 0xff53, 0xff51),
                    (0, -1, 0xff52, 0xff54),
                    (0, 1, 0xff54, 0xff52),
                ] {
                    let n = Position {
                        x: (i32::from(x) + dx).rem_euclid(70) as u8,
                        y: (i32::from(y) + dy).rem_euclid(80) as u8,
                    };
                    if matches!(view.tile(j.world.area, n)?, 2 | 11..=14) {
                        let distance = x.abs_diff(old.x) as u16 + y.abs_diff(old.y) as u16;
                        candidates.push((distance, y, x, n.x, n.y, key, back));
                    }
                }
            }
        }
        candidates.sort_unstable();
        let (_, y, x, wx, wy, key, back) = candidates.first().copied().ok_or("沒有普通原圖水岸")?;
        j.world.position = Position { x, y };
        metadata += &format!("route\t{key}\nwater_x\t{wx}\nwater_y\t{wy}\nback\t{back}\n");
    } else {
        return Err("fixture模式錯誤".into());
    }
    metadata += &format!(
        "area\t{}\nx\t{}\ny\t{}\n",
        j.world.area, j.world.position.x, j.world.position.y
    );
    let out = Path::new(&a[3]);
    std::fs::create_dir(out).map_err(|e| e.to_string())?;
    j.save(out, &c, &d)?;
    std::fs::write(out.join("fixture.tsv"), metadata).map_err(|e| e.to_string())?;
    Ok(())
}
