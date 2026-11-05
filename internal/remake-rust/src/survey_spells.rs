//! Spec031: original sub_16E32 stop-time and sub_180D8 temporary bird view.
use crate::journey::Journey;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Survey {
    pub stopped: bool,
    pub tempo: u8,
    pub bird: bool,
}
impl Default for Survey {
    fn default() -> Self {
        Self {
            stopped: false,
            tempo: 6,
            bird: false,
        }
    }
}
pub fn extension(rank: u8, remaining: u16) -> Result<(u16, u8), String> {
    if !(1..=5).contains(&rank) || remaining == 0 {
        return Err("停時階級或步數錯誤".into());
    }
    let factor = [8, 10, 12, 15, 18][usize::from(rank - 1)];
    let product = u32::from(remaining) * u32::from(factor);
    if product > 32767 {
        return Err("停時超出已驗正數乘積範圍".into());
    }
    Ok(((product / 6) as u16, factor))
}
impl Survey {
    pub(crate) fn validate(&self, j: &Journey<'_>) -> Result<(), String> {
        if if self.stopped {
            !matches!(self.tempo, 8 | 10 | 12 | 15 | 18)
        } else {
            self.tempo != 6
        } {
            return Err("停時旗標與時鐘比率不符".into());
        }
        if j.month.pending.is_some() && self.stopped {
            return Err("月報尚存舊停時狀態".into());
        }
        if self.bird
            && (!j.magic.book
                || j.magic.selected != 5
                || j.magic.direction
                || j.magic.shop.is_some()
                || j.resource_notice.is_some()
                || j.battle.is_some()
                || j.cue.is_some()
                || j.camps.pending.is_some()
                || j.month.pending.is_some()
                || j.treasure.pending.is_some())
        {
            return Err("鳥瞰階段衝突".into());
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    pub fn cast_stop_time(&mut self) -> Result<(), String> {
        if self.phase() != "world" || !self.magic.book || self.magic.charges[4] == 0 {
            return Err("目前不能施展停時術".into());
        }
        let mut s = self.clone();
        if !s.survey.stopped {
            let (remaining, tempo) = extension(s.world.rank, s.world.remaining)?;
            s.world.remaining = remaining;
            s.survey.tempo = tempo;
            s.survey.stopped = true;
        }
        s.magic.charges[4] -= 1;
        s.magic.selected = 4;
        s.survey.validate(&s)?;
        *self = s;
        Ok(())
    }
    pub fn begin_bird_view(&mut self) -> Result<(), String> {
        if self.phase() != "world" || !self.magic.book || self.magic.charges[5] == 0 {
            return Err("目前不能施展鳥瞰術".into());
        }
        let mut s = self.clone();
        s.magic.charges[5] -= 1;
        s.magic.selected = 5;
        s.survey.bird = true;
        s.survey.validate(&s)?;
        *self = s;
        Ok(())
    }
    pub fn close_bird_view(&mut self) -> Result<(), String> {
        if !self.survey.bird {
            return Err("沒有待關閉鳥瞰圖".into());
        }
        self.survey.validate(self)?;
        self.survey.bird = false;
        Ok(())
    }
}
#[cfg(test)]
#[path = "survey_spells_tests.rs"]
mod tests;
