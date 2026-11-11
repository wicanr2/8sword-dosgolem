//! Spec031 resource spells. Inherited original/Go receipts, no guest execution.
use crate::battle::Stack;
use crate::catalog::{Catalog, UnitId};
use crate::controller::OriginalRng;
use crate::journey::{Journey, army_ok};
pub fn alchemy_amount(roll: u16, bonus: bool) -> Result<u16, String> {
    if roll > 32767 {
        return Err("煉金亂數超界".into());
    }
    Ok(roll / 260 + if bonus { 40 } else { 0 })
}
pub fn summon_payload(rank: u8, roll: u16, bonus: bool) -> Result<(u8, u16), String> {
    if !(1..=5).contains(&rank) || roll > 32767 {
        return Err("召兵階級或亂數錯誤".into());
    }
    let count = 24 - u16::from(rank) * 4;
    Ok((
        (roll / 6600 * 5) as u8 + rank,
        if bonus { count * 3 / 2 } else { count },
    ))
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Effect {
    pub gold: u64,
    pub army: [Stack; 6],
    pub amount: u16,
    pub kind: u8,
    pub count: u16,
    pub joined: bool,
}
pub fn plan(
    c: &Catalog,
    army: [Stack; 6],
    rank: u8,
    gold: u64,
    lead: u64,
    spell: u8,
    roll: u16,
    bonus: bool,
) -> Result<Effect, String> {
    if !army_ok(&army, false) || gold > 30000 || lead > 30000 || !(1..=5).contains(&rank) {
        return Err("資源法術輸入錯誤".into());
    }
    let mut out = Effect {
        gold,
        army,
        amount: 0,
        kind: 0,
        count: 0,
        joined: false,
    };
    match spell {
        1 => {
            out.amount = alchemy_amount(roll, bonus)?;
            out.gold = (gold + u64::from(out.amount)).min(30000);
        }
        2 => {
            let (kind, count) = summon_payload(rank, roll, bonus)?;
            let id = UnitId::parse(&format!("native:{kind:02}"))?;
            out.kind = kind;
            out.count = count;
            if let Some(at) = army
                .iter()
                .position(|s| s.unit == Some(id))
                .or_else(|| army.iter().position(|s| s.count == 0))
            {
                let n = army[at]
                    .count
                    .checked_add(u32::from(count))
                    .ok_or("召兵兵數超界")?;
                if n > 32767 {
                    return Err("召兵超過已驗戰場兵數範圍".into());
                }
                out.army[at] = Stack {
                    unit: Some(id),
                    count: n,
                };
                out.joined = true;
            }
            let mut used = 0u64;
            for s in out.army {
                if let Some(id) = s.unit {
                    used = used
                        .checked_add(
                            c.get(id)
                                .command
                                .checked_mul(u64::from(s.count))
                                .ok_or("領導用量超界")?,
                        )
                        .ok_or("領導用量超界")?;
                }
            }
            if used > lead {
                return Err("召兵超出領導用量".into());
            }
        }
        _ => return Err("未接資源法術".into()),
    }
    Ok(out)
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Notice {
    pub spell: u8,
    pub seed_before: u32,
    pub gold_before: u64,
    pub uses_before: u16,
    pub army_before: [Stack; 6],
}
impl Notice {
    pub fn effect(&self, j: &Journey<'_>, c: &Catalog) -> Result<Effect, String> {
        let mut rng = OriginalRng {
            seed: self.seed_before,
        };
        plan(
            c,
            self.army_before,
            j.world.rank,
            self.gold_before,
            j.resources[4],
            self.spell,
            rng.next15(),
            j.has_item(if self.spell == 1 { 2 } else { 3 }),
        )
    }
    pub(crate) fn validate(&self, j: &Journey<'_>, c: &Catalog) -> Result<(), String> {
        if !matches!(self.spell, 1 | 2)
            || self.uses_before == 0
            || self.uses_before > 30000
            || j.battle.is_some()
            || j.cue.is_some()
            || j.camps.pending.is_some()
            || j.month.pending.is_some()
            || j.treasure.pending.is_some()
            || j.magic.shop.is_some()
            || j.magic.direction
            || !j.magic.book
        {
            return Err("資源法術結果階段錯誤".into());
        }
        let mut rng = OriginalRng {
            seed: self.seed_before,
        };
        let _ = rng.next15();
        let out = self.effect(j, c)?;
        if j.world.rng != rng
            || j.resources[3] != out.gold
            || j.army != out.army
            || j.magic.charges[usize::from(self.spell)] != self.uses_before - 1
        {
            return Err("資源法術結果綁定錯誤".into());
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    pub fn cast_resource(&mut self, c: &Catalog, spell: u8) -> Result<(), String> {
        if self.phase() != "world"
            || !self.magic.book
            || !matches!(spell, 1 | 2)
            || self.magic.charges[usize::from(spell)] == 0
        {
            return Err("目前不能施展此法術".into());
        }
        let mut s = self.clone();
        let notice = Notice {
            spell,
            seed_before: s.world.rng.seed,
            gold_before: s.resources[3],
            uses_before: s.magic.charges[usize::from(spell)],
            army_before: s.army,
        };
        let out = notice.effect(&s, c)?;
        let _ = s.world.rng.next15();
        s.resources[3] = out.gold;
        s.army = out.army;
        s.magic.charges[usize::from(spell)] -= 1;
        s.magic.selected = spell;
        notice.validate(&s, c)?;
        s.resource_notice = Some(notice);
        *self = s;
        Ok(())
    }
    pub fn close_resource_notice(&mut self, c: &Catalog) -> Result<(), String> {
        self.resource_notice
            .as_ref()
            .ok_or("沒有法術結果")?
            .validate(self, c)?;
        self.resource_notice = None;
        Ok(())
    }
}
#[cfg(test)]
#[path = "resource_spells_tests.rs"]
mod tests;
