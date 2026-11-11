use crate::catalog::UnitId;
use std::collections::BTreeMap;
use std::fs::File;
use std::io::Read;
use std::path::Path;

pub fn checksum(bytes: &[u8]) -> u64 {
    bytes.iter().fold(14695981039346656037u64, |hash, byte| {
        (hash ^ u64::from(*byte)).wrapping_mul(1099511628211)
    })
}

pub(crate) fn read_checked(path: &Path, magic: &[u8; 8], max: u64) -> Result<Vec<u8>, String> {
    let meta = path
        .symlink_metadata()
        .map_err(|e| format!("{}: {e}", path.display()))?;
    if !meta.file_type().is_file() || meta.len() < 16 || meta.len() > max {
        return Err("素材不是合法一般檔案".into());
    }
    let mut data = Vec::new();
    File::open(path)
        .map_err(|e| e.to_string())?
        .take(max + 1)
        .read_to_end(&mut data)
        .map_err(|e| e.to_string())?;
    if data.len() < 16 || data.len() as u64 > max || &data[..8] != magic {
        return Err("素材標頭無效".into());
    }
    let tail = data.len() - 8;
    let expected = u64::from_le_bytes(data[tail..].try_into().map_err(|_| "素材校驗尾碼無效")?);
    if checksum(&data[..tail]) != expected {
        return Err("素材校驗失敗".into());
    }
    data.truncate(tail);
    Ok(data)
}

#[derive(Clone)]
pub struct Image {
    pub width: usize,
    pub height: usize,
    pub pixels: Vec<u8>,
}
impl Image {
    pub fn load(path: &Path, width: usize, height: usize) -> Result<Self, String> {
        let data = read_checked(path, b"8SRGBA01", 64 << 20)?;
        if data.len() < 16 {
            return Err("圖片標頭截斷".into());
        }
        let w = u32::from_le_bytes(data[8..12].try_into().map_err(|_| "圖片寬度無效")?) as usize;
        let h = u32::from_le_bytes(data[12..16].try_into().map_err(|_| "圖片高度無效")?) as usize;
        let expected = w
            .checked_mul(h)
            .and_then(|n| n.checked_mul(4))
            .and_then(|n| n.checked_add(16))
            .ok_or("圖片尺寸越界")?;
        if w != width || h != height || data.len() != expected {
            return Err("圖片尺寸或長度不符".into());
        }
        Ok(Self {
            width: w,
            height: h,
            pixels: data[16..].into(),
        })
    }
}

pub struct Font {
    pub glyphs: BTreeMap<char, Vec<u8>>,
}
impl Font {
    pub fn load(path: &Path) -> Result<Self, String> {
        let data = read_checked(path, b"8SGLYP01", 32 << 20)?;
        if data.len() < 12 {
            return Err("字型標頭截斷".into());
        }
        let count =
            u32::from_le_bytes(data[8..12].try_into().map_err(|_| "字型列數無效")?) as usize;
        if count == 0 || count > 4096 || data.len() != 12 + count * 4100 {
            return Err("字型尺寸或長度不符".into());
        }
        let mut glyphs = BTreeMap::new();
        for raw in data[12..].chunks_exact(4100) {
            let code = u32::from_le_bytes(raw[..4].try_into().map_err(|_| "字碼截斷")?);
            let ch = char::from_u32(code).ok_or("字碼無效")?;
            if glyphs.insert(ch, raw[4..].into()).is_some() {
                return Err("字型字碼重複".into());
            }
        }
        Ok(Self { glyphs })
    }
}

pub struct Music {
    pub pcm: Vec<u8>,
    pub frames: u64,
}
impl Music {
    #[cfg(not(feature = "desktop"))]
    pub fn load(_path: &Path) -> Result<Self, String> {
        Err("音樂解碼需要desktop功能".into())
    }
    #[cfg(feature = "desktop")]
    pub fn load(path: &Path) -> Result<Self, String> {
        crate::sndfile::decode(path)
    }
}

pub struct MediaPack {
    pub background: Image,
    pub units: BTreeMap<UnitId, Image>,
    pub fonts: Vec<Font>,
    pub music: Music,
    pub spell_fx: Vec<Image>,
}
impl MediaPack {
    pub fn load(root: &Path) -> Result<Self, String> {
        let background = Image::load(&root.join("background.rgba"), 1920, 1200)?;
        if background.pixels.chunks_exact(4).any(|p| p[3] != 255) {
            return Err("戰場底圖必須不透明".into());
        }
        let mut units = BTreeMap::new();
        for name in [
            "openkb:wolf",
            "openkb:arcr",
            "native:06",
            "native:11",
            "native:16",
        ] {
            let id = UnitId::parse(name)?;
            units.insert(
                id,
                Image::load(
                    &root.join(format!("unit_{}.rgba", name.replace(':', "_"))),
                    264,
                    300,
                )?,
            );
        }
        let fonts = ["noto", "lishu", "caoshu"]
            .iter()
            .map(|name| Font::load(&root.join(format!("font-{name}.bin"))))
            .collect::<Result<_, _>>()?;
        Ok(Self {
            background,
            units,
            fonts,
            music: Music::load(&root.join("music.ogg"))?,
            spell_fx: Vec::new(),
        })
    }
    pub fn load_spell_assets(&mut self, root: &Path) -> Result<(), String> {
        let mut units = Vec::new();
        for kind in [1, 10, 12] {
            units.push((
                UnitId::parse(&format!("native:{kind:02}"))?,
                Image::load(&root.join(format!("unit_native_{kind:02}.rgba")), 264, 300)?,
            ));
        }
        let effects = (0..4)
            .map(|i| Image::load(&root.join(format!("spell-impact-{i}.rgba")), 264, 300))
            .collect::<Result<Vec<_>, _>>()?;
        self.units.extend(units);
        self.spell_fx = effects;
        Ok(())
    }
    pub fn load_native_units(&mut self, root: &Path) -> Result<(), String> {
        let mut units = Vec::new();
        for kind in 1..=25 {
            units.push((
                UnitId::parse(&format!("native:{kind:02}"))?,
                Image::load(&root.join(format!("unit_native_{kind:02}.rgba")), 264, 300)?,
            ));
        }
        self.units.extend(units);
        Ok(())
    }
    pub fn load_extra_units(&mut self, root: &Path) -> Result<(), String> {
        let mut units = Vec::new();
        for name in crate::management::EXTRA {
            let id = UnitId::parse(name)?;
            units.push((
                id,
                Image::load(
                    &root.join(format!("unit_{}.rgba", name.replace(':', "_"))),
                    264,
                    300,
                )?,
            ));
        }
        self.units.extend(units);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_checked_but_wrong_geometry_and_corrupted_font() {
        let folder = std::env::temp_dir().join(format!("8sword-media-{}", std::process::id()));
        std::fs::create_dir(&folder).unwrap();
        let path = folder.join("image.rgba");
        let mut bytes = b"8SRGBA01".to_vec();
        bytes.extend(1u32.to_le_bytes());
        bytes.extend(1u32.to_le_bytes());
        bytes.extend([1, 2, 3, 255]);
        bytes.extend(checksum(&bytes).to_le_bytes());
        std::fs::write(&path, &bytes).unwrap();
        assert!(Image::load(&path, 1, 1).is_ok());
        assert!(Image::load(&path, 1920, 1200).is_err());
        bytes[16] ^= 1;
        std::fs::write(&path, &bytes).unwrap();
        assert!(Image::load(&path, 1, 1).is_err());
        let mut bytes = b"8SGLYP01".to_vec();
        bytes.extend(u32::MAX.to_le_bytes());
        bytes.extend(checksum(&bytes).to_le_bytes());
        std::fs::write(&path, bytes).unwrap();
        assert!(Font::load(&path).is_err());
        std::fs::remove_dir_all(folder).unwrap();
    }
}
