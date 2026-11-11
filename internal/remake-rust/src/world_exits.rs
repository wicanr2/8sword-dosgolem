//! Spec031: sub_12446 exits and shared sub_1151C encounter tail.
use crate::{
    catalog::Catalog,
    journey::Journey,
    world::{Boundary, Position, WalkResult, WorldData},
};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Exit {
    pub area: u8,
    pub position: Position,
    pub tile: u8,
}
impl Exit {
    pub fn destination(self) -> u8 {
        if self.tile == 49 {
            self.area - 1
        } else {
            self.area + 1
        }
    }
}
pub fn exits() -> &'static [Exit; 13] {
    static DATA: std::sync::OnceLock<[Exit; 13]> = std::sync::OnceLock::new();
    DATA.get_or_init(|| {
        include_str!("../world-exits.tsv")
            .lines()
            .filter(|s| !s.starts_with('#'))
            .map(|line| {
                let f: Vec<u8> = line
                    .split('\t')
                    .map(|s| s.parse().expect("fixed exit integer"))
                    .collect();
                assert_eq!(f.len(), 4);
                assert!(f[0] < 7 && f[1] < 70 && f[2] < 80 && matches!(f[3], 49 | 50));
                assert!(f[3] != 49 || f[0] > 0);
                Exit {
                    area: f[0],
                    position: Position { x: f[1], y: f[2] },
                    tile: f[3],
                }
            })
            .collect::<Vec<_>>()
            .try_into()
            .expect("fixed 13 exits")
    })
}
pub fn validate(d: &WorldData) -> Result<(), String> {
    for e in exits() {
        if d.tile(e.area, e.position)? != e.tile {
            return Err("原圖缺少預期出口".into());
        }
    }
    for area in 0..8 {
        if d.tile(area, d.starts[usize::from(area)])? != 1 {
            return Err("出口落點不屬已驗原圖".into());
        }
        for y in 0..80 {
            for x in 0..70 {
                let position = Position { x, y };
                let tile = d.tile(area, position)?;
                if matches!(tile, 49 | 50)
                    != exits().iter().any(|e| {
                        *e == Exit {
                            area,
                            position,
                            tile,
                        }
                    })
                {
                    return Err("原圖出口清單不符".into());
                }
            }
        }
    }
    Ok(())
}
impl<'a> Journey<'a> {
    pub(crate) fn run_encounter_tail(&mut self, d: &WorldData) -> Result<(), String> {
        match self.world.encounter_tail(d, false)? {
            WalkResult::Boundary(Boundary::Encounter(cue)) => {
                self.receive_encounter(cue)?;
            }
            _ => {}
        }
        Ok(())
    }
    pub(crate) fn cross_exit(
        &mut self,
        d: &WorldData,
        key: u16,
        tile: u8,
        c: &Catalog,
    ) -> Result<(), String> {
        if self.phase() != "world" {
            return Err("目前不能跨區".into());
        }
        let view = self.magic.view(d)?;
        let mut s = self.clone();
        s.world = s.world.event_step(&view, key, tile)?;
        let site = exits()
            .iter()
            .find(|e| e.area == s.world.area && e.position == s.world.position && e.tile == tile)
            .ok_or("出口不屬原圖清單")?;
        s.complete_exit(d, *site, key, false, c)?;
        *self = s;
        Ok(())
    }
    pub(crate) fn complete_exit(
        &mut self,
        d: &WorldData,
        site: Exit,
        key: u16,
        blocked: bool,
        c: &Catalog,
    ) -> Result<(), String> {
        let mut s = self.clone();
        if site.tile == 49 {
            s.world.reveal();
        }
        let old = s.world.area;
        s.world.area = site.destination();
        s.world.position = d.starts[usize::from(s.world.area)];
        s.magic.bridges.retain(|at| {
            let a = usize::from(*at) / 5600;
            a != usize::from(old) && a != usize::from(s.world.area)
        });
        let view = s.magic.view(d)?;
        s.world.reveal();
        if !blocked && key != 0x3920 && s.world.remaining == 1 {
            let tile = view.tile(s.world.area, s.world.position)?;
            s.begin_month(c, &view, tile)?;
        } else {
            if !blocked && key != 0x3920 {
                s.world.remaining -= 1;
            }
            s.run_encounter_tail(&view)?;
        }
        *self = s;
        Ok(())
    }
}
#[cfg(test)]
#[path = "world_exits_tests.rs"]
mod tests;
