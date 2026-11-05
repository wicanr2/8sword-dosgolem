//! Spec031: sub_16EF6 teleport and its map reload boundary.
use crate::{journey::Journey, world::WorldData};
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Travel {
    /// Native modal transaction: its single charge is already committed.
    pub teleport: Option<u8>,
}
pub fn regions() -> [&'static str; 8] {
    let mut out = [""; 8];
    for line in include_str!("../teleport-regions.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let (i, name) = line.split_once('\t').expect("compiled region table");
        out[i.parse::<usize>().expect("compiled region index")] = name;
    }
    out
}
impl Travel {
    pub(crate) fn validate(&self, j: &Journey<'_>) -> Result<(), String> {
        if let Some(area) = self.teleport {
            if area >= 8
                || !j.magic.book
                || j.magic.selected != 7
                || j.magic.direction
                || j.magic.shop.is_some()
                || j.survey.bird
                || j.resource_notice.is_some()
                || j.battle.is_some()
                || j.cue.is_some()
                || j.camps.pending.is_some()
                || j.month.pending.is_some()
                || j.treasure.pending.is_some()
            {
                return Err("傳送待選資料或階段衝突".into());
            }
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    pub fn begin_teleport(&mut self) -> Result<(), String> {
        if self.phase() != "world" || !self.magic.book || self.magic.charges[7] == 0 {
            return Err("目前不能施展傳送術".into());
        }
        let mut s = self.clone();
        s.magic.charges[7] -= 1;
        s.magic.selected = 7;
        s.travel_spell.teleport = Some(s.world.area);
        s.travel_spell.validate(&s)?;
        *self = s;
        Ok(())
    }
    pub fn select_teleport(&mut self, area: u8) -> Result<(), String> {
        self.travel_spell.validate(self)?;
        if self.travel_spell.teleport.is_none() || area >= 8 {
            return Err("沒有此傳送目的地".into());
        }
        self.travel_spell.teleport = Some(area);
        Ok(())
    }
    pub fn finish_teleport(&mut self, d: &WorldData, confirm: bool) -> Result<(), String> {
        self.travel_spell.validate(self)?;
        let area = self.travel_spell.teleport.ok_or("沒有待確認傳送")?;
        let mut s = self.clone();
        if confirm {
            let old = s.world.area;
            s.world.area = area;
            s.world.position = d.starts[usize::from(area)];
            s.world.boat = 0;
            // Original full-map reload discards constructed bridges. The old
            // exploration file is saved with bridge characters normalised.
            s.magic.bridges.retain(|at| {
                let a = usize::from(*at) / 5600;
                a != usize::from(old) && a != usize::from(area)
            });
            // Loading/redrawing a map is not a movement or reveal operation.
        }
        s.travel_spell.teleport = None;
        *self = s;
        Ok(())
    }
}
#[cfg(test)]
#[path = "travel_spells_tests.rs"]
mod tests;
