use crate::battle::{ActionResult, Battle, BattleError, Modifiers, Outcome, Rows, Side};
use crate::catalog::Catalog;
use crate::formation::{initial_formation, motion_plan, sort_plan};
use crate::spells::{Spell, SpellBook, SpellEffect, SpellError, SpellResult, amount, clone_plan};
#[path = "enemy.rs"]
mod enemy;
pub use enemy::{EnemyConfig, enemy_amount, enemy_selector};

// Original PAM MZ body + 1D780h + DS:708A/708E/7092/7096.
const ORDERS: [[u8; 3]; 4] = [[2, 4, 5], [1, 3, 5], [1, 4, 5], [0, 3, 5]];
pub const POSITIONS: [[i32; 2]; 12] = [
    [552, 300],
    [552, 600],
    [552, 900],
    [288, 450],
    [288, 750],
    [24, 600],
    [816, 300],
    [816, 600],
    [816, 900],
    [1080, 450],
    [1080, 750],
    [1344, 600],
];
// Original DS:709A, nodes 1..6 enemy, 7..12 player; up/down/left/right.
pub const NAVIGATION: [[u8; 4]; 13] = [
    [0, 0, 0, 0],
    [0, 2, 7, 4],
    [1, 3, 8, 4],
    [2, 0, 9, 5],
    [0, 5, 2, 6],
    [4, 0, 2, 6],
    [0, 0, 5, 0],
    [0, 8, 10, 1],
    [7, 9, 10, 2],
    [8, 0, 11, 3],
    [0, 11, 12, 8],
    [10, 0, 12, 8],
    [0, 0, 0, 11],
];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Actor {
    pub side: Side,
    pub slot: usize,
    pub raw: usize,
    pub ranged: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ControlError {
    Battle(BattleError),
    InvalidTarget,
    NoActor,
    UnsupportedArmy,
    Budget,
    Spell(SpellError),
    NoCharge,
    WrongPhase,
}
impl From<BattleError> for ControlError {
    fn from(e: BattleError) -> Self {
        Self::Battle(e)
    }
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
struct Scan {
    front: usize,
    rear: usize,
    activity: bool,
}
impl Scan {
    fn start() -> Self {
        Self {
            front: 0,
            rear: 3,
            activity: false,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Controller<'a> {
    catalog: &'a Catalog,
    battle: Battle<'a>,
    slots: [[u8; 6]; 2],
    remaining: [[u16; 6]; 2],
    side: Side,
    actor: Option<Actor>,
    scan: Scan,
    half_turn: u64,
    modifiers: Modifiers,
    book: Option<SpellBook>,
    selected_spell: Option<Spell>,
    spell_returns: u64,
    enemy_config: Option<EnemyConfig>,
    enemy_returns: u64,
}

impl<'a> Controller<'a> {
    pub fn new(
        catalog: &'a Catalog,
        rows: Rows,
        first: Side,
        modifiers: Modifiers,
    ) -> Result<Self, ControlError> {
        Self::create(catalog, rows, first, modifiers, None, None)
    }
    pub fn with_spells(
        catalog: &'a Catalog,
        rows: Rows,
        first: Side,
        modifiers: Modifiers,
        book: SpellBook,
    ) -> Result<Self, ControlError> {
        if book.stat_26ae > 6552 {
            return Err(ControlError::Spell(SpellError::Range));
        }
        Self::create(catalog, rows, first, modifiers, Some(book), None)
    }
    fn create(
        catalog: &'a Catalog,
        rows: Rows,
        first: Side,
        modifiers: Modifiers,
        book: Option<SpellBook>,
        enemy_config: Option<EnemyConfig>,
    ) -> Result<Self, ControlError> {
        for (side, army) in rows.iter().enumerate() {
            for stack in army {
                if stack.count > 32767
                    || stack.unit.is_some_and(|id| {
                        id.is_native_caster()
                            && if side == 1 {
                                enemy_config.is_none()
                            } else {
                                book.is_none()
                            }
                    })
                {
                    return Err(ControlError::UnsupportedArmy);
                }
            }
        }
        let formation = initial_formation(catalog, &rows)?;
        let mut c = Self {
            catalog,
            battle: Battle::new(catalog, rows)?,
            slots: formation.slots,
            remaining: [[0; 6]; 2],
            side: first,
            actor: None,
            scan: Scan::start(),
            half_turn: 1,
            modifiers,
            book,
            selected_spell: None,
            spell_returns: 0,
            enemy_config,
            enemy_returns: 0,
        };
        c.remaining[first.index()] = [1; 6];
        Ok(c)
    }
    pub fn battle(&self) -> &Battle<'a> {
        &self.battle
    }
    pub fn slots(&self) -> &[[u8; 6]; 2] {
        &self.slots
    }
    pub fn remaining(&self) -> &[[u16; 6]; 2] {
        &self.remaining
    }
    pub fn half_turn(&self) -> u64 {
        self.half_turn
    }
    pub fn current(&self) -> Option<Actor> {
        self.actor
    }

    fn sort_opponent(&mut self) -> Result<(), ControlError> {
        let side = 1 - self.side.index();
        let caster_front = side == 0
            && !self.battle.rows()[0]
                .iter()
                .any(|s| s.count > 0 && s.unit.is_some_and(|id| !id.is_native_caster()))
            && self
                .book
                .as_ref()
                .is_some_and(|b| b.charges.iter().all(|n| *n == 0));
        self.slots[side] = sort_plan(
            self.catalog,
            &self.battle.rows()[side],
            self.slots[side],
            ORDERS,
            caster_front,
        )?;
        Ok(())
    }
    fn next_inner(&mut self) -> Result<Option<Actor>, ControlError> {
        for _ in 0..64 {
            if self.battle.outcome().is_some() {
                self.actor = None;
                return Ok(None);
            }
            if let Some(actor) = self.actor {
                return Ok(Some(actor));
            }
            let side = self.side.index();
            while self.scan.front < 3 || self.scan.rear < 6 {
                let slot = if self.scan.front < 3 {
                    self.scan.front
                } else {
                    self.scan.rear
                };
                let raw = usize::from(self.slots[side][slot]);
                let stack = self.battle.rows()[side][raw];
                let ranged = stack.unit.is_some_and(|id| self.catalog.get(id).ranged);
                let caster = slot >= 3 && stack.unit.is_some_and(|id| id.is_native_caster());
                if stack.count != 0
                    && self.remaining[side][raw] != 0
                    && (slot < 3 || ranged || caster)
                {
                    self.remaining[side][raw] -= 1;
                    self.scan.activity |= ranged || caster;
                    let actor = Actor {
                        side: self.side,
                        slot,
                        raw,
                        ranged,
                    };
                    self.actor = Some(actor);
                    if caster
                        && self.side == Side::Player
                        && !self.book.as_ref().is_some_and(SpellBook::available)
                    {
                        self.finish_cast()?;
                        continue;
                    }
                    return Ok(Some(actor));
                }
                if slot < 3 {
                    self.scan.front += 1;
                } else {
                    self.scan.rear += 1;
                }
            }
            if self.scan.activity {
                self.sort_opponent()?;
                self.scan = Scan::start();
                continue;
            }
            self.side = if self.side == Side::Player {
                Side::Enemy
            } else {
                Side::Player
            };
            self.half_turn = self.half_turn.checked_add(1).ok_or(ControlError::Budget)?;
            self.remaining[self.side.index()] = [1; 6];
            self.scan = Scan::start();
        }
        Err(ControlError::Budget)
    }
    pub fn next_actor(&mut self) -> Result<Option<Actor>, ControlError> {
        let mut staged = self.clone();
        let actor = staged.next_inner()?;
        *self = staged;
        Ok(actor)
    }
    pub fn legal_targets(&self) -> Result<Vec<usize>, ControlError> {
        let actor = self.actor.ok_or(ControlError::NoActor)?;
        if self.is_enemy_caster() {
            return Err(ControlError::WrongPhase);
        }
        if self.is_caster() {
            return if self.selected_spell.is_some() {
                self.spell_targets()
            } else {
                Ok(Vec::new())
            };
        }
        let enemy = 1 - actor.side.index();
        let alive = |slot: usize| {
            self.battle.rows()[enemy][usize::from(self.slots[enemy][slot])].count != 0
        };
        if actor.ranged {
            return Ok((0..6).filter(|slot| alive(*slot)).collect());
        }
        if actor.side == Side::Enemy {
            if actor.slot < 3 && alive(actor.slot) {
                return Ok(vec![actor.slot]);
            }
            let front: Vec<_> = (0..3).filter(|slot| alive(*slot)).collect();
            return Ok(if front.is_empty() {
                (3..6).filter(|slot| alive(*slot)).collect()
            } else {
                front
            });
        }
        let front_alive = (0..3).any(alive);
        Ok((0..6)
            .filter(|slot| {
                alive(*slot) && (*slot < 3 || (!front_alive && (*slot < 5 || !(0..5).any(alive))))
            })
            .collect())
    }
    fn attack_inner(&mut self, target: usize) -> Result<ActionResult, ControlError> {
        let actor = self.actor.ok_or(ControlError::NoActor)?;
        if self.is_caster() || self.is_enemy_caster() {
            return Err(ControlError::WrongPhase);
        }
        if target >= 6 || !self.legal_targets()?.contains(&target) {
            return Err(ControlError::InvalidTarget);
        }
        let side = actor.side.index();
        let target_raw = usize::from(self.slots[1 - side][target]);
        let motion = if actor.ranged {
            self.slots[side]
        } else {
            motion_plan(
                &self.battle.rows()[side],
                self.slots[side],
                actor.slot,
                target,
            )?
        };
        let action = if actor.slot < 3
            && self.battle.rows()[side][actor.raw]
                .unit
                .is_some_and(|id| id.is_native_caster())
        {
            self.battle
                .attack_front_caster(actor.side, actor.raw, target_raw, self.modifiers)?
        } else {
            self.battle
                .attack(actor.side, actor.raw, target_raw, self.modifiers)?
        };
        self.slots[side] = motion;
        self.actor = None;
        if self.battle.outcome().is_none() {
            self.sort_opponent()?;
        }
        self.scan = Scan::start();
        Ok(action)
    }
    pub fn attack(&mut self, target: usize) -> Result<ActionResult, ControlError> {
        let mut staged = self.clone();
        let action = staged.attack_inner(target)?;
        *self = staged;
        Ok(action)
    }
    pub fn skip(&mut self) -> Result<Actor, ControlError> {
        if self.actor.is_none_or(|actor| actor.side != Side::Player) {
            return Err(ControlError::NoActor);
        }
        if self.is_caster() {
            if self.selected_spell.is_some() {
                return Err(ControlError::WrongPhase);
            }
            let mut staged = self.clone();
            let actor = staged.actor.ok_or(ControlError::NoActor)?;
            staged.finish_cast()?;
            *self = staged;
            return Ok(actor);
        }
        let actor = self.actor.take().ok_or(ControlError::NoActor)?;
        if actor.slot < 3 {
            self.scan.front = actor.slot + 1;
        } else {
            self.scan.rear = actor.slot + 1;
        }
        Ok(actor)
    }
    pub fn retreat(&mut self) -> Result<Outcome, ControlError> {
        let returns = if self.is_caster() {
            self.spell_returns
                .checked_add(1)
                .ok_or(ControlError::Budget)?
        } else {
            self.spell_returns
        };
        let result = self.battle.retreat()?;
        self.actor = None;
        self.selected_spell = None;
        self.spell_returns = returns;
        Ok(result)
    }
    pub fn enemy_target(&self, rng: &mut OriginalRng) -> Result<usize, ControlError> {
        let actor = self.actor.ok_or(ControlError::NoActor)?;
        if actor.side != Side::Enemy {
            return Err(ControlError::NoActor);
        }
        let candidates = self.legal_targets()?;
        let mut staged = *rng;
        if !actor.ranged && candidates == [actor.slot] {
            staged.next15();
            *rng = staged;
            return Ok(actor.slot);
        }
        let (base, modulus) = if actor.ranged {
            (0, 6)
        } else if candidates.iter().any(|slot| *slot < 3) {
            (0, 3)
        } else {
            (3, 3)
        };
        for _ in 0..128 {
            let slot = base + usize::from(staged.next15()) % modulus;
            if candidates.contains(&slot) {
                *rng = staged;
                return Ok(slot);
            }
        }
        Err(ControlError::Budget)
    }

    pub fn is_caster(&self) -> bool {
        self.actor.is_some_and(|a| {
            a.side == Side::Player
                && a.slot >= 3
                && self.battle.rows()[0][a.raw]
                    .unit
                    .is_some_and(|id| id.is_native_caster())
        })
    }
    pub fn spell_book(&self) -> Option<&SpellBook> {
        self.book.as_ref()
    }
    pub fn selected_spell(&self) -> Option<Spell> {
        self.selected_spell
    }
    pub fn spell_returns(&self) -> u64 {
        self.spell_returns
    }
    fn caster_kind(&self) -> Result<u8, ControlError> {
        if !self.is_caster() {
            return Err(ControlError::WrongPhase);
        }
        let a = self.actor.ok_or(ControlError::NoActor)?;
        self.battle.rows()[0][a.raw]
            .unit
            .and_then(|id| id.native_kind())
            .ok_or(ControlError::UnsupportedArmy)
    }
    fn finish_cast(&mut self) -> Result<(), ControlError> {
        self.spell_returns = self
            .spell_returns
            .checked_add(1)
            .ok_or(ControlError::Budget)?;
        self.selected_spell = None;
        self.actor = None;
        self.scan = Scan::start();
        if self.battle.outcome().is_none() {
            self.sort_opponent()?;
        }
        Ok(())
    }
    pub fn spell_targets(&self) -> Result<Vec<usize>, ControlError> {
        self.caster_kind()?;
        let spell = self.selected_spell.ok_or(ControlError::WrongPhase)?;
        let side = if spell == Spell::Clone { 0 } else { 1 };
        Ok((0..6)
            .filter(|slot| {
                let row = self.battle.rows()[side][usize::from(self.slots[side][*slot])];
                row.count > 0 && row.unit.is_some_and(|id| id.native_kind().is_some())
            })
            .collect())
    }
    pub fn select_spell(&mut self, spell: Spell) -> Result<Option<SpellResult>, ControlError> {
        let mut staged = self.clone();
        staged.caster_kind()?;
        if staged.selected_spell.is_some() {
            return Err(ControlError::WrongPhase);
        }
        if staged.battle.rows()[1]
            .iter()
            .any(|s| s.count > 0 && s.unit.is_some_and(|id| id.native_kind().is_none()))
        {
            return Err(ControlError::UnsupportedArmy);
        }
        let book = staged.book.as_mut().ok_or(ControlError::WrongPhase)?;
        if !book.enabled || book.charges[spell.index()] == 0 {
            return Err(ControlError::NoCharge);
        }
        book.charges[spell.index()] -= 1;
        staged.selected_spell = Some(spell);
        let eligible = spell != Spell::Exorcism
            || staged.battle.rows()[1].iter().any(|s| {
                s.count > 0
                    && s.unit
                        .and_then(|id| id.native_kind())
                        .is_some_and(|n| (6..=15).contains(&n))
            });
        let result = if !spell.targeted() || !eligible {
            Some(staged.resolve_spell(None, None)?)
        } else {
            None
        };
        *self = staged;
        Ok(result)
    }
    pub fn target_spell(
        &mut self,
        target: usize,
        rng: &mut OriginalRng,
    ) -> Result<SpellResult, ControlError> {
        let mut staged = self.clone();
        let mut random = *rng;
        if !staged.spell_targets()?.contains(&target) {
            return Err(ControlError::InvalidTarget);
        }
        let result = staged.resolve_spell(Some(target), Some(&mut random))?;
        *self = staged;
        *rng = random;
        Ok(result)
    }
    pub fn cancel_spell_target(&mut self, retreat: bool) -> Result<(), ControlError> {
        let mut staged = self.clone();
        staged.caster_kind()?;
        let spell = staged.selected_spell.ok_or(ControlError::WrongPhase)?;
        if retreat {
            staged.battle.retreat()?;
        } else {
            let b = staged.book.as_mut().ok_or(ControlError::WrongPhase)?;
            b.charges[spell.index()] = b.charges[spell.index()]
                .checked_add(1)
                .ok_or(ControlError::Budget)?;
        }
        staged.finish_cast()?;
        *self = staged;
        Ok(())
    }
    fn resolve_spell(
        &mut self,
        target: Option<usize>,
        mut rng: Option<&mut OriginalRng>,
    ) -> Result<SpellResult, ControlError> {
        let kind = self.caster_kind()?;
        let actor = self.actor.ok_or(ControlError::NoActor)?;
        let spell = self.selected_spell.ok_or(ControlError::WrongPhase)?;
        let book = self.book.as_ref().ok_or(ControlError::WrongPhase)?;
        let stat = book.stat_26b0;
        let ability = book.stat_26ae;
        let mut result = SpellResult {
            spell,
            effects: Vec::new(),
            refunded: false,
            roll: None,
        };
        if spell == Spell::Freeze {
            for raw in self.slots[0] {
                self.remaining[0][usize::from(raw)] = self.remaining[0][usize::from(raw)]
                    .checked_add(1)
                    .ok_or(ControlError::Budget)?;
            }
        } else if spell == Spell::Clone {
            let slot = target.ok_or(ControlError::InvalidTarget)?;
            let raw = usize::from(self.slots[0][slot]);
            let before = self.battle.rows()[0][raw].count;
            let (scaled, after, _) = clone_plan(kind, before).map_err(ControlError::Spell)?;
            let display = if scaled >= before {
                (before..=scaled).map(|n| n as u16).collect()
            } else {
                Vec::new()
            };
            self.battle.spell_counts(&[(Side::Player, raw, after)])?;
            result.effects.push(SpellEffect {
                side: Side::Player,
                slot,
                raw,
                before,
                after,
                amount: 0,
                display,
            });
        } else {
            let targets: Vec<usize> = if matches!(spell, Spell::Thunder | Spell::Quake) {
                (0..6)
                    .filter(|s| self.battle.rows()[1][usize::from(self.slots[1][*s])].count > 0)
                    .collect()
            } else {
                target.into_iter().collect()
            };
            let success = if spell == Spell::Assassination {
                let roll = rng.as_mut().ok_or(ControlError::WrongPhase)?.next15();
                result.roll = Some(roll);
                u32::from(roll % 50) < u32::from(ability) * 10 + 10
            } else {
                true
            };
            let mut updates = Vec::new();
            for slot in targets {
                if !success {
                    break;
                }
                let raw = usize::from(self.slots[1][slot]);
                let row = self.battle.rows()[1][raw];
                let id = row.unit.ok_or(ControlError::UnsupportedArmy)?;
                let n = amount(
                    spell,
                    kind,
                    self.battle.rows()[0][actor.raw].count,
                    row.count,
                    self.catalog.get(id).hp,
                    id.native_kind().ok_or(ControlError::UnsupportedArmy)?,
                    stat,
                )
                .map_err(ControlError::Spell)?;
                let after = row.count.saturating_sub(u32::from(n));
                let display = if spell == Spell::Quake {
                    Vec::new()
                } else {
                    let start = if after == 0 {
                        row.count.min(5)
                    } else if n >= 5 {
                        after + 5
                    } else {
                        row.count
                    };
                    (after..=start).rev().map(|n| n as u16).collect()
                };
                result.effects.push(SpellEffect {
                    side: Side::Enemy,
                    slot,
                    raw,
                    before: row.count,
                    after,
                    amount: n,
                    display,
                });
                updates.push((Side::Enemy, raw, after));
            }
            if !updates.is_empty() {
                self.battle.spell_counts(&updates)?;
            }
        }
        self.finish_cast()?;
        Ok(result)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OriginalRng {
    pub seed: u32,
}
impl OriginalRng {
    pub fn next15(&mut self) -> u16 {
        self.seed = self.seed.wrapping_mul(214013).wrapping_add(2531011);
        ((self.seed >> 16) & 32767) as u16
    }
}
