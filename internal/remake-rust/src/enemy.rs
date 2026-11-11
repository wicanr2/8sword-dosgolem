//! Original sub_1F266, IDA MZ linear base10000h; runtime0F67:0CF6.
//! Evidence and compatibility bounds: spec031 Rust敵方八分派.
use super::*;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EnemyConfig {
    pub stat_26ae: u16,
    // Original DS:6FB4, combined player/enemy raw index, not a battlefield slot.
    pub shifted_alias: u8,
}

pub fn enemy_selector(roll: u16) -> Spell {
    match roll % 340 {
        0..100 | 330..340 => Spell::Fireball,
        100..150 => Spell::Thunder,
        150..220 => Spell::Exorcism,
        220..270 => Spell::Assassination,
        270..300 => Spell::Freeze,
        300..310 => Spell::Halve,
        _ => Spell::Clone,
    }
}

pub fn enemy_amount(spell: Spell, kind: u8, count: u32) -> Result<u16, SpellError> {
    if ![10, 12].contains(&kind) {
        return Err(SpellError::Identity);
    }
    if count > 32767 || (count == 0 && spell != Spell::Halve) {
        return Err(SpellError::Range);
    }
    let n = match spell {
        Spell::Fireball | Spell::Thunder => {
            if kind == 12 {
                2
            } else {
                5
            }
        }
        Spell::Exorcism => {
            if kind == 12 {
                6
            } else {
                15
            }
        }
        Spell::Assassination => count,
        Spell::Halve => count / if kind == 12 { 3 } else { 2 } + 1,
        Spell::Quake => {
            if count < 50 {
                count
            } else {
                let product = count * 6;
                if product > 65535 {
                    return Err(SpellError::Range);
                }
                product / if kind == 12 { 20 } else { 10 } + 1
            }
        }
        _ => return Err(SpellError::Unsupported),
    };
    Ok(n as u16)
}

impl<'a> Controller<'a> {
    pub fn with_enemy_spells(
        catalog: &'a Catalog,
        rows: Rows,
        first: Side,
        modifiers: Modifiers,
        book: Option<SpellBook>,
        config: EnemyConfig,
    ) -> Result<Self, ControlError> {
        if config.stat_26ae > 6552
            || config.shifted_alias >= 12
            || book.as_ref().is_some_and(|b| b.stat_26ae > 6552)
            || rows[1]
                .iter()
                .any(|r| r.count > 0 && r.unit.is_some_and(|id| id.native_kind().is_none()))
        {
            return Err(ControlError::UnsupportedArmy);
        }
        Self::create(catalog, rows, first, modifiers, book, Some(config))
    }
    pub fn is_enemy_caster(&self) -> bool {
        self.actor.is_some_and(|a| {
            a.side == Side::Enemy
                && a.slot >= 3
                && self.battle.rows()[1][a.raw]
                    .unit
                    .is_some_and(|id| id.is_native_caster())
        })
    }
    pub fn enemy_returns(&self) -> u64 {
        self.enemy_returns
    }
    fn enemy_kind(&self) -> Result<u8, ControlError> {
        if !self.is_enemy_caster() {
            return Err(ControlError::WrongPhase);
        }
        self.battle.rows()[1][self.actor.ok_or(ControlError::NoActor)?.raw]
            .unit
            .and_then(|id| id.native_kind())
            .ok_or(ControlError::UnsupportedArmy)
    }
    pub fn enemy_spell_targets(&self, spell: Spell) -> Result<Vec<usize>, ControlError> {
        self.enemy_kind()?;
        let config = self.enemy_config.ok_or(ControlError::WrongPhase)?;
        let alive = |side: usize, raw: usize| self.battle.rows()[side][raw].count > 0;
        Ok((0..6)
            .filter(|slot| {
                let side = usize::from(spell == Spell::Clone);
                let raw = usize::from(self.slots[side][*slot]);
                match spell {
                    Spell::Fireball | Spell::Assassination | Spell::Clone => alive(side, raw),
                    Spell::Exorcism => {
                        alive(0, raw)
                            && self.battle.rows()[0][raw]
                                .unit
                                .and_then(|id| id.native_kind())
                                .is_some_and(|n| (6..=15).contains(&n))
                    }
                    Spell::Halve => {
                        if *slot == 0 {
                            alive(
                                usize::from(config.shifted_alias / 6),
                                usize::from(config.shifted_alias % 6),
                            )
                        } else {
                            alive(0, usize::from(self.slots[0][slot - 1]))
                        }
                    }
                    _ => false,
                }
            })
            .collect())
    }
    /// Controlled original comparison entry. Production uses enemy_cast below.
    /// Gate is rand%50, already selected; never silently rerolled.
    pub fn enemy_cast_choice(
        &mut self,
        spell: Spell,
        target: Option<usize>,
        gate: Option<u16>,
    ) -> Result<SpellResult, ControlError> {
        let mut staged = self.clone();
        let result = staged.resolve_enemy(spell, target, gate)?;
        *self = staged;
        Ok(result)
    }
    pub fn enemy_cast(&mut self, rng: &mut OriginalRng) -> Result<SpellResult, ControlError> {
        self.enemy_cast_ai(rng, crate::ai::Mode::Native)
            .map(|v| v.0)
    }
    pub fn enemy_cast_ai(
        &mut self,
        rng: &mut OriginalRng,
        mode: crate::ai::Mode,
    ) -> Result<(SpellResult, Option<crate::ai::Decision>), ControlError> {
        let mut staged = self.clone();
        let mut random = *rng;
        staged.enemy_kind()?;
        let spell = enemy_selector(random.next15());
        let candidates = staged.enemy_spell_targets(spell)?;
        let targeted = matches!(
            spell,
            Spell::Fireball | Spell::Exorcism | Spell::Assassination | Spell::Halve | Spell::Clone
        );
        let target = if targeted && !(spell == Spell::Exorcism && candidates.is_empty()) {
            if candidates.is_empty() {
                return Err(ControlError::Budget);
            }
            let mut selected = None;
            for _ in 0..128 {
                let slot = usize::from(random.next15() % 6);
                if candidates.contains(&slot) {
                    selected = Some(slot);
                    break;
                }
            }
            Some(selected.ok_or(ControlError::Budget)?)
        } else {
            None
        };
        let decision = if mode == crate::ai::Mode::Target
            && matches!(spell, Spell::Fireball | Spell::Exorcism | Spell::Halve)
        {
            target
                .map(|n| staged.ai_decision(crate::ai::Route::Special(spell), n))
                .transpose()?
        } else {
            None
        };
        let target = decision.as_ref().map(|d| d.selected).or(target);
        let gate = if spell == Spell::Assassination {
            Some(random.next15() % 50)
        } else {
            None
        };
        let result = staged.resolve_enemy(spell, target, gate)?;
        *self = staged;
        *rng = random;
        Ok((result, decision))
    }
    fn resolve_enemy(
        &mut self,
        spell: Spell,
        target: Option<usize>,
        gate: Option<u16>,
    ) -> Result<SpellResult, ControlError> {
        let kind = self.enemy_kind()?;
        let config = self.enemy_config.ok_or(ControlError::WrongPhase)?;
        let targeted = matches!(
            spell,
            Spell::Fireball | Spell::Exorcism | Spell::Assassination | Spell::Halve | Spell::Clone
        );
        let candidates = self.enemy_spell_targets(spell)?;
        let empty_ghost = spell == Spell::Exorcism && candidates.is_empty();
        if (targeted && !empty_ghost && !target.is_some_and(|n| candidates.contains(&n)))
            || ((!targeted || empty_ghost) && target.is_some())
            || (spell == Spell::Assassination && gate.is_none_or(|n| n >= 50))
            || (spell != Spell::Assassination && gate.is_some())
        {
            return Err(ControlError::InvalidTarget);
        }
        let mut result = SpellResult {
            spell,
            effects: Vec::new(),
            refunded: false,
            roll: gate,
        };
        if spell == Spell::Freeze {
            for raw in self.slots[1] {
                let n = &mut self.remaining[1][usize::from(raw)];
                *n = n.checked_add(1).ok_or(ControlError::Budget)?;
            }
        } else if spell == Spell::Clone {
            let slot = target.ok_or(ControlError::InvalidTarget)?;
            let raw = usize::from(self.slots[1][slot]);
            let before = self.battle.rows()[1][raw].count;
            let (scaled, after, _) = clone_plan(kind, before).map_err(ControlError::Spell)?;
            self.battle.spell_counts(&[(Side::Enemy, raw, after)])?;
            result.effects.push(SpellEffect {
                side: Side::Enemy,
                slot,
                raw,
                before,
                after,
                amount: 0,
                display: if scaled >= before {
                    (before..=scaled).map(|n| n as u16).collect()
                } else {
                    Vec::new()
                },
            });
        } else {
            let targets: Vec<_> = if matches!(spell, Spell::Thunder | Spell::Quake) {
                (0..6)
                    .filter(|s| self.battle.rows()[0][usize::from(self.slots[0][*s])].count > 0)
                    .collect()
            } else {
                target.into_iter().collect()
            };
            let success = spell != Spell::Assassination
                || u32::from(gate.ok_or(ControlError::InvalidTarget)?)
                    < u32::from(config.stat_26ae) * 10 + 10;
            let mut updates = Vec::new();
            for slot in targets {
                if !success {
                    break;
                }
                let raw = usize::from(self.slots[0][slot]);
                let before = self.battle.rows()[0][raw].count;
                let n = enemy_amount(spell, kind, before).map_err(ControlError::Spell)?;
                let after = before.saturating_sub(u32::from(n));
                let start = if after == 0 {
                    before.min(5)
                } else if n >= 5 {
                    after + 5
                } else {
                    before
                };
                result.effects.push(SpellEffect {
                    side: Side::Player,
                    slot,
                    raw,
                    before,
                    after,
                    amount: n,
                    display: if spell == Spell::Quake {
                        Vec::new()
                    } else {
                        (after..=start).rev().map(|n| n as u16).collect()
                    },
                });
                if before > 0 {
                    updates.push((Side::Player, raw, after));
                }
            }
            if !updates.is_empty() {
                self.battle.spell_counts(&updates)?;
            }
        }
        self.enemy_returns = self
            .enemy_returns
            .checked_add(1)
            .ok_or(ControlError::Budget)?;
        self.actor = None;
        self.scan = Scan::start();
        if self.battle.outcome().is_none() {
            self.sort_opponent()?;
        }
        Ok(result)
    }
}

#[cfg(test)]
#[path = "enemy_tests.rs"]
mod tests;
