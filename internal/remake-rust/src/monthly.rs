//! Spec031 player finances, camp/NPC refill and the observed two month-end RNG calls.
use crate::battle::Stack;
use crate::catalog::{Catalog, UnitId};
use crate::journey::Journey;
use crate::management::{EXTRA, camps};
use crate::media_assets::checksum;
use crate::world::{Boundary, WalkResult, WorldData};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Budget {
    pub before: u64,
    pub income: u64,
    pub due: u64,
    pub charged: u64,
    pub after: u64,
    pub disbanded: bool,
}
pub fn plan(c: &Catalog, army: [Stack; 6], before: u64, income: u64) -> Result<Budget, String> {
    if before > 30000 || income > 30000 {
        return Err("月報資源超界".into());
    }
    let mut due = 0u64;
    for row in army {
        match row.unit {
            Some(id) if row.count > 0 => {
                due = due
                    .checked_add(
                        c.get(id)
                            .gold
                            .checked_mul(u64::from(row.count))
                            .ok_or("軍費超界")?,
                    )
                    .ok_or("軍費超界")?;
            }
            None if row.count == 0 => {}
            _ => return Err("月報軍隊錯誤".into()),
        }
    }
    let total = before + income;
    let disbanded = due > total;
    let charged = if disbanded { 0 } else { due };
    Ok(Budget {
        before,
        income,
        due,
        charged,
        after: (total - charged).min(30000),
        disbanded,
    })
}
pub fn caps() -> &'static [u32; 120] {
    static DATA: std::sync::OnceLock<[u32; 120]> = std::sync::OnceLock::new();
    DATA.get_or_init(|| {
        let rows: Vec<u32> = include_str!("../monthly-caps.tsv")
            .lines()
            .map(|s| s.parse().expect("fixed cap integer"))
            .collect();
        assert_eq!(rows.len(), 120);
        assert!(rows.iter().all(|n| *n <= 30000));
        rows.try_into().unwrap()
    })
}
pub fn fingerprint() -> u64 {
    checksum(include_bytes!("../monthly-caps.tsv"))
}
pub fn refill(stock: u32, cap: u32, native: bool) -> Result<u32, String> {
    let next = u64::from(stock) + u64::from((stock / 10).max(10));
    if native && next > 32767 {
        return Err("原店補貨超出已驗域".into());
    }
    Ok(next.min(u64::from(cap)) as u32)
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Report {
    pub budget: Budget,
    pub army_before: [Stack; 6],
    pub tile: u8,
}
#[derive(Clone, Debug, PartialEq, Eq, Default)]
pub struct Monthly {
    pub months: u64,
    pub pending: Option<Report>,
}
impl Monthly {
    pub(crate) fn validate(
        &self,
        j: &Journey<'_>,
        c: &Catalog,
        d: &WorldData,
    ) -> Result<(), String> {
        if let Some(r) = &self.pending {
            let b = plan(c, r.army_before, r.budget.before, r.budget.income)?;
            if self.months == 0
                || !crate::journey::army_ok(&r.army_before, false)
                || b != r.budget
                || j.resources[3] != b.after
                || j.resources[2] != b.income
                || j.army
                    != if b.disbanded {
                        [Stack::default(); 6]
                    } else {
                        r.army_before
                    }
                || j.world.remaining != 324
                || j.battle.is_some()
                || j.cue.is_some()
                || j.camps.pending.is_some()
                || d.tile(j.world.area, j.world.position)? != r.tile
                || matches!(r.tile, 49 | 50)
                || j.treasure.pending.is_some()
            {
                return Err("待確認月報狀態錯誤".into());
            }
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    pub fn travel(
        &mut self,
        d: &WorldData,
        key: u16,
        c: &Catalog,
    ) -> Result<Option<Boundary>, String> {
        let view = self.magic.view(d)?;
        let mut s = self.clone();
        if s.phase() == "world"
            && s.travel_spell.jump == crate::jump_spell::Jump::Ready
            && key != 0x3920
        {
            s.jump_move(&view, key)?;
            *self = s;
            return Ok(None);
        }
        let out = s.walk(&view, key)?;
        let target = crate::world::motion(s.world.position, key, s.world.facing, false)?.0;
        if crate::map_notice::sites()
            .iter()
            .any(|s| s.area == self.world.area && s.position == target)
            && (out == Some(Boundary::Terrain(51))
                || (out == Some(Boundary::BoatExit)
                    && crate::jump_spell::DIRECTIONS.contains(&key)
                    && view.tile(s.world.area, target)? == 51))
        {
            s.open_map_notice(&view, key)?;
            *self = s;
            return Ok(None);
        }
        if out == Some(Boundary::BoatExit) && s.supported_shore(&view, key)? {
            s.world = s.world.prepare_shore(&view, key)?;
            s.travel_spell.shore = Some(crate::travel_spells::Shore { key, yes: true });
            s.travel_spell.validate(&s)?;
            *self = s;
            return Ok(None);
        }
        if out == Some(Boundary::Terrain(65))
            && crate::guards::sites()
                .iter()
                .any(|s| s.area == self.world.area && s.position == target)
        {
            s.open_guard(&view, key, c)?;
            *self = s;
            return Ok(None);
        }
        if out == Some(Boundary::Monthly) {
            s.world = s.world.monthly_step(&view, key)?;
            let tile = view.tile(s.world.area, s.world.position)?;
            s.begin_month(c, &view, tile)?;
            *self = s;
            return Ok(None);
        }
        if let Some(Boundary::Terrain(tile @ (49 | 50))) = out {
            s.cross_exit(d, key, tile, c)?;
            *self = s;
            return Ok(None);
        }
        if out == Some(Boundary::Terrain(59)) {
            s.open_treasure(d, key, c)?;
            *self = s;
            return Ok(None);
        }
        if out == Some(Boundary::Terrain(53)) && s.open_magic_shop(&view, key)? {
            *self = s;
            return Ok(None);
        }
        *self = s;
        Ok(out)
    }
    pub(crate) fn begin_month(
        &mut self,
        c: &Catalog,
        d: &WorldData,
        tile: u8,
    ) -> Result<(), String> {
        if self.month.pending.is_some()
            || self.world.remaining != 1
            || self.battle.is_some()
            || self.cue.is_some()
            || self.camps.pending.is_some()
            || self.treasure.pending.is_some()
            || self.survey.bird
            || self.travel_spell.teleport.is_some()
            || self.travel_spell.shore.is_some()
            || matches!(
                self.travel_spell.jump,
                crate::jump_spell::Jump::Flying { .. }
            )
        {
            return Err("不在月結邊界".into());
        }
        let mut s = self.clone();
        let b = plan(c, s.army, s.resources[3], s.resources[2])?;
        let before = s.army;
        // Original sub16226, return CS0110:6494. Its result is unused.
        s.world.rng.next15();
        for (i, site) in camps().iter().enumerate() {
            if site.kind == 0 {
                continue;
            }
            s.camps.stock[i] = refill(s.camps.stock[i], caps()[i], true)?;
            if let Some(rows) = &mut s.camps.extras[i] {
                let p = c.get(UnitId::parse(&format!("native:{:02}", site.kind))?);
                for (n, id) in EXTRA.iter().enumerate() {
                    let cap = (u64::from(caps()[i]) * p.gold / c.get(UnitId::parse(id)?).gold)
                        .try_into()
                        .map_err(|_| "增援補貨超界")?;
                    rows[n] = refill(rows[n], cap, false)?;
                }
            }
        }
        s.guards.refill_monthly()?;
        s.resources[3] = b.after;
        if b.disbanded {
            s.army = [Stack::default(); 6];
        }
        // Original sub1716C, return CS0110:71B3, before resetting the month.
        s.world.rng.next15();
        s.world.remaining = 324;
        s.survey.stopped = false;
        s.survey.tempo = 6;
        s.month.months = s.month.months.checked_add(1).ok_or("月結次數超界")?;
        s.month.pending = Some(Report {
            budget: b,
            army_before: before,
            tile,
        });
        s.month.validate(&s, c, d)?;
        *self = s;
        Ok(())
    }
    pub fn close_month(&mut self, d: &WorldData) -> Result<(), String> {
        let view = self.magic.view(d)?;
        let d = &view;
        let mut s = self.clone();
        let r = s.month.pending.take().ok_or("沒有待確認月報")?;
        match s.world.walk_site(d, r.tile)? {
            WalkResult::Boundary(Boundary::Encounter(cue)) => {
                s.receive_encounter(cue)?;
            }
            WalkResult::Boundary(b) => return Err(format!("月報返回邊界：{b:?}")),
            _ => {}
        }
        *self = s;
        Ok(())
    }
}
#[cfg(test)]
#[path = "monthly_tests.rs"]
mod tests;
