//! Spec031: sub_16EF6 teleport and its map reload boundary.
use crate::{journey::Journey, world::WorldData};
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Travel {
    /// Native modal transaction: its single charge is already committed.
    pub teleport: Option<u8>,
    pub shore: Option<Shore>,
    pub jump: crate::jump_spell::Jump,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Shore {
    pub key: u16,
    pub yes: bool,
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
        if let Some(p) = self.shore {
            if j.world.boat != 2
                || self.teleport.is_some()
                || ![
                    0x4700, 0x4800, 0x4900, 0x4b00, 0x4d00, 0x4f00, 0x5000, 0x5100, 0x3920,
                ]
                .contains(&p.key)
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
                return Err("上岸待選資料或階段衝突".into());
            }
        }
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
    pub fn cast_water(&mut self) -> Result<(), String> {
        if self.phase() != "world" || !self.magic.book || self.magic.charges[6] == 0 {
            return Err("目前不能施展涉水術".into());
        }
        self.magic.charges[6] -= 1;
        self.magic.selected = 6;
        self.world.boat = 1;
        Ok(())
    }
    pub fn select_shore(&mut self, yes: bool) -> Result<(), String> {
        self.travel_spell.validate(self)?;
        self.travel_spell
            .shore
            .as_mut()
            .ok_or("沒有待確認上岸")?
            .yes = yes;
        Ok(())
    }
    pub fn finish_shore(
        &mut self,
        d: &WorldData,
        c: &crate::catalog::Catalog,
    ) -> Result<(), String> {
        self.travel_spell.validate(self)?;
        let p = self.travel_spell.shore.ok_or("沒有待確認上岸")?;
        let view = self.magic.view(d)?;
        if !self.world.plain_shore(&view, p.key)? {
            return Err("上岸落點不符".into());
        }
        let mut s = self.clone();
        s.travel_spell.shore = None;
        if p.yes {
            s.world.boat = 0;
            if let Some(b) = s.travel(d, p.key, c)? {
                return Err(format!("上岸尚未接入：{b:?}"));
            }
        } else {
            match s.world.reject_shore(&view, p.key)? {
                crate::world::WalkResult::Boundary(crate::world::Boundary::Encounter(cue)) => {
                    if s.army[0].count > 0 {
                        s.cue = Some(cue);
                    }
                }
                crate::world::WalkResult::Committed { .. } => {}
                _ => return Err("上岸拒絕返回未知邊界".into()),
            }
        }
        *self = s;
        Ok(())
    }
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

#[cfg(test)]
#[path = "water_spell_tests.rs"]
mod water_tests;
