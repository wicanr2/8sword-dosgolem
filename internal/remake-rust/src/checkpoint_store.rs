//! Atomic, single-slot development checkpoint. No Go or DOS sidecar.
use crate::catalog::Catalog;
use crate::controller::Checkpoint;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
const NAME: &str = "battle.chk";
const LIMIT: u64 = 4096;
static NONCE: AtomicU64 = AtomicU64::new(0);
pub fn check_directory(dir: &Path) -> Result<(), String> {
    let st = dir.symlink_metadata().map_err(|e| e.to_string())?;
    if !st.is_dir() || st.file_type().is_symlink() {
        return Err("存檔目錄不合法".into());
    }
    Ok(())
}
fn read_file(path: &Path, limit: u64) -> Result<Vec<u8>, String> {
    let st = path.symlink_metadata().map_err(|e| e.to_string())?;
    if !st.is_file() || st.len() > limit {
        return Err("存檔檔案不合法".into());
    }
    let f = File::open(path).map_err(|e| e.to_string())?;
    let mut bytes = Vec::new();
    f.take(limit + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() as u64 > limit {
        return Err("存檔過大".into());
    }
    Ok(bytes)
}
pub fn load<'a>(dir: &Path, catalog: &'a Catalog) -> Result<Checkpoint<'a>, String> {
    check_directory(dir)?;
    let raw = read_file(&dir.join(NAME), LIMIT)?;
    let mut cp = Checkpoint::decode(catalog, &raw)?;
    cp.controller
        .restore_rules(crate::rules::read_marker(dir, NAME, &raw)?);
    Ok(cp)
}
fn fresh(path: &Path) -> Result<File, String> {
    let mut options = OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    options.open(path).map_err(|e| e.to_string())
}
struct Pending {
    lock: PathBuf,
    temp: PathBuf,
    owns_temp: bool,
}
impl Drop for Pending {
    fn drop(&mut self) {
        if self.owns_temp {
            let _ = fs::remove_file(&self.temp);
        }
        let _ = fs::remove_file(&self.lock);
    }
}
pub fn save(dir: &Path, checkpoint: &Checkpoint<'_>) -> Result<(), String> {
    save_inner(dir, checkpoint, false)
}
fn save_inner(dir: &Path, checkpoint: &Checkpoint<'_>, interrupt: bool) -> Result<(), String> {
    let raw = checkpoint.encode()?;
    save_named(
        dir,
        NAME,
        &raw,
        LIMIT,
        |b| Checkpoint::decode(checkpoint.catalog(), b).map(|_| ()),
        interrupt,
    )?;
    crate::rules::write_marker(dir, NAME, &raw, checkpoint.controller.rules())
}
pub(crate) fn read_named(dir: &Path, name: &str, limit: u64) -> Result<Vec<u8>, String> {
    check_directory(dir)?;
    if ![NAME, "world-preview.chk", "journey.chk"].contains(&name)
        || limit > if name == "journey.chk" { 131072 } else { 16384 }
    {
        return Err("檢查點槽位錯誤".into());
    }
    read_file(&dir.join(name), limit)
}
pub(crate) fn save_named(
    dir: &Path,
    name: &str,
    raw: &[u8],
    limit: u64,
    validate: impl Fn(&[u8]) -> Result<(), String>,
    interrupt: bool,
) -> Result<(), String> {
    save_named_inner(dir, name, raw, limit, validate, interrupt, false)
}
/// The start menu calls this only after explicit new-game confirmation.
pub(crate) fn reset_journey(
    dir: &Path,
    raw: &[u8],
    validate: impl Fn(&[u8]) -> Result<(), String>,
) -> Result<(), String> {
    save_named_inner(dir, "journey.chk", raw, 131072, validate, false, true)
}
fn save_named_inner(
    dir: &Path,
    name: &str,
    raw: &[u8],
    limit: u64,
    validate: impl Fn(&[u8]) -> Result<(), String>,
    interrupt: bool,
    reset: bool,
) -> Result<(), String> {
    check_directory(dir)?;
    if ![NAME, "world-preview.chk", "journey.chk"].contains(&name)
        || limit > if name == "journey.chk" { 131072 } else { 16384 }
        || raw.len() as u64 > limit
    {
        return Err("檢查點槽位錯誤".into());
    }
    validate(raw)?;
    let lock = dir.join(".battle-checkpoint.lock");
    let _lock_file = fresh(&lock)?;
    let temp = dir.join(format!(
        ".battle-{}-{}.tmp",
        std::process::id(),
        NONCE.fetch_add(1, Ordering::Relaxed)
    ));
    let mut pending = Pending {
        lock,
        temp,
        owns_temp: false,
    };
    let path = dir.join(name);
    match path.symlink_metadata() {
        Ok(st) => {
            if reset {
                if !st.is_file() || st.file_type().is_symlink() {
                    return Err("新遊戲進度槽位不合法".into());
                }
            } else {
                validate(&read_file(&path, limit)?)?;
            }
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
        Err(e) => return Err(e.to_string()),
    }
    let mut f = fresh(&pending.temp)?;
    pending.owns_temp = true;
    f.write_all(&raw)
        .and_then(|_| f.sync_all())
        .map_err(|e| e.to_string())?;
    drop(f);
    if interrupt {
        return Err("受控提交前中斷".into());
    }
    crate::platform::replace_file(&pending.temp, &path).map_err(|e| e.to_string())?;
    crate::platform::sync_directory(dir).map_err(|e| e.to_string())?;
    drop(pending);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::battle::{Modifiers, Side, Stack};
    use crate::catalog::UnitId;
    use crate::controller::{Controller, OriginalRng, ViewState};
    fn fixture(c: &Catalog) -> Checkpoint<'_> {
        let mut rows = [[Stack::default(); 6]; 2];
        rows[0][0] = Stack {
            unit: Some(UnitId::parse("openkb:wolf").unwrap()),
            count: 10,
        };
        rows[1][0] = Stack {
            unit: Some(UnitId::parse("native:16").unwrap()),
            count: 10,
        };
        Checkpoint {
            controller: Controller::new(c, rows, Side::Player, Modifiers::default()).unwrap(),
            rng: OriginalRng { seed: 1 },
            view: ViewState::default(),
        }
    }
    #[test]
    fn atomic_replace_interrupt_and_lock_leave_old_checkpoint_intact() {
        let c = Catalog::builtin().unwrap();
        let mut a = fixture(&c);
        let dir = std::env::temp_dir().join(format!("8sword-store-{}", std::process::id()));
        fs::create_dir(&dir).unwrap();
        save(&dir, &a).unwrap();
        let before = fs::read(dir.join(NAME)).unwrap();
        a.rng.next15();
        assert!(save_inner(&dir, &a, true).is_err());
        assert_eq!(fs::read(dir.join(NAME)).unwrap(), before);
        assert_eq!(fs::read_dir(&dir).unwrap().count(), 1);
        fs::write(dir.join(".battle-checkpoint.lock"), b"other writer").unwrap();
        assert!(save(&dir, &a).is_err());
        assert_eq!(fs::read(dir.join(NAME)).unwrap(), before);
        fs::remove_file(dir.join(".battle-checkpoint.lock")).unwrap();
        save(&dir, &a).unwrap();
        assert_eq!(load(&dir, &c).unwrap(), a);
        fs::write(dir.join(NAME), b"corrupt").unwrap();
        assert!(save(&dir, &a).is_err());
        assert_eq!(fs::read(dir.join(NAME)).unwrap(), b"corrupt");
        fs::remove_dir_all(dir).unwrap();
    }
    #[cfg(unix)]
    #[test]
    fn links_directories_and_oversized_inputs_are_rejected() {
        use std::os::unix::fs::symlink;
        let c = Catalog::builtin().unwrap();
        let a = fixture(&c);
        let base = std::env::temp_dir().join(format!("8sword-links-{}", std::process::id()));
        fs::create_dir(&base).unwrap();
        let dir = base.join("save");
        fs::create_dir(&dir).unwrap();
        let outside = base.join("outside");
        fs::write(&outside, b"untouched").unwrap();
        symlink(&outside, dir.join(NAME)).unwrap();
        assert!(load(&dir, &c).is_err());
        assert!(save(&dir, &a).is_err());
        assert_eq!(fs::read(&outside).unwrap(), b"untouched");
        fs::remove_file(dir.join(NAME)).unwrap();
        fs::create_dir(dir.join(NAME)).unwrap();
        assert!(save(&dir, &a).is_err());
        fs::remove_dir(dir.join(NAME)).unwrap();
        fs::write(dir.join(NAME), vec![0; 4097]).unwrap();
        assert!(load(&dir, &c).is_err());
        let alias = base.join("alias");
        symlink(&dir, &alias).unwrap();
        assert!(load(&alias, &c).is_err());
        assert!(save(&alias, &a).is_err());
        fs::remove_dir_all(base).unwrap();
    }
}
