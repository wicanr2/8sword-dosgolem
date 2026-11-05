//! Spec031: original six-stack management and five fixed camp groups.
use crate::battle::Stack;
use crate::catalog::{Catalog, UnitId};
use crate::journey::Journey;
use crate::media_assets::checksum;
use crate::world::{Boundary, WalkResult, WorldData};
pub const EXTRA: [&str; 8] = [
    "openkb:arcr",
    "openkb:pike",
    "openkb:wolf",
    "openkb:skel",
    "openkb:troll",
    "openkb:drui",
    "openkb:vamp",
    "openkb:drag",
];
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Camp {
    pub area: u8,
    pub x: u8,
    pub y: u8,
    pub kind: u8,
    pub stock: u32,
}
pub fn camps() -> &'static [Camp; 120] {
    static DATA: std::sync::OnceLock<[Camp; 120]> = std::sync::OnceLock::new();
    DATA.get_or_init(|| {
        let mut out = [Camp {
            area: 0,
            x: 0,
            y: 0,
            kind: 0,
            stock: 0,
        }; 120];
        for line in include_str!("../camp-catalog.tsv")
            .lines()
            .filter(|l| !l.starts_with('#'))
        {
            let f: Vec<usize> = line
                .split('\t')
                .map(|v| v.parse().expect("fixed camp integer"))
                .collect();
            assert!(
                f.len() == 7
                    && f[0] < 5
                    && f[1] < 24
                    && f[2] < 8
                    && f[3] < 70
                    && f[4] < 80
                    && f[5] <= 25
                    && f[6] <= 32767
            );
            out[f[0] * 24 + f[1]] = Camp {
                area: f[2] as u8,
                x: f[3] as u8,
                y: f[4] as u8,
                kind: f[5] as u8,
                stock: f[6] as u32,
            };
        }
        out
    })
}
pub fn camp_fingerprint() -> u64 {
    checksum(include_bytes!("../camp-catalog.tsv"))
}
#[cfg(test)]
#[path = "management_tests.rs"]
mod tests;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CampState {
    pub stock: [u32; 120],
    pub extras: [Option<[u32; 8]>; 120],
    pub pending: Option<usize>,
}
impl Default for CampState {
    fn default() -> Self {
        Self {
            stock: std::array::from_fn(|i| camps()[i].stock),
            extras: [None; 120],
            pending: None,
        }
    }
}
impl CampState {
    pub(crate) fn validate(&self, c: &Catalog) -> Result<(), String> {
        for (i, site) in camps().iter().enumerate() {
            let bound = site.stock.max(crate::monthly::caps()[i]);
            if self.stock[i] > bound {
                return Err("營地原庫存超界".into());
            }
            if let Some(ex) = self.extras[i] {
                if site.kind == 0 {
                    return Err("空營地有增援".into());
                }
                let p = c.get(UnitId::parse(&format!("native:{:02}", site.kind))?);
                for (n, id) in EXTRA.iter().enumerate() {
                    let max = u64::from(bound).checked_mul(p.gold).ok_or("庫存超界")?
                        / c.get(UnitId::parse(id)?).gold;
                    if u64::from(ex[n]) > max {
                        return Err("營地增援超界".into());
                    }
                }
            }
        }
        if self
            .pending
            .is_some_and(|i| i >= 120 || camps()[i].kind == 0)
        {
            return Err("營地位置錯誤".into());
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    fn camp_index(&self) -> Result<usize, String> {
        self.camps
            .pending
            .filter(|i| *i < 120 && camps()[*i].kind > 0)
            .ok_or_else(|| "未在有效營地".into())
    }
    pub fn used(&self, c: &Catalog) -> Result<u64, String> {
        let mut total = 0u64;
        for s in self.army {
            if let Some(id) = s.unit {
                total = total
                    .checked_add(
                        c.get(id)
                            .command
                            .checked_mul(u64::from(s.count))
                            .ok_or("領導用量超界")?,
                    )
                    .ok_or("領導用量超界")?;
            }
        }
        Ok(total)
    }
    pub fn dismiss(&mut self, slot: usize) -> Result<(), String> {
        if self.battle.is_some()
            || self.cue.is_some()
            || self.camps.pending.is_some()
            || self.month.pending.is_some()
            || self.treasure.pending.is_some()
            || self.magic.shop.is_some()
            || self.magic.direction
            || self.resource_notice.is_some()
            || self.survey.bird
            || self.travel_spell.teleport.is_some()
            || slot >= 6
            || self.army[slot].count == 0
        {
            return Err("無法解雇此部隊".into());
        }
        for i in slot..5 {
            self.army[i] = self.army[i + 1];
        }
        self.army[5] = Stack::default();
        Ok(())
    }
    pub fn open_extra(&mut self, c: &Catalog) -> Result<(), String> {
        let i = self.camp_index()?;
        if self.camps.extras[i].is_none() {
            let site = camps()[i];
            let price = c
                .get(UnitId::parse(&format!("native:{:02}", site.kind))?)
                .gold;
            let mut stock = [0; 8];
            for (n, id) in EXTRA.iter().enumerate() {
                stock[n] = (u64::from(self.camps.stock[i])
                    .checked_mul(price)
                    .ok_or("增援庫存超界")?
                    / c.get(UnitId::parse(id)?).gold)
                    .try_into()
                    .map_err(|_| "增援庫存超界")?;
            }
            self.camps.extras[i] = Some(stock);
        }
        Ok(())
    }
    pub fn offer(&self, extra: Option<usize>) -> Result<(UnitId, u32), String> {
        let i = self.camp_index()?;
        if let Some(n) = extra {
            let id = EXTRA.get(n).ok_or("增援選取錯誤")?;
            Ok((
                UnitId::parse(id)?,
                self.camps.extras[i].ok_or("未開增援頁")?[n],
            ))
        } else {
            Ok((
                UnitId::parse(&format!("native:{:02}", camps()[i].kind))?,
                self.camps.stock[i],
            ))
        }
    }
    pub fn maximum(&self, c: &Catalog, extra: Option<usize>) -> Result<u32, String> {
        let (id, stock) = self.offer(extra)?;
        let p = c.get(id);
        if u64::from(p.rank) > self.resources[0] {
            return Err("階級不足".into());
        }
        let slot = self
            .army
            .iter()
            .position(|s| s.unit == Some(id))
            .or_else(|| self.army.iter().position(|s| s.count == 0))
            .ok_or("已滿六隊")?;
        let used = self.used(c)?;
        let remaining = self.resources[4].checked_sub(used).ok_or("超出領導用量")?;
        Ok(u64::from(stock)
            .min(self.resources[3] / p.gold)
            .min(remaining / p.command)
            .min(u64::from(
                32767u32
                    .checked_sub(self.army[slot].count)
                    .ok_or("兵數超界")?,
            ))
            .min(9999) as u32)
    }
    pub fn recruit(&mut self, c: &Catalog, extra: Option<usize>, count: u32) -> Result<(), String> {
        if self.battle.is_some()
            || self.cue.is_some()
            || count == 0
            || count > self.maximum(c, extra)?
        {
            return Err("招募數量超過金錢、庫存或領導限制".into());
        }
        let (id, _) = self.offer(extra)?;
        let at = self
            .army
            .iter()
            .position(|s| s.unit == Some(id))
            .or_else(|| self.army.iter().position(|s| s.count == 0))
            .ok_or("已滿六隊")?;
        let cost = c
            .get(id)
            .gold
            .checked_mul(u64::from(count))
            .ok_or("費用超界")?;
        let gold = self.resources[3].checked_sub(cost).ok_or("金錢不足")?;
        let i = self.camp_index()?;
        self.army[at] = Stack {
            unit: Some(id),
            count: self.army[at].count + count,
        };
        self.resources[3] = gold;
        if let Some(n) = extra {
            self.camps.extras[i].as_mut().ok_or("未開增援頁")?[n] -= count;
        } else {
            self.camps.stock[i] -= count;
        }
        Ok(())
    }
    pub fn close_camp(
        &mut self,
        data: &WorldData,
        catalog: &Catalog,
    ) -> Result<Option<Boundary>, String> {
        let view = self.magic.view(data)?;
        let data = &view;
        let mut s = self.clone();
        let i = s.camp_index()?;
        let tile = 54 + (i / 24) as u8;
        if s.world.remaining <= 1 {
            s.camps.pending = None;
            s.begin_month(catalog, data, tile)?;
            *self = s;
            return Ok(None);
        }
        s.world.remaining -= 1;
        s.camps.pending = None;
        let result = s.world.walk_site(data, tile)?;
        let boundary = match result {
            WalkResult::Boundary(Boundary::Encounter(cue)) => {
                if s.army[0].count > 0 {
                    s.cue = Some(cue);
                }
                None
            }
            WalkResult::Boundary(b) => return Err(format!("營地返回邊界：{b:?}")),
            _ => None,
        };
        *self = s;
        Ok(boundary)
    }
}
