//! Spec031: original eight items, with one owner for each persisted flag.
use crate::{battle::Modifiers, journey::Journey, media_assets::checksum};
pub const SUFFIX: usize = 9;
pub const MASK: u8 = 0x9e; // 1/2/3/4/7; book and movement flags already exist.
pub fn names() -> [&'static str; 8] {
    include_str!("../item-names.tsv")
        .lines()
        .collect::<Vec<_>>()
        .try_into()
        .expect("eight original names")
}
pub fn fingerprint() -> u64 {
    checksum(include_bytes!("../item-names.tsv"))
}
pub fn recruit_ceiling(lead: u64, used: u64, cost: u64, token: bool) -> Result<u64, String> {
    if lead > 30000 || used > lead || cost == 0 {
        return Err("超出領導用量或單兵用量錯誤".into());
    }
    let count = ((lead - used) / cost) as u16;
    // Original155E4 shifts the already divided word, then tests it signed.
    Ok(
        i16::from_le_bytes(if token { count.wrapping_mul(2) } else { count }.to_le_bytes()).max(0)
            as u64,
    )
}
impl Journey<'_> {
    pub fn has_item(&self, index: usize) -> bool {
        match index {
            0 => self.magic.book,
            5 => self.world.bamboo,
            6 => self.world.mountain,
            1..=4 | 7 => self.artifacts & (1 << index) != 0,
            _ => false,
        }
    }
    pub fn item_flags(&self) -> [bool; 8] {
        std::array::from_fn(|i| self.has_item(i))
    }
    pub fn item_modifiers(&self) -> Modifiers {
        Modifiers {
            player_attack: u16::from(self.has_item(4)),
            player_boost: u16::from(self.has_item(7)),
            enemy_defense: u16::from(self.has_item(1)),
        }
    }
    pub fn displayed_leadership(&self) -> u64 {
        self.resources[4] * if self.has_item(7) { 2 } else { 1 }
    }
    pub fn search_item(&mut self) -> Result<Option<u8>, String> {
        if self.phase() != "world" {
            return Err("目前不能尋寶".into());
        }
        let mut s = self.clone();
        // Original17FC6 -> sub16226 -> _rand, even for empty/repeated searches.
        s.world.rng.next15();
        let found = crate::world_magic::items()
            .into_iter()
            .find(|v| {
                (v[1], v[2], v[3]) == (s.world.area, s.world.position.x, s.world.position.y)
                    && !s.has_item(usize::from(v[0]))
            })
            .map(|v| v[0]);
        if let Some(i) = found {
            match i {
                0 => {
                    s.magic.book = true;
                    s.resources[5] = 3;
                }
                5 => s.world.bamboo = true,
                6 => s.world.mountain = true,
                _ => s.artifacts |= 1 << i,
            }
        }
        *self = s;
        Ok(found)
    }
}
#[cfg(test)]
#[path = "items_tests.rs"]
mod tests;
