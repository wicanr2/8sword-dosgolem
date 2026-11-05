//! Spec031: F5 projects the saved exploration mask, without advancing the world.
use crate::pointer::Rect;
use crate::world::{Position, WorldData, WorldState};
pub const REGION: Rect = Rect(300, 126, 840, 960);
pub const UI_TEXT: &str = "現在位置查看地圖返回地圖，";
pub const RGB: [[u8; 3]; 16] = [
    [0, 0, 0],
    [0, 0, 170],
    [0, 170, 0],
    [0, 170, 170],
    [170, 0, 0],
    [170, 0, 170],
    [170, 85, 0],
    [170, 170, 170],
    [85, 85, 85],
    [85, 85, 255],
    [85, 255, 85],
    [85, 255, 255],
    [255, 85, 85],
    [255, 85, 255],
    [255, 255, 85],
    [255, 255, 255],
];
pub fn color(tile: u8) -> Result<u8, String> {
    Ok(match tile {
        0 | 47 | 48 => 0,
        1 | 3..=10 | 59 => 10,
        2 | 11..=14 => 9,
        15..=30 => 6,
        31..=45 => 14,
        46 => 2,
        52 => 7,
        49..=65 => 12,
        _ => return Err("地圖總覽地形錯誤".into()),
    })
}
pub fn cell(position: Position) -> Result<Rect, String> {
    if position.x >= 70 || position.y >= 80 {
        return Err("地圖總覽座標錯誤".into());
    }
    Ok(Rect(
        REGION.0 + i32::from(position.x) * 12,
        REGION.1 + i32::from(position.y) * 12,
        12,
        12,
    ))
}
pub fn cells(data: &WorldData, state: &WorldState) -> Result<Vec<u8>, String> {
    project(data, state, false)
}
pub fn all_cells(data: &WorldData, state: &WorldState) -> Result<Vec<u8>, String> {
    project(data, state, true)
}
fn project(data: &WorldData, state: &WorldState, full: bool) -> Result<Vec<u8>, String> {
    state.encode(data)?;
    let mask = &state.explored[usize::from(state.area)];
    (0..5600)
        .map(|i| {
            if !full && mask[i / 8] & (1 << (i % 8)) == 0 {
                Ok(0)
            } else {
                color(data.tile(
                    state.area,
                    Position {
                        x: (i % 70) as u8,
                        y: (i / 70) as u8,
                    },
                )?)
            }
        })
        .collect()
}

#[cfg(all(test, feature = "desktop"))]
mod tests {
    use super::*;
    use crate::{
        catalog::Catalog,
        journey::Journey,
        management_ui::{Manager, Page},
        pointer::{self, Screen},
    };
    #[test]
    fn fixed_original_colors_and_sparse_5600_cell_receipt_match() {
        let mut count = 0;
        for line in include_str!("../minimap-colors.tsv")
            .lines()
            .filter(|s| !s.starts_with('#'))
        {
            let f: Vec<u8> = line.split('\t').map(|s| s.parse().unwrap()).collect();
            assert_eq!(color(f[0]).unwrap(), f[1]);
            count += 1;
        }
        assert_eq!(count, 66);
        assert!(color(66).is_err());
        let data = WorldData::minimap_fixture();
        let mut state = WorldState::new(&data, 1);
        state.explored[0].fill(0);
        let mut expected = vec![[0; 3]; 5600];
        for line in include_str!("../minimap-reference.tsv")
            .lines()
            .filter(|s| !s.starts_with('#'))
        {
            let f: Vec<u8> = line.split('\t').map(|s| s.parse().unwrap()).collect();
            let at = usize::from(f[1]) * 70 + usize::from(f[0]);
            state.explored[0][at / 8] |= 1 << (at % 8);
            expected[at] = if f[6] == 1 {
                RGB[10]
            } else {
                [f[3], f[4], f[5]]
            };
        }
        let before = state.clone();
        let actual = cells(&data, &state).unwrap();
        assert_eq!(
            actual
                .iter()
                .map(|c| RGB[usize::from(*c)])
                .collect::<Vec<_>>(),
            expected
        );
        assert_eq!(state, before);
    }
    #[test]
    fn mask_stays_private_to_each_area_and_geometry_is_bounded() {
        let data = WorldData::flat_fixture();
        let mut state = WorldState::new(&data, 1);
        assert_eq!(
            cells(&data, &state)
                .unwrap()
                .iter()
                .filter(|c| **c != 0)
                .count(),
            9
        );
        state.position = Position { x: 0, y: 0 };
        state.explored[0].fill(0);
        state.reveal();
        let colors = cells(&data, &state).unwrap();
        assert_eq!(colors.iter().filter(|c| **c != 0).count(), 9);
        assert_eq!(colors[5599], 10);
        state.area = 1;
        assert!(cells(&data, &state).unwrap().iter().all(|c| *c == 0));
        state.explored[0].pop();
        assert!(cells(&data, &state).is_err());
        assert_eq!(
            cell(Position { x: 69, y: 79 }).unwrap(),
            Rect(1128, 1074, 12, 12)
        );
        assert!(cell(Position { x: 70, y: 0 }).is_err());
    }
    #[test]
    fn f5_enter_escape_mouse_and_save_leave_the_world_unchanged() {
        let data = WorldData::flat_fixture();
        let c = Catalog::builtin().unwrap();
        let mut j = Journey::new(&data, 1);
        let before = j.encode(&c, &data).unwrap();
        let mut ui = Manager::default();
        for exit in [13, 27] {
            ui.key(1073741886, &mut j, &c, &data);
            assert_eq!(ui.page, Page::Minimap);
            for key in [32, 1073741903, 1073741906, 1073741882] {
                ui.key(key, &mut j, &c, &data);
                assert_eq!(ui.page, Page::Minimap);
            }
            assert_eq!(pointer::hit(Screen::Minimap, 780, 610), None);
            ui.key(exit, &mut j, &c, &data);
            assert_eq!(ui.page, Page::World);
            assert_eq!(j.encode(&c, &data).unwrap(), before);
        }
        let cold = Journey::decode(&c, &data, &before).unwrap();
        assert_eq!(
            cells(&data, &j.world).unwrap(),
            cells(&data, &cold.world).unwrap()
        );
        j.camps.pending = Some(1);
        ui.key(1073741886, &mut j, &c, &data);
        assert_eq!(ui.page, Page::World);
    }
}
