//! Spec031 one-time chest resources; the original 145FA scan defines row identity.
use crate::catalog::Catalog;
use crate::journey::Journey;
use crate::media_assets::checksum;
use crate::world::{Boundary, WalkResult, WorldData};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Site {
    pub area: u8,
    pub row: u8,
    pub x: u8,
    pub y: u8,
    pub amount: u16,
}
pub fn sites() -> &'static [Site; 80] {
    static DATA: std::sync::OnceLock<[Site; 80]> = std::sync::OnceLock::new();
    DATA.get_or_init(|| {
        let rows: Vec<Site> = include_str!("../treasure-catalog.tsv")
            .lines()
            .filter(|s| !s.starts_with('#'))
            .enumerate()
            .map(|(i, s)| {
                let f: Vec<u16> = s
                    .split('\t')
                    .map(|v| v.parse().expect("fixed treasure integer"))
                    .collect();
                assert!(
                    f.len() == 5
                        && f[0] == (i / 10) as u16
                        && f[1] == (i % 10) as u16
                        && f[2] < 70
                        && f[3] < 80
                        && f[4] <= 30000
                );
                Site {
                    area: f[0] as u8,
                    row: f[1] as u8,
                    x: f[2] as u8,
                    y: f[3] as u8,
                    amount: f[4],
                }
            })
            .collect();
        assert_eq!(rows.len(), 80);
        rows.try_into().unwrap()
    })
}
pub fn fingerprint() -> u64 {
    checksum(include_bytes!("../treasure-catalog.tsv"))
}
pub fn validate_maps(d: &WorldData) -> Result<(), String> {
    for area in 0..8 {
        let mut found = Vec::new();
        for y in 0..80 {
            for x in 0..70 {
                if d.tile(area, crate::world::Position { x, y })? == 59 {
                    found.push((x, y));
                }
            }
        }
        let expected: Vec<_> = sites()
            .iter()
            .filter(|s| s.area == area)
            .map(|s| (s.x, s.y))
            .collect();
        if found != expected {
            return Err("寶箱地圖順序或數量不符".into());
        }
    }
    Ok(())
}
pub fn award(gold: u64, lead: u64, amount: u16, choice: u8) -> Result<(u64, u64, bool), String> {
    if gold > 30000 || lead > 30000 || amount > 30000 || choice > 2 {
        return Err("寶箱資源或選項錯誤".into());
    }
    if choice == 0 || amount == 0 {
        return Ok((gold, lead, false));
    }
    Ok(if choice == 1 {
        ((gold + u64::from(amount)).min(30000), lead, true)
    } else {
        (gold, (lead + u64::from(amount / 10)).min(30000), true)
    })
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Pending {
    pub index: u8,
    pub choice: u8,
    pub moved: bool,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Treasure {
    pub amounts: [u16; 80],
    pub pending: Option<Pending>,
}
impl Default for Treasure {
    fn default() -> Self {
        Self {
            amounts: std::array::from_fn(|i| sites()[i].amount),
            pending: None,
        }
    }
}
impl Treasure {
    pub(crate) fn validate(&self, j: &Journey<'_>, d: &WorldData) -> Result<(), String> {
        self.validate_inner(j, d, false)
    }
    fn validate_inner(
        &self,
        j: &Journey<'_>,
        d: &WorldData,
        allow_empty: bool,
    ) -> Result<(), String> {
        if self
            .amounts
            .iter()
            .enumerate()
            .any(|(i, n)| *n != 0 && *n != sites()[i].amount)
        {
            return Err("寶箱價值不符原紀錄".into());
        }
        if let Some(p) = self.pending {
            let s = sites().get(usize::from(p.index)).ok_or("寶箱索引超界")?;
            if (self.amounts[usize::from(p.index)] == 0 && !allow_empty)
                || !(1..=2).contains(&p.choice)
                || j.world.area != s.area
                || j.world.position.x != s.x
                || j.world.position.y != s.y
                || d.tile(s.area, j.world.position)? != 59
                || j.battle.is_some()
                || j.cue.is_some()
                || j.camps.pending.is_some()
                || j.month.pending.is_some()
            {
                return Err("待選寶箱狀態錯誤".into());
            }
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    pub(crate) fn open_treasure(
        &mut self,
        d: &WorldData,
        key: u16,
        c: &Catalog,
    ) -> Result<(), String> {
        if self.phase() != "world" {
            return Err("目前不能開啟寶箱".into());
        }
        let mut s = self.clone();
        s.world = s.world.event_step(d, key, 59)?;
        let at = sites()
            .iter()
            .position(|v| {
                v.area == s.world.area && v.x == s.world.position.x && v.y == s.world.position.y
            })
            .ok_or("寶箱座標沒有唯一紀錄")?;
        s.treasure.pending = Some(Pending {
            index: at as u8,
            choice: 1,
            moved: key != 0x3920,
        });
        if s.treasure.amounts[at] == 0 {
            s.finish_treasure(c, d, true)?;
        } else {
            s.treasure.validate(&s, d)?;
        }
        *self = s;
        Ok(())
    }
    pub fn select_treasure(&mut self, choice: u8) -> Result<(), String> {
        if !(1..=2).contains(&choice) {
            return Err("寶箱選項錯誤".into());
        }
        self.treasure.pending.as_mut().ok_or("沒有待選寶箱")?.choice = choice;
        Ok(())
    }
    pub fn finish_treasure(
        &mut self,
        c: &Catalog,
        d: &WorldData,
        cancel: bool,
    ) -> Result<(), String> {
        self.treasure.validate_inner(self, d, cancel)?;
        let mut s = self.clone();
        let p = s.treasure.pending.take().ok_or("沒有待選寶箱")?;
        let at = usize::from(p.index);
        let amount = *s.treasure.amounts.get(at).ok_or("寶箱索引超界")?;
        if !cancel {
            if amount == 0 {
                return Err("寶箱已領取".into());
            }
            let (gold, lead, consumed) = award(s.resources[3], s.resources[4], amount, p.choice)?;
            if !consumed {
                return Err("未提交寶箱獎勵".into());
            }
            s.resources[3] = gold;
            s.resources[4] = lead;
            s.treasure.amounts[at] = 0;
        }
        if p.moved {
            if s.world.remaining == 1 {
                s.begin_month(c, d, 59)?;
                *self = s;
                return Ok(());
            }
            s.world.remaining -= 1;
        }
        match s.world.walk_site(d, 59)? {
            WalkResult::Boundary(Boundary::Encounter(cue)) => {
                if s.army[0].count > 0 {
                    s.cue = Some(cue);
                }
            }
            WalkResult::Boundary(b) => return Err(format!("寶箱返回邊界：{b:?}")),
            _ => {}
        }
        *self = s;
        Ok(())
    }
}
#[cfg(test)]
#[path = "treasure_tests.rs"]
mod tests;
