//! Spec031, original sub_1E8A4 / DS:26B0 and DS:26AE. No emulated code.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Spell {
    Fireball,
    Thunder,
    Exorcism,
    Assassination,
    Freeze,
    Halve,
    Clone,
    Quake,
}
impl Spell {
    pub const ALL: [Self; 8] = [
        Self::Fireball,
        Self::Thunder,
        Self::Exorcism,
        Self::Assassination,
        Self::Freeze,
        Self::Halve,
        Self::Clone,
        Self::Quake,
    ];
    pub fn index(self) -> usize {
        Self::ALL
            .iter()
            .position(|s| *s == self)
            .expect("closed spell enum")
    }
    pub fn name(self) -> &'static str {
        [
            "火球術",
            "雷火術",
            "殺鬼術",
            "暗殺術",
            "凝滯術",
            "滅半術",
            "複製術",
            "地震術",
        ][self.index()]
    }
    pub fn targeted(self) -> bool {
        !matches!(self, Self::Thunder | Self::Freeze | Self::Quake)
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpellBook {
    pub enabled: bool,
    pub charges: [u16; 8],
    pub stat_26b0: u16,
    pub stat_26ae: u16,
}
impl SpellBook {
    pub fn available(&self) -> bool {
        self.enabled && self.charges.iter().any(|n| *n > 0)
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpellError {
    Identity,
    Range,
    Empty,
    Unsupported,
}

/// Same truncation and compatibility bounds as verified Go originalSpellAmount.
pub fn amount(
    spell: Spell,
    kind: u8,
    source: u32,
    target: u32,
    hp: u64,
    target_kind: u8,
    stat: u16,
) -> Result<u16, SpellError> {
    if !matches!(kind, 10 | 12) || source == 0 || source > 32767 || target == 0 || target > 32767 {
        return Err(SpellError::Identity);
    }
    let stat = u64::from(stat);
    let value = match spell {
        Spell::Fireball | Spell::Thunder | Spell::Exorcism => {
            let ghost = spell == Spell::Exorcism;
            let factor = match (ghost, kind) {
                (true, 12) => stat * 4 + 6,
                (true, _) => stat * 10 + 10,
                (false, 12) => stat * 2 + 2,
                (false, _) => stat * 5 + 5,
            };
            if ghost && !(6..=15).contains(&target_kind) {
                factor
            } else {
                let term = if ghost {
                    u64::from(source) + 1
                } else {
                    u64::from(source / 3 + 1)
                };
                let product = term * factor;
                if hp / 10 == 0 || product > 65535 {
                    return Err(SpellError::Range);
                }
                product / (hp / 10) + 2
            }
        }
        Spell::Assassination => u64::from(target),
        Spell::Halve => u64::from(target / 2 + 1),
        Spell::Quake => {
            if target < 50 {
                u64::from(target)
            } else {
                let product = u64::from(target) * 6;
                if product > 65535 {
                    return Err(SpellError::Range);
                }
                product / if kind == 12 { 20 } else { 10 } + stat * 10 + 1
            }
        }
        _ => return Err(SpellError::Unsupported),
    };
    value.try_into().map_err(|_| SpellError::Range)
}
pub fn clone_plan(kind: u8, count: u32) -> Result<(u32, u32, u16), SpellError> {
    if !matches!(kind, 10 | 12) || count == 0 || count > 32767 {
        return Err(SpellError::Identity);
    }
    let factor = match count {
        0..50 => 20,
        50..100 => 14,
        100..200 => 13,
        200..300 => 12,
        300..400 => 11,
        _ => 10,
    };
    let product = count * factor;
    if product > 65535 {
        return Err(SpellError::Range);
    }
    let scaled = product / if kind == 12 { 20 } else { 10 };
    if scaled > 32767 {
        return Err(SpellError::Range);
    }
    Ok((scaled, scaled.max(count), factor as u16))
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpellEffect {
    pub side: crate::battle::Side,
    pub slot: usize,
    pub raw: usize,
    pub before: u32,
    pub after: u32,
    pub amount: u16,
    pub display: Vec<u16>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpellResult {
    pub spell: Spell,
    pub effects: Vec<SpellEffect>,
    pub refunded: bool,
    pub roll: Option<u16>,
}
