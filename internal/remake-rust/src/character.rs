//! Spec031 F1: original fields; inventory ownership remains outside this slice.
use crate::pointer::Rect;
pub const UI_TEXT: &str = "等級經驗月薪現金領導能力法術寶物八大名劍";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Field {
    pub label: String,
    pub label_box: Rect,
    pub value_box: Rect,
    pub value: u64,
}
pub fn fields(resources: [u64; 6]) -> Result<[Field; 6], String> {
    if !(1..=5).contains(&resources[0]) || resources.iter().any(|n| *n > 30000) {
        return Err("人物資料超界".into());
    }
    let mut rows = Vec::new();
    for line in include_str!("../character-layout.tsv").lines() {
        if line.starts_with('#') {
            continue;
        }
        let f: Vec<_> = line.split('\t').collect();
        if f.first() != Some(&"STAT") {
            continue;
        }
        if f.len() != 6 {
            return Err("人物欄位格式錯誤".into());
        }
        let n = |i: usize| {
            f[i].parse::<i32>()
                .map_err(|_| "人物欄位座標錯誤".to_string())
        };
        let index = usize::try_from(n(1)?).map_err(|_| "人物欄位索引錯誤")?;
        if index != rows.len() || index >= 6 {
            return Err("人物欄位順序錯誤".into());
        }
        rows.push(Field {
            label: f[5].into(),
            label_box: Rect(n(2)?, n(3)?, 240, 96),
            value_box: Rect(n(4)?, n(3)?, 240, 96),
            value: resources[index],
        });
    }
    rows.try_into().map_err(|_| "人物欄位數量錯誤".into())
}
pub fn heading(swords: bool) -> Result<&'static str, String> {
    include_str!("../character-layout.tsv")
        .lines()
        .find_map(|line| {
            let f: Vec<_> = line.split('\t').collect();
            (f.len() == 3 && f[0] == "HEADING" && f[1] == if swords { "1" } else { "0" })
                .then(|| f[2])
        })
        .ok_or_else(|| "缺少人物頁標題".into())
}

#[cfg(all(test, feature = "desktop"))]
mod tests {
    use super::*;
    use crate::{
        catalog::Catalog,
        journey::Journey,
        management_ui::{Manager, Page},
        world::WorldData,
    };
    #[test]
    fn original_fields_are_read_only_across_toggle_save_and_cold_load() {
        let c = Catalog::builtin().unwrap();
        let d = WorldData::flat_fixture();
        let mut j = Journey::new(&d, 1);
        j.resources = [5, 30000, 30000, 30000, 30000, 30000];
        j.world.rank = 5;
        let before = j.encode(&c, &d).unwrap();
        let mut ui = Manager::default();
        ui.key(1073741882, &mut j, &c, &d);
        assert_eq!(ui.page, Page::Character);
        let rows = fields(j.resources).unwrap();
        assert_eq!(
            rows.iter().map(|r| r.value).collect::<Vec<_>>(),
            j.resources
        );
        for r in rows {
            let width: i32 = r
                .label
                .chars()
                .map(|c| if c.is_ascii() { 24 } else { 48 })
                .sum();
            assert!(width <= r.label_box.2 && r.label_box.0 + width < r.value_box.0);
            assert!(r.value.to_string().len() as i32 * 24 <= r.value_box.2);
            assert!(r.value_box.1 + r.value_box.3 <= 1170);
        }
        ui.key(13, &mut j, &c, &d);
        assert!(ui.swords);
        assert_eq!(heading(true).unwrap(), "八大名劍 :");
        ui.key(1073741903, &mut j, &c, &d);
        assert!(ui.swords);
        ui.key(13, &mut j, &c, &d);
        assert_eq!(ui.page, Page::World);
        ui.key(1073741882, &mut j, &c, &d);
        assert!(!ui.swords);
        ui.key(27, &mut j, &c, &d);
        assert_eq!(ui.page, Page::World);
        assert_eq!(j.encode(&c, &d).unwrap(), before);
        let mut cold = Journey::decode(&c, &d, &before).unwrap();
        ui.key(1073741882, &mut cold, &c, &d);
        assert_eq!(
            fields(cold.resources).unwrap(),
            fields(j.resources).unwrap()
        );
        assert_eq!(cold.encode(&c, &d).unwrap(), before);
        assert!(fields([0; 6]).is_err());
        assert!(fields([1, 0, 0, 30001, 0, 0]).is_err());
    }
    #[test]
    fn character_cannot_open_over_another_world_event() {
        let c = Catalog::builtin().unwrap();
        let d = WorldData::flat_fixture();
        let mut j = Journey::new(&d, 1);
        j.camps.pending = Some(1);
        let mut ui = Manager::default();
        ui.key(1073741882, &mut j, &c, &d);
        assert_eq!(ui.page, Page::World);
        j.camps.pending = None;
        j.cue = Some(1);
        ui.key(1073741882, &mut j, &c, &d);
        assert_eq!(ui.page, Page::World);
    }
}
