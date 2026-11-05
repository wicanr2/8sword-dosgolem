//! Spec031 natural bamboo book, bridge shop and original F4 bridge effect.
use crate::catalog::Catalog;
use crate::journey::Journey;
use crate::media_assets::checksum;
use crate::world::{Boundary, Position, WalkResult, WorldData};
pub fn supported(offer: u8) -> bool {
    matches!(offer, 0 | 1 | 2 | 4 | 5)
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Shop {
    pub area: u8,
    pub row: u8,
    pub x: u8,
    pub y: u8,
    pub offer: u8,
}
pub fn shops() -> &'static Vec<Shop> {
    static DATA: std::sync::OnceLock<Vec<Shop>> = std::sync::OnceLock::new();
    DATA.get_or_init(|| {
        include_str!("../magic-shops.tsv")
            .lines()
            .filter(|s| !s.starts_with('#'))
            .map(|s| {
                let f: Vec<u8> = s
                    .split('\t')
                    .map(|v| v.parse().expect("fixed shop integer"))
                    .collect();
                assert!(f.len() == 5 && f[0] < 8 && f[2] < 70 && f[3] < 80 && f[4] < 16);
                Shop {
                    area: f[0],
                    row: f[1],
                    x: f[2],
                    y: f[3],
                    offer: f[4],
                }
            })
            .collect()
    })
}
pub fn items() -> Vec<[u8; 4]> {
    include_str!("../magic-items.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
        .map(|s| {
            let f: Vec<u8> = s
                .split('\t')
                .map(|v| v.parse().expect("fixed item integer"))
                .collect();
            f.try_into().expect("fixed item columns")
        })
        .collect()
}
pub fn names() -> Vec<(&'static str, &'static str, u16)> {
    include_str!("../magic-names.tsv")
        .lines()
        .map(|s| {
            let f: Vec<_> = s.split('\t').collect();
            (f[0], f[1], f[2].parse().expect("fixed price"))
        })
        .collect()
}
pub fn fingerprint() -> u64 {
    checksum(
        [
            include_bytes!("../magic-shops.tsv").as_slice(),
            include_bytes!("../magic-items.tsv"),
            include_bytes!("../magic-names.tsv"),
        ]
        .concat()
        .as_slice(),
    )
}
pub fn validate_maps(d: &WorldData) -> Result<(), String> {
    for a in 0..8 {
        let mut actual = Vec::new();
        for y in 0..80 {
            for x in 0..70 {
                if d.tile(a, Position { x, y })? == 53 {
                    actual.push((x, y));
                }
            }
        }
        let expected: Vec<_> = shops()
            .iter()
            .filter(|s| s.area == a)
            .map(|s| (s.x, s.y))
            .collect();
        if actual != expected {
            return Err("法術商店位置或順序不符".into());
        }
    }
    Ok(())
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PendingShop {
    pub index: u8,
    pub moved: bool,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Magic {
    pub book: bool,
    pub charges: [u16; 8],
    pub selected: u8,
    pub shop: Option<PendingShop>,
    pub direction: bool,
    pub bridges: Vec<u16>,
}
impl Magic {
    pub fn view(&self, d: &WorldData) -> Result<WorldData, String> {
        d.with_bridges(&self.bridges)
    }
    pub(crate) fn validate(&self, j: &Journey<'_>, d: &WorldData) -> Result<(), String> {
        self.view(d)?;
        if self.selected >= 8
            || [self.charges[3], self.charges[6], self.charges[7]]
                .iter()
                .any(|n| *n != 0)
            || (!self.book
                && (self.charges != [0; 8] || self.direction || !self.bridges.is_empty()))
            || self.charges.iter().map(|n| u64::from(*n)).sum::<u64>() + u64::from(self.direction)
                > j.resources[5]
            || self.shop.is_some() && self.direction
        {
            return Err("地圖法術資料超出已接範圍".into());
        }
        if self.shop.is_some() || self.direction {
            if j.battle.is_some()
                || j.cue.is_some()
                || j.camps.pending.is_some()
                || j.month.pending.is_some()
                || j.treasure.pending.is_some()
            {
                return Err("地圖法術階段衝突".into());
            }
        }
        if let Some(p) = self.shop {
            let s = shops()
                .get(usize::from(p.index))
                .ok_or("法術商店索引超界")?;
            if !supported(s.offer)
                || (j.world.area, j.world.position.x, j.world.position.y) != (s.area, s.x, s.y)
                || d.tile(s.area, j.world.position)? != 53
            {
                return Err("法術商店位置錯誤".into());
            }
        }
        if self.direction && (!self.book || self.selected != 0) {
            return Err("造橋方向階段錯誤".into());
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    pub fn search_book(&mut self) -> Result<bool, String> {
        if self.phase() != "world" {
            return Err("目前不能尋寶".into());
        }
        let found = items().into_iter().find(|s| {
            (s[1], s[2], s[3])
                == (
                    self.world.area,
                    self.world.position.x,
                    self.world.position.y,
                )
        });
        match found {
            Some([0, _, _, _]) if !self.magic.book => {
                self.magic.book = true;
                self.resources[5] = 3;
                Ok(true)
            }
            Some([0, _, _, _]) | None => Ok(false),
            _ => Err("此寶物取得尚未接入".into()),
        }
    }
    pub(crate) fn open_magic_shop(&mut self, d: &WorldData, key: u16) -> Result<bool, String> {
        let (at, _) = crate::world::motion(self.world.position, key, self.world.facing, false)?;
        let Some(i) = shops().iter().position(|s| {
            s.area == self.world.area && s.x == at.x && s.y == at.y && supported(s.offer)
        }) else {
            return Ok(false);
        };
        self.world = self.world.event_step(d, key, 53)?;
        self.magic.shop = Some(PendingShop {
            index: i as u8,
            moved: key != 0x3920,
        });
        Ok(true)
    }
    pub fn buy_bridge(&mut self) -> Result<(), String> {
        self.buy_world_spell()
    }
    pub fn magic_offer(&self) -> Result<usize, String> {
        let p = self.magic.shop.ok_or("未在法術商店")?;
        let s = shops()
            .get(usize::from(p.index))
            .ok_or("法術商店索引錯誤")?;
        if !supported(s.offer) {
            return Err("未接法術商品".into());
        }
        Ok(usize::from(s.offer))
    }
    pub fn buy_world_spell(&mut self) -> Result<(), String> {
        let index = self.magic_offer()?;
        let price = u64::from(names()[index].2);
        if !self.magic.book {
            return Err("你不會使用法術".into());
        }
        if self
            .magic
            .charges
            .iter()
            .map(|n| u64::from(*n))
            .sum::<u64>()
            >= self.resources[5]
        {
            return Err("法術容量已滿".into());
        }
        if self.resources[3] < price {
            return Err("金錢不足".into());
        }
        let count = self.magic.charges[index]
            .checked_add(1)
            .ok_or("法術次數超界")?;
        self.resources[3] -= price;
        self.magic.charges[index] = count;
        Ok(())
    }
    pub fn close_magic_shop(&mut self, c: &Catalog, d: &WorldData) -> Result<(), String> {
        self.magic.validate(self, d)?;
        let view = self.magic.view(d)?;
        let mut s = self.clone();
        let p = s.magic.shop.take().ok_or("沒有待完成法術商店")?;
        if p.moved {
            if s.world.remaining == 1 {
                s.begin_month(c, &view, 53)?;
                *self = s;
                return Ok(());
            }
            s.world.remaining -= 1;
        }
        match s.world.walk_site(&view, 53)? {
            WalkResult::Boundary(Boundary::Encounter(cue)) => {
                if s.army[0].count > 0 {
                    s.cue = Some(cue)
                }
            }
            WalkResult::Boundary(b) => return Err(format!("法術商店返回邊界：{b:?}")),
            _ => {}
        }
        *self = s;
        Ok(())
    }
    pub fn begin_bridge(&mut self) -> Result<(), String> {
        if self.phase() != "world" || !self.magic.book || self.magic.charges[0] == 0 {
            return Err("目前不能施展造橋術".into());
        }
        self.magic.charges[0] -= 1;
        self.magic.selected = 0;
        self.magic.direction = true;
        Ok(())
    }
    pub fn finish_bridge(&mut self, d: &WorldData, key: u16) -> Result<(), String> {
        self.magic.validate(self, d)?;
        if !self.magic.direction {
            return Err("沒有等待造橋方向".into());
        }
        let (dx, dy) = match key {
            0x4800 => (0, -1),
            0x5000 => (0, 1),
            0x4b00 => (-1, 0),
            0x4d00 => (1, 0),
            0x4700 | 0x4900 | 0x4f00 | 0x5100 | 0x3920 => (0, 0),
            _ => return Err("等待方向或Space".into()),
        };
        let mut s = self.clone();
        let view = s.magic.view(d)?;
        if key == 0x3920 {
            s.world.remaining = s.world.remaining.checked_add(1).ok_or("剩餘步數超界")?;
        }
        if (dx, dy) != (0, 0) {
            let p = s.world.position;
            let center = view.tile(s.world.area, p)?;
            for n in [1, if (3..=10).contains(&center) { 0 } else { 2 }] {
                let at = Position {
                    x: (i32::from(p.x) + dx * n).rem_euclid(70) as u8,
                    y: (i32::from(p.y) + dy * n).rem_euclid(80) as u8,
                };
                if (2..=14).contains(&view.tile(s.world.area, at)?) {
                    let index =
                        u16::from(s.world.area) * 5600 + u16::from(at.y) * 70 + u16::from(at.x);
                    if let Err(i) = s.magic.bridges.binary_search(&index) {
                        s.magic.bridges.insert(i, index);
                    }
                }
            }
        }
        s.magic.direction = false;
        s.magic.validate(&s, d)?;
        *self = s;
        Ok(())
    }
}
#[cfg(test)]
#[path = "world_magic_tests.rs"]
mod tests;
