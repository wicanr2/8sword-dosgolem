//! Platform packaging boundaries; game state and save bytes are unchanged.
use std::path::{Path, PathBuf};

pub const VERSION: &str = match option_env!("EIGHTSWORD_BUILD_VERSION") {
    Some(v) => v,
    None => "v.0.1.0-dev",
};

pub fn asset_root(exe: &Path) -> Result<PathBuf, String> {
    let parent = exe.parent().ok_or("執行檔路徑錯誤")?;
    #[cfg(target_os = "macos")]
    if parent.file_name().is_some_and(|s| s == "MacOS") {
        return Ok(parent
            .parent()
            .ok_or("應用程式路徑錯誤")?
            .join("Resources/pack"));
    }
    Ok(parent.join("pack"))
}

pub fn replace_file(from: &Path, to: &Path) -> std::io::Result<()> {
    #[cfg(windows)]
    {
        use std::os::windows::ffi::OsStrExt;
        #[link(name = "kernel32")]
        unsafe extern "system" {
            fn MoveFileExW(from: *const u16, to: *const u16, flags: u32) -> i32;
        }
        let wide = |p: &Path| -> std::io::Result<Vec<u16>> {
            let mut v: Vec<_> = p.as_os_str().encode_wide().collect();
            if v.contains(&0) {
                return Err(std::io::Error::new(
                    std::io::ErrorKind::InvalidInput,
                    "路徑含空字元",
                ));
            }
            v.push(0);
            Ok(v)
        };
        let a = wide(from)?;
        let b = wide(to)?;
        if unsafe { MoveFileExW(a.as_ptr(), b.as_ptr(), 1 | 8) } == 0 {
            return Err(std::io::Error::last_os_error());
        }
        Ok(())
    }
    #[cfg(not(windows))]
    {
        std::fs::rename(from, to)
    }
}

pub fn sync_directory(dir: &Path) -> std::io::Result<()> {
    #[cfg(unix)]
    {
        std::fs::File::open(dir)?.sync_all()
    }
    #[cfg(not(unix))]
    {
        let _ = dir;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn unicode_replacement_and_failed_source_preserve_file() {
        let dir = std::env::temp_dir().join(format!("八劍包裝測試-{}", std::process::id()));
        std::fs::create_dir(&dir).unwrap();
        let target = dir.join("存檔.chk");
        let temp = dir.join("暫存.tmp");
        std::fs::write(&target, b"old").unwrap();
        std::fs::write(&temp, b"new").unwrap();
        super::replace_file(&temp, &target).unwrap();
        super::sync_directory(&dir).unwrap();
        assert_eq!(std::fs::read(&target).unwrap(), b"new");
        assert!(super::replace_file(&temp, &target).is_err());
        assert_eq!(std::fs::read(&target).unwrap(), b"new");
        std::fs::remove_dir_all(dir).unwrap();
    }
}
