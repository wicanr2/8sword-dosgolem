//! Spec031: sub_12446 shore result plus actual post-rollback consumer lookup.
use crate::{
    catalog::Catalog,
    journey::Journey,
    management::camps,
    world::{Boundary, WalkResult, WorldData, motion},
    world_exits::exits,
    world_magic::{PendingShop, shops, supported},
};
#[cfg(test)]
fn water(t: u8) -> bool {
    matches!(t, 2 | 11..=14)
}
impl<'a> Journey<'a> {
    pub(crate) fn supported_shore(&self, d: &WorldData, key: u16) -> Result<bool, String> {
        if self.world.plain_shore(d, key)? {
            return Ok(true);
        }
        let mut probe = self.world.clone();
        if probe.walk_encounter(d, key)? != WalkResult::Boundary(Boundary::BoatExit)
            || !(crate::jump_spell::DIRECTIONS.contains(&key)
                || key == 0x3920 && self.wait_event.is_some())
        {
            return Ok(false);
        }
        let p = motion(self.world.position, key, self.world.facing, false)?.0;
        Ok(match d.tile(self.world.area, p)? {
            49 | 50 => exits()
                .iter()
                .any(|e| e.area == self.world.area && e.position == p),
            65 => crate::guards::sites()
                .iter()
                .any(|s| s.area == self.world.area && s.position == p),
            51 => crate::map_notice::sites()
                .iter()
                .any(|s| s.area == self.world.area && s.position == p),
            53 => shops().iter().any(|s| {
                s.area == self.world.area && s.x == p.x && s.y == p.y && supported(s.offer)
            }),
            t @ 54..=58 => camps().iter().enumerate().any(|(i, s)| {
                i / 24 == usize::from(t - 54)
                    && s.kind > 0
                    && s.area == self.world.area
                    && s.x == p.x
                    && s.y == p.y
            }),
            59 => crate::treasure::sites()
                .iter()
                .any(|s| s.area == self.world.area && s.x == p.x && s.y == p.y),
            _ => false,
        })
    }
    pub(crate) fn validate_refused_shop(&self, d: &WorldData) -> Result<(), String> {
        let key = self.travel_spell.refused_shop.ok_or("缺少拒絕方向")?;
        let p = self.magic.shop.ok_or("缺少拒絕商店")?;
        let site = shops()
            .get(usize::from(p.index))
            .ok_or("拒絕商店索引錯誤")?;
        let (at, face) = motion(self.world.position, key, self.world.facing, false)?;
        if !crate::jump_spell::DIRECTIONS.contains(&key)
            || p.moved
            || self.world.boat != 2
            || face != self.world.facing
            || (self.world.area, at.x, at.y) != (site.area, site.x, site.y)
            || d.tile(site.area, at)? != 53
            || !supported(site.offer)
        {
            return Err("拒絕商店與水岸不符".into());
        }
        Ok(())
    }
    pub(crate) fn refuse_special_shore(
        &mut self,
        d: &WorldData,
        key: u16,
        c: &Catalog,
    ) -> Result<bool, String> {
        let view = self.magic.view(d)?;
        let (target, face) = motion(self.world.position, key, self.world.facing, false)?;
        let tile = view.tile(self.world.area, target)?;
        if !matches!(tile, 49..=51 | 53..=59 | 65) {
            return Ok(false);
        }
        if !self.supported_shore(&view, key)? {
            return Err("未接特殊上岸拒絕".into());
        }
        let mut s = self.clone();
        s.world.facing = face;
        if key == 0x3920 {
            s.wait_event.as_mut().ok_or("缺少Space事務")?.blocked = true;
            match tile {
                49 | 50 => {
                    let e = *exits()
                        .iter()
                        .find(|e| e.area == s.world.area && e.position == target && e.tile == tile)
                        .ok_or("缺少Space出口")?;
                    s.complete_exit(d, e, key, true, c)?;
                }
                53 => {
                    let index = shops()
                        .iter()
                        .position(|p| p.area == s.world.area && p.x == target.x && p.y == target.y)
                        .ok_or("缺少Space商店")?;
                    s.world.rng.next15();
                    s.magic.shop = Some(PendingShop {
                        index: index as u8,
                        moved: false,
                    });
                }
                54..=58 => {
                    let index = camps()
                        .iter()
                        .enumerate()
                        .position(|(i, p)| {
                            i / 24 == usize::from(tile - 54)
                                && p.kind > 0
                                && p.area == s.world.area
                                && p.x == target.x
                                && p.y == target.y
                        })
                        .ok_or("缺少Space營地")?;
                    s.queue_camp(index)?;
                }
                59 => s.queue_treasure(c, &view, false)?,
                65 => s.queue_guard(&view, key, c)?,
                _ => s.run_encounter_tail(&view)?,
            }
            *self = s;
            return Ok(true);
        }
        if tile == 65 {
            if matches!(face, 1 | 3) {
                let index = crate::guards::sites()
                    .iter()
                    .position(|p| p.area == s.world.area && p.position == target)
                    .ok_or("缺少拒絕上岸守軍")?;
                s.guards.pending = Some(crate::guards::Pending {
                    site: index as u8,
                    key,
                    stage: crate::guards::Stage::Refused,
                    yes: false,
                    before: s.resources,
                    reward_seed: s.world.rng.seed,
                });
                s.guards.validate(&s, d)?;
            } else {
                s.finish_guard_tail(d, key, c, true)?;
            }
        } else if matches!(tile, 49 | 50) {
            let e = *exits()
                .iter()
                .find(|e| e.area == s.world.area && e.position == target && e.tile == tile)
                .ok_or("缺少跨區出口")?;
            s.complete_exit(d, e, key, true, c)?;
        } else if tile == 53 {
            let index = shops()
                .iter()
                .position(|e| e.area == s.world.area && e.x == target.x && e.y == target.y)
                .ok_or("缺少法術店")?;
            s.world.rng.next15();
            s.magic.shop = Some(PendingShop {
                index: index as u8,
                moved: false,
            });
            s.travel_spell.refused_shop = Some(key);
            s.validate_refused_shop(d)?;
        } else {
            if (54..=58).contains(&tile) {
                s.world.rng.next15();
            }
            match s.world.reject_shore(&view, key)? {
                WalkResult::Boundary(Boundary::Encounter(cue)) => {
                    s.receive_encounter(cue)?;
                }
                WalkResult::Committed { .. } => {}
                _ => return Err("拒絕上岸尾段錯誤".into()),
            }
        }
        *self = s;
        Ok(true)
    }
}
#[cfg(test)]
#[path = "special_shore_tests.rs"]
mod tests;
