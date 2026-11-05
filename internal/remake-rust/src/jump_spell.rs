//! Spec031: original DS56CC, sub_10B38/10C32/11F60/12014.
use crate::{
    journey::Journey,
    world::{Position, WorldData, motion},
};
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum Jump {
    #[default]
    Idle,
    Ready,
    Flying {
        key: u16,
    },
}
pub const DIRECTIONS: [u16; 8] = [
    0x4700, 0x4800, 0x4900, 0x4b00, 0x4d00, 0x4f00, 0x5000, 0x5100,
];
pub fn landable(tile: u8) -> bool {
    matches!(tile, 1 | 3..=10)
}
pub fn plan(
    jump: Jump,
    p: Position,
    facing: u8,
    input: u16,
    tile: u8,
) -> Result<(Position, u8, Jump, bool), String> {
    if !(1..=65).contains(&tile) {
        return Err("跳躍地形錯誤".into());
    }
    let key = match jump {
        Jump::Idle => return Err("沒有待跳狀態".into()),
        Jump::Ready if input == 0x3920 => return Ok((p, facing, Jump::Ready, true)),
        Jump::Ready => input,
        Jump::Flying { key } => key,
    };
    if !DIRECTIONS.contains(&key) {
        return Err("跳躍方向錯誤".into());
    }
    let (p, face) = motion(p, key, facing, false)?;
    Ok((
        p,
        face,
        if landable(tile) {
            Jump::Idle
        } else {
            Jump::Flying { key }
        },
        false,
    ))
}
impl<'a> Journey<'a> {
    pub(crate) fn jump_tile(&self, d: &WorldData, p: Position) -> Result<u8, String> {
        let tile = d.tile(self.world.area, p)?;
        if tile != 59 {
            return Ok(tile);
        }
        let i = crate::treasure::sites()
            .iter()
            .position(|s| s.area == self.world.area && s.x == p.x && s.y == p.y)
            .ok_or("跳躍寶箱缺少原記錄")?;
        Ok(if self.treasure.amounts[i] == 0 { 1 } else { 59 })
    }
    pub(crate) fn validate_jump(&self, d: &WorldData) -> Result<(), String> {
        if self.travel_spell.jump != Jump::Idle && !self.magic.book {
            return Err("沒有竹簡卻持有跳躍".into());
        }
        if let Jump::Flying { key } = self.travel_spell.jump {
            if !DIRECTIONS.contains(&key)
                || landable(self.jump_tile(d, self.world.position)?)
                || motion(self.world.position, key, self.world.facing, false)?.1
                    != self.world.facing
                || self.travel_spell.shore.is_some()
                || self.travel_spell.teleport.is_some()
                || self.magic.direction
                || self.magic.shop.is_some()
                || self.survey.bird
                || self.resource_notice.is_some()
                || self.battle.is_some()
                || self.cue.is_some()
                || self.camps.pending.is_some()
                || self.month.pending.is_some()
                || self.treasure.pending.is_some()
            {
                return Err("跳躍途中狀態不符".into());
            }
        }
        Ok(())
    }
    pub fn cast_jump(&mut self) -> Result<(), String> {
        if self.phase() != "world" || !self.magic.book || self.magic.charges[3] == 0 {
            return Err("目前不能施展跳躍術".into());
        }
        self.magic.charges[3] -= 1;
        self.magic.selected = 3;
        self.travel_spell.jump = Jump::Ready;
        Ok(())
    }
    pub(crate) fn jump_move(&mut self, d: &WorldData, input: u16) -> Result<(), String> {
        let key = match self.travel_spell.jump {
            Jump::Ready => input,
            Jump::Flying { key } => key,
            _ => return Err("沒有跳躍可移動".into()),
        };
        if !DIRECTIONS.contains(&key) {
            return Err("跳躍移動方向錯誤".into());
        }
        let target = motion(self.world.position, key, self.world.facing, false)?.0;
        let (p, face, jump, regular) = plan(
            self.travel_spell.jump,
            self.world.position,
            self.world.facing,
            input,
            self.jump_tile(d, target)?,
        )?;
        if regular {
            return Err("跳躍不能代走普通尾段".into());
        }
        let mut s = self.clone();
        s.world.position = p;
        s.world.facing = face;
        s.travel_spell.jump = jump;
        s.world.reveal();
        s.validate_jump(d)?;
        *self = s;
        Ok(())
    }
    pub fn advance_jump(&mut self, d: &WorldData) -> Result<(), String> {
        if !matches!(self.travel_spell.jump, Jump::Flying { .. }) {
            return Err("沒有自動前進的跳躍".into());
        }
        let view = self.magic.view(d)?;
        self.validate_jump(&view)?;
        self.jump_move(&view, 0)
    }
}
#[cfg(test)]
#[path = "jump_spell_tests.rs"]
mod tests;
