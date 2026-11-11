//! Spec031: sub_1151C six-stack scan and1168B..116A4 empty-army loss.
use crate::{
    battle::Stack,
    controller::OriginalRng,
    journey::{Journey, army_ok},
};
pub fn has_troops(army: &[Stack; 6]) -> bool {
    army.iter().any(|s| s.count > 0)
}
pub fn loss(gold: u64, roll: u16) -> Result<u64, String> {
    if gold > 30000 || roll > 32767 {
        return Err("遇劫金錢或亂數超界".into());
    }
    Ok(gold / (u64::from(roll) / 2730 + 2))
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Theft {
    pub cue: u8,
    pub seed_before: u32,
    pub gold_before: u16,
}
impl Theft {
    pub fn amount(&self) -> u64 {
        let mut r = OriginalRng {
            seed: self.seed_before,
        };
        u64::from(self.gold_before) / (u64::from(r.next15()) / 2730 + 2)
    }
    pub(crate) fn validate(&self, j: &Journey<'_>) -> Result<(), String> {
        let mut r = OriginalRng {
            seed: self.seed_before,
        };
        r.next15();
        if self.cue > 13
            || self.gold_before > 30000
            || self.cue != (((self.seed_before >> 16) & 32767) / 2341) as u8
            || !army_ok(&j.army, false)
            || has_troops(&j.army)
            || j.world.actions == 0
            || j.world.rng != r
            || j.resources[3] != u64::from(self.gold_before) - self.amount()
            || j.cue.is_some()
            || j.battle.is_some()
            || j.camps.pending.is_some()
            || j.month.pending.is_some()
            || j.treasure.pending.is_some()
            || j.magic.shop.is_some()
            || j.magic.direction
            || j.resource_notice.is_some()
            || j.survey.bird
            || j.travel_spell.teleport.is_some()
            || j.travel_spell.shore.is_some()
            || j.travel_spell.refused_shop.is_some()
        {
            return Err("待確認遇劫紀錄不符".into());
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    /// Every committed encounter passes here, including events and jump cells.
    pub(crate) fn receive_encounter(&mut self, cue: u8) -> Result<(), String> {
        if cue > 13
            || self.theft.is_some()
            || self.cue.is_some()
            || self.battle.is_some()
            || !army_ok(&self.army, false)
        {
            return Err("遇敵接收階段錯誤".into());
        }
        if has_troops(&self.army) {
            self.cue = Some(cue);
            return Ok(());
        }
        let mut s = self.clone();
        let notice = Theft {
            cue,
            seed_before: s.world.rng.seed,
            gold_before: s.resources[3].try_into().map_err(|_| "遇劫前金錢超界")?,
        };
        let amount = loss(s.resources[3], s.world.rng.next15())?;
        s.resources[3] -= amount;
        s.theft = Some(notice);
        notice.validate(&s)?;
        *self = s;
        Ok(())
    }
    pub fn close_theft(&mut self) -> Result<(), String> {
        self.theft.ok_or("沒有待確認遇劫")?.validate(self)?;
        self.theft = None;
        Ok(())
    }
}
#[cfg(test)]
#[path = "theft_tests.rs"]
mod tests;
