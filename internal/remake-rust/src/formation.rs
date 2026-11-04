use crate::battle::{BattleError, Rows, Stack};
use crate::catalog::Catalog;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Formation {
    pub slots: [[u8; 6]; 2],
    pub hp: [[u64; 6]; 2],
}

pub fn initial_formation(catalog: &Catalog, rows: &Rows) -> Result<Formation, BattleError> {
    let mut plan = Formation {
        slots: [[u8::MAX; 6]; 2],
        hp: [[0; 6]; 2],
    };
    for (side, army) in rows.iter().enumerate() {
        let mut last_empty = 5;
        let mut occupied = [false; 6];
        let mut assigned = [false; 6];
        let mut seen = Vec::new();
        let place = |raw: usize, back: bool, slots: &mut [u8; 6], occupied: &mut [bool; 6]| {
            for index in 0..6 {
                let slot = if back { 5 - index } else { index };
                if !occupied[slot] {
                    slots[slot] = raw as u8;
                    occupied[slot] = true;
                    break;
                }
            }
        };
        for (raw, stack) in army.iter().enumerate() {
            match (stack.unit, stack.count) {
                (None, 0) => {
                    last_empty = raw as u8;
                    continue;
                }
                (Some(id), count) if count > 0 => {
                    if seen.contains(&id) {
                        return Err(BattleError::InvalidArmy);
                    }
                    seen.push(id);
                    plan.hp[side][raw] = catalog
                        .get(id)
                        .hp
                        .checked_mul(u64::from(count))
                        .ok_or(BattleError::Overflow)?;
                    if id.is_native_caster() {
                        place(raw, true, &mut plan.slots[side], &mut occupied);
                        assigned[raw] = true;
                    }
                }
                _ => return Err(BattleError::InvalidArmy),
            }
        }
        for (raw, stack) in army.iter().enumerate() {
            if let Some(id) = stack.unit {
                if !assigned[raw] {
                    place(
                        raw,
                        catalog.get(id).ranged,
                        &mut plan.slots[side],
                        &mut occupied,
                    );
                }
            }
        }
        for slot in &mut plan.slots[side] {
            if *slot == u8::MAX {
                *slot = last_empty;
            }
        }
    }
    Ok(plan)
}

fn valid_slots(slots: &[u8; 6]) -> Result<(), BattleError> {
    if slots.iter().any(|raw| *raw >= 6) {
        Err(BattleError::InvalidSlot)
    } else {
        Ok(())
    }
}

pub fn sort_plan(
    catalog: &Catalog,
    rows: &[Stack; 6],
    slots: [u8; 6],
    orders: [[u8; 3]; 4],
    caster_front: bool,
) -> Result<[u8; 6], BattleError> {
    valid_slots(&slots)?;
    if orders.iter().flatten().any(|slot| *slot >= 6) {
        return Err(BattleError::InvalidSlot);
    }
    let mut out = slots;
    for order in orders {
        for a in 0..3 {
            if rows[usize::from(out[usize::from(order[a])])].count > 0 {
                continue;
            }
            for b in a + 1..3 {
                let stack = rows[usize::from(out[usize::from(order[b])])];
                if stack.count == 0 {
                    continue;
                }
                let id = stack.unit.ok_or(BattleError::InvalidArmy)?;
                if catalog.get(id).ranged || (!caster_front && id.is_native_caster()) {
                    continue;
                }
                out.swap(usize::from(order[a]), usize::from(order[b]));
                break;
            }
        }
    }
    Ok(out)
}

pub fn motion_plan(
    rows: &[Stack; 6],
    slots: [u8; 6],
    from: usize,
    target: usize,
) -> Result<[u8; 6], BattleError> {
    valid_slots(&slots)?;
    if from >= 3 || target >= 6 {
        return Err(BattleError::InvalidSlot);
    }
    let to = if target < 3 {
        target
    } else if (from == 0 && target == 4) || (from == 2 && target == 3) {
        1
    } else {
        from
    };
    if rows[usize::from(slots[from])].count == 0 {
        return Err(BattleError::DeadStack);
    }
    let mut out = slots;
    let raw = out[from];
    if rows[usize::from(out[to])].count == 0 {
        out[from] = out[to];
    } else if from < to {
        for slot in from..to {
            out[slot] = out[slot + 1];
        }
    } else {
        for slot in (to + 1..=from).rev() {
            out[slot] = out[slot - 1];
        }
    }
    out[to] = raw;
    Ok(out)
}
