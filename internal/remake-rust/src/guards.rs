//! Spec031: persistent original65 guard records and sub12DDE/sub11ABE.
use crate::{
    battle::{Outcome, Side, Stack},
    catalog::{Catalog, UnitId},
    controller::{Checkpoint, Controller, EnemyConfig, OriginalRng, ViewState},
    journey::{Journey, army_ok, compact},
    media_assets::checksum,
    spells::SpellBook,
    world::{Position, WorldData, motion},
};
pub const SUFFIX: usize = 1286;
#[derive(Clone, Copy, Debug)]
pub struct Site {
    pub area: u8,
    pub index: u8,
    pub position: Position,
    pub boss: bool,
    pub final_guard: bool,
    pub initial: [Stack; 6],
}
pub fn sites() -> &'static [Site; 42] {
    static S: std::sync::OnceLock<[Site; 42]> = std::sync::OnceLock::new();
    S.get_or_init(|| {
        include_str!("../guard-catalog.tsv")
            .lines()
            .filter(|s| !s.starts_with('#'))
            .map(|l| {
                let v: Vec<u16> = l
                    .split('\t')
                    .map(|s| s.parse().expect("fixed guard table"))
                    .collect();
                assert_eq!(v.len(), 19);
                let mut initial = [Stack::default(); 6];
                for (i, row) in initial.iter_mut().enumerate() {
                    if v[7 + 2 * i] > 0 {
                        *row = Stack {
                            unit: Some(
                                UnitId::parse(&format!("native:{:02}", v[7 + 2 * i]))
                                    .expect("fixed guard unit"),
                            ),
                            count: u32::from(v[8 + 2 * i]),
                        };
                    }
                }
                Site {
                    area: v[0] as u8,
                    index: v[1] as u8,
                    position: Position {
                        x: v[2] as u8,
                        y: v[3] as u8,
                    },
                    boss: v[4] == 1,
                    final_guard: v[5] == 1,
                    initial,
                }
            })
            .collect::<Vec<_>>()
            .try_into()
            .expect("42 original guards")
    })
}
pub fn fingerprint() -> u64 {
    checksum(include_str!("../guard-catalog.tsv").as_bytes())
}
/// PAM sub12856: signed word growth, original SLOT cap, then minimum ten.
/// Counts above 24575 intentionally wrap before the signed comparison.
pub fn monthly_growth(count: u32, cap: u32) -> Result<u32, String> {
    if count > 32767 || cap > 32767 {
        return Err("守軍月結超出原word已驗域".into());
    }
    if count == 0 {
        return Ok(0);
    }
    let next = (count as u16).wrapping_add((count / 3) as u16) as i16;
    Ok(next.min(cap as i16).max(10) as u32)
}
pub fn retreat_loss(gold: u64, roll: u16) -> u64 {
    gold / (u64::from(roll) / 2730 + 3)
}
pub fn validate_maps(d: &WorldData) -> Result<(), String> {
    for area in 0..8 {
        let mut i = 0;
        for y in 0..80 {
            for x in 0..70 {
                let p = Position { x, y };
                if d.tile(area, p)? == 65 {
                    if !sites()
                        .iter()
                        .any(|s| s.area == area && s.index == i && s.position == p)
                    {
                        return Err("原圖守軍順序不符".into());
                    }
                    i += 1;
                }
            }
        }
        if usize::from(i) != sites().iter().filter(|s| s.area == area).count() {
            return Err("原圖守軍數量不符".into());
        }
    }
    Ok(())
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub enum Stage {
    Prompt,
    Battle,
    Cleared,
    NoArmy,
    Missing,
    Win,
    Retreat,
    Refused,
}
impl Stage {
    pub fn decode(v: u8) -> Result<Self, String> {
        Ok(match v {
            0 => Self::Prompt,
            1 => Self::Battle,
            2 => Self::Cleared,
            3 => Self::NoArmy,
            4 => Self::Missing,
            5 => Self::Win,
            6 => Self::Retreat,
            7 => Self::Refused,
            _ => return Err("守軍階段錯誤".into()),
        })
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Pending {
    pub site: u8,
    pub key: u16,
    pub stage: Stage,
    pub yes: bool,
    pub before: [u64; 6],
    pub reward_seed: u32,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Guards {
    pub rows: [[Stack; 6]; 42],
    pub swords: [bool; 8],
    pub pending: Option<Pending>,
    pub ending: Option<crate::ending::Progress>,
}
impl Default for Guards {
    fn default() -> Self {
        Self {
            rows: sites().map(|s| s.initial),
            swords: [false; 8],
            pending: None,
            ending: None,
        }
    }
}
pub fn reward(
    mut before: [u64; 6],
    area: u8,
    book: bool,
    outcome: Outcome,
    rng: &mut OriginalRng,
) -> Result<[u64; 6], String> {
    if area >= 8 || before.iter().any(|n| *n > 30000) || !(1..=5).contains(&before[0]) {
        return Err("守軍獎勵輸入錯誤".into());
    }
    match outcome {
        Outcome::Win => {
            before[2] = (before[2] + 20 * (u64::from(area) + 1)).min(30000);
            if book {
                before[5] = (before[5] + u64::from(area) + 1).min(30000);
            }
        }
        Outcome::Retreat => {
            before[3] -= retreat_loss(before[3], rng.next15());
        }
        Outcome::Loss => {}
    }
    Ok(before)
}
impl Guards {
    pub(crate) fn refill_monthly(&mut self) -> Result<(), String> {
        let mut rows = self.rows;
        for (i, row) in rows.iter_mut().enumerate() {
            for (slot, stack) in row.iter_mut().enumerate() {
                stack.count = monthly_growth(stack.count, sites()[i].initial[slot].count)?;
            }
        }
        self.rows = rows;
        Ok(())
    }
    pub(crate) fn validate(&self, j: &Journey<'_>, d: &WorldData) -> Result<(), String> {
        for (i, rows) in self.rows.iter().enumerate() {
            if !army_ok(rows, true)
                || rows.iter().any(|r| {
                    r.unit.is_some() && !sites()[i].initial.iter().any(|s| s.unit == r.unit)
                })
            {
                return Err("守軍種類或兵數錯誤".into());
            }
        }
        if let Some(ending) = self.ending {
            let final_site = sites()
                .iter()
                .position(|s| s.final_guard)
                .ok_or("缺少最終守軍")?;
            let site = sites()[final_site];
            if ending.elapsed_ms > crate::ending::DURATION
                || !self.swords.iter().all(|v| *v)
                || self.rows[final_site].iter().any(|r| r.count > 0)
                || j.world.area != site.area
                || j.world.position != site.position
                || !matches!(j.world.facing, 1 | 3)
                || self.pending.is_some()
                || j.battle.is_some()
                || j.cue.is_some()
                || j.enemy != [Stack::default(); 6]
                || j.generation_seed != 0
                || j.enemy_first
                || j.camps.pending.is_some()
                || j.month.pending.is_some()
                || j.treasure.pending.is_some()
                || j.magic.shop.is_some()
                || j.magic.direction
                || j.resource_notice.is_some()
                || j.survey.bird
                || j.theft.is_some()
                || j.map_notice.is_some()
                || j.travel_spell.teleport.is_some()
                || j.travel_spell.shore.is_some()
                || j.travel_spell.refused_shop.is_some()
                || matches!(j.travel_spell.jump, crate::jump_spell::Jump::Flying { .. })
            {
                return Err("結局與最終戰果不符".into());
            }
            return Ok(());
        }
        let Some(p) = self.pending else { return Ok(()) };
        let site = sites().get(usize::from(p.site)).ok_or("守軍索引超界")?;
        if (!crate::jump_spell::DIRECTIONS.contains(&p.key) && p.key != 0x3920)
            || p.before.iter().any(|n| *n > 30000)
            || !(1..=5).contains(&p.before[0])
        {
            return Err("守軍來源錯誤".into());
        }
        let pos = if p.stage == Stage::Refused {
            if j.world.boat != 2 || !matches!(d.tile(j.world.area, j.world.position)?, 2 | 11..=14)
            {
                return Err("拒絕守軍上岸來源錯誤".into());
            }
            motion(j.world.position, p.key, j.world.facing, false)?.0
        } else {
            j.world.position
        };
        if j.world.area != site.area
            || pos != site.position
            || d.tile(site.area, pos)? != 65
            || !matches!(j.world.facing, 1 | 3)
            || (p.key != 0x3920
                && motion(j.world.position, p.key, j.world.facing, false)?.1 != j.world.facing)
            || j.cue.is_some()
            || j.theft.is_some()
            || j.map_notice.is_some()
            || j.camps.pending.is_some()
            || j.month.pending.is_some()
            || j.treasure.pending.is_some()
            || j.magic.direction
            || j.magic.shop.is_some()
            || j.resource_notice.is_some()
            || j.survey.bird
            || j.travel_spell.shore.is_some()
            || j.travel_spell.teleport.is_some()
            || j.travel_spell.refused_shop.is_some()
            || matches!(j.travel_spell.jump, crate::jump_spell::Jump::Flying { .. })
        {
            return Err("守軍位置或互斥階段不符".into());
        }
        let alive = self.rows[usize::from(p.site)][0].count > 0;
        match p.stage {
            Stage::Battle => {
                if (site.final_guard && !self.swords.iter().all(|v| *v))
                    || !alive
                    || j.battle.is_none()
                    || j.enemy != self.rows[usize::from(p.site)]
                    || j.enemy_first
                    || j.generation_seed != 0
                    || j.resources != p.before
                {
                    return Err("守軍戰中綁定錯誤".into());
                }
            }
            Stage::Win | Stage::Retreat => {
                let mut rng = OriginalRng {
                    seed: p.reward_seed,
                };
                let expected = reward(
                    p.before,
                    site.area,
                    j.magic.book,
                    if p.stage == Stage::Win {
                        Outcome::Win
                    } else {
                        Outcome::Retreat
                    },
                    &mut rng,
                )?;
                if (site.final_guard && p.stage == Stage::Win)
                    || j.resources != expected
                    || rng != j.world.rng
                    || j.battle.is_some()
                    || (p.stage == Stage::Win && alive)
                    || (p.stage == Stage::Retreat && (!alive || j.army[0].count == 0))
                    || (p.stage == Stage::Win && site.boss && !self.swords[usize::from(site.area)])
                {
                    return Err("守軍待確認戰果錯誤".into());
                }
            }
            _ => {
                if j.battle.is_some()
                    || j.resources != p.before
                    || j.world.rng.seed != p.reward_seed
                {
                    return Err("守軍提示已變動".into());
                }
                if (p.stage == Stage::Cleared && alive)
                    || (p.stage == Stage::Prompt && !alive)
                    || (p.stage == Stage::NoArmy && (!alive || j.army[0].count > 0))
                    || (p.stage == Stage::Missing
                        && (!site.final_guard || self.swords.iter().all(|s| *s)))
                {
                    return Err("守軍提示條件錯誤".into());
                }
            }
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    pub(crate) fn open_guard(
        &mut self,
        d: &WorldData,
        key: u16,
        c: &Catalog,
    ) -> Result<(), String> {
        if self.phase() != "world" {
            return Err("目前不能攻城".into());
        }
        let mut s = self.clone();
        s.world = s.world.event_step(d, key, 65)?;
        let i = sites()
            .iter()
            .position(|v| v.area == s.world.area && v.position == s.world.position)
            .ok_or("缺少原守軍")?;
        if !matches!(s.world.facing, 1 | 3) {
            s.finish_guard_tail(d, key, c, false)?;
        } else {
            s.world.reveal();
            s.guards.pending = Some(Pending {
                site: i as u8,
                key,
                stage: if s.guards.rows[i][0].count == 0 {
                    Stage::Cleared
                } else {
                    Stage::Prompt
                },
                yes: true,
                before: s.resources,
                reward_seed: s.world.rng.seed,
            });
            s.guards.validate(&s, d)?;
        }
        *self = s;
        Ok(())
    }
    pub fn select_guard(&mut self, yes: bool) -> Result<(), String> {
        let p = self.guards.pending.as_mut().ok_or("沒有守軍選擇")?;
        if p.stage != Stage::Prompt {
            return Err("不在攻城確認".into());
        }
        p.yes = yes;
        Ok(())
    }
    pub fn choose_guard(&mut self, d: &WorldData, c: &'a Catalog, yes: bool) -> Result<(), String> {
        self.guards.validate(self, d)?;
        let p = self.guards.pending.ok_or("沒有守軍確認")?;
        if p.stage != Stage::Prompt {
            return Err("不在攻城確認".into());
        }
        if !yes {
            return self.close_guard(d, c);
        }
        let mut s = self.clone();
        let site = sites()[usize::from(p.site)];
        if site.final_guard && !s.guards.swords.iter().all(|n| *n) {
            s.guards.pending.as_mut().unwrap().stage = Stage::Missing;
        } else if s.army[0].count == 0 {
            s.guards.pending.as_mut().unwrap().stage = Stage::NoArmy;
        } else {
            let enemies = s.guards.rows[usize::from(p.site)];
            let book = s
                .army
                .iter()
                .any(|r| r.unit.is_some_and(UnitId::is_native_caster))
                .then_some(SpellBook {
                    enabled: false,
                    charges: [0; 8],
                    stat_26b0: u16::from(s.has_item(3)),
                    stat_26ae: u16::from(s.has_item(2)),
                });
            let scenario = if book.is_some() { 10 } else { 8 };
            s.battle = Some(Checkpoint {
                controller: Controller::with_enemy_spells(
                    c,
                    [s.army, enemies],
                    Side::Player,
                    s.item_modifiers(),
                    book,
                    EnemyConfig {
                        stat_26ae: u16::from(s.has_item(2)),
                        shifted_alias: 0,
                    },
                )
                .and_then(|c| c.with_rule_mode(s.rules))
                .map_err(|e| format!("{e:?}"))?,
                rng: s.world.rng,
                view: ViewState {
                    font: s.world.font,
                    music: s.world.music,
                    scenario,
                    ..ViewState::default()
                },
            });
            s.enemy = enemies;
            s.guards.pending.as_mut().unwrap().stage = Stage::Battle;
        }
        s.guards.validate(&s, d)?;
        *self = s;
        Ok(())
    }
    pub(crate) fn finish_guard_tail(
        &mut self,
        d: &WorldData,
        key: u16,
        c: &Catalog,
        blocked: bool,
    ) -> Result<(), String> {
        let view = self.magic.view(d)?;
        if !blocked && key != 0x3920 && self.world.remaining == 1 {
            let tile = view.tile(self.world.area, self.world.position)?;
            self.begin_month(c, &view, tile)?;
        } else {
            if !blocked && key != 0x3920 {
                self.world.remaining -= 1;
            }
            self.run_encounter_tail(&view)?;
        }
        Ok(())
    }
    pub fn close_guard(&mut self, d: &WorldData, c: &Catalog) -> Result<(), String> {
        self.guards.validate(self, d)?;
        let p = self.guards.pending.ok_or("沒有守軍提示")?;
        if p.stage == Stage::Battle {
            return Err("戰鬥尚未完成".into());
        }
        let mut s = self.clone();
        s.guards.pending = None;
        s.finish_guard_tail(d, p.key, c, p.stage == Stage::Refused)?;
        *self = s;
        Ok(())
    }
    pub(crate) fn finish_guard_battle(
        &mut self,
        c: &Catalog,
        d: &WorldData,
        origin: Option<bool>,
    ) -> Result<Outcome, String> {
        self.guards.validate(self, d)?;
        let mut s = self.clone();
        let mut p = s.guards.pending.ok_or("沒有守軍戰鬥")?;
        if p.stage != Stage::Battle {
            return Err("不在守軍戰場".into());
        }
        let cp = s.battle.as_ref().ok_or("缺少戰場")?;
        let outcome = cp.controller.battle().outcome().ok_or("戰鬥未完成")?;
        if (outcome == Outcome::Loss) != origin.is_some() {
            return Err("全滅須選去向".into());
        }
        let rows = *cp.controller.battle().rows();
        s.army = compact(rows[0]);
        s.guards.rows[usize::from(p.site)] = compact(rows[1]);
        s.world.rng = cp.rng;
        s.world.font = cp.view.font;
        s.world.music = cp.view.music;
        p.reward_seed = s.world.rng.seed;
        let site = sites()[usize::from(p.site)];
        let final_win = site.final_guard && outcome == Outcome::Win;
        if !final_win {
            s.resources = reward(
                p.before,
                s.world.area,
                s.magic.book,
                outcome,
                &mut s.world.rng,
            )?;
        }
        if outcome == Outcome::Win && site.boss {
            s.guards.swords[usize::from(site.area)] = true;
        }
        s.battle = None;
        s.enemy = [Stack::default(); 6];
        s.generation_seed = 0;
        s.enemy_first = false;
        s.battles = s.battles.checked_add(1).ok_or("戰鬥次數超界")?;
        if final_win {
            s.guards.pending = None;
            s.guards.ending = Some(crate::ending::Progress::default());
            s.guards.validate(&s, d)?;
        } else if outcome == Outcome::Loss {
            s.guards.pending = None;
            if origin == Some(true) {
                let old = s.world.area;
                s.magic.bridges.retain(|at| {
                    usize::from(*at) / 5600 != usize::from(old) && usize::from(*at) / 5600 != 0
                });
                s.world.area = 0;
                s.world.position = d.starts[0];
                s.world.facing = 3;
                s.world.boat = 0;
            }
            s.world.reveal();
            s.finish_guard_tail(d, p.key, c, false)?;
        } else {
            p.stage = if outcome == Outcome::Win {
                Stage::Win
            } else {
                Stage::Retreat
            };
            s.guards.pending = Some(p);
            s.guards.validate(&s, d)?;
        }
        *self = s;
        Ok(outcome)
    }
}
pub fn sword_names() -> [&'static str; 8] {
    [
        "掩 日 劍",
        "斷 水 劍",
        "轉 魄 劍",
        "驚 霓 劍",
        "滅 魂 劍",
        "卻 邪 劍",
        "真 剛 劍",
        "大 限 劍",
    ]
}
#[cfg(test)]
#[path = "guards_tests.rs"]
mod tests;
