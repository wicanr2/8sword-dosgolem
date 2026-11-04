use crate::battle::{ActionResult, Battle, BattleError, Modifiers, Outcome, Rows, Side};
use crate::catalog::Catalog;
use crate::formation::{initial_formation, motion_plan, sort_plan};

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
}

impl<'a> Controller<'a> {
    pub fn new(
        catalog: &'a Catalog,
        rows: Rows,
        first: Side,
        modifiers: Modifiers,
    ) -> Result<Self, ControlError> {
        for stack in rows.iter().flatten() {
            if stack.count > 32767 || stack.unit.is_some_and(|id| id.is_native_caster()) {
                return Err(ControlError::UnsupportedArmy);
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
        self.slots[side] = sort_plan(
            self.catalog,
            &self.battle.rows()[side],
            self.slots[side],
            ORDERS,
            false,
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
                if stack.count != 0 && self.remaining[side][raw] != 0 && (slot < 3 || ranged) {
                    self.remaining[side][raw] -= 1;
                    self.scan.activity |= ranged;
                    let actor = Actor {
                        side: self.side,
                        slot,
                        raw,
                        ranged,
                    };
                    self.actor = Some(actor);
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
        let action = self
            .battle
            .attack(actor.side, actor.raw, target_raw, self.modifiers)?;
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
        let actor = self.actor.take().ok_or(ControlError::NoActor)?;
        if actor.slot < 3 {
            self.scan.front = actor.slot + 1;
        } else {
            self.scan.rear = actor.slot + 1;
        }
        Ok(actor)
    }
    pub fn retreat(&mut self) -> Result<Outcome, ControlError> {
        let result = self.battle.retreat()?;
        self.actor = None;
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
