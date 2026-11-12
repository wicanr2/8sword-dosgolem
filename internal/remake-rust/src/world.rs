//! Spec031: original map data and bounded manual movement preview.
use crate::controller::OriginalRng;
use crate::media_assets::checksum;
use std::path::Path;
pub const WIDTH: usize = 70;
pub const HEIGHT: usize = 80;
const CELLS: usize = WIDTH * HEIGHT;
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Position {
    pub x: u8,
    pub y: u8,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MenuLabel {
    pub x: u16,
    pub y: u16,
    pub text: String,
}
#[derive(Debug, Clone)]
pub struct WorldData {
    maps: [Vec<u8>; 8],
    pub starts: [Position; 8],
    pub remaining: u16,
    pub rank: u8,
    pub facing: u8,
    pub menu: Vec<MenuLabel>,
    pub fingerprint: u64,
    pub(crate) notice_text: Vec<String>,
}
pub fn decode_map(raw: &[u8]) -> Result<Vec<u8>, String> {
    if raw.len() < 8 || raw.len() > 65535 {
        return Err("地圖長度錯誤".into());
    }
    let word = |at: usize| u16::from_le_bytes([raw[at], raw[at + 1]]) as usize;
    let (n, root) = (word(0), word(2));
    if n != 5761 || !(256..=511).contains(&root) {
        return Err("地圖壓縮表頭錯誤".into());
    }
    let start = 4 + (root - 255) * 4;
    if start >= raw.len() {
        return Err("地圖壓縮樹截斷".into());
    }
    for node in 0..=root - 256 {
        for branch in 0..2 {
            if word(4 + node * 4 + branch * 2) >= 256 + node {
                return Err("地圖壓縮樹循環".into());
            }
        }
    }
    let mut out = Vec::with_capacity(n);
    let mut node = root;
    'stream: for byte in &raw[start..] {
        for bit in 0..8 {
            node = word(4 + (node - 256) * 4 + if byte & (1 << bit) == 0 { 2 } else { 0 });
            if node < 256 {
                out.push(node as u8);
                node = root;
                if out.len() == n {
                    break 'stream;
                }
            }
        }
    }
    if out.len() != n || out[5760] != 26 {
        return Err("地圖壓縮資料截斷".into());
    }
    let mut cells = Vec::with_capacity(CELLS);
    for row in out[..5760].chunks_exact(72) {
        if row[70..] != [13, 10] || row[..70].iter().any(|v| !(49..=113).contains(v)) {
            return Err("地圖列或地形錯誤".into());
        }
        cells.extend(row[..70].iter().map(|v| v - 48));
    }
    Ok(cells)
}

#[cfg(test)]
mod tests {
    use super::*;
    fn data() -> WorldData {
        WorldData {
            maps: std::array::from_fn(|_| vec![1; 5600]),
            starts: [Position { x: 40, y: 40 }; 8],
            remaining: 324,
            rank: 1,
            facing: 3,
            menu: vec![],
            fingerprint: 123,
            notice_text: vec![String::from("地圖提示"); 131],
        }
    }
    fn compressed() -> Vec<u8> {
        let mut raw = 5761u16.to_le_bytes().to_vec();
        raw.extend(258u16.to_le_bytes());
        for v in [49u16, 13, 10, 26, 256, 257] {
            raw.extend(v.to_le_bytes());
        }
        let mut body = Vec::new();
        for _ in 0..80 {
            body.extend([49u8; 70]);
            body.extend([13, 10]);
        }
        body.push(26);
        let mut bits = Vec::new();
        for b in body {
            bits.extend(match b {
                49 => [1, 1],
                13 => [1, 0],
                10 => [0, 1],
                _ => [0, 0],
            });
        }
        for chunk in bits.chunks(8) {
            raw.push(chunk.iter().enumerate().fold(0, |a, (i, v)| a | v << i));
        }
        raw
    }
    #[test]
    fn original_cpu_movement_rollback_and_terrain_880_cases() {
        let mut count = 0;
        for line in include_str!("../world-reference.tsv")
            .lines()
            .filter(|l| !l.starts_with('#'))
        {
            let f: Vec<_> = line.split('\t').collect();
            let n = |i: usize| f[i].parse::<u16>().unwrap();
            match f[0] {
                "MOVE" | "ROLLBACK" => {
                    let (p, face) = motion(
                        Position {
                            x: n(2) as u8,
                            y: n(3) as u8,
                        },
                        n(1),
                        3,
                        f[0] == "ROLLBACK",
                    )
                    .unwrap();
                    assert_eq!(
                        (p.x, p.y, face),
                        (n(4) as u8, n(5) as u8, n(6) as u8),
                        "{line}"
                    );
                }
                "GUARD" => {
                    let (b, boat) =
                        guard(n(1) as u8, n(2) as u8, n(3) & 1 != 0, n(3) & 2 != 0).unwrap();
                    assert_eq!((boat, u16::from(b)), (n(4) as u8, n(5)), "{line}");
                    assert_eq!((n(6), n(7)), (if b { 40 } else { 41 }, 40));
                }
                _ => panic!("unknown original case"),
            };
            count += 1;
        }
        assert_eq!(count, 880);
    }
    #[test]
    fn compressed_maps_reject_cycles_truncation_and_bad_rows() {
        let raw = compressed();
        assert_eq!(decode_map(&raw).unwrap(), vec![1; 5600]);
        for n in [0, 3, 8, raw.len() - 2] {
            assert!(decode_map(&raw[..n]).is_err());
        }
        let mut bad = raw.clone();
        bad[12..14].copy_from_slice(&258u16.to_le_bytes());
        assert!(decode_map(&bad).is_err());
        let mut bad = raw.clone();
        bad[4..6].copy_from_slice(&48u16.to_le_bytes());
        assert!(decode_map(&bad).is_err());
        let mut bad = raw;
        bad[6..8].copy_from_slice(&10u16.to_le_bytes());
        assert!(decode_map(&bad).is_err());
    }
    #[test]
    fn manual_move_block_wait_reveal_and_all_event_boundaries_are_atomic() {
        let mut d = data();
        let mut s = WorldState::new(&d, 1);
        let before = s.clone();
        d.maps[0][40 * 70 + 41] = 2;
        assert_eq!(
            s.walk(&d, 0x4d00).unwrap(),
            WalkResult::Committed { blocked: true }
        );
        assert_eq!(s.position, before.position);
        assert_eq!(s.remaining, 324);
        assert_eq!(s.facing, 4);
        assert_eq!(
            s.walk(&d, 0x3920).unwrap(),
            WalkResult::Committed { blocked: false }
        );
        assert_eq!(s.remaining, 324);
        for tile in [49, 50, 51, 53, 54, 55, 56, 57, 58, 59, 65] {
            d.maps[0][40 * 70 + 41] = tile;
            let old = s.clone();
            assert_eq!(
                s.walk(&d, 0x4d00).unwrap(),
                WalkResult::Boundary(Boundary::Terrain(tile))
            );
            assert_eq!(s, old);
        }
        d.maps[0][40 * 70 + 41] = 1;
        s.boat = 2;
        let old = s.clone();
        assert_eq!(
            s.walk(&d, 0x4d00).unwrap(),
            WalkResult::Boundary(Boundary::BoatExit)
        );
        assert_eq!(s, old);
        s.boat = 0;
        s.remaining = 1;
        let old = s.clone();
        assert_eq!(
            s.walk(&d, 0x4d00).unwrap(),
            WalkResult::Boundary(Boundary::Monthly)
        );
        assert_eq!(s, old);
        s.remaining = 324;
        s.position = Position { x: 0, y: 0 };
        s.explored[0].fill(0);
        s.reveal();
        assert_eq!(s.explored[0].iter().map(|n| n.count_ones()).sum::<u32>(), 9);
        assert_ne!(s.explored[0][5599 / 8] & (1 << (5599 % 8)), 0);
        // Explicit controlled seed makes the first rand quotient one. No reroll.
        // Inverse of the LCG for next state 1000 << 16, not a sampled seed.
        s.rng.seed = 0x5578f641;
        let old = s.clone();
        let mut r = s.rng;
        let roll = r.next15();
        assert!((640..1280).contains(&roll), "{roll}");
        assert!(matches!(
            s.walk(&d, 0x4d00).unwrap(),
            WalkResult::Boundary(Boundary::Encounter(_))
        ));
        assert_eq!(s, old);
    }
    #[test]
    fn world_checkpoint_cold_continuation_and_semantic_rejections() {
        let d = data();
        let mut s = WorldState::new(&d, 1);
        s.walk(&d, 0x5000).unwrap();
        s.font = 1;
        s.music = false;
        let raw = s.encode(&d).unwrap();
        assert_eq!(raw.len(), 5648);
        let mut cold = WorldState::decode(&d, &raw).unwrap();
        assert_eq!(cold, s);
        for key in [0x5000, 0x4b00, 0x4700, 0x3920] {
            assert_eq!(cold.walk(&d, key), s.walk(&d, key));
            assert_eq!(cold, s);
        }
        for at in [0, 8, 16, 17, 18, 19, 22, 23, 24, 25, 38, 39] {
            let mut bad = raw.clone();
            bad[at] = 255;
            let n = bad.len() - 8;
            let hash = checksum(&bad[..n]);
            bad[n..].copy_from_slice(&hash.to_le_bytes());
            assert!(WorldState::decode(&d, &bad).is_err(), "{at}");
        }
        for n in [0, 8, 5647] {
            assert!(WorldState::decode(&d, &raw[..n]).is_err());
        }
    }
    #[test]
    fn separate_world_file_and_failed_replace_preserve_previous_checkpoint() {
        let d = data();
        let mut s = WorldState::new(&d, 1);
        let dir = std::env::temp_dir().join(format!("8sword-world-{}", std::process::id()));
        std::fs::create_dir(&dir).unwrap();
        s.save(&dir, &d).unwrap();
        std::fs::write(dir.join("battle.chk"), b"unrelated").unwrap();
        s.walk(&d, 0x5000).unwrap();
        s.save(&dir, &d).unwrap();
        assert_eq!(WorldState::load(&dir, &d).unwrap(), s);
        assert_eq!(std::fs::read(dir.join("battle.chk")).unwrap(), b"unrelated");
        let old = std::fs::read(dir.join("world-preview.chk")).unwrap();
        s.walk(&d, 0x4b00).unwrap();
        assert!(
            crate::checkpoint_store::save_named(
                &dir,
                "world-preview.chk",
                &s.encode(&d).unwrap(),
                8192,
                |b| WorldState::decode(&d, b).map(|_| ()),
                true
            )
            .is_err()
        );
        assert_eq!(std::fs::read(dir.join("world-preview.chk")).unwrap(), old);
        std::fs::write(dir.join("world-preview.chk"), b"bad").unwrap();
        assert!(s.save(&dir, &d).is_err());
        assert!(WorldState::load(&dir, &d).is_err());
        std::fs::remove_dir_all(dir).unwrap();
    }
}
impl WorldData {
    #[cfg(test)]
    pub(crate) fn guards_fixture(water: bool) -> Self {
        let mut d = Self::flat_fixture();
        for s in crate::guards::sites() {
            d.maps[usize::from(s.area)]
                [usize::from(s.position.y) * 70 + usize::from(s.position.x)] = 65;
        }
        if water {
            for s in crate::guards::sites() {
                for key in [0x4800, 0x5000, 0x4b00, 0x4d00] {
                    let p = motion(s.position, key, 3, true).unwrap().0;
                    assert_ne!(
                        d.maps[usize::from(s.area)][usize::from(p.y) * 70 + usize::from(p.x)],
                        65
                    );
                    d.maps[usize::from(s.area)][usize::from(p.y) * 70 + usize::from(p.x)] = 2;
                }
            }
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn notice_fixture(water: bool) -> Self {
        let mut d = Self::flat_fixture();
        for s in crate::map_notice::sites() {
            d.maps[usize::from(s.area)]
                [usize::from(s.position.y) * 70 + usize::from(s.position.x)] = 51;
        }
        if water {
            let s = crate::map_notice::sites()[0];
            d.maps[usize::from(s.area)]
                [usize::from(s.position.y) * 70 + usize::from(s.position.x) - 1] = 2;
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn shore_vectors_fixture() -> Self {
        let mut d = Self::special_shore_fixture();
        for area in 0..8 {
            for i in 0..5600 {
                let p = Position {
                    x: (i % 70) as u8,
                    y: (i / 70) as u8,
                };
                if !matches!(d.maps[area][i], 49 | 50 | 53..=59) && p != d.starts[area] {
                    d.maps[area][i] = 2;
                }
            }
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn special_shore_fixture() -> Self {
        let mut d = Self::exits_fixture();
        for s in crate::world_magic::shops() {
            d.maps[usize::from(s.area)][usize::from(s.y) * 70 + usize::from(s.x)] = 53;
        }
        for (i, s) in crate::management::camps()
            .iter()
            .enumerate()
            .filter(|(_, s)| s.kind > 0)
        {
            d.maps[usize::from(s.area)][usize::from(s.y) * 70 + usize::from(s.x)] =
                54 + (i / 24) as u8;
        }
        for s in crate::treasure::sites() {
            d.maps[usize::from(s.area)][usize::from(s.y) * 70 + usize::from(s.x)] = 59;
        }
        for a in 0..8 {
            let positions: Vec<_> = d.maps[a]
                .iter()
                .enumerate()
                .filter(|(_, t)| matches!(**t, 49 | 50 | 53..=59))
                .map(|(i, _)| Position {
                    x: (i % 70) as u8,
                    y: (i / 70) as u8,
                })
                .collect();
            for p in positions {
                for key in [0x4d00, 0x4b00, 0x4800, 0x5000] {
                    let from = motion(p, key, 3, true).unwrap().0;
                    let at = usize::from(from.y) * 70 + usize::from(from.x);
                    if d.maps[a][at] == 1 && from != d.starts[a] {
                        d.maps[a][at] = 2;
                        break;
                    }
                }
            }
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn exits_fixture() -> Self {
        let mut d = Self::flat_fixture();
        d.starts = [
            (40, 40),
            (36, 36),
            (16, 5),
            (66, 4),
            (23, 18),
            (40, 4),
            (18, 5),
            (15, 5),
        ]
        .map(|(x, y)| Position { x, y });
        for a in 0..8 {
            d.maps[a][0] = 2;
        }
        for e in crate::world_exits::exits() {
            d.maps[usize::from(e.area)]
                [usize::from(e.position.y) * 70 + usize::from(e.position.x)] = e.tile;
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn jump_fixture(tile: u8) -> Self {
        let mut d = Self::flat_fixture();
        for m in &mut d.maps {
            m.fill(tile);
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn water_event_fixture(tile: u8) -> Self {
        let mut d = Self::water_fixture();
        d.maps[0][40 * 70 + 43] = tile;
        d
    }
    #[cfg(test)]
    pub(crate) fn water_fixture() -> Self {
        let mut d = Self::flat_fixture();
        d.maps[0][40 * 70 + 41] = 2;
        d.maps[0][40 * 70 + 42] = 11;
        d
    }
    #[cfg(test)]
    pub(crate) fn bridge_reference_fixture() -> Self {
        let mut d = Self::flat_fixture();
        for row in include_str!("../magic-bridge-reference.tsv")
            .lines()
            .filter(|s| !s.starts_with('#'))
        {
            let f: Vec<usize> = row.split('\t').map(|s| s.parse().unwrap()).collect();
            d.maps[0][f[1] * 70 + f[0]] = f[2] as u8;
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn bridge_wrap_fixture() -> Self {
        let mut d = Self::flat_fixture();
        d.maps[0][79 * 70] = 2;
        d.maps[0][78 * 70] = 14;
        d
    }
    #[cfg(test)]
    pub(crate) fn bridge_and_treasure_fixture() -> Self {
        let mut d = Self::treasure_fixture();
        d.maps[0][40 * 70 + 41] = 2;
        d.maps[0][40 * 70 + 42] = 2;
        d
    }
    #[cfg(test)]
    pub(crate) fn magic_fixture(center: u8) -> Self {
        let mut d = Self::flat_fixture();
        for s in crate::world_magic::shops() {
            d.maps[usize::from(s.area)][usize::from(s.y) * 70 + usize::from(s.x)] = 53;
        }
        for dy in -2i32..=2 {
            for dx in -2i32..=2 {
                let x = (40 + dx).rem_euclid(70) as usize;
                let y = (40 + dy).rem_euclid(80) as usize;
                d.maps[0][y * 70 + x] = if dx == 0 && dy == 0 { center } else { 2 };
            }
        }
        d
    }
    /// Validated v5 patches are independent of the immutable input fingerprint.
    pub fn with_bridges(&self, indices: &[u16]) -> Result<Self, String> {
        if indices.len() > 44800 || indices.windows(2).any(|p| p[0] >= p[1]) {
            return Err("橋格重複或順序錯誤".into());
        }
        let mut d = self.clone();
        for index in indices {
            let at = usize::from(*index);
            if at >= 44800 || !(2..=14).contains(&self.maps[at / 5600][at % 5600]) {
                return Err("橋格不屬原圖可改地形".into());
            }
            d.maps[at / 5600][at % 5600] = 52;
        }
        Ok(d)
    }
    #[cfg(test)]
    pub(crate) fn minimap_fixture() -> Self {
        let mut d = Self::flat_fixture();
        for line in include_str!("../minimap-reference.tsv")
            .lines()
            .filter(|s| !s.starts_with('#'))
        {
            let f: Vec<usize> = line.split('\t').map(|s| s.parse().unwrap()).collect();
            d.maps[0][f[1] * 70 + f[0]] = f[2] as u8;
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn treasure_fixture() -> Self {
        let mut d = Self::flat_fixture();
        for s in crate::treasure::sites() {
            d.maps[usize::from(s.area)][usize::from(s.y) * 70 + usize::from(s.x)] = 59;
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn camp_fixture() -> Self {
        let mut d = Self::flat_fixture();
        d.maps[0][38 * 70 + 39] = 54;
        d
    }
    #[cfg(test)]
    pub(crate) fn land_shore_fixture() -> Self {
        let mut d = Self::special_shore_fixture();
        for map in &mut d.maps {
            for tile in map {
                if matches!(*tile, 2 | 11..=14) {
                    *tile = 1;
                }
            }
        }
        for site in crate::guards::sites() {
            d.maps[usize::from(site.area)]
                [usize::from(site.position.y) * 70 + usize::from(site.position.x)] = 65;
        }
        for site in crate::map_notice::sites() {
            d.maps[usize::from(site.area)]
                [usize::from(site.position.y) * 70 + usize::from(site.position.x)] = 51;
        }
        d
    }
    #[cfg(test)]
    pub(crate) fn flat_fixture() -> Self {
        Self {
            maps: std::array::from_fn(|_| vec![1; 5600]),
            starts: [Position { x: 40, y: 40 }; 8],
            remaining: 324,
            rank: 1,
            facing: 3,
            menu: Vec::new(),
            fingerprint: 123,
            notice_text: vec![String::from("地圖提示"); 131],
        }
    }
    pub fn load(root: &Path) -> Result<Self, String> {
        let mut maps: [Vec<u8>; 8] = std::array::from_fn(|_| Vec::new());
        let mut binding = Vec::new();
        for (i, m) in maps.iter_mut().enumerate() {
            let p = root.join(format!("map{}.ay", i + 1));
            let st = p.symlink_metadata().map_err(|e| e.to_string())?;
            if !st.is_file() || st.len() > 65535 {
                return Err("地圖來源檔案錯誤".into());
            }
            let raw = std::fs::read(p).map_err(|e| e.to_string())?;
            *m = decode_map(&raw)?;
            binding.extend((raw.len() as u32).to_le_bytes());
            binding.extend(raw);
        }
        let p = root.join("world-start.tsv");
        let st = p.symlink_metadata().map_err(|e| e.to_string())?;
        if !st.is_file() || st.len() > 4096 {
            return Err("地圖起始檔案錯誤".into());
        }
        let start = std::fs::read_to_string(p).map_err(|e| e.to_string())?;
        if start.len() > 4096 {
            return Err("地圖起始資料過大".into());
        }
        binding.extend(start.as_bytes());
        let mut starts = [Position { x: 255, y: 255 }; 8];
        let (mut remaining, mut rank, mut facing) = (0, 0, 0);
        let mut menu = Vec::new();
        for line in start.lines() {
            let f: Vec<_> = line.split('\t').collect();
            let number = |i: usize| f[i].parse::<u16>().map_err(|_| "地圖起始數值錯誤");
            match f.first().copied() {
                Some("START") if f.len() == 4 => {
                    let i = usize::from(number(1)?);
                    let (x, y) = (number(2)?, number(3)?);
                    if i >= 8 || x >= 70 || y >= 80 || starts[i].x != 255 {
                        return Err("地圖起始座標錯誤".into());
                    }
                    starts[i] = Position {
                        x: x as u8,
                        y: y as u8,
                    };
                }
                Some("CLOCK") if f.len() == 4 => {
                    if remaining != 0 {
                        return Err("重複地圖時鐘".into());
                    }
                    remaining = number(1)?;
                    rank = u8::try_from(number(2)?).map_err(|_| "地圖階級超界")?;
                    facing = u8::try_from(number(3)?).map_err(|_| "地圖方向超界")?;
                }
                Some("MENU") if f.len() == 4 => {
                    let (x, y) = (number(1)?, number(2)?);
                    if x != 59 || usize::from(y) != 12 + 27 * menu.len() || f[3].len() > 80 {
                        return Err("地圖欄位錯誤".into());
                    }
                    menu.push(MenuLabel {
                        x,
                        y,
                        text: f[3].into(),
                    });
                }
                _ => return Err("未知地圖起始欄位".into()),
            }
        }
        if starts.iter().any(|p| p.x == 255)
            || remaining != 324
            || rank != 1
            || facing != 3
            || menu.len() != 7
        {
            return Err("地圖起始版本不符".into());
        }
        let data = Self {
            maps,
            starts,
            remaining,
            rank,
            facing,
            menu,
            fingerprint: checksum(&binding),
            notice_text: crate::map_notice::load_texts(root)?,
        };
        crate::world_exits::validate(&data)?;
        crate::map_notice::validate_maps(&data)?;
        crate::guards::validate_maps(&data)?;
        Ok(data)
    }
    pub fn tile(&self, area: u8, p: Position) -> Result<u8, String> {
        if p.x >= 70 || p.y >= 80 {
            return Err("地圖座標錯誤".into());
        }
        self.maps
            .get(usize::from(area))
            .and_then(|m| m.get(usize::from(p.y) * WIDTH + usize::from(p.x)))
            .copied()
            .ok_or_else(|| "地圖區域錯誤".into())
    }
}
pub fn motion(p: Position, key: u16, facing: u8, reverse: bool) -> Result<(Position, u8), String> {
    if p.x >= 70 || p.y >= 80 || !(1..=4).contains(&facing) {
        return Err("世界座標或方向錯誤".into());
    }
    let (dx, dy, face) = match key {
        0x4700 => (-1, -1, 3),
        0x4800 => (0, -1, 1),
        0x4900 => (1, -1, 4),
        0x4b00 => (-1, 0, 3),
        0x4d00 => (1, 0, 4),
        0x4f00 => (-1, 1, 3),
        0x5000 => (0, 1, 2),
        0x5100 => (1, 1, 4),
        _ => (0, 0, facing),
    };
    let factor = if reverse { -1 } else { 1 };
    Ok((
        Position {
            x: (i32::from(p.x) + dx * factor).rem_euclid(70) as u8,
            y: (i32::from(p.y) + dy * factor).rem_euclid(80) as u8,
        },
        face,
    ))
}
pub fn guard(tile: u8, boat: u8, mountain: bool, bamboo: bool) -> Result<(bool, u8), String> {
    if !(1..=65).contains(&tile) || boat > 2 {
        return Err("地形或船狀態錯誤".into());
    }
    let water = matches!(tile, 2 | 11..=14);
    let blocked = water && boat == 0
        || matches!(tile, 15..=30) && !mountain
        || tile == 46 && !bamboo
        || matches!(tile, 60..=62);
    Ok((blocked, if water && boat == 1 { 2 } else { boat }))
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Boundary {
    Terrain(u8),
    BoatExit,
    Monthly,
    Encounter(u8),
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WalkResult {
    Committed { blocked: bool },
    Boundary(Boundary),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorldState {
    pub area: u8,
    pub position: Position,
    pub facing: u8,
    pub remaining: u16,
    pub rank: u8,
    pub boat: u8,
    pub mountain: bool,
    pub bamboo: bool,
    pub rng: OriginalRng,
    pub actions: u64,
    pub explored: [Vec<u8>; 8],
    pub font: u8,
    pub music: bool,
}
impl WorldState {
    pub fn save(&self, dir: &Path, data: &WorldData) -> Result<(), String> {
        let raw = self.encode(data)?;
        crate::checkpoint_store::save_named(
            dir,
            "world-preview.chk",
            &raw,
            8192,
            |b| Self::decode(data, b).map(|_| ()),
            false,
        )
    }
    pub fn load(dir: &Path, data: &WorldData) -> Result<Self, String> {
        Self::decode(
            data,
            &crate::checkpoint_store::read_named(dir, "world-preview.chk", 8192)?,
        )
    }
    pub fn new(data: &WorldData, seed: u32) -> Self {
        let mut s = Self {
            area: 0,
            position: data.starts[0],
            facing: data.facing,
            remaining: data.remaining,
            rank: data.rank,
            boat: 0,
            mountain: false,
            bamboo: false,
            rng: OriginalRng { seed },
            actions: 0,
            explored: std::array::from_fn(|_| vec![0; 700]),
            font: 0,
            music: true,
        };
        s.reveal();
        s
    }
    pub(crate) fn reveal(&mut self) {
        for dy in -1..=1 {
            for dx in -1..=1 {
                let x = (i32::from(self.position.x) + dx).rem_euclid(70) as usize;
                let y = (i32::from(self.position.y) + dy).rem_euclid(80) as usize;
                let at = y * 70 + x;
                self.explored[usize::from(self.area)][at / 8] |= 1 << (at % 8);
            }
        }
    }
    fn validate(&self) -> Result<(), String> {
        if self.area >= 8
            || self.position.x >= 70
            || self.position.y >= 80
            || !(1..=4).contains(&self.facing)
            || self.remaining == 0
            || !(1..=5).contains(&self.rank)
            || self.boat > 2
            || self.font >= 3
            || self.explored.iter().any(|v| v.len() != 700)
        {
            Err("世界預覽狀態錯誤".into())
        } else {
            Ok(())
        }
    }
    pub fn walk(&mut self, data: &WorldData, key: u16) -> Result<WalkResult, String> {
        self.walk_inner(data, key, false, None)
    }
    pub(crate) fn walk_encounter(
        &mut self,
        data: &WorldData,
        key: u16,
    ) -> Result<WalkResult, String> {
        self.walk_inner(data, key, true, None)
    }
    pub(crate) fn walk_site(&mut self, data: &WorldData, tile: u8) -> Result<WalkResult, String> {
        self.walk_inner(data, 0x3920, true, Some(tile))
    }
    pub(crate) fn monthly_step(&self, data: &WorldData, key: u16) -> Result<Self, String> {
        // The regular preflight must prove this is exactly the last valid step.
        let mut probe = self.clone();
        if probe.walk_encounter(data, key)? != WalkResult::Boundary(Boundary::Monthly) {
            return Err("非月末有效移動".into());
        }
        let mut s = self.clone();
        let (target, face) = motion(s.position, key, s.facing, false)?;
        let (_, boat) = guard(data.tile(s.area, target)?, s.boat, s.mountain, s.bamboo)?;
        s.position = target;
        s.facing = face;
        s.boat = boat;
        Ok(s)
    }
    pub(crate) fn event_step(&self, data: &WorldData, key: u16, tile: u8) -> Result<Self, String> {
        let mut probe = self.clone();
        if probe.walk_encounter(data, key)? != WalkResult::Boundary(Boundary::Terrain(tile)) {
            return Err("非已驗事件入口".into());
        }
        let mut s = self.clone();
        let (target, face) = motion(s.position, key, s.facing, false)?;
        let (_, boat) = guard(data.tile(s.area, target)?, s.boat, s.mountain, s.bamboo)?;
        s.position = target;
        s.facing = face;
        s.boat = boat;
        Ok(s)
    }
    fn walk_inner(
        &mut self,
        data: &WorldData,
        key: u16,
        commit_encounter: bool,
        allowed_site: Option<u8>,
    ) -> Result<WalkResult, String> {
        self.walk_policy(data, key, commit_encounter, allowed_site, false)
    }
    pub(crate) fn plain_shore(&self, data: &WorldData, key: u16) -> Result<bool, String> {
        let mut probe = self.clone();
        if probe.walk_encounter(data, key)? != WalkResult::Boundary(Boundary::BoatExit) {
            return Ok(false);
        }
        let target = motion(self.position, key, self.facing, false)?.0;
        Ok(!matches!(data.tile(self.area, target)?, 49..=51 | 53..=59 | 65))
    }
    pub(crate) fn prepare_shore(&self, data: &WorldData, key: u16) -> Result<Self, String> {
        let mut probe = self.clone();
        if probe.walk_encounter(data, key)? != WalkResult::Boundary(Boundary::BoatExit) {
            return Err("非上岸入口".into());
        }
        let mut s = self.clone();
        s.position = motion(self.position, key, self.facing, false)?.0;
        s.reveal();
        s.position = self.position;
        Ok(s)
    }
    pub(crate) fn reject_shore(
        &mut self,
        data: &WorldData,
        key: u16,
    ) -> Result<WalkResult, String> {
        let mut probe = self.clone();
        if probe.walk_encounter(data, key)? != WalkResult::Boundary(Boundary::BoatExit) {
            return Err("非上岸拒絕邊界".into());
        }
        self.walk_policy(data, key, true, None, true)
    }
    fn walk_policy(
        &mut self,
        data: &WorldData,
        key: u16,
        commit_encounter: bool,
        allowed_site: Option<u8>,
        reject_shore: bool,
    ) -> Result<WalkResult, String> {
        self.validate()?;
        if ![
            0x4700, 0x4800, 0x4900, 0x4b00, 0x4d00, 0x4f00, 0x5000, 0x5100, 0x3920,
        ]
        .contains(&key)
        {
            return Err("世界移動按鍵錯誤".into());
        }
        let mut s = self.clone();
        let (target, face) = motion(s.position, key, s.facing, false)?;
        let tile = data.tile(s.area, target)?;
        let (blocked, boat) = guard(tile, s.boat, s.mountain, s.bamboo)?;
        let blocked = blocked || reject_shore;
        s.facing = face;
        if !blocked {
            if s.boat == 2 && !matches!(tile, 2 | 11..=14) {
                return Ok(WalkResult::Boundary(Boundary::BoatExit));
            }
            if matches!(tile,49..=51|53..=59|65) && allowed_site != Some(tile) {
                return Ok(WalkResult::Boundary(Boundary::Terrain(tile)));
            }
            if key != 0x3920 && s.remaining == 1 {
                return Ok(WalkResult::Boundary(Boundary::Monthly));
            }
            s.position = target;
            s.boat = boat;
            if key != 0x3920 {
                s.remaining -= 1;
            }
        }
        let result = s.encounter_tail(data, blocked)?;
        if commit_encounter || !matches!(result, WalkResult::Boundary(Boundary::Encounter(_))) {
            *self = s;
        }
        Ok(result)
    }
    /// sub_1151C runs after ordinary movement and every jump cell alike.
    pub(crate) fn encounter_tail(
        &mut self,
        data: &WorldData,
        blocked: bool,
    ) -> Result<WalkResult, String> {
        self.validate()?;
        let mut s = self.clone();
        let divisor = [640, 576, 512, 448, 384][usize::from(s.rank - 1)];
        let roll = s.rng.next15();
        if roll / divisor == 1 {
            let ahead = motion(
                s.position,
                match s.facing {
                    1 => 0x4800,
                    2 => 0x5000,
                    3 => 0x4b00,
                    _ => 0x4d00,
                },
                s.facing,
                false,
            )?
            .0;
            if data.tile(s.area, ahead)? < 47 {
                let cue = (s.rng.next15() / 2341) as u8;
                s.actions = s.actions.checked_add(1).ok_or("世界操作次數超界")?;
                s.reveal();
                *self = s;
                return Ok(WalkResult::Boundary(Boundary::Encounter(cue)));
            }
        }
        s.actions = s.actions.checked_add(1).ok_or("世界操作次數超界")?;
        s.reveal();
        *self = s;
        Ok(WalkResult::Committed { blocked })
    }
    pub fn encode(&self, data: &WorldData) -> Result<Vec<u8>, String> {
        self.validate()?;
        let mut b = b"8SWMOV01".to_vec();
        b.extend(data.fingerprint.to_le_bytes());
        b.extend([self.area, self.position.x, self.position.y, self.facing]);
        b.extend(self.remaining.to_le_bytes());
        b.extend([
            self.rank,
            self.boat,
            u8::from(self.mountain),
            u8::from(self.bamboo),
        ]);
        b.extend(self.rng.seed.to_le_bytes());
        b.extend(self.actions.to_le_bytes());
        b.extend([self.font, u8::from(self.music)]);
        for v in &self.explored {
            b.extend(v);
        }
        b.extend(checksum(&b).to_le_bytes());
        Ok(b)
    }
    pub fn decode(data: &WorldData, b: &[u8]) -> Result<Self, String> {
        if b.len() != 5648 || &b[..8] != b"8SWMOV01" {
            return Err("世界預覽檢查點格式錯誤".into());
        }
        let q = |at: usize| u64::from_le_bytes(b[at..at + 8].try_into().unwrap());
        if q(8) != data.fingerprint
            || q(b.len() - 8) != checksum(&b[..b.len() - 8])
            || [b[24], b[25], b[39]].iter().any(|n| *n > 1)
        {
            return Err("世界預覽檢查點不相容".into());
        }
        let s = Self {
            area: b[16],
            position: Position { x: b[17], y: b[18] },
            facing: b[19],
            remaining: u16::from_le_bytes([b[20], b[21]]),
            rank: b[22],
            boat: b[23],
            mountain: b[24] != 0,
            bamboo: b[25] != 0,
            rng: OriginalRng {
                seed: u32::from_le_bytes(b[26..30].try_into().unwrap()),
            },
            actions: q(30),
            font: b[38],
            music: b[39] != 0,
            explored: std::array::from_fn(|i| b[40 + i * 700..40 + (i + 1) * 700].to_vec()),
        };
        s.validate()?;
        Ok(s)
    }
}
