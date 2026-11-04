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
