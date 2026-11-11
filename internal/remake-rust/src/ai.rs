//! Spec030 target policy. Scores never mutate battle data or consume randomness.
use crate::{
    battle::Side,
    controller::{ControlError, Controller, OriginalRng},
    spells::Spell,
};
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum Mode {
    #[default]
    Native,
    Target,
}
impl Mode {
    pub fn parse(s: &str) -> Result<Self, String> {
        match s {
            "native" => Ok(Self::Native),
            "target" => Ok(Self::Target),
            _ => Err("AI模式無效".into()),
        }
    }
    pub fn name(self) -> &'static str {
        match self {
            Self::Native => "native",
            Self::Target => "target",
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Route {
    Normal,
    Ranged,
    Special(Spell),
}
impl Route {
    pub fn name(self) -> &'static str {
        match self {
            Self::Normal => "normal",
            Self::Ranged => "ranged",
            Self::Special(Spell::Fireball) => "special0",
            Self::Special(Spell::Exorcism) => "special2",
            Self::Special(Spell::Halve) => "special5",
            _ => "unsupported",
        }
    }
}
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Unit {
    pub kind: u8,
    pub count: u16,
    pub attack: u16,
    pub hp: u16,
    pub ranged: bool,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct View {
    pub rows: [[Unit; 6]; 2],
    pub slots: [[u8; 6]; 2],
    pub source: usize,
    pub original: usize,
    pub divisor: u16,
    pub alias_alive: bool,
    pub route: Route,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Candidate {
    pub slot: usize,
    pub raw: usize,
    pub count: u16,
    pub amount: u16,
    pub loss: u16,
    pub eliminates: bool,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Decision {
    pub source: usize,
    pub original: usize,
    pub selected: usize,
    pub route: Route,
    pub candidates: Vec<Candidate>,
    pub reason: &'static str,
}
impl View {
    pub fn choose(&self) -> Result<Decision, &'static str> {
        if self.source >= 6 || self.original >= 6 {
            return Err("AI slot out of range");
        }
        for side in 0..2 {
            let mut seen = [false; 6];
            for &raw in &self.slots[side] {
                if raw >= 6 {
                    return Err("AI mapping out of range");
                }
                let raw = usize::from(raw);
                if self.rows[side][raw].count > 0 {
                    if seen[raw] {
                        return Err("AI duplicate live mapping");
                    }
                    seen[raw] = true;
                }
            }
        }
        let source = self.rows[1][usize::from(self.slots[1][self.source])];
        if source.count == 0 {
            return Err("AI empty source");
        }
        match self.route {
            Route::Normal if self.source >= 3 || source.ranged => {
                return Err("AI normal route mismatch");
            }
            Route::Ranged if !source.ranged => return Err("AI ranged route mismatch"),
            Route::Special(s)
                if self.source < 3
                    || !matches!(source.kind, 10 | 12)
                    || !matches!(s, Spell::Fireball | Spell::Exorcism | Spell::Halve) =>
            {
                return Err("AI unsupported special");
            }
            _ => {}
        }
        let alive = |s: usize| self.rows[0][usize::from(self.slots[0][s])].count > 0;
        let (first, last) = if self.route == Route::Normal {
            if !(0..3).any(alive) {
                (3, 6)
            } else if alive(self.source) {
                (self.source, self.source + 1)
            } else {
                (0, 3)
            }
        } else {
            (0, 6)
        };
        let mut candidates = Vec::new();
        for slot in first..last {
            let raw = usize::from(self.slots[0][slot]);
            let target = self.rows[0][raw];
            if target.count == 0 {
                continue;
            }
            if self.route == Route::Special(Spell::Exorcism) && !(6..=15).contains(&target.kind) {
                continue;
            }
            if self.route == Route::Special(Spell::Halve)
                && !(if slot == 0 {
                    self.alias_alive
                } else {
                    alive(slot - 1)
                })
            {
                continue;
            }
            let (amount, loss) = match self.route {
                Route::Normal | Route::Ranged => {
                    let divisor = self.divisor.wrapping_add(5);
                    if divisor == 0 || target.hp == 0 {
                        return Err("AI zero factor");
                    }
                    let amount =
                        (u32::from(source.attack) * u32::from(source.count)) as u16 / divisor;
                    let encoded = (amount / target.hp).wrapping_add(1);
                    let loss = if encoded <= 1 {
                        0
                    } else if encoded >= target.count {
                        target.count
                    } else {
                        encoded - 1
                    };
                    (amount, loss)
                }
                Route::Special(spell) => {
                    let amount = match spell {
                        Spell::Fireball => {
                            if source.kind == 12 {
                                2
                            } else {
                                5
                            }
                        }
                        Spell::Exorcism => {
                            if source.kind == 12 {
                                6
                            } else {
                                15
                            }
                        }
                        Spell::Halve => target.count / (if source.kind == 12 { 3 } else { 2 }) + 1,
                        _ => return Err("AI unsupported special"),
                    };
                    (amount, amount.min(target.count))
                }
            };
            candidates.push(Candidate {
                slot,
                raw,
                count: target.count,
                amount,
                loss,
                eliminates: loss == target.count,
            });
        }
        let mut d = Decision {
            source: self.source,
            original: self.original,
            selected: self.original,
            route: self.route,
            candidates,
            reason: "ranked",
        };
        if d.candidates.is_empty() {
            d.reason = "no-live-target";
            return Ok(d);
        }
        let mut best = d.candidates.iter().find(|c| c.slot == self.original);
        if best.is_none() && self.route != Route::Special(Spell::Halve) {
            return Err("AI original target is illegal");
        }
        if best.is_none() {
            best = d.candidates.first();
        }
        let mut best = best.ok_or("AI no candidate")?;
        for c in &d.candidates {
            if (c.eliminates && !best.eliminates)
                || (c.eliminates == best.eliminates
                    && u64::from(c.loss) * u64::from(best.count)
                        > u64::from(best.loss) * u64::from(c.count))
            {
                best = c;
            }
        }
        d.selected = best.slot;
        Ok(d)
    }
}
impl Controller<'_> {
    pub(crate) fn ai_decision(
        &self,
        route: Route,
        original: usize,
    ) -> Result<Decision, ControlError> {
        let actor = self.current().ok_or(ControlError::NoActor)?;
        if actor.side != Side::Enemy {
            return Err(ControlError::NoActor);
        }
        let mut rows = [[Unit::default(); 6]; 2];
        for (side, army) in self.battle().rows().iter().enumerate() {
            for (raw, stack) in army.iter().enumerate() {
                if let Some(id) = stack.unit {
                    let p = self.ai_catalog().get(id);
                    rows[side][raw] = Unit {
                        kind: id.native_kind().unwrap_or(0),
                        count: stack
                            .count
                            .try_into()
                            .map_err(|_| ControlError::UnsupportedArmy)?,
                        attack: p
                            .attack
                            .try_into()
                            .map_err(|_| ControlError::UnsupportedArmy)?,
                        hp: p.hp.try_into().map_err(|_| ControlError::UnsupportedArmy)?,
                        ranged: p.ranged,
                    };
                } else if stack.count != 0 {
                    return Err(ControlError::UnsupportedArmy);
                }
            }
        }
        let alias_alive = self.enemy_config().is_some_and(|c| {
            let n = usize::from(c.shifted_alias);
            self.battle().rows()[n / 6][n % 6].count > 0
        });
        View {
            rows,
            slots: *self.slots(),
            source: actor.slot,
            original,
            divisor: self.modifiers().enemy_defense,
            alias_alive,
            route,
        }
        .choose()
        .map_err(ControlError::AI)
    }
    pub fn enemy_target_ai(
        &self,
        rng: &mut OriginalRng,
        mode: Mode,
    ) -> Result<(usize, Option<Decision>), ControlError> {
        let mut random = *rng;
        let original = self.enemy_target(&mut random)?;
        let decision = if mode == Mode::Target {
            let actor = self.current().ok_or(ControlError::NoActor)?;
            Some(self.ai_decision(
                if actor.ranged {
                    Route::Ranged
                } else {
                    Route::Normal
                },
                original,
            )?)
        } else {
            None
        };
        let target = decision.as_ref().map_or(original, |d| d.selected);
        *rng = random;
        Ok((target, decision))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{
        battle::{Modifiers, Stack},
        catalog::{Catalog, UnitId},
        controller::EnemyConfig,
    };
    #[test]
    fn ordinary_openkb_policy_changes_target_without_extra_rng_or_state_writes() {
        let catalog = Catalog::builtin().unwrap();
        let mut rows = [[Stack::default(); 6]; 2];
        for (side, raw, id, count) in [
            (0, 0, "native:06", 100),
            (0, 1, "native:11", 2),
            (1, 0, "openkb:arcr", 250),
        ] {
            rows[side][raw] = Stack {
                unit: Some(UnitId::parse(id).unwrap()),
                count,
            };
        }
        let mut c = Controller::new(&catalog, rows, Side::Enemy, Modifiers::default()).unwrap();
        c.next_actor().unwrap();
        let before = c.clone();
        let mut native = OriginalRng { seed: 1 };
        let mut policy = native;
        let original = c.enemy_target(&mut native).unwrap();
        let (target, d) = c.enemy_target_ai(&mut policy, Mode::Target).unwrap();
        assert_eq!(original, 0);
        assert_eq!(target, 1);
        assert_eq!(native, policy);
        assert_eq!(c, before);
        let d = d.unwrap();
        assert!(
            d.candidates
                .iter()
                .find(|v| v.slot == 1)
                .unwrap()
                .eliminates
        );
        c.attack(target).unwrap();
        assert_eq!(c.battle().rows()[0][0].count, 100);
        assert_eq!(c.battle().rows()[0][1].count, 0);
    }
    #[test]
    fn enemy_spell_policy_preserves_selector_rng_and_pending_hp_for_fixed_seed_matrix() {
        let catalog = Catalog::builtin().unwrap();
        let mut rows = [[Stack::default(); 6]; 2];
        for (side, raw, id, count) in [
            (0, 0, "native:06", 31),
            (0, 1, "native:15", 69),
            (1, 0, "native:12", 3),
        ] {
            rows[side][raw] = Stack {
                unit: Some(UnitId::parse(id).unwrap()),
                count,
            };
        }
        for seed in 1..=64 {
            let mut a = Controller::with_enemy_spells(
                &catalog,
                rows,
                Side::Enemy,
                Modifiers::default(),
                None,
                EnemyConfig {
                    stat_26ae: 4,
                    shifted_alias: 0,
                },
            )
            .unwrap();
            a.next_actor().unwrap();
            let mut b = a.clone();
            let mut ra = OriginalRng { seed };
            let mut rb = ra;
            let ar = a.enemy_cast(&mut ra).unwrap();
            let (br, d) = b.enemy_cast_ai(&mut rb, Mode::Target).unwrap();
            assert_eq!(ra, rb);
            assert_eq!(ar.spell, br.spell);
            assert_eq!(ar.roll, br.roll);
            assert_eq!(a.battle().hp(), b.battle().hp());
            if !matches!(ar.spell, Spell::Fireball | Spell::Exorcism | Spell::Halve) {
                assert!(d.is_none());
                assert_eq!(a, b);
                assert_eq!(ar, br);
            }
        }
    }
    #[test]
    fn existing_go_policy_vectors_match() {
        let mut checked = 0;
        for line in include_str!("../ai-reference.tsv")
            .lines()
            .filter(|l| !l.starts_with('#'))
        {
            let mut fields = line.split('\t');
            let nums: Vec<u16> = fields
                .next()
                .unwrap()
                .split(',')
                .map(|n| n.parse().unwrap())
                .collect();
            let expected = fields.next().unwrap();
            let list = fields.next().unwrap();
            let route = match nums[0] {
                0 => Route::Normal,
                1 => Route::Ranged,
                2 => Route::Special(Spell::Fireball),
                3 => Route::Special(Spell::Exorcism),
                4 => Route::Special(Spell::Halve),
                _ => panic!("route"),
            };
            let mut at = 5;
            let mut slots = [[0; 6]; 2];
            for army in &mut slots {
                for raw in army {
                    *raw = nums[at] as u8;
                    at += 1;
                }
            }
            let mut rows = [[Unit::default(); 6]; 2];
            for army in &mut rows {
                for u in army {
                    *u = Unit {
                        kind: nums[at] as u8,
                        count: nums[at + 1],
                        attack: nums[at + 2],
                        hp: nums[at + 3],
                        ranged: nums[at + 4] != 0,
                    };
                    at += 5;
                }
            }
            assert_eq!(at, nums.len());
            let view = View {
                rows,
                slots,
                source: usize::from(nums[1]),
                original: usize::from(nums[2]),
                divisor: nums[3],
                alias_alive: nums[4] != 0,
                route,
            };
            let d = view.choose().unwrap();
            if expected == "NONE" {
                assert!(d.candidates.is_empty());
            } else {
                assert_eq!(d.selected.to_string(), expected);
            }
            let actual = d
                .candidates
                .iter()
                .map(|c| {
                    format!(
                        "{},{},{},{},{},{}",
                        c.slot,
                        c.raw,
                        c.count,
                        c.amount,
                        c.loss,
                        u8::from(c.eliminates)
                    )
                })
                .collect::<Vec<_>>()
                .join(";");
            assert_eq!(actual, list);
            checked += 1;
        }
        assert!(checked >= 400);
    }
    #[test]
    fn modes_are_strict_and_default_native() {
        assert_eq!(Mode::default(), Mode::Native);
        assert!(Mode::parse("auto").is_err());
        assert_eq!(Mode::parse("target").unwrap(), Mode::Target);
    }
    #[test]
    fn invalid_view_is_rejected_without_mutating_input() {
        let mut v = View {
            rows: [[Unit::default(); 6]; 2],
            slots: [[0, 1, 2, 3, 4, 5]; 2],
            source: 0,
            original: 0,
            divisor: 0,
            alias_alive: false,
            route: Route::Ranged,
        };
        v.rows[1][0] = Unit {
            kind: 3,
            count: 1,
            attack: 40,
            hp: 40,
            ranged: true,
        };
        v.rows[0][0] = Unit {
            kind: 1,
            count: 2,
            attack: 30,
            hp: 0,
            ranged: false,
        };
        let before = v.clone();
        assert!(v.choose().is_err());
        assert_eq!(v, before);
        v.rows[0][0].hp = 25;
        v.slots[0][1] = 0;
        assert!(v.choose().is_err());
        v.slots[0][1] = 1;
        v.divisor = 65531;
        assert!(v.choose().is_err());
    }
}
