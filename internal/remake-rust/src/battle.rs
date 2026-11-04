use crate::catalog::{Catalog, UnitId};
use crate::formation::initial_formation;
use crate::{AttackError, AttackInput, player_attack};

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct Stack {
    pub unit: Option<UnitId>,
    pub count: u32,
}
pub type Rows = [[Stack; 6]; 2];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Side {
    Player,
    Enemy,
}
impl Side {
    pub fn index(self) -> usize {
        match self {
            Self::Player => 0,
            Self::Enemy => 1,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Outcome {
    Win,
    Loss,
    Retreat,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct Modifiers {
    pub player_attack: u16,
    pub player_boost: u16,
    pub enemy_defense: u16,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BattleError {
    InvalidArmy,
    InvalidSlot,
    DeadStack,
    UnsupportedSpecial,
    CompatibilityRange,
    InvalidModifier,
    Finished,
    Overflow,
    Arithmetic(AttackError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Hit {
    pub damage: u64,
    pub encoded: u16,
    pub before_hp: u64,
    pub after_hp: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ActionResult {
    pub before: u32,
    pub after: u32,
    pub loss: u32,
    pub hits: Vec<Hit>,
    pub display: Vec<u16>,
    pub sequence: u64,
}

/// Ordinary state transitions. Selection, turn order and animation belong to
/// the original-style controller, not to this raw-row resolution API.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Battle<'a> {
    catalog: &'a Catalog,
    rows: Rows,
    hp: [[u64; 6]; 2],
    sequence: u64,
    exit: Option<Outcome>,
}

impl<'a> Battle<'a> {
    pub fn new(catalog: &'a Catalog, rows: Rows) -> Result<Self, BattleError> {
        let formation = initial_formation(catalog, &rows)?;
        Ok(Self {
            catalog,
            rows,
            hp: formation.hp,
            sequence: 0,
            exit: None,
        })
    }
    pub fn rows(&self) -> &Rows {
        &self.rows
    }
    pub fn hp(&self) -> &[[u64; 6]; 2] {
        &self.hp
    }
    pub fn sequence(&self) -> u64 {
        self.sequence
    }
    pub fn outcome(&self) -> Option<Outcome> {
        if self.rows[1].iter().all(|row| row.count == 0) {
            Some(Outcome::Win)
        } else if self.rows[0].iter().all(|row| row.count == 0) {
            Some(Outcome::Loss)
        } else {
            self.exit
        }
    }
    pub fn retreat(&mut self) -> Result<Outcome, BattleError> {
        if self.outcome().is_some() {
            return Err(BattleError::Finished);
        }
        self.exit = Some(Outcome::Retreat);
        Ok(Outcome::Retreat)
    }

    /// Original spell count updates leave the ordinary pending-HP pool intact.
    pub(crate) fn spell_counts(
        &mut self,
        updates: &[(Side, usize, u32)],
    ) -> Result<(), BattleError> {
        if self.outcome().is_some() {
            return Err(BattleError::Finished);
        }
        let mut seen = Vec::new();
        for &(side, raw, count) in updates {
            if raw >= 6 {
                return Err(BattleError::InvalidSlot);
            }
            if count > 32767 {
                return Err(BattleError::CompatibilityRange);
            }
            if self.rows[side.index()][raw].count == 0 {
                return Err(BattleError::DeadStack);
            }
            if seen.contains(&(side, raw)) {
                return Err(BattleError::InvalidSlot);
            }
            seen.push((side, raw));
        }
        for &(side, raw, count) in updates {
            self.rows[side.index()][raw].count = count;
        }
        Ok(())
    }

    pub fn attack(
        &mut self,
        side: Side,
        source_raw: usize,
        target_raw: usize,
        modifiers: Modifiers,
    ) -> Result<ActionResult, BattleError> {
        self.attack_inner(side, source_raw, target_raw, modifiers, false)
    }
    pub(crate) fn attack_front_caster(
        &mut self,
        side: Side,
        source_raw: usize,
        target_raw: usize,
        modifiers: Modifiers,
    ) -> Result<ActionResult, BattleError> {
        self.attack_inner(side, source_raw, target_raw, modifiers, true)
    }
    fn attack_inner(
        &mut self,
        side: Side,
        source_raw: usize,
        target_raw: usize,
        modifiers: Modifiers,
        front_caster: bool,
    ) -> Result<ActionResult, BattleError> {
        if self.outcome().is_some() {
            return Err(BattleError::Finished);
        }
        if source_raw >= 6 || target_raw >= 6 {
            return Err(BattleError::InvalidSlot);
        }
        let s = side.index();
        let t = 1 - s;
        let source = self.rows[s][source_raw];
        let target = self.rows[t][target_raw];
        if source.count == 0 || target.count == 0 {
            return Err(BattleError::DeadStack);
        }
        let source_id = source.unit.ok_or(BattleError::InvalidArmy)?;
        let target_id = target.unit.ok_or(BattleError::InvalidArmy)?;
        if source_id.is_native_caster() && !front_caster {
            return Err(BattleError::UnsupportedSpecial);
        }
        if source.count > u32::from(u16::MAX) || target.count > 32767 {
            return Err(BattleError::CompatibilityRange);
        }
        let profile = self.catalog.get(source_id);
        let defender = self.catalog.get(target_id);
        let (divisor, multiplier) = if side == Side::Player {
            if modifiers.player_attack >= 5 {
                return Err(BattleError::InvalidModifier);
            }
            (
                5 - modifiers.player_attack,
                modifiers
                    .player_boost
                    .checked_add(1)
                    .ok_or(BattleError::InvalidModifier)?,
            )
        } else {
            (
                modifiers
                    .enemy_defense
                    .checked_add(5)
                    .ok_or(BattleError::InvalidModifier)?,
                1,
            )
        };
        let amount = player_attack(AttackInput {
            attack: profile.attack,
            count: source.count as u16,
            hp: defender.hp,
            divisor,
            multiplier,
            pending_hp: self.hp[t][target_raw],
            target_count: target.count,
        })
        .map_err(BattleError::Arithmetic)?;
        let count_after = if side == Side::Player {
            amount.count_after
        } else if amount.encoded == 1 {
            target.count
        } else if u32::from(amount.encoded) >= target.count {
            0
        } else {
            target.count - u32::from(amount.encoded) + 1
        };
        let call_count = if side == Side::Enemy && !profile.ranged && amount.encoded != 1 {
            2
        } else {
            1
        };
        let mut pending = self.hp[t][target_raw];
        let mut hits = Vec::new();
        for _ in 0..call_count {
            let after = pending.saturating_sub(amount.damage);
            hits.push(Hit {
                damage: amount.damage,
                encoded: amount.encoded,
                before_hp: pending,
                after_hp: after,
            });
            pending = after;
        }
        let mut display = Vec::new();
        if side == Side::Player || amount.encoded != 1 {
            let (start, end) = if count_after == 0 {
                (target.count.min(5), 0)
            } else if amount.encoded >= 5 {
                (target.count - u32::from(amount.encoded) + 5, count_after)
            } else {
                (target.count, count_after)
            };
            for value in (end..=start).rev() {
                display.push(value as u16);
            }
        }
        let sequence = self.sequence.checked_add(1).ok_or(BattleError::Overflow)?;
        // All fallible checks precede the single formal troop-count commit.
        self.rows[t][target_raw].count = count_after;
        self.hp[t][target_raw] = pending;
        self.sequence = sequence;
        Ok(ActionResult {
            before: target.count,
            after: count_after,
            loss: target.count - count_after,
            hits,
            display,
            sequence,
        })
    }
}
