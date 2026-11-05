//! Spec031: native arithmetic migrated from the verified original-interface
//! Go player helper. No executable, emulated CPU, global state or asset loader.

pub mod battle;
pub mod catalog;
pub mod checkpoint_store;
pub mod controller;
pub mod media_assets;

#[cfg(feature = "desktop")]
pub mod desktop;
pub mod formation;
pub mod journey;
#[cfg(feature = "desktop")]
pub mod journey_desktop;
pub mod management;
#[cfg(feature = "desktop")]
pub(crate) mod management_ui;
pub mod pointer;
pub mod replay;
#[cfg(feature = "desktop")]
mod sdl;
#[cfg(feature = "desktop")]
mod sndfile;
pub mod spells;
pub mod world;
#[cfg(feature = "desktop")]
pub mod world_desktop;

#[cfg(test)]
mod native_tests;

#[cfg(test)]
mod controller_tests;
#[cfg(test)]
mod spell_tests;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AttackInput {
    pub attack: u64,
    pub count: u16,
    pub hp: u64,
    pub divisor: u16,
    pub multiplier: u16,
    pub pending_hp: u64,
    pub target_count: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AttackResult {
    pub damage: u64,
    pub encoded: u16,
    pub pending_after: u64,
    pub count_after: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AttackError {
    InvalidFactor,
    Overflow,
    CompatibilityRange,
}

pub fn player_attack(input: AttackInput) -> Result<AttackResult, AttackError> {
    let AttackInput {
        attack,
        count,
        hp,
        divisor,
        multiplier,
        pending_hp,
        target_count,
    } = input;
    if attack == 0 || hp == 0 || divisor == 0 || multiplier == 0 {
        return Err(AttackError::InvalidFactor);
    }
    let damage = attack
        .checked_mul(u64::from(count))
        .ok_or(AttackError::Overflow)?
        / u64::from(divisor);
    let damage = damage
        .checked_mul(u64::from(multiplier))
        .ok_or(AttackError::Overflow)?;
    // Bound damage before the +1 so u64::MAX cannot wrap during rejection.
    if damage > u64::from(u16::MAX) {
        return Err(AttackError::CompatibilityRange);
    }
    let encoded = damage / hp + 1;
    let encoded = u16::try_from(encoded).map_err(|_| AttackError::CompatibilityRange)?;
    Ok(AttackResult {
        damage,
        encoded,
        pending_after: pending_hp.saturating_sub(damage),
        count_after: target_count.saturating_sub(u32::from(encoded)),
    })
}

/// Strict migration receipt parser; this is not a game save format.
pub fn check_reference(text: &str) -> Result<usize, String> {
    let mut count = 0;
    for (index, line) in text.lines().enumerate() {
        if line.starts_with('#') || line.trim().is_empty() {
            continue;
        }
        let fields: Vec<_> = line.split('\t').collect();
        let fail = || format!("參考向量第 {} 行不符", index + 1);
        if fields.len() != 8 && fields.len() != 11 {
            return Err(fail());
        }
        let number = |at: usize| fields[at].parse::<u64>().map_err(|_| fail());
        let input = AttackInput {
            attack: number(0)?,
            count: number(1)?.try_into().map_err(|_| fail())?,
            hp: number(2)?,
            divisor: number(3)?.try_into().map_err(|_| fail())?,
            multiplier: number(4)?.try_into().map_err(|_| fail())?,
            pending_hp: number(5)?,
            target_count: number(6)?.try_into().map_err(|_| fail())?,
        };
        let actual = player_attack(input);
        if fields.len() == 8 {
            if fields[7] != "ERR" || actual.is_ok() {
                return Err(fail());
            }
        } else {
            let expected = AttackResult {
                damage: number(7)?,
                encoded: number(8)?.try_into().map_err(|_| fail())?,
                pending_after: number(9)?,
                count_after: number(10)?.try_into().map_err(|_| fail())?,
            };
            if actual != Ok(expected) {
                return Err(fail());
            }
        }
        count += 1;
    }
    if count == 0 {
        return Err("參考向量不可為空".into());
    }
    Ok(count)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn matches_verified_go_reference() {
        assert_eq!(check_reference(include_str!("../reference.tsv")), Ok(201));
    }

    #[test]
    fn rejects_corrupt_or_empty_receipts() {
        assert!(check_reference("").is_err());
        assert!(check_reference("1\t1\t1\t1\t1\t2\t3\tERR").is_err());
        assert!(check_reference("1\t65536\t1\t1\t1\t2\t3\tERR").is_err());
    }
}
