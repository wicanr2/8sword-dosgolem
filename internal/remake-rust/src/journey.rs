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
pub(crate) fn compact(rows: [Stack; 6]) -> [Stack; 6] {
    let mut out = [Stack::default(); 6];
    for (i, s) in rows.into_iter().filter(|s| s.count > 0).enumerate() {
        out[i] = s;
    }
    out
}
pub(crate) fn army_ok(rows: &[Stack; 6], native: bool) -> bool {
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
    pub month: crate::monthly::Monthly,
    pub treasure: crate::treasure::Treasure,
    pub magic: crate::world_magic::Magic,
    pub resource_notice: Option<crate::resource_spells::Notice>,
    pub survey: crate::survey_spells::Survey,
    pub travel_spell: crate::travel_spells::Travel,
    pub theft: Option<crate::theft::Theft>,
    pub map_notice: Option<crate::map_notice::Notice>,
    pub guards: crate::guards::Guards,
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
            month: crate::monthly::Monthly::default(),
            treasure: crate::treasure::Treasure::default(),
            magic: crate::world_magic::Magic::default(),
            resource_notice: None,
            survey: crate::survey_spells::Survey::default(),
            travel_spell: crate::travel_spells::Travel::default(),
            theft: None,
            map_notice: None,
            guards: crate::guards::Guards::default(),
        }
    }
    pub fn phase(&self) -> &'static str {
        if self
            .guards
            .pending
            .is_some_and(|p| p.stage != crate::guards::Stage::Battle)
        {
            return "guard";
        }
        if self.map_notice.is_some() {
            return "map-notice";
        }
        if self.theft.is_some() {
            return "theft";
        }
        if matches!(
            self.travel_spell.jump,
            crate::jump_spell::Jump::Flying { .. }
        ) && self.cue.is_none()
            && self.battle.is_none()
        {
            "jump-flight"
        } else if self.travel_spell.shore.is_some() {
            "shore"
        } else if self.travel_spell.teleport.is_some() {
            "teleport"
        } else if self.survey.bird {
            "birdseye"
        } else if self.resource_notice.is_some() {
            "resource-result"
        } else if self.magic.direction {
            "bridge-direction"
        } else if self.magic.shop.is_some() {
            "magic-shop"
        } else if self.treasure.pending.is_some() {
            "treasure"
        } else if self.month.pending.is_some() {
            "monthly"
        } else if self.battle.is_some() {
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
        if self.guards.pending.is_some()
            || self.map_notice.is_some()
            || self.theft.is_some()
            || self.cue.is_some()
            || self.battle.is_some()
            || self.camps.pending.is_some()
            || self.month.pending.is_some()
            || self.treasure.pending.is_some()
            || self.magic.direction
            || self.magic.shop.is_some()
            || self.resource_notice.is_some()
            || self.survey.bird
            || self.travel_spell.teleport.is_some()
            || self.travel_spell.shore.is_some()
            || matches!(
                self.travel_spell.jump,
                crate::jump_spell::Jump::Flying { .. }
            )
        {
            return Err("遭遇尚未完成".into());
        }
        match self.world.walk_encounter(data, key)? {
            WalkResult::Boundary(Boundary::Encounter(c)) => {
                self.receive_encounter(c)?;
                Ok(None)
            }
            WalkResult::Boundary(Boundary::Terrain(tile @ 54..=58)) => {
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
                    self.world.rng.next15(); // Original125A8..125D8 discarded entry roll.
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
        if self
            .guards
            .pending
            .is_some_and(|p| p.stage == crate::guards::Stage::Battle)
        {
            return self.finish_guard_battle(catalog, data, origin);
        }
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
        if matches!(s.travel_spell.jump, crate::jump_spell::Jump::Flying { .. })
            && crate::jump_spell::landable(s.jump_tile(&s.magic.view(data)?, s.world.position)?)
        {
            s.travel_spell.jump = crate::jump_spell::Jump::Idle;
        }
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
        self.guards.validate(self, data)?;
        if let Some(n) = self.map_notice {
            n.validate(self, data)?;
        }
        if let Some(n) = self.theft {
            n.validate(self)?;
        }
        self.travel_spell.validate(self)?;
        self.survey.validate(self)?;
        if let Some(n) = &self.resource_notice {
            n.validate(self, catalog)?;
        }
        self.magic.validate(self, data)?;
        let view = self.magic.view(data)?;
        self.validate_jump(&view)?;
        if let Some(p) = self.travel_spell.shore {
            if !self.supported_shore(&view, p.key)?
                || self.world.prepare_shore(&view, p.key)? != self.world
            {
                return Err("上岸待選落點不符".into());
            }
        }
        self.world.encode(data)?;
        self.camps.validate(catalog)?;
        self.month.validate(self, catalog, &view)?;
        self.treasure.validate(self, data)?;
        if let Some(i) = self.camps.pending {
            let c = camps()[i];
            if self.battle.is_some()
                || self.cue.is_some()
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
            let guarded = self
                .guards
                .pending
                .is_some_and(|p| p.stage == crate::guards::Stage::Battle);
            if (!guarded && self.cue.is_none())
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
            if !guarded
                && (generate(self.world.area, self.world.rank, &mut rng)? != self.enemy
                    || rng != self.world.rng)
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
        let mut b = b"8SJRN014".to_vec();
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
        b.extend(crate::monthly::fingerprint().to_le_bytes());
        b.extend(self.month.months.to_le_bytes());
        b.push(u8::from(self.month.pending.is_some()));
        if let Some(r) = &self.month.pending {
            let m = r.budget;
            for n in [m.before, m.income, m.due, m.charged, m.after] {
                b.extend(n.to_le_bytes());
            }
            b.extend([u8::from(m.disbanded), r.tile]);
            put_army(&mut b, &r.army_before);
        }
        b.extend(crate::treasure::fingerprint().to_le_bytes());
        for n in self.treasure.amounts {
            b.extend(n.to_le_bytes());
        }
        b.push(u8::from(self.treasure.pending.is_some()));
        if let Some(p) = self.treasure.pending {
            b.extend([p.index, p.choice, u8::from(p.moved)]);
        }
        b.extend(crate::world_magic::fingerprint().to_le_bytes());
        b.extend([
            u8::from(self.magic.book),
            self.magic.selected,
            u8::from(self.magic.direction),
        ]);
        for n in self.magic.charges {
            b.extend(n.to_le_bytes());
        }
        b.extend([
            self.magic.shop.map(|p| p.index).unwrap_or(255),
            u8::from(self.magic.shop.is_some_and(|p| p.moved)),
        ]);
        b.extend((self.magic.bridges.len() as u16).to_le_bytes());
        for n in &self.magic.bridges {
            b.extend(n.to_le_bytes());
        }
        b.push(u8::from(self.resource_notice.is_some()));
        if let Some(n) = &self.resource_notice {
            b.push(n.spell);
            b.extend(n.seed_before.to_le_bytes());
            b.extend(n.gold_before.to_le_bytes());
            b.extend(n.uses_before.to_le_bytes());
            put_army(&mut b, &n.army_before);
        }
        b.extend([
            u8::from(self.survey.stopped),
            self.survey.tempo,
            u8::from(self.survey.bird),
        ]);
        b.push(self.travel_spell.teleport.unwrap_or(255));
        let shore = self.travel_spell.shore;
        b.extend(shore.map_or(0, |p| p.key).to_le_bytes());
        b.push(u8::from(shore.is_some_and(|p| p.yes)));
        let (flag, key) = match self.travel_spell.jump {
            crate::jump_spell::Jump::Idle => (0, 0u16),
            crate::jump_spell::Jump::Ready => (1, 0),
            crate::jump_spell::Jump::Flying { key } => (2, key),
        };
        b.push(flag);
        b.extend(key.to_le_bytes());
        b.extend(self.travel_spell.refused_shop.unwrap_or(0).to_le_bytes());
        b.push(u8::from(self.theft.is_some()));
        if let Some(n) = self.theft {
            b.push(n.cue);
            b.extend(n.seed_before.to_le_bytes());
            b.extend(n.gold_before.to_le_bytes());
        }
        b.push(u8::from(self.map_notice.is_some()));
        if let Some(n) = self.map_notice {
            b.push(n.site);
            b.extend(n.key.to_le_bytes());
        }
        b.extend(crate::guards::fingerprint().to_le_bytes());
        for rows in &self.guards.rows {
            for row in rows {
                b.push(row.unit.and_then(UnitId::native_kind).unwrap_or(0) as u8);
                b.extend(row.count.to_le_bytes());
            }
        }
        b.extend(self.guards.swords.map(u8::from));
        b.push(self.guards.pending.map(|p| p.site).unwrap_or(255));
        if let Some(p) = self.guards.pending {
            b.extend(p.key.to_le_bytes());
            b.extend([p.stage as u8, u8::from(p.yes)]);
            for v in p.before {
                b.extend(v.to_le_bytes());
            }
            b.extend(p.reward_seed.to_le_bytes());
        }
        b.extend(checksum(&b).to_le_bytes());
        if b.len() > 131072 {
            return Err("旅程檢查點過大".into());
        }
        Ok(b)
    }
    pub fn decode(catalog: &'a Catalog, data: &WorldData, b: &[u8]) -> Result<Self, String> {
        if b.len() < 5730
            || b.len() > 131072
            || (&b[..8] != b"8SJRN001"
                && &b[..8] != b"8SJRN002"
                && &b[..8] != b"8SJRN003"
                && &b[..8] != b"8SJRN004"
                && &b[..8] != b"8SJRN005"
                && &b[..8] != b"8SJRN006"
                && &b[..8] != b"8SJRN007"
                && &b[..8] != b"8SJRN008"
                && &b[..8] != b"8SJRN009"
                && &b[..8] != b"8SJRN010"
                && &b[..8] != b"8SJRN011"
                && &b[..8] != b"8SJRN012"
                && &b[..8] != b"8SJRN013"
                && &b[..8] != b"8SJRN014")
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
        if &b[..8] != b"8SJRN001" {
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
        let mut month = crate::monthly::Monthly::default();
        if &b[..8] >= b"8SJRN003" {
            if r.q()? != crate::monthly::fingerprint() {
                return Err("補貨上限版本不符".into());
            }
            month.months = r.q()?;
            match r.byte()? {
                0 => {}
                1 => {
                    let before = r.q()?;
                    let income = r.q()?;
                    let due = r.q()?;
                    let charged = r.q()?;
                    let after = r.q()?;
                    let disbanded = match r.byte()? {
                        0 => false,
                        1 => true,
                        _ => return Err("月報旗標錯誤".into()),
                    };
                    let tile = r.byte()?;
                    let army_before = r.army()?;
                    month.pending = Some(crate::monthly::Report {
                        budget: crate::monthly::Budget {
                            before,
                            income,
                            due,
                            charged,
                            after,
                            disbanded,
                        },
                        tile,
                        army_before,
                    });
                }
                _ => return Err("月報狀態錯誤".into()),
            }
        }
        let mut treasure = crate::treasure::Treasure::default();
        if &b[..8] >= b"8SJRN004" {
            if r.q()? != crate::treasure::fingerprint() {
                return Err("寶箱資料版本不符".into());
            }
            for n in &mut treasure.amounts {
                *n = u16::from_le_bytes(r.take(2)?.try_into().unwrap());
            }
            match r.byte()? {
                0 => {}
                1 => {
                    let index = r.byte()?;
                    let choice = r.byte()?;
                    let moved = match r.byte()? {
                        0 => false,
                        1 => true,
                        _ => return Err("寶箱移動旗標錯誤".into()),
                    };
                    treasure.pending = Some(crate::treasure::Pending {
                        index,
                        choice,
                        moved,
                    });
                }
                _ => return Err("寶箱階段錯誤".into()),
            }
        }
        let mut magic = crate::world_magic::Magic::default();
        if &b[..8] >= b"8SJRN005" {
            if r.q()? != crate::world_magic::fingerprint() {
                return Err("世界法術資料版本不符".into());
            }
            let flag = |v: u8| match v {
                0 => Ok(false),
                1 => Ok(true),
                _ => Err("法術旗標錯誤".to_string()),
            };
            magic.book = flag(r.byte()?)?;
            magic.selected = r.byte()?;
            magic.direction = flag(r.byte()?)?;
            for n in &mut magic.charges {
                *n = u16::from_le_bytes(r.take(2)?.try_into().unwrap());
            }
            let shop = r.byte()?;
            let moved = flag(r.byte()?)?;
            if shop != 255 {
                magic.shop = Some(crate::world_magic::PendingShop { index: shop, moved });
            } else if moved {
                return Err("空商店移動旗標錯誤".into());
            }
            let n = u16::from_le_bytes(r.take(2)?.try_into().unwrap());
            for _ in 0..n {
                magic
                    .bridges
                    .push(u16::from_le_bytes(r.take(2)?.try_into().unwrap()));
            }
        }
        let resource_notice = if &b[..8] >= b"8SJRN006" {
            match r.byte()? {
                0 => None,
                1 => Some(crate::resource_spells::Notice {
                    spell: r.byte()?,
                    seed_before: u32::from_le_bytes(r.take(4)?.try_into().unwrap()),
                    gold_before: r.q()?,
                    uses_before: u16::from_le_bytes(r.take(2)?.try_into().unwrap()),
                    army_before: r.army()?,
                }),
                _ => return Err("法術結果旗標錯誤".into()),
            }
        } else {
            None
        };
        let mut survey = crate::survey_spells::Survey::default();
        if &b[..8] >= b"8SJRN007" {
            survey.stopped = match r.byte()? {
                0 => false,
                1 => true,
                _ => return Err("停時旗標錯誤".into()),
            };
            survey.tempo = r.byte()?;
            survey.bird = match r.byte()? {
                0 => false,
                1 => true,
                _ => return Err("鳥瞰旗標錯誤".into()),
            };
        }
        let mut travel_spell = crate::travel_spells::Travel {
            refused_shop: None,
            shore: None,
            jump: crate::jump_spell::Jump::Idle,
            teleport: if &b[..8] >= b"8SJRN008" {
                match r.byte()? {
                    255 => None,
                    n if n < 8 => Some(n),
                    _ => return Err("傳送區域錯誤".into()),
                }
            } else {
                None
            },
        };
        if &b[..8] >= b"8SJRN009" {
            let key = u16::from_le_bytes(r.take(2)?.try_into().unwrap());
            let yes = match r.byte()? {
                0 => false,
                1 => true,
                _ => return Err("上岸選擇錯誤".into()),
            };
            if key == 0 {
                if yes {
                    return Err("空上岸仍有選擇".into());
                }
            } else {
                travel_spell.shore = Some(crate::travel_spells::Shore { key, yes });
            }
        }
        if &b[..8] >= b"8SJRN010" {
            let flag = r.byte()?;
            let key = u16::from_le_bytes(r.take(2)?.try_into().unwrap());
            travel_spell.jump = match (flag, key) {
                (0, 0) => crate::jump_spell::Jump::Idle,
                (1, 0) => crate::jump_spell::Jump::Ready,
                (2, key) if crate::jump_spell::DIRECTIONS.contains(&key) => {
                    crate::jump_spell::Jump::Flying { key }
                }
                _ => return Err("跳躍保存欄位錯誤".into()),
            };
        }
        if &b[..8] >= b"8SJRN011" {
            let key = u16::from_le_bytes(r.take(2)?.try_into().unwrap());
            if key != 0 {
                travel_spell.refused_shop = Some(key);
            }
        }
        let theft = if &b[..8] >= b"8SJRN012" {
            match r.byte()? {
                0 => None,
                1 => Some(crate::theft::Theft {
                    cue: r.byte()?,
                    seed_before: u32::from_le_bytes(r.take(4)?.try_into().unwrap()),
                    gold_before: u16::from_le_bytes(r.take(2)?.try_into().unwrap()),
                }),
                _ => return Err("遇劫保存旗標錯誤".into()),
            }
        } else {
            None
        };
        let map_notice = if &b[..8] >= b"8SJRN013" {
            match r.byte()? {
                0 => None,
                1 => Some(crate::map_notice::Notice {
                    site: r.byte()?,
                    key: u16::from_le_bytes(r.take(2)?.try_into().unwrap()),
                }),
                _ => return Err("地圖提示旗標錯誤".into()),
            }
        } else {
            None
        };
        let mut guards = crate::guards::Guards::default();
        if &b[..8] >= b"8SJRN014" {
            if r.q()? != crate::guards::fingerprint() {
                return Err("守軍資料版本不符".into());
            }
            for rows in &mut guards.rows {
                for row in rows {
                    let kind = r.byte()?;
                    if kind > 25 {
                        return Err("守軍ID超界".into());
                    }
                    *row = Stack {
                        unit: if kind == 0 {
                            None
                        } else {
                            Some(UnitId::parse(&format!("native:{kind:02}"))?)
                        },
                        count: u32::from_le_bytes(r.take(4)?.try_into().unwrap()),
                    };
                }
            }
            for flag in &mut guards.swords {
                *flag = match r.byte()? {
                    0 => false,
                    1 => true,
                    _ => return Err("劍旗標錯誤".into()),
                };
            }
            let site = r.byte()?;
            if site != 255 {
                let key = u16::from_le_bytes(r.take(2)?.try_into().unwrap());
                let stage = crate::guards::Stage::decode(r.byte()?)?;
                let yes = match r.byte()? {
                    0 => false,
                    1 => true,
                    _ => return Err("攻城選擇錯誤".into()),
                };
                let mut before = [0; 6];
                for v in &mut before {
                    *v = r.q()?;
                }
                let reward_seed = u32::from_le_bytes(r.take(4)?.try_into().unwrap());
                guards.pending = Some(crate::guards::Pending {
                    site,
                    key,
                    stage,
                    yes,
                    before,
                    reward_seed,
                });
            }
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
            month,
            treasure,
            magic,
            resource_notice,
            survey,
            travel_spell,
            theft,
            map_notice,
            guards,
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
            131072,
            |b| Self::decode(catalog, data, b).map(|_| ()),
            false,
        )
    }
    pub fn load(dir: &Path, catalog: &'a Catalog, data: &WorldData) -> Result<Self, String> {
        Self::decode(
            catalog,
            data,
            &crate::checkpoint_store::read_named(dir, "journey.chk", 131072)?,
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
