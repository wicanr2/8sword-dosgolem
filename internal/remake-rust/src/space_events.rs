//! Spec031: original10C0C credits Space;126DF debits only an unblocked return.
use crate::{
    catalog::Catalog,
    journey::Journey,
    world::{self, Boundary, WorldData},
};
pub const SUFFIX: usize = 1;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Wait {
    pub blocked: bool,
}
impl<'a> Journey<'a> {
    fn wait_modal(&self) -> bool {
        self.map_notice.is_some()
            || self.travel_spell.shore.is_some()
            || self.magic.shop.is_some()
            || self.camps.pending.is_some()
            || self.treasure.pending.is_some()
            || self.guards.pending.is_some()
    }
    pub(crate) fn validate_wait(&self) -> Result<(), String> {
        let Some(wait) = self.wait_event else {
            return Ok(());
        };
        if self.world.remaining < 2
            || !self.wait_modal()
            || self.month.pending.is_some()
            || self.guards.ending.is_some()
            || self.cue.is_some()
            || self.theft.is_some()
            || self.guards.pending.is_some_and(|p| p.key != 0x3920)
            || self.map_notice.is_some_and(|p| p.key != 0x3920)
            || self.travel_spell.shore.is_some_and(|p| p.key != 0x3920)
            || self.magic.shop.is_some_and(|p| p.moved)
            || self.treasure.pending.is_some_and(|p| p.moved)
            || wait.blocked && (self.travel_spell.shore.is_some() || self.map_notice.is_some())
        {
            return Err("Space事務與階段不符".into());
        }
        Ok(())
    }
    pub(crate) fn finish_wait_clock(&mut self) -> Result<(), String> {
        if let Some(wait) = self.wait_event.take() {
            if !wait.blocked {
                self.world.remaining = self
                    .world
                    .remaining
                    .checked_sub(1)
                    .filter(|v| *v > 0)
                    .ok_or("Space步數錯誤")?;
            }
        }
        Ok(())
    }
    pub fn travel(
        &mut self,
        d: &WorldData,
        key: u16,
        c: &Catalog,
    ) -> Result<Option<Boundary>, String> {
        if key != 0x3920
            || self.phase() != "world"
            || self.travel_spell.jump != crate::jump_spell::Jump::Idle
        {
            return self.travel_inner(d, key, c);
        }
        let mut s = self.clone();
        let view = s.magic.view(d)?;
        if s.wait_event.is_none() {
            let (blocked, _) = world::guard(
                view.tile(s.world.area, s.world.position)?,
                s.world.boat,
                s.world.mountain,
                s.world.bamboo,
            )?;
            s.world.remaining = s
                .world
                .remaining
                .checked_add(1)
                .ok_or("Space步數超出原word範圍")?;
            s.wait_event = Some(Wait { blocked });
        }
        let out = s.travel_inner(d, key, c)?;
        if s.wait_event.is_some() && !s.wait_modal() {
            s.finish_wait_clock()?;
        }
        *self = s;
        Ok(out)
    }
}

#[cfg(test)]
#[path = "space_events_tests.rs"]
mod tests;
