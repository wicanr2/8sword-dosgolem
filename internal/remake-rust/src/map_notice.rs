//! Spec031: sub145FA scan, sub1649A text and124DE notice before time/shore.
use crate::{
    catalog::Catalog,
    journey::Journey,
    media_assets::checksum,
    world::{Position, WorldData, motion},
};
#[derive(Clone, Copy, Debug)]
pub struct Site {
    pub area: u8,
    pub index: u8,
    pub position: Position,
    pub text_hash: u64,
}
/// Up to three 72px rows inside [72,792,1248,252]. ASCII uses half-width.
pub fn lines(text: &str) -> Result<Vec<String>, String> {
    let chars: Vec<char> = text.chars().collect();
    if chars.len() > 60 || chars.iter().any(|c| c.is_control()) {
        return Err("地圖提示超出文字安全區".into());
    }
    let mut rows = Vec::new();
    let mut row = String::new();
    let mut width = 0;
    for ch in chars {
        let w = if ch.is_ascii() { 36 } else { 72 };
        if width + w > 1248 {
            rows.push(row);
            row = String::new();
            width = 0;
        }
        row.push(ch);
        width += w;
    }
    if !row.is_empty() {
        rows.push(row);
    }
    if rows.len() > 3 {
        return Err("地圖提示超出三行".into());
    }
    Ok(rows)
}
pub fn sites() -> &'static [Site] {
    static S: std::sync::OnceLock<Vec<Site>> = std::sync::OnceLock::new();
    S.get_or_init(|| {
        include_str!("../notice-catalog.tsv")
            .lines()
            .filter(|s| !s.starts_with('#'))
            .map(|line| {
                let v: Vec<u64> = line
                    .split('\t')
                    .map(|s| s.parse().expect("fixed notice integer"))
                    .collect();
                assert_eq!(v.len(), 5);
                assert!(v[0] < 8 && v[1] < 31 && v[2] < 70 && v[3] < 80);
                Site {
                    area: v[0] as u8,
                    index: v[1] as u8,
                    position: Position {
                        x: v[2] as u8,
                        y: v[3] as u8,
                    },
                    text_hash: v[4],
                }
            })
            .collect()
    })
}
pub fn parse_texts(raw: &str) -> Result<Vec<String>, String> {
    let lines: Vec<_> = raw.lines().collect();
    if raw.len() > 32768 || lines.len() != sites().len() {
        return Err("地圖提示數量錯誤".into());
    }
    for (text, s) in lines.iter().zip(sites()) {
        if text.chars().count() > 60
            || text.chars().any(char::is_control)
            || checksum(text.as_bytes()) != s.text_hash
        {
            return Err("地圖提示文字不符".into());
        }
    }
    Ok(lines.into_iter().map(str::to_owned).collect())
}
pub(crate) fn load_texts(root: &std::path::Path) -> Result<Vec<String>, String> {
    let p = root.join("map-notices.tsv");
    let st = p.symlink_metadata().map_err(|e| e.to_string())?;
    if !st.is_file() || st.len() > 32768 {
        return Err("地圖提示檔案錯誤".into());
    }
    parse_texts(&std::fs::read_to_string(p).map_err(|e| e.to_string())?)
}
pub fn validate_maps(d: &WorldData) -> Result<(), String> {
    for area in 0..8 {
        let mut i = 0;
        for y in 0..80 {
            for x in 0..70 {
                let p = Position { x, y };
                if d.tile(area, p)? == 51 {
                    if !sites()
                        .iter()
                        .any(|s| s.area == area && s.index == i && s.position == p)
                    {
                        return Err("原圖提示順序不符".into());
                    }
                    i += 1;
                }
            }
        }
        if usize::from(i) != sites().iter().filter(|s| s.area == area).count() {
            return Err("原圖提示數量不符".into());
        }
    }
    Ok(())
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Notice {
    pub site: u8,
    pub key: u16,
}
impl Notice {
    pub(crate) fn validate(&self, j: &Journey<'_>, d: &WorldData) -> Result<(), String> {
        let s = sites().get(usize::from(self.site)).ok_or("提示索引超界")?;
        if !crate::jump_spell::DIRECTIONS.contains(&self.key) && self.key != 0x3920 {
            return Err("提示按鍵錯誤".into());
        }
        let position = if j.world.boat == 2 {
            if !crate::jump_spell::DIRECTIONS.contains(&self.key)
                && !(self.key == 0x3920 && j.wait_event.is_some())
            {
                return Err("未接提示上岸方向".into());
            }
            motion(j.world.position, self.key, j.world.facing, false)?.0
        } else {
            if self.key != 0x3920
                && motion(j.world.position, self.key, j.world.facing, false)?.1 != j.world.facing
            {
                return Err("提示方向不符".into());
            }
            j.world.position
        };
        if s.area != j.world.area
            || s.position != position
            || d.tile(s.area, position)? != 51
            || j.theft.is_some()
            || j.cue.is_some()
            || j.battle.is_some()
            || j.month.pending.is_some()
            || j.camps.pending.is_some()
            || j.treasure.pending.is_some()
            || j.magic.direction
            || j.magic.shop.is_some()
            || j.resource_notice.is_some()
            || j.survey.bird
            || j.travel_spell.shore.is_some()
            || j.travel_spell.teleport.is_some()
            || j.travel_spell.refused_shop.is_some()
            || matches!(j.travel_spell.jump, crate::jump_spell::Jump::Flying { .. })
        {
            return Err("地圖提示與位置或階段不符".into());
        }
        Ok(())
    }
}
impl<'a> Journey<'a> {
    pub(crate) fn open_map_notice(&mut self, d: &WorldData, key: u16) -> Result<(), String> {
        if self.phase() != "world" {
            return Err("目前不能開啟提示".into());
        }
        let target = motion(self.world.position, key, self.world.facing, false)?.0;
        let i = sites()
            .iter()
            .position(|s| s.area == self.world.area && s.position == target)
            .ok_or("沒有原圖提示")?;
        let mut s = self.clone();
        if s.world.boat == 2 {
            if !crate::jump_spell::DIRECTIONS.contains(&key)
                && !(key == 0x3920 && s.wait_event.is_some())
            {
                return Err("未接提示上岸方向".into());
            }
            s.world = s.world.prepare_shore(d, key)?;
        } else {
            s.world = s.world.event_step(d, key, 51)?;
            s.world.reveal();
        }
        let n = Notice { site: i as u8, key };
        s.map_notice = Some(n);
        n.validate(&s, d)?;
        *self = s;
        Ok(())
    }
    pub(crate) fn finish_notice_tail(
        &mut self,
        d: &WorldData,
        key: u16,
        c: &Catalog,
    ) -> Result<(), String> {
        let view = self.magic.view(d)?;
        if self.wait_event.is_some() {
            return self.run_encounter_tail(&view);
        }
        if key != 0x3920 && self.world.remaining == 1 {
            self.begin_month(c, &view, 51)?
        } else {
            if key != 0x3920 {
                self.world.remaining -= 1;
            }
            self.run_encounter_tail(&view)?;
        }
        Ok(())
    }
    pub fn close_map_notice(&mut self, d: &WorldData, c: &Catalog) -> Result<(), String> {
        let n = self.map_notice.ok_or("沒有待確認地圖提示")?;
        n.validate(self, d)?;
        let mut s = self.clone();
        s.map_notice = None;
        if s.world.boat == 2 {
            s.travel_spell.shore = Some(crate::travel_spells::Shore {
                key: n.key,
                yes: true,
            });
        } else {
            s.finish_notice_tail(d, n.key, c)?;
        }
        *self = s;
        Ok(())
    }
}
#[cfg(test)]
#[path = "map_notice_tests.rs"]
mod tests;
