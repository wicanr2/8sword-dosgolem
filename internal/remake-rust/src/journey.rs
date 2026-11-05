//! Spec031 bounded random-encounter journey. No guest state or executable.
use crate::battle::{Modifiers, Outcome, Side, Stack};
use crate::catalog::{Catalog, UnitId};
use crate::controller::{Checkpoint, Controller, EnemyConfig, OriginalRng, ViewState};
use crate::management::{CampState, camp_fingerprint, camps};
use crate::media_assets::checksum;
use crate::spells::SpellBook;
use crate::world::{Boundary, WalkResult, WorldData, WorldState};
use std::path::Path;
pub const INITIAL: [u64; 6] = [1, 0, 100, 500, 100, 0];
pub const THRESHOLDS: [u64; 6] = [0, 2000, 5000, 8000, 12000, 30000];
pub fn generate(area: u8, rank: u8, rng: &mut OriginalRng) -> Result<[Stack; 6], String> {
    if area >= 8 || !(1..=5).contains(&rank) {
        return Err("敵軍區域或等級錯誤".into());
    }
    let mut r = *rng;
    let mut army = [Stack::default(); 6];
    let mut count = 0;
    loop {
        if count >= 3 && r.next15() / 4682 <= count as u16 {
            break;
        }
        let a = (i32::from(rank) - i32::from(r.next15() / 5462)).max(1) as u16;
        let kind = 5 * (r.next15() / 8192) + a + 5;
        let n = u32::from((r.next15() / 1000 / a) * (u16::from(area) + 1) + 10);
        army[count] = Stack {
            unit: Some(UnitId::parse(&format!("native:{kind:02}"))?),
            count: n,
        };
        count += 1;
        if count == 6 {
            let _ = r.next15();
            break;
        }
    }
    // Original 1364E..136B4 deletes duplicates, does not merge counts.
    for i in 0..6 {
        for j in 0..6 {
            if i != j && army[i].unit == army[j].unit {
                for k in j..5 {
                    army[k] = army[k + 1];
                }
            }
        }
    }
    *rng = r;
    Ok(army)
}

pub fn settle_resources(
    catalog: &Catalog,
    mut resources: [u64; 6],
    enemy: [Stack; 6],
    outcome: Outcome,
    rng: &mut OriginalRng,
) -> Result<[u64; 6], String> {
    if !(1..=5).contains(&resources[0])
        || resources.iter().any(|n| *n > 30000)
        || !army_ok(&enemy, true)
        || enemy[0].count == 0
    {
        return Err("戰果輸入錯誤".into());
    }
    let mut next = *rng;
    match outcome {
        Outcome::Win => {
            let (mut gold, mut merit) = (0u64, 0u64);
            for row in enemy {
                if let Some(id) = row.unit {
                    let p = catalog.get(id);
                    gold = gold
                        .checked_add(
                            p.gold
                                .checked_mul(u64::from(row.count))
                                .ok_or("戰果金錢超界")?,
                        )
                        .ok_or("戰果金錢超界")?;
                    merit = merit
                        .checked_add(
                            p.command
                                .checked_mul(u64::from(row.count))
                                .ok_or("戰果戰績超界")?,
                        )
                        .ok_or("戰果戰績超界")?;
                }
            }
            resources[3] = resources[3]
                .checked_add(gold)
                .ok_or("戰果金錢超界")?
                .min(30000);
            resources[1] = resources[1]
                .checked_add(merit / 2)
                .ok_or("戰果戰績超界")?
                .min(30000);
        }
        Outcome::Retreat => {
            let r = u64::from(next.next15());
            resources[3] -= resources[3] / (r / 2730 + 3);
        }
        Outcome::Loss => {}
    }
    if outcome != Outcome::Loss
        && resources[0] < 5
        && resources[1] > THRESHOLDS[resources[0] as usize]
    {
        resources[0] += 1;
        resources[2] = (resources[2] + 100).min(30000);
        resources[4] = (resources[4] + 100).min(30000);
        resources[5] = (resources[5] + resources[0] * 3).min(30000);
    }
    *rng = next;
    Ok(resources)
}
fn compact(rows: [Stack; 6]) -> [Stack; 6] {
    let mut out = [Stack::default(); 6];
    for (i, s) in rows.into_iter().filter(|s| s.count > 0).enumerate() {
        out[i] = s;
    }
    out
}
fn army_ok(rows: &[Stack; 6], native: bool) -> bool {
    let mut empty = false;
    let mut seen = Vec::new();
    for s in rows {
        if s.count == 0 {
            if s.unit.is_some() {
                return false;
            }
            empty = true;
            continue;
        }
        let Some(id) = s.unit else { return false };
        if empty || s.count > 32767 || seen.contains(&id) || native && id.native_kind().is_none() {
            return false;
        }
        seen.push(id);
    }
    true
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Journey<'a> {
    pub world: WorldState,
    pub army: [Stack; 6],
    pub resources: [u64; 6],
    pub cue: Option<u8>,
    pub enemy: [Stack; 6],
    pub generation_seed: u32,
    pub enemy_first: bool,
    pub battle: Option<Checkpoint<'a>>,
    pub battles: u64,
    pub camps: CampState,
}
impl<'a> Journey<'a> {
    pub fn new(data: &WorldData, seed: u32) -> Self {
        let mut army = [Stack::default(); 6];
        army[0] = Stack {
            unit: Some(UnitId::parse("native:01").expect("initial native ID")),
            count: 30,
        };
        Self {
            world: WorldState::new(data, seed),
            army,
            resources: INITIAL,
            cue: None,
            enemy: [Stack::default(); 6],
            generation_seed: 0,
            enemy_first: false,
            battle: None,
            battles: 0,
            camps: CampState::default(),
        }
    }
    pub fn phase(&self) -> &'static str {
        if self.battle.is_some() {
            "battle"
        } else if self.cue.is_some() {
            "prompt"
        } else if self.camps.pending.is_some() {
            "camp"
        } else {
            "world"
        }
    }
    pub fn walk(&mut self, data: &WorldData, key: u16) -> Result<Option<Boundary>, String> {
        if self.cue.is_some() || self.battle.is_some() || self.camps.pending.is_some() {
            return Err("遭遇尚未完成".into());
        }
        match self.world.walk_encounter(data, key)? {
            WalkResult::Boundary(Boundary::Encounter(c)) => {
                if self.army[0].count > 0 {
                    self.cue = Some(c);
                }
                Ok(None)
            }
            WalkResult::Boundary(Boundary::Terrain(tile @ 54..=58)) => {
                if self.world.remaining <= 1 {
                    return Ok(Some(Boundary::Monthly));
                }
                let (target, facing) =
                    crate::world::motion(self.world.position, key, self.world.facing, false)?;
                if let Some((i, _)) = camps().iter().enumerate().find(|(i, c)| {
                    *i / 24 == usize::from(tile - 54)
                        && c.kind > 0
                        && c.area == self.world.area
                        && c.x == target.x
                        && c.y == target.y
                }) {
                    self.world.position = target;
                    self.world.facing = facing;
                    self.camps.pending = Some(i);
                    Ok(None)
                } else {
                    Ok(Some(Boundary::Terrain(tile)))
                }
            }
            WalkResult::Boundary(b) => Ok(Some(b)),
            _ => Ok(None),
        }
    }
    pub fn choose(&mut self, catalog: &'a Catalog, accept: bool) -> Result<(), String> {
        if self.cue.is_none() || self.battle.is_some() || self.camps.pending.is_some() {
            return Err("未在遭遇確認".into());
        }
        let mut s = self.clone();
        let first = if accept {
            false
        } else {
            s.world.rng.next15() / 8192 == 1
        };
        if !accept && !first {
            s.cue = None;
            *self = s;
            return Ok(());
        }
        s.generation_seed = s.world.rng.seed;
        s.enemy = generate(s.world.area, s.world.rank, &mut s.world.rng)?;
        s.enemy_first = first;
        let book = self
            .army
            .iter()
            .any(|s| s.unit.is_some_and(UnitId::is_native_caster))
            .then_some(SpellBook {
                enabled: false,
                charges: [0; 8],
                stat_26b0: 0,
                stat_26ae: 0,
            });
        let scenario = if book.is_some() { 10 } else { 8 };
        let controller = Controller::with_enemy_spells(
            catalog,
            [s.army, s.enemy],
            if first { Side::Enemy } else { Side::Player },
            Modifiers::default(),
            book,
            EnemyConfig {
                stat_26ae: 0,
                shifted_alias: 0,
            },
        )
        .map_err(|e| format!("{e:?}"))?;
        s.battle = Some(Checkpoint {
            controller,
            rng: s.world.rng,
            view: ViewState {
                font: s.world.font,
                music: s.world.music,
                scenario,
                ..ViewState::default()
            },
        });
        *self = s;
        Ok(())
    }
    pub fn finish(
        &mut self,
        catalog: &Catalog,
        data: &WorldData,
        origin: Option<bool>,
    ) -> Result<Outcome, String> {
        self.validate(catalog, data)?;
        let mut s = self.clone();
        let cp = s.battle.as_ref().ok_or("不在戰場")?;
        let outcome = cp.controller.battle().outcome().ok_or("戰鬥未完成")?;
        if (outcome == Outcome::Loss) != origin.is_some() {
            return Err("全滅須明確選擇去向".into());
        }
        let rows = *cp.controller.battle().rows();
        s.army = compact(rows[0]);
        s.world.rng = cp.rng;
        s.world.font = cp.view.font;
        s.world.music = cp.view.music;
        s.resources = settle_resources(catalog, s.resources, s.enemy, outcome, &mut s.world.rng)?;
        if origin == Some(true) {
            s.world.area = 0;
            s.world.position = data.starts[0];
            s.world.facing = 3;
        }
        s.world.rank = s.resources[0] as u8;
        s.world.reveal();
        s.battles = s.battles.checked_add(1).ok_or("戰鬥次數超界")?;
        s.cue = None;
        s.battle = None;
        s.enemy = [Stack::default(); 6];
        s.generation_seed = 0;
        s.enemy_first = false;
        s.validate(catalog, data)?;
        *self = s;
        Ok(outcome)
    }
    fn validate(&self, catalog: &Catalog, data: &WorldData) -> Result<(), String> {
        self.world.encode(data)?;
        self.camps.validate(catalog)?;
        if let Some(i) = self.camps.pending {
            let c = camps()[i];
            if self.battle.is_some()
                || self.cue.is_some()
                || self.world.remaining <= 1
                || self.world.area != c.area
                || self.world.position.x != c.x
                || self.world.position.y != c.y
            {
                return Err("營地待完成狀態錯誤".into());
            }
        }
        if self.resources[0] != u64::from(self.world.rank)
            || self.resources.iter().any(|n| *n > 30000)
            || !army_ok(&self.army, false)
            || self.cue.is_some_and(|n| n > 13)
        {
            return Err("旅程資源或軍隊錯誤".into());
        }
        if let Some(cp) = &self.battle {
            cp.encode()?;
            if self.cue.is_none()
                || cp.view.font != self.world.font
                || cp.view.music != self.world.music
                || cp.controller.spell_book().is_some_and(|b| {
                    b.enabled || b.charges != [0; 8] || b.stat_26b0 != 0 || b.stat_26ae != 0
                })
            {
                return Err("旅程戰場狀態錯誤".into());
            }
            let mut rng = OriginalRng {
                seed: self.generation_seed,
            };
            if generate(self.world.area, self.world.rank, &mut rng)? != self.enemy
                || rng != self.world.rng
            {
                return Err("旅程敵軍來源錯誤".into());
            }
            for side in 0..2 {
                let before = if side == 0 { self.army } else { self.enemy };
                for (i, s) in cp.controller.battle().rows()[side].iter().enumerate() {
                    if s.unit != before[i].unit || side == 0 && s.count > before[i].count {
                        return Err("旅程戰場軍隊綁定錯誤".into());
                    }
                }
            }
        } else if self.enemy != [Stack::default(); 6]
            || self.generation_seed != 0
            || self.enemy_first
        {
            return Err("旅程空閒狀態錯誤".into());
        }
        if self.cue.is_some() && self.army[0].count == 0 {
            return Err("空軍隊不可進戰".into());
        }
        let _ = catalog;
        Ok(())
    }
    pub fn encode(&self, catalog: &Catalog, data: &WorldData) -> Result<Vec<u8>, String> {
        self.validate(catalog, data)?;
        let mut b = b"8SJRN002".to_vec();
        b.extend(catalog_hash(catalog).to_le_bytes());
        b.extend(self.world.encode(data)?);
        for n in self.resources {
            b.extend(n.to_le_bytes());
        }
        b.extend(self.battles.to_le_bytes());
        b.push(self.cue.unwrap_or(255));
        b.extend(self.generation_seed.to_le_bytes());
        b.push(u8::from(self.enemy_first));
        put_army(&mut b, &self.army);
        put_army(&mut b, &self.enemy);
        let c = self
            .battle
            .as_ref()
            .map(|c| c.encode())
            .transpose()?
            .unwrap_or_default();
        b.extend((c.len() as u16).to_le_bytes());
        b.extend(c);
        b.extend(camp_fingerprint().to_le_bytes());
        for i in 0..120 {
            b.extend(self.camps.stock[i].to_le_bytes());
            b.push(u8::from(self.camps.extras[i].is_some()));
            if let Some(rows) = self.camps.extras[i] {
                for n in rows {
                    b.extend(n.to_le_bytes());
                }
            }
        }
        b.push(self.camps.pending.map(|i| i as u8).unwrap_or(255));
        b.extend(checksum(&b).to_le_bytes());
        if b.len() > 16384 {
            return Err("旅程檢查點過大".into());
        }
        Ok(b)
    }
    pub fn decode(catalog: &'a Catalog, data: &WorldData, b: &[u8]) -> Result<Self, String> {
        if b.len() < 5730
            || b.len() > 16384
            || (&b[..8] != b"8SJRN001" && &b[..8] != b"8SJRN002")
            || u64::from_le_bytes(b[b.len() - 8..].try_into().unwrap())
                != checksum(&b[..b.len() - 8])
        {
            return Err("旅程檢查點格式錯誤".into());
        }
        let mut r = Reader {
            b: &b[8..b.len() - 8],
            at: 0,
        };
        if r.q()? != catalog_hash(catalog) {
            return Err("旅程兵種版本不符".into());
        }
        let world = WorldState::decode(data, r.take(5648)?)?;
        let mut resources = [0; 6];
        for n in &mut resources {
            *n = r.q()?;
        }
        let battles = r.q()?;
        let cue = match r.byte()? {
            255 => None,
            n => Some(n),
        };
        let generation_seed = u32::from_le_bytes(r.take(4)?.try_into().unwrap());
        let enemy_first = match r.byte()? {
            0 => false,
            1 => true,
            _ => return Err("旅程先手錯誤".into()),
        };
        let army = r.army()?;
        let enemy = r.army()?;
        let n = u16::from_le_bytes(r.take(2)?.try_into().unwrap()) as usize;
        let battle = if n == 0 {
            None
        } else {
            Some(Checkpoint::decode(catalog, r.take(n)?)?)
        };
        let mut camps = CampState::default();
        if &b[..8] == b"8SJRN002" {
            if r.q()? != camp_fingerprint() {
                return Err("營地版本不符".into());
            }
            for i in 0..120 {
                camps.stock[i] = u32::from_le_bytes(r.take(4)?.try_into().unwrap());
                match r.byte()? {
                    0 => {}
                    1 => {
                        let mut ex = [0; 8];
                        for n in &mut ex {
                            *n = u32::from_le_bytes(r.take(4)?.try_into().unwrap());
                        }
                        camps.extras[i] = Some(ex);
                    }
                    _ => return Err("增援狀態錯誤".into()),
                }
            }
            camps.pending = match r.byte()? {
                255 => None,
                n => Some(usize::from(n)),
            };
        }
        if r.at != r.b.len() {
            return Err("旅程尾端多餘資料".into());
        }
        let s = Self {
            world,
            army,
            resources,
            cue,
            enemy,
            generation_seed,
            enemy_first,
            battle,
            battles,
            camps,
        };
        s.validate(catalog, data)?;
        Ok(s)
    }
    pub fn save(&self, dir: &Path, catalog: &'a Catalog, data: &WorldData) -> Result<(), String> {
        let raw = self.encode(catalog, data)?;
        crate::checkpoint_store::save_named(
            dir,
            "journey.chk",
            &raw,
            16384,
            |b| Self::decode(catalog, data, b).map(|_| ()),
            false,
        )
    }
    pub fn load(dir: &Path, catalog: &'a Catalog, data: &WorldData) -> Result<Self, String> {
        Self::decode(
            catalog,
            data,
            &crate::checkpoint_store::read_named(dir, "journey.chk", 16384)?,
        )
    }
}
fn catalog_hash(c: &Catalog) -> u64 {
    checksum(format!("{:?}", c.profiles()).as_bytes())
}
fn put_army(b: &mut Vec<u8>, army: &[Stack; 6]) {
    for s in army {
        let id = s.unit.map(|u| u.to_string()).unwrap_or_default();
        b.push(id.len() as u8);
        b.extend(id.as_bytes());
        b.extend(s.count.to_le_bytes());
    }
}
struct Reader<'b> {
    b: &'b [u8],
    at: usize,
}
#[cfg(test)]
#[path = "journey_tests.rs"]
mod tests;
impl<'b> Reader<'b> {
    fn take(&mut self, n: usize) -> Result<&'b [u8], String> {
        let end = self.at.checked_add(n).ok_or("旅程長度超界")?;
        let out = self.b.get(self.at..end).ok_or("旅程資料截斷")?;
        self.at = end;
        Ok(out)
    }
    fn byte(&mut self) -> Result<u8, String> {
        Ok(self.take(1)?[0])
    }
    fn q(&mut self) -> Result<u64, String> {
        Ok(u64::from_le_bytes(self.take(8)?.try_into().unwrap()))
    }
    fn army(&mut self) -> Result<[Stack; 6], String> {
        let mut a = [Stack::default(); 6];
        for s in &mut a {
            let n = usize::from(self.byte()?);
            if n > 16 {
                return Err("旅程ID過長".into());
            }
            let unit = if n == 0 {
                None
            } else {
                Some(UnitId::parse(
                    std::str::from_utf8(self.take(n)?).map_err(|_| "旅程ID編碼錯誤")?,
                )?)
            };
            *s = Stack {
                unit,
                count: u32::from_le_bytes(self.take(4)?.try_into().unwrap()),
            };
        }
        Ok(a)
    }
}
