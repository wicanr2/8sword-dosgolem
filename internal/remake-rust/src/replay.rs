use crate::battle::{Battle, Modifiers, Outcome, Rows, Side, Stack};
use crate::catalog::{Catalog, UnitId};
use crate::formation::{initial_formation, motion_plan, sort_plan};
use std::str::FromStr;

pub fn parse_rows(text: &str) -> Result<[Stack; 6], String> {
    let values: Vec<_> = text
        .split(',')
        .map(|entry| {
            let (id, amount) = entry.split_once('=').ok_or("軍隊欄位無效")?;
            let count: u32 = amount.parse().map_err(|_| "兵數無效")?;
            let unit = if id == "-" {
                None
            } else {
                Some(UnitId::parse(id)?)
            };
            if unit.is_none() && count != 0 {
                return Err("空兵種不可有兵數".into());
            }
            Ok(Stack { unit, count })
        })
        .collect::<Result<_, String>>()?;
    values.try_into().map_err(|_| "軍隊必須有六列".into())
}

pub fn check_spells(catalog: &Catalog, text: &str) -> Result<(usize, usize), String> {
    use crate::controller::{Controller, OriginalRng};
    use crate::spells::{Spell, SpellBook, SpellEffect};
    let mut models = 0;
    let mut cases = 0;
    let mut effects: Vec<SpellEffect> = Vec::new();
    let mut at = 0;
    for (number, line) in text.lines().enumerate() {
        if line.starts_with('#') || line.trim().is_empty() {
            continue;
        }
        let f: Vec<_> = line.split('\t').collect();
        let bad = || format!("法術參考第{}行不符", number + 1);
        let n = |i: usize| f[i].parse::<u64>().map_err(|_| bad());
        match f[0] {
            "AMOUNT" if f.len() == 9 => {
                let spell = *Spell::ALL.get(n(1)? as usize).ok_or_else(bad)?;
                let actual = crate::spells::amount(
                    spell,
                    n(2)? as u8,
                    n(3)? as u32,
                    n(4)? as u32,
                    n(5)?,
                    n(6)? as u8,
                    n(7)? as u16,
                );
                if f[8] == "ERR" {
                    if actual.is_ok() {
                        return Err(bad());
                    }
                } else if actual.map_err(|_| bad())? != n(8)? as u16 {
                    return Err(bad());
                }
                models += 1;
            }
            "CLONE" if f.len() == 4 => {
                let actual = crate::spells::clone_plan(n(1)? as u8, n(2)? as u32);
                if f[3] == "ERR" {
                    if actual.is_ok() {
                        return Err(bad());
                    }
                } else {
                    let expected: Vec<u32> = numbers(f[3])?;
                    let (scaled, after, factor) = actual.map_err(|_| bad())?;
                    if expected != [scaled, after, u32::from(factor)] {
                        return Err(bad());
                    }
                }
                models += 1;
            }
            "CASE" if f.len() == 13 => {
                let mut rows = [[Stack::default(); 6]; 2];
                rows[0][0] = Stack {
                    unit: Some(UnitId::parse("native:01")?),
                    count: n(3)? as u32,
                };
                rows[0][1] = Stack {
                    unit: Some(UnitId::parse(&format!("native:{:02}", n(2)?))?),
                    count: 2,
                };
                for (raw, id, count) in [
                    (0, "native:06", 11),
                    (1, "native:16", 35),
                    (2, "native:11", 29),
                ] {
                    rows[1][raw] = Stack {
                        unit: Some(UnitId::parse(id)?),
                        count,
                    };
                }
                let mut c = Controller::with_spells(
                    catalog,
                    rows,
                    Side::Player,
                    Modifiers::default(),
                    SpellBook {
                        enabled: true,
                        charges: [3; 8],
                        stat_26b0: 2,
                        stat_26ae: n(6)? as u16,
                    },
                )
                .map_err(|_| bad())?;
                c.next_actor().map_err(|_| bad())?;
                c.attack(0).map_err(|_| bad())?;
                c.next_actor().map_err(|_| bad())?;
                if !c.is_caster() {
                    return Err(bad());
                }
                let hp = *c.battle().hp();
                let seq = c.battle().sequence();
                let mut rng = OriginalRng { seed: n(7)? as u32 };
                effects.clear();
                at = 0;
                if f[5] == "menu" {
                    c.retreat().map_err(|_| bad())?;
                } else {
                    let spell = *Spell::ALL.get(n(4)? as usize).ok_or_else(bad)?;
                    let result = c
                        .select_spell(spell)
                        .map_err(|e| format!("{} {e:?}", bad()))?;
                    if let Some(result) = result {
                        effects = result.effects;
                    } else if f[5] == "target" || f[5] == "target-space" {
                        c.cancel_spell_target(f[5] == "target").map_err(|_| bad())?;
                    } else {
                        effects = c
                            .target_spell(if spell == Spell::Clone { 0 } else { 1 }, &mut rng)
                            .map_err(|e| format!("{} {e:?}", bad()))?
                            .effects;
                    }
                }
                if c.battle().rows() != &[parse_rows(f[9])?, parse_rows(f[10])?]
                    || c.spell_book().ok_or_else(bad)?.charges.as_slice()
                        != numbers::<u16>(f[11])?.as_slice()
                    || c.battle().hp() != &hp
                    || c.battle().sequence() != seq
                    || rng.seed != n(8)? as u32
                {
                    return Err(format!("{} state", bad()));
                }
                if f[12] != "-" && c.remaining()[0] != six(f[12])? {
                    return Err(format!("{} counters", bad()));
                }
                cases += 1;
            }
            "EFFECT" if f.len() == 8 => {
                let e = effects.get(at).ok_or_else(bad)?;
                if e.side.index() != n(1)? as usize
                    || e.slot != n(2)? as usize
                    || e.raw != n(3)? as usize
                    || u64::from(e.amount) != n(4)?
                    || u64::from(e.before) != n(5)?
                    || u64::from(e.after) != n(6)?
                    || e.display != numbers::<u16>(f[7])?
                {
                    return Err(bad());
                }
                at += 1;
            }
            "END" if f.len() == 1 => {
                if at != effects.len() {
                    return Err(bad());
                }
            }
            _ => return Err(bad()),
        }
    }
    if models == 0 || cases == 0 {
        return Err("法術參考不完整".into());
    }
    Ok((models, cases))
}

fn numbers<T: FromStr>(text: &str) -> Result<Vec<T>, String> {
    if text == "-" {
        return Ok(Vec::new());
    }
    text.split(',')
        .map(|v| v.parse().map_err(|_| "參考數字無效".into()))
        .collect()
}
fn six<T: FromStr>(text: &str) -> Result<[T; 6], String> {
    numbers(text)?
        .try_into()
        .map_err(|_| "參考資料必須有六欄".into())
}

#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct ControllerCount {
    pub battles: usize,
    pub offers: usize,
    pub actions: usize,
    pub skips: usize,
}

pub fn check_controller(catalog: &Catalog, text: &str) -> Result<ControllerCount, String> {
    use crate::controller::Controller;
    let mut current: Option<Controller<'_>> = None;
    let mut count = ControllerCount::default();
    for (line_number, line) in text.lines().enumerate() {
        if line.starts_with('#') || line.trim().is_empty() {
            continue;
        }
        let f: Vec<_> = line.split('\t').collect();
        let bad = || format!("回合控制第 {} 行不符", line_number + 1);
        match f[0] {
            "START" if f.len() == 5 => {
                if current.is_some() {
                    return Err(bad());
                }
                let first = match f[2] {
                    "0" => Side::Player,
                    "1" => Side::Enemy,
                    _ => return Err(bad()),
                };
                current = Some(
                    Controller::new(
                        catalog,
                        [parse_rows(f[3])?, parse_rows(f[4])?],
                        first,
                        Modifiers::default(),
                    )
                    .map_err(|e| format!("{} {e:?}", bad()))?,
                );
                count.battles += 1;
            }
            "OFFER" if f.len() == 9 => {
                let c = current.as_mut().ok_or_else(bad)?;
                let actor = c
                    .next_actor()
                    .map_err(|e| format!("{} {e:?}", bad()))?
                    .ok_or_else(bad)?;
                let side: usize = f[1].parse().map_err(|_| bad())?;
                if side >= 2
                    || actor.side.index() != side
                    || actor.slot != f[2].parse().map_err(|_| bad())?
                    || actor.raw != f[3].parse().map_err(|_| bad())?
                    || c.slots() != &[six(f[4])?, six(f[5])?]
                    || c.remaining()[side] != six(f[6])?
                    || c.battle().hp() != &[six(f[7])?, six(f[8])?]
                {
                    return Err(format!(
                        "{} actor={actor:?} slots={:?} remaining={:?}",
                        bad(),
                        c.slots(),
                        c.remaining()
                    ));
                }
                count.offers += 1;
            }
            "ATTACK" if f.len() == 2 => {
                current
                    .as_mut()
                    .ok_or_else(bad)?
                    .attack(f[1].parse().map_err(|_| bad())?)
                    .map_err(|e| format!("{} {e:?}", bad()))?;
                count.actions += 1;
            }
            "SKIP" if f.len() == 1 => {
                current
                    .as_mut()
                    .ok_or_else(bad)?
                    .skip()
                    .map_err(|e| format!("{} {e:?}", bad()))?;
                count.skips += 1;
            }
            "RETREAT" if f.len() == 1 => {
                current
                    .as_mut()
                    .ok_or_else(bad)?
                    .retreat()
                    .map_err(|_| bad())?;
            }
            "END" if f.len() == 6 => {
                let mut c = current.take().ok_or_else(bad)?;
                let expected = match f[1] {
                    "win" => Outcome::Win,
                    "loss" => Outcome::Loss,
                    "retreat" => Outcome::Retreat,
                    _ => return Err(bad()),
                };
                if c.next_actor().map_err(|_| bad())?.is_some()
                    || c.battle().outcome() != Some(expected)
                    || c.battle().rows() != &[parse_rows(f[2])?, parse_rows(f[3])?]
                    || c.slots() != &[six(f[4])?, six(f[5])?]
                {
                    return Err(bad());
                }
            }
            _ => return Err(bad()),
        }
    }
    if current.is_some() || count.battles == 0 {
        return Err("回合控制記錄未結束".into());
    }
    Ok(count)
}

#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct ModelCount {
    pub setup: usize,
    pub sort: usize,
    pub motion: usize,
}

pub fn check_models(catalog: &Catalog, text: &str) -> Result<ModelCount, String> {
    let mut count = ModelCount::default();
    for (line_number, line) in text.lines().enumerate() {
        if line.starts_with('#') || line.trim().is_empty() {
            continue;
        }
        let f: Vec<_> = line.split('\t').collect();
        let bad = || format!("陣位向量第 {} 行不符", line_number + 1);
        match f[0] {
            "SETUP" if f.len() == 4 || f.len() == 7 => {
                let rows = [parse_rows(f[1])?, parse_rows(f[2])?];
                let actual = initial_formation(catalog, &rows);
                if f.len() == 4 {
                    if f[3] != "ERR" || actual.is_ok() {
                        return Err(bad());
                    }
                } else {
                    let actual = actual.map_err(|_| bad())?;
                    if actual.slots != [six(f[3])?, six(f[4])?]
                        || actual.hp != [six(f[5])?, six(f[6])?]
                    {
                        return Err(bad());
                    }
                }
                count.setup += 1;
            }
            "SORT" if f.len() == 6 => {
                let flat: Vec<u8> = numbers(f[3])?;
                if flat.len() != 12 {
                    return Err(bad());
                }
                let orders =
                    std::array::from_fn(|i| [flat[i * 3], flat[i * 3 + 1], flat[i * 3 + 2]]);
                let caster = match f[4] {
                    "true" => true,
                    "false" => false,
                    _ => return Err(bad()),
                };
                let actual = sort_plan(catalog, &parse_rows(f[1])?, six(f[2])?, orders, caster)
                    .map_err(|_| bad())?;
                if actual != six::<u8>(f[5])? {
                    return Err(bad());
                }
                count.sort += 1;
            }
            "MOTION" if f.len() == 6 => {
                let actual = motion_plan(
                    &parse_rows(f[1])?,
                    six(f[2])?,
                    f[3].parse().map_err(|_| bad())?,
                    f[4].parse().map_err(|_| bad())?,
                );
                if f[5] == "ERR" {
                    if actual.is_ok() {
                        return Err(bad());
                    }
                } else if actual.map_err(|_| bad())? != six::<u8>(f[5])? {
                    return Err(bad());
                }
                count.motion += 1;
            }
            _ => return Err(bad()),
        }
    }
    if count.setup == 0 || count.sort == 0 || count.motion == 0 {
        return Err("陣位向量不完整".into());
    }
    Ok(count)
}

#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct ReplayCount {
    pub battles: usize,
    pub actions: usize,
    pub wins: usize,
    pub losses: usize,
    pub retreats: usize,
}

/// Consume recorded choices only. Expected count/HP fields are compared after
/// resolution; they are never injected into the next native state.
pub fn check_battles(catalog: &Catalog, text: &str) -> Result<ReplayCount, String> {
    let mut count = ReplayCount::default();
    let mut current: Option<Battle<'_>> = None;
    for (line_number, line) in text.lines().enumerate() {
        if line.starts_with('#') || line.trim().is_empty() {
            continue;
        }
        let f: Vec<_> = line.split('\t').collect();
        let bad = || format!("戰鬥重播第 {} 行不符", line_number + 1);
        let number = |at: usize| f[at].parse::<u64>().map_err(|_| bad());
        match f[0] {
            "BATTLE" if f.len() == 4 => {
                if current.is_some() {
                    return Err(bad());
                }
                let rows: Rows = [parse_rows(f[2])?, parse_rows(f[3])?];
                current = Some(Battle::new(catalog, rows).map_err(|_| bad())?);
                count.battles += 1;
            }
            "STEP" if f.len() == 12 => {
                let battle = current.as_mut().ok_or_else(bad)?;
                let side = match f[1] {
                    "0" => Side::Player,
                    "1" => Side::Enemy,
                    _ => return Err(bad()),
                };
                let source: usize = number(2)?.try_into().map_err(|_| bad())?;
                let target: usize = number(3)?.try_into().map_err(|_| bad())?;
                if source >= 6 || target >= 6 {
                    return Err(bad());
                }
                if u64::from(battle.rows()[side.index()][source].count) != number(4)?
                    || u64::from(battle.rows()[1 - side.index()][target].count) != number(5)?
                {
                    return Err(bad());
                }
                let action = battle
                    .attack(side, source, target, Modifiers::default())
                    .map_err(|e| format!("{}：{e:?}", bad()))?;
                let before_hp: Vec<u64> = action.hits.iter().map(|hit| hit.before_hp).collect();
                let after_hp: Vec<u64> = action.hits.iter().map(|hit| hit.after_hp).collect();
                if u64::from(action.after) != number(6)?
                    || action.hits[0].damage != number(7)?
                    || u64::from(action.hits[0].encoded) != number(8)?
                    || before_hp != numbers::<u64>(f[9])?
                    || after_hp != numbers::<u64>(f[10])?
                    || action.display != numbers::<u16>(f[11])?
                {
                    return Err(bad());
                }
                count.actions += 1;
            }
            "END" if f.len() == 4 => {
                let mut battle = current.take().ok_or_else(bad)?;
                let expected = match f[1] {
                    "win" => {
                        count.wins += 1;
                        Outcome::Win
                    }
                    "loss" => {
                        count.losses += 1;
                        Outcome::Loss
                    }
                    "retreat" => {
                        count.retreats += 1;
                        battle.retreat().map_err(|_| bad())?;
                        Outcome::Retreat
                    }
                    _ => return Err(bad()),
                };
                if battle.outcome() != Some(expected)
                    || battle.rows() != &[parse_rows(f[2])?, parse_rows(f[3])?]
                {
                    return Err(bad());
                }
            }
            _ => return Err(bad()),
        }
    }
    if current.is_some() || count.battles == 0 {
        return Err("戰鬥重播未結束".into());
    }
    Ok(count)
}
