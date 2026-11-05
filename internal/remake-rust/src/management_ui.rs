use crate::catalog::Catalog;
use crate::desktop::{GOLD, border, fill, glyph, sprite, text};
use crate::journey::Journey;
use crate::management::EXTRA;
use crate::media_assets::{Font, Image, MediaPack};
use crate::pointer::{Screen, TABS, army_box, digit_box, offer_box};
use crate::world::WorldData;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Page {
    World,
    Character,
    Minimap,
    Review,
    Dismiss,
    Shop,
    Quantity,
    Monthly,
    Treasure,
    Magic,
    Bridge,
    MagicShop,
    Message,
    ResourceResult,
    Bird,
    Teleport,
}
pub struct Manager {
    pub page: Page,
    pub selected: usize,
    pub extra: bool,
    pub digits: String,
    pub message: String,
    pub swords: bool,
}
impl Default for Manager {
    fn default() -> Self {
        Self {
            page: Page::World,
            selected: 0,
            extra: false,
            digits: String::new(),
            message: String::new(),
            swords: false,
        }
    }
}
impl Manager {
    pub fn sync(&mut self, j: &Journey<'_>) {
        if j.travel_spell.teleport.is_some() {
            self.page = Page::Teleport;
            return;
        }
        if j.survey.bird {
            self.page = Page::Bird;
            return;
        }
        if j.resource_notice.is_some() {
            self.page = Page::ResourceResult;
            return;
        }
        if j.magic.direction {
            self.page = Page::Bridge;
            return;
        }
        if j.magic.shop.is_some() {
            self.page = Page::MagicShop;
            return;
        }
        if j.treasure.pending.is_some() {
            self.page = Page::Treasure;
            return;
        }
        if j.month.pending.is_some() {
            self.page = Page::Monthly;
            return;
        }
        if self.page == Page::World && j.camps.pending.is_some() {
            self.page = Page::Shop;
            self.extra = false;
            self.digits.clear();
            self.message.clear();
        }
    }
    pub fn screen(&self) -> Option<Screen> {
        match self.page {
            Page::Teleport => Some(Screen::Teleport),
            Page::Bird => Some(Screen::Minimap),
            Page::ResourceResult => Some(Screen::Report),
            Page::Magic => Some(Screen::Magic),
            Page::Bridge => Some(Screen::Bridge),
            Page::MagicShop => Some(Screen::MagicShop),
            Page::Message => Some(Screen::Report),
            Page::Character => Some(Screen::Character),
            Page::Minimap => Some(Screen::Minimap),
            Page::Treasure => Some(Screen::Treasure),
            Page::Monthly => Some(Screen::Report),
            Page::Review | Page::Dismiss => Some(Screen::Army),
            Page::Shop | Page::Quantity => Some(Screen::Shop {
                extra: self.extra,
                quantity: self.page == Page::Quantity,
            }),
            _ => None,
        }
    }
    pub fn extra(&mut self, j: &mut Journey<'_>, c: &Catalog, value: bool) {
        self.message.clear();
        if !matches!(self.page, Page::Shop | Page::Quantity) {
            return;
        }
        if value {
            if let Err(e) = j.open_extra(c) {
                self.message = e;
                return;
            }
            self.selected = 2;
        }
        self.extra = value;
        self.page = Page::Shop;
        self.digits.clear();
    }
    pub fn key(&mut self, key: i32, j: &mut Journey<'_>, c: &Catalog, data: &WorldData) {
        if let Err(e) = self.key_inner(key, j, c, data) {
            self.message = e;
        }
    }
    fn key_inner(
        &mut self,
        key: i32,
        j: &mut Journey<'_>,
        c: &Catalog,
        data: &WorldData,
    ) -> Result<(), String> {
        if self.page == Page::World {
            if j.phase() == "world" {
                self.page = match key {
                    1073741885 => {
                        self.selected = usize::from(j.magic.selected);
                        if j.magic.book {
                            Page::Magic
                        } else {
                            self.message = "你不會使用法術".into();
                            Page::Message
                        }
                    }
                    1073741887 => {
                        self.message = if j.search_book()? {
                            "你找到魔法竹簡".into()
                        } else {
                            "這裡沒有寶物".into()
                        };
                        Page::Message
                    }
                    1073741882 => Page::Character,
                    1073741886 => Page::Minimap,
                    1073741883 => Page::Review,
                    1073741884 => Page::Dismiss,
                    _ => return Ok(()),
                };
                if self.page != Page::Magic {
                    self.selected = 0;
                }
                self.swords = false;
                if self.page != Page::Message {
                    self.message.clear();
                }
            }
            return Ok(());
        }
        if self.page == Page::ResourceResult {
            if key == 13 || key == 27 {
                j.close_resource_notice(c)?;
                self.page = Page::World;
                self.message.clear();
            }
            return Ok(());
        }
        if self.page == Page::Message {
            if key == 13 || key == 27 {
                self.page = Page::World;
                self.message.clear();
            }
            return Ok(());
        }
        if self.page == Page::Magic {
            match key {
                1073741906 => self.selected = (self.selected + 7) % 8,
                1073741905 => self.selected = (self.selected + 1) % 8,
                27 => self.page = Page::World,
                13 if j.magic.charges[self.selected] > 0 => {
                    if self.selected == 0 {
                        j.begin_bridge()?;
                        self.page = Page::Bridge;
                    } else if self.selected == 4 {
                        j.cast_stop_time()?;
                        self.page = Page::World;
                    } else if self.selected == 7 {
                        j.begin_teleport()?;
                        self.page = Page::Teleport;
                    } else if self.selected == 5 {
                        j.begin_bird_view()?;
                        self.page = Page::Bird;
                    } else {
                        j.cast_resource(c, self.selected as u8)?;
                        self.page = Page::ResourceResult;
                    }
                    self.message.clear();
                }
                _ => {}
            }
            return Ok(());
        }
        if self.page == Page::Bridge {
            if let Some(k) = crate::world_desktop::key_motion(key) {
                j.finish_bridge(data, k)?;
                self.page = Page::World;
                self.message.clear();
            }
            return Ok(());
        }
        if self.page == Page::MagicShop {
            if key == 13 {
                j.buy_world_spell()?;
                self.message = "已購入法術".into();
            }
            if key == 27 {
                j.close_magic_shop(c, data)?;
                self.page = Page::World;
                self.message.clear();
            }
            return Ok(());
        }
        if self.page == Page::Teleport {
            let area = j.travel_spell.teleport.ok_or("傳送階段遺失")?;
            match key {
                1073741906 => j.select_teleport((area + 7) % 8)?,
                1073741905 => j.select_teleport((area + 1) % 8)?,
                13 | 27 => {
                    j.finish_teleport(data, key == 13)?;
                    self.page = Page::World;
                    self.message.clear();
                }
                _ => {}
            }
            return Ok(());
        }
        if self.page == Page::Bird {
            if key == 13 || key == 27 {
                j.close_bird_view()?;
                self.page = Page::World;
                self.message.clear();
            }
            return Ok(());
        }
        if self.page == Page::Minimap {
            if key == 13 || key == 27 {
                self.page = Page::World;
            }
            return Ok(());
        }
        if self.page == Page::Character {
            if key == 13 {
                if self.swords {
                    self.page = Page::World;
                } else {
                    self.swords = true;
                }
            }
            if key == 27 {
                self.page = Page::World;
            }
            return Ok(());
        }
        if self.page == Page::Treasure {
            match key {
                13 | 27 => {
                    j.finish_treasure(c, data, key == 27)?;
                    self.page = Page::World;
                    self.message.clear();
                }
                49 | 50 => j.select_treasure((key - 48) as u8)?,
                1073741906 | 1073741905 | 1073741904 | 1073741903 => {
                    let choice = j.treasure.pending.ok_or("沒有寶箱選項")?.choice;
                    j.select_treasure(3 - choice)?;
                }
                _ => {}
            }
            return Ok(());
        }
        if self.page == Page::Monthly {
            if [13, 27, 32].contains(&key) {
                j.close_month(data)?;
                self.page = Page::World;
                self.message.clear();
            }
            return Ok(());
        }
        if matches!(self.page, Page::Review | Page::Dismiss) {
            if key == 27 || self.page == Page::Review && (key == 13 || key == 32) {
                self.page = Page::World;
                self.message.clear();
                return Ok(());
            }
            if self.page == Page::Dismiss && key == 13 {
                if j.army[self.selected].count > 0 {
                    j.dismiss(self.selected)?;
                    self.selected = self.selected.min(
                        j.army
                            .iter()
                            .filter(|s| s.count > 0)
                            .count()
                            .saturating_sub(1),
                    );
                    self.message = "部隊已解雇".into();
                }
                return Ok(());
            }
            let (col, row) = (self.selected / 3, self.selected % 3);
            let at = match key {
                1073741906 => col * 3 + (row + 2) % 3,
                1073741905 => col * 3 + (row + 1) % 3,
                1073741904 | 1073741903 => (1 - col) * 3 + row,
                _ => self.selected,
            };
            if j.army[at].count > 0 {
                self.selected = at;
            }
            return Ok(());
        }
        if key == 9 {
            self.extra(j, c, !self.extra);
            return Ok(());
        }
        if self.page == Page::Shop {
            if key == 27 {
                j.close_camp(data, c)?;
                self.page = Page::World;
                self.message.clear();
                return Ok(());
            }
            if key == 13 {
                j.maximum(c, self.extra.then_some(self.selected))?;
                self.page = Page::Quantity;
                self.digits.clear();
                self.message.clear();
            }
            if self.extra {
                self.selected = match key {
                    1073741906 => (self.selected + 7) % 8,
                    1073741905 => (self.selected + 1) % 8,
                    1073741904 | 1073741903 => (self.selected + 4) % 8,
                    _ => self.selected,
                };
            }
            return Ok(());
        }
        if key == 27 {
            self.page = Page::Shop;
            self.digits.clear();
            self.message.clear();
            return Ok(());
        }
        if (48..=57).contains(&key) && self.digits.len() < 4 {
            self.digits
                .push(char::from_u32(key as u32).ok_or("數字錯誤")?);
            self.message.clear();
        }
        if key == 8 {
            self.digits.pop();
        }
        if key == 127 {
            self.digits.clear();
        }
        if key == 13 {
            let n = self.digits.parse::<u32>().unwrap_or(0);
            j.recruit(c, self.extra.then_some(self.selected), n)?;
            self.digits.clear();
            self.message = "招募完成".into();
        }
        Ok(())
    }
}
fn field(f: &mut [u8], font: &Font, value: &str, x: i32, y: i32, width: i32) -> Result<(), String> {
    let mut pos = x;
    for ch in value.chars() {
        let w = if ch.is_ascii() { 24 } else { 48 };
        if pos + w > x + width {
            return Err("軍隊欄位超界".into());
        }
        glyph(f, font, ch, [pos, y, w, 78], GOLD)?;
        pos += w;
    }
    Ok(())
}
pub fn draw(
    f: &mut [u8],
    ui: &Manager,
    j: &Journey<'_>,
    catalog: &Catalog,
    pack: &MediaPack,
    building: &Image,
    portrait: &Image,
    book: &Image,
    magic_building: &Image,
    data: &WorldData,
    marker_light: bool,
) -> Result<(), String> {
    if ui.page == Page::World {
        return Ok(());
    }
    let font = &pack.fonts[usize::from(j.world.font)];
    if ui.page == Page::ResourceResult {
        let n = j.resource_notice.as_ref().ok_or("缺少法術結果")?;
        let out = n.effect(j, catalog)?;
        fill(f, [24, 684, 1344, 480], [82, 82, 82]);
        border(f, [24, 684, 1344, 480], [206, 170, 74]);
        if n.spell == 1 {
            text(
                f,
                font,
                &format!("煉金術 煉出金錢 {}", out.amount),
                96,
                756,
                48,
                1200,
            )?;
            text(f, font, &format!("現金 {}", out.gold), 96, 876, 48, 1200)?;
        } else {
            let id = crate::catalog::UnitId::parse(&format!("native:{:02}", out.kind))?;
            sprite(f, pack.units.get(&id).ok_or("缺少召兵圖像")?, 72, 792);
            text(
                f,
                font,
                &format!("召兵術 {} {}人", catalog.get(id).name, out.count),
                384,
                756,
                48,
                936,
            )?;
            text(
                f,
                font,
                if out.joined {
                    "已加入部隊"
                } else {
                    "六隊已滿 無法加入"
                },
                384,
                900,
                48,
                936,
            )?;
        }
        return Ok(());
    }
    if ui.page == Page::Message || ui.page == Page::Bridge {
        fill(f, [24, 684, 1344, 480], [82, 82, 82]);
        border(f, [24, 684, 1344, 480], [206, 170, 74]);
        text(
            f,
            font,
            if ui.page == Page::Bridge {
                "造橋術：請選擇方向"
            } else {
                &ui.message
            },
            96,
            756,
            48,
            1200,
        )?;
        if ui.page == Page::Message && j.magic.book && ui.message == "你找到魔法竹簡" {
            sprite(f, book, 312, 870);
        }
        return Ok(());
    }
    if ui.page == Page::Teleport {
        fill(f, [24, 120, 1344, 1050], [10, 37, 29]);
        for (i, name) in crate::travel_spells::regions().iter().enumerate() {
            let y = 186 + i as i32 * 120;
            if j.travel_spell.teleport == Some(i as u8) {
                fill(f, [552, y, 408, 84], [119, 44, 41]);
            }
            field(f, font, name, 576, y, 384)?;
        }
        return Ok(());
    }
    if ui.page == Page::Magic {
        fill(f, [24, 120, 1344, 1050], [10, 37, 29]);
        for (i, (map, battle, _)) in crate::world_magic::names().iter().enumerate() {
            let y = 186 + i as i32 * 120;
            field(f, font, battle, 240, y, 264)?;
            field(f, font, "0", 504, y, 96)?;
            if ui.selected == i {
                fill(f, [792, y, 312, 84], [119, 44, 41]);
            }
            field(f, font, map, 816, y, 288)?;
            field(f, font, &j.magic.charges[i].to_string(), 1104, y, 120)?;
        }
        return Ok(());
    }
    if ui.page == Page::MagicShop {
        sprite(f, magic_building, 24, 120);
        fill(f, [24, 720, 1344, 450], [82, 82, 82]);
        let offer = j.magic_offer()?;
        let data = crate::world_magic::names();
        let lines = [
            format!("法術 {}", data[offer].0),
            format!("價格 {}", data[offer].2),
            format!(
                "金錢 {}  次數 {}/{}",
                j.resources[3],
                j.magic.charges.iter().map(|n| u64::from(*n)).sum::<u64>(),
                j.resources[5]
            ),
            if ui.message.is_empty() {
                "是否購買？".into()
            } else {
                ui.message.clone()
            },
        ];
        for (i, line) in lines.iter().enumerate() {
            text(f, font, line, 72, 744 + i as i32 * 96, 42, 1248)?;
        }
        return Ok(());
    }
    if matches!(ui.page, Page::Minimap | Page::Bird) {
        fill(f, [24, 120, 1344, 1050], [10, 37, 29]);
        let cells = if ui.page == Page::Bird {
            crate::minimap::all_cells(data, &j.world)?
        } else {
            crate::minimap::cells(data, &j.world)?
        };
        for (i, code) in cells.iter().enumerate() {
            let r = crate::minimap::cell(crate::world::Position {
                x: (i % 70) as u8,
                y: (i / 70) as u8,
            })?;
            fill(f, r.array(), crate::minimap::RGB[usize::from(*code)]);
        }
        let marker = crate::minimap::cell(j.world.position)?;
        fill(
            f,
            marker.array(),
            crate::minimap::RGB[if marker_light { 15 } else { 0 }],
        );
        field(f, font, " 現 在 位 置 :", 408, 1086, 336)?;
        field(f, font, &j.world.position.x.to_string(), 768, 1086, 96)?;
        field(f, font, "，", 864, 1086, 48)?;
        field(f, font, &j.world.position.y.to_string(), 912, 1086, 96)?;
        return Ok(());
    }
    if ui.page == Page::Character {
        fill(f, [24, 120, 1344, 1050], [10, 37, 29]);
        sprite(f, portrait, 72, 126);
        for row in crate::character::fields(j.resources)? {
            field(
                f,
                font,
                &row.label,
                row.label_box.0,
                row.label_box.1,
                row.label_box.2,
            )?;
            field(
                f,
                font,
                &row.value.to_string(),
                row.value_box.0,
                row.value_box.1,
                row.value_box.2,
            )?;
        }
        field(
            f,
            font,
            crate::character::heading(ui.swords)?,
            648,
            282,
            288,
        )?;
        if !ui.swords && j.magic.book {
            sprite(f, book, 912, 282);
            field(f, font, "魔 法 竹 簡", 1032, 282, 288)?;
        }
        return Ok(());
    }
    if ui.page == Page::Treasure {
        let p = j.treasure.pending.ok_or("缺少寶箱選項")?;
        let amount = j.treasure.amounts[usize::from(p.index)];
        fill(f, [24, 684, 1344, 480], [82, 82, 82]);
        border(f, [24, 684, 1344, 480], [206, 170, 74]);
        text(
            f,
            font,
            &format!("你得到一個寶箱，箱中物品價值 {}", amount),
            72,
            720,
            42,
            1248,
        )?;
        for (i, r) in crate::pointer::TREASURE_CHOICES.iter().enumerate() {
            fill(
                f,
                r.array(),
                if p.choice == i as u8 + 1 {
                    [255, 90, 90]
                } else {
                    [82, 82, 82]
                },
            );
            text(
                f,
                font,
                &if i == 0 {
                    "（1）納入自己總財產".into()
                } else {
                    format!("（2）分贈部隊，增加領導能力 {}", amount / 10)
                },
                r.0 + 12,
                r.1 + 24,
                42,
                r.2 - 24,
            )?;
        }
        return Ok(());
    }
    if ui.page == Page::Monthly {
        let b = j.month.pending.as_ref().ok_or("缺少月報")?.budget;
        fill(f, [24, 120, 1872, 1116], [8, 36, 25]);
        border(f, [24, 120, 1872, 1116], [206, 170, 74]);
        text(f, font, "神州八劍 每月收支統計", 60, 150, 48, 1800)?;
        for (i, (label, value)) in [
            ("月初金錢", b.before),
            ("月薪收入", b.income),
            ("軍費應付", b.due),
            ("軍費實付", b.charged),
            ("現金餘額", b.after),
        ]
        .iter()
        .enumerate()
        {
            let y = 264 + i as i32 * 156;
            fill(f, [80, y, 1760, 116], [20, 56, 41]);
            text(f, font, label, 120, y + 24, 48, 720)?;
            text(f, font, &value.to_string(), 944, y + 24, 48, 880)?;
        }
        if b.disbanded {
            text(
                f,
                font,
                "金錢不足 全軍離隊 本次軍費免收",
                96,
                1080,
                42,
                1728,
            )?;
        }
        return Ok(());
    }
    fill(f, [24, 120, 1344, 1050], [10, 37, 29]);
    if matches!(ui.page, Page::Review | Page::Dismiss) {
        for (i, s) in j.army.iter().enumerate() {
            if let Some(id) = s.unit {
                let b = army_box(i);
                let p = catalog.get(id);
                sprite(f, pack.units.get(&id).ok_or("缺少軍隊圖像")?, b.0, b.1);
                let label = b.0 + 264;
                let value = label + 120;
                let max = b.2 - 384;
                for (n, (title, v)) in [
                    ("種類:", p.name.clone()),
                    ("數量:", s.count.to_string()),
                    (
                        "月薪:",
                        p.gold
                            .checked_mul(u64::from(s.count))
                            .ok_or("月薪超界")?
                            .to_string(),
                    ),
                ]
                .iter()
                .enumerate()
                {
                    let y = b.1 + n as i32 * 96;
                    field(f, font, title, label, y, 120)?;
                    field(f, font, v, value, y, max)?;
                }
                if ui.page == Page::Dismiss && ui.selected == i {
                    border(f, b.array(), [235, 191, 74]);
                }
            }
        }
    } else {
        sprite(f, building, 24, 120);
        for (i, r) in TABS.iter().enumerate() {
            fill(
                f,
                r.array(),
                if ui.extra == (i == 1) {
                    [119, 44, 41]
                } else {
                    [20, 55, 40]
                },
            );
            border(f, r.array(), [206, 170, 74]);
            text(
                f,
                font,
                ["原店", "增援"][i],
                r.0 + 18,
                r.1 + 8,
                42,
                r.2 - 36,
            )?;
        }
        let (id, stock) = j.offer(ui.extra.then_some(ui.selected))?;
        let p = catalog.get(id);
        sprite(f, pack.units.get(&id).ok_or("缺少募兵圖像")?, 72, 834);
        if ui.page == Page::Shop && ui.extra {
            for (i, id) in EXTRA.iter().enumerate() {
                let id = crate::catalog::UnitId::parse(id)?;
                let r = offer_box(i);
                if i == ui.selected {
                    fill(f, r.array(), [119, 44, 41]);
                }
                text(
                    f,
                    font,
                    &catalog.get(id).name,
                    r.0 + 12,
                    r.1 + 10,
                    42,
                    r.2 - 24,
                )?;
            }
        } else {
            let maximum = j.maximum(catalog, ui.extra.then_some(ui.selected));
            let limit = maximum
                .as_ref()
                .map(|v| v.to_string())
                .unwrap_or_else(|e| e.clone());
            let quantity = if ui.page == Page::Quantity {
                format!(
                    "數量 {}",
                    if ui.digits.is_empty() {
                        "0"
                    } else {
                        &ui.digits
                    }
                )
            } else {
                "確認後輸入數量".into()
            };
            let lines = [
                format!("種類 {}", p.name),
                format!("價格 {}  存量 {}", p.gold, stock),
                format!("最多 {}", limit),
                quantity,
            ];
            for (n, line) in lines.iter().enumerate() {
                text(f, font, line, 384, 822 + n as i32 * 78, 48, 960)?;
            }
        }
        fill(f, [1392, 120, 504, 1080], [10, 37, 29]);
        if ui.page == Page::Quantity {
            for (i, label) in [
                "1", "2", "3", "4", "5", "6", "7", "8", "9", "刪字", "0", "清空",
            ]
            .iter()
            .enumerate()
            {
                let r = digit_box(i);
                border(f, r.array(), [206, 170, 74]);
                text(f, font, label, r.0 + 16, r.1 + 32, 42, r.2 - 32)?;
            }
        }
    }
    let summary = if ui.message.is_empty() {
        format!(
            "金錢 {}  領導用量 {}/{}",
            j.resources[3],
            j.used(catalog)?,
            j.resources[4]
        )
    } else {
        ui.message.clone()
    };
    fill(f, [24, 1188, 1344, 48], [9, 36, 29]);
    text(f, font, &summary, 36, 1194, 32, 1320)?;
    Ok(())
}
