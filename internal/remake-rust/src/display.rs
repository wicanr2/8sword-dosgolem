//! Presentation-only mode and the complete original-pixel asset group.
use std::{
    collections::BTreeMap,
    fs,
    io::Write,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum Mode {
    #[default]
    Hd,
    Original,
}
impl Mode {
    pub fn parse(s: &str) -> Result<Self, String> {
        match s {
            "hd" => Ok(Self::Hd),
            "original" => Ok(Self::Original),
            _ => Err("畫面模式無效".into()),
        }
    }
    pub fn name(self) -> &'static str {
        match self {
            Self::Hd => "hd",
            Self::Original => "original",
        }
    }
    pub fn original(self) -> bool {
        self == Self::Original
    }
}
pub fn expected() -> BTreeMap<String, (usize, usize)> {
    let mut m = BTreeMap::new();
    for (n, w, h) in [
        ("background.rgba", 1920, 1200),
        ("world-frame.rgba", 1920, 1200),
        ("recruit-building.rgba", 1344, 600),
        ("magic-building.rgba", 1344, 600),
        ("hero-portrait.rgba", 240, 240),
        ("magic-book.rgba", 96, 96),
    ] {
        m.insert(n.into(), (w, h));
    }
    for (prefix, count, w, h) in [
        ("map-tile-", 65, 192, 150),
        ("map-hero-", 12, 192, 150),
        ("unit_native_", 25, 264, 300),
    ] {
        for i in 0..count {
            m.insert(
                format!(
                    "{prefix}{:02}.rgba",
                    i + usize::from(prefix == "unit_native_")
                ),
                (w, h),
            );
        }
    }
    for i in 0..4 {
        m.insert(format!("spell-impact-{i}.rgba"), (264, 300));
    }
    for i in 1..8 {
        m.insert(format!("item-{i}.rgba"), (96, 96));
    }
    for n in [
        "arcr", "pike", "wolf", "skel", "troll", "drui", "vamp", "drag",
    ] {
        m.insert(format!("unit_openkb_{n}.rgba"), (264, 300));
    }
    m
}
pub fn preflight(root: &Path) -> Result<bool, String> {
    let dir = root.join("original");
    match dir.symlink_metadata() {
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(false),
        Ok(s) if s.file_type().is_dir() => {}
        _ => return Err("原圖素材組形態無效".into()),
    }
    let path = dir.join("images.tsv");
    let st = path.symlink_metadata().map_err(|_| "原圖素材索引缺失")?;
    if !st.file_type().is_file() || st.len() > 32768 {
        return Err("原圖素材索引形態無效".into());
    }
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    if lines.next() != Some("8SORIG01") {
        return Err("原圖素材索引版本無效".into());
    }
    let mut wanted = expected();
    for line in lines {
        let v: Vec<_> = line.split('\t').collect();
        if v.len() != 4 {
            return Err("原圖素材索引欄位無效".into());
        }
        let (w, h) = wanted.remove(v[0]).ok_or("原圖素材重複或未知")?;
        if v[1] != w.to_string() || v[2] != h.to_string() {
            return Err("原圖素材索引尺寸不符".into());
        }
        let p = dir.join(v[0]);
        crate::media_assets::Image::load(&p, w, h)?;
        if crate::sha256::hex(&fs::read(p).map_err(|e| e.to_string())?) != v[3] {
            return Err("原圖素材SHA不符".into());
        }
    }
    if !wanted.is_empty() {
        return Err("原圖素材組不完整".into());
    }
    Ok(true)
}
pub fn select_group<'a>(
    images: impl IntoIterator<Item = &'a mut crate::media_assets::Image>,
    original: bool,
) -> Result<(), String> {
    let images: Vec<_> = images.into_iter().collect();
    if images.iter().any(|im| !im.can_select(original)) {
        return Err("原圖素材組尚未完整預載".into());
    }
    for im in images {
        im.select(original)?;
    }
    Ok(())
}
fn preference(raw: &[u8]) -> Result<Mode, String> {
    if raw.len() > 4096 {
        return Err("畫面偏好過大".into());
    }
    let s = std::str::from_utf8(raw).map_err(|_| "畫面偏好字碼無效")?;
    let mut quoted = false;
    let mut compact = String::new();
    for c in s.chars() {
        if c == '"' {
            quoted = !quoted;
        }
        if quoted || !matches!(c, ' ' | '\r' | '\n' | '\t') {
            compact.push(c);
        }
    }
    for mode in [Mode::Hd, Mode::Original] {
        if compact == format!("{{\"schema\":1,\"mode\":\"{}\"}}", mode.name())
            || compact == format!("{{\"mode\":\"{}\",\"schema\":1}}", mode.name())
        {
            return Ok(mode);
        }
    }
    Err("畫面偏好無效".into())
}
static NONCE: AtomicU64 = AtomicU64::new(0);
#[derive(Default)]
pub struct Settings {
    pub mode: Mode,
    pub available: bool,
    pub configured: bool,
    path: Option<PathBuf>,
}
impl Settings {
    pub fn load(root: &Path, store: Option<&Path>) -> Result<Self, String> {
        let mut s = Self {
            available: preflight(root)?,
            path: store.map(|p| p.join("display.json")),
            ..Self::default()
        };
        if let Some(path) = &s.path {
            match path.symlink_metadata() {
                Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
                Ok(st) if st.file_type().is_file() && st.len() <= 4096 => {
                    s.mode = preference(&fs::read(path).map_err(|e| e.to_string())?)?;
                    s.configured = true;
                }
                _ => return Err("畫面偏好形態無效".into()),
            }
        }
        if s.mode.original() && !s.available {
            return Err("此資料包沒有原圖素材組".into());
        }
        Ok(s)
    }
    pub fn choose(&mut self, mode: Mode, persist: bool) -> Result<(), String> {
        if mode.original() && !self.available {
            return Err("此資料包沒有原圖素材組".into());
        }
        if persist {
            if let Some(path) = &self.path {
                crate::checkpoint_store::check_directory(path.parent().ok_or("畫面偏好目錄無效")?)?;
                match path.symlink_metadata() {
                    Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
                    Ok(st) if st.file_type().is_file() => {}
                    _ => return Err("畫面偏好形態無效".into()),
                }
                let temp = path.with_file_name(format!(
                    ".display-{}-{}.tmp",
                    std::process::id(),
                    NONCE.fetch_add(1, Ordering::Relaxed)
                ));
                let mut options = fs::OpenOptions::new();
                options.write(true).create_new(true);
                #[cfg(unix)]
                {
                    use std::os::unix::fs::OpenOptionsExt;
                    options.mode(0o600);
                }
                let mut f = options.open(&temp).map_err(|e| e.to_string())?;
                let result = (|| {
                    f.write_all(
                        format!("{{\"schema\":1,\"mode\":\"{}\"}}\n", mode.name()).as_bytes(),
                    )
                    .and_then(|_| f.sync_all())
                    .map_err(|e| e.to_string())?;
                    drop(f);
                    fs::rename(&temp, path).map_err(|e| e.to_string())?;
                    fs::File::open(path.parent().unwrap())
                        .and_then(|f| f.sync_all())
                        .map_err(|e| e.to_string())
                })();
                if result.is_err() {
                    let _ = fs::remove_file(temp);
                }
                result?;
            }
        }
        self.mode = mode;
        if persist {
            self.configured = true;
        }
        Ok(())
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn fixed_group_and_strict_preferences() {
        assert_eq!(expected().len(), 127);
        assert_eq!(
            preference(b"{\"schema\":1,\"mode\":\"original\"}").unwrap(),
            Mode::Original
        );
        assert_eq!(
            preference(b"{ \"mode\":\"hd\",\"schema\":1 }").unwrap(),
            Mode::Hd
        );
        for s in [
            b"{}".as_slice(),
            b"{\"schema\":1,\"mode\":\"auto\"}",
            b"{\"schema\":1,\"mode\":\"hd\",\"x\":0}",
            b"{\"schema\":1,\"mode\":\"hd\"}\x0b",
        ] {
            assert!(preference(s).is_err());
        }
        assert!(Mode::parse("auto").is_err());
    }
    #[test]
    fn old_pack_missing_group_is_hd_and_bad_group_rejects() {
        let d = std::env::temp_dir().join(format!("8s-display-group-{}", std::process::id()));
        fs::create_dir(&d).unwrap();
        let mut s = Settings::load(&d, None).unwrap();
        assert!(!s.available);
        assert!(s.choose(Mode::Original, true).is_err());
        assert_eq!(s.mode, Mode::Hd);
        fs::create_dir(d.join("original")).unwrap();
        assert!(preflight(&d).is_err());
        fs::write(d.join("original/images.tsv"), b"8SORIG01\n").unwrap();
        assert!(preflight(&d).is_err());
        fs::remove_dir_all(d).unwrap();
    }
    #[test]
    fn preferences_round_trip_and_failed_commit_keeps_mode() {
        let d = std::env::temp_dir().join(format!("8s-display-save-{}", std::process::id()));
        fs::create_dir(&d).unwrap();
        let mut s = Settings {
            available: true,
            path: Some(d.join("display.json")),
            ..Settings::default()
        };
        s.choose(Mode::Original, true).unwrap();
        assert_eq!(
            preference(&fs::read(d.join("display.json")).unwrap()).unwrap(),
            Mode::Original
        );
        fs::remove_file(d.join("display.json")).unwrap();
        fs::create_dir(d.join("display.json")).unwrap();
        assert!(s.choose(Mode::Hd, true).is_err());
        assert_eq!(s.mode, Mode::Original);
        fs::remove_dir_all(d).unwrap();
    }
    #[cfg(unix)]
    #[test]
    fn preferences_reject_symlinks_and_load_old_hd_without_asset_group() {
        use std::os::unix::fs::symlink;
        let d = std::env::temp_dir().join(format!("8s-display-links-{}", std::process::id()));
        fs::create_dir(&d).unwrap();
        fs::write(d.join("outside"), b"untouched").unwrap();
        symlink(d.join("outside"), d.join("display.json")).unwrap();
        assert!(Settings::load(&d, Some(&d)).is_err());
        let mut s = Settings {
            available: true,
            path: Some(d.join("display.json")),
            ..Settings::default()
        };
        assert!(s.choose(Mode::Original, true).is_err());
        assert_eq!(s.mode, Mode::Hd);
        assert_eq!(fs::read(d.join("outside")).unwrap(), b"untouched");
        fs::remove_file(d.join("display.json")).unwrap();
        s.choose(Mode::Hd, true).unwrap();
        let cold = Settings::load(&d, Some(&d)).unwrap();
        assert!(cold.configured);
        assert_eq!(cold.mode, Mode::Hd);
        fs::remove_dir_all(d).unwrap();
    }
}
