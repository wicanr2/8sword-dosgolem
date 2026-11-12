//! The approved optional formation and archer-pressure rules, shared with AI.
use std::{
    fs,
    io::{Read, Write},
    path::Path,
    sync::atomic::{AtomicU64, Ordering},
};
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum Mode {
    #[default]
    Native,
    Formation,
    Tactics,
}
impl Mode {
    pub fn parse(s: &str) -> Result<Self, String> {
        match s {
            "native" => Ok(Self::Native),
            "formation" => Ok(Self::Formation),
            "tactics" => Ok(Self::Tactics),
            _ => Err("規則模式無效".into()),
        }
    }
    pub fn name(self) -> &'static str {
        match self {
            Self::Native => "native",
            Self::Formation => "formation",
            Self::Tactics => "tactics",
        }
    }
    pub fn index(self) -> usize {
        match self {
            Self::Native => 0,
            Self::Formation => 1,
            Self::Tactics => 2,
        }
    }
    pub fn from_index(n: usize) -> Self {
        match n {
            1 => Self::Formation,
            2 => Self::Tactics,
            _ => Self::Native,
        }
    }
}
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Scale {
    pub pressure: bool,
    pub formation: bool,
}
impl Scale {
    pub fn apply(self, amount: u64) -> u64 {
        let mut n = u128::from(amount);
        if self.pressure {
            n = n * 75 / 100;
        }
        if self.formation {
            n = n * 80 / 100;
        }
        n as u64
    }
}
pub fn scale(
    mode: Mode,
    source_slot: usize,
    source_kind: u8,
    source_count: u32,
    target_slot: usize,
    target_kind: u8,
    target_count: u32,
    front: [u32; 3],
) -> Scale {
    Scale {
        pressure: mode == Mode::Tactics
            && source_slot < 3
            && source_kind == 3
            && source_count > 0
            && front[source_slot] > 0,
        formation: mode != Mode::Native
            && target_slot < 3
            && target_kind == 1
            && target_count > 0
            && front
                .iter()
                .enumerate()
                .any(|(i, n)| i != target_slot && *n > 0),
    }
}
const LIMIT: u64 = 4096;
static NONCE: AtomicU64 = AtomicU64::new(0);
fn marker_name(name: &str) -> Result<String, String> {
    if !["battle.chk", "journey.chk"].contains(&name) {
        return Err("規則進度槽位無效".into());
    }
    Ok(format!("{name}.rules.json"))
}
fn parse(raw: &[u8], data: &[u8]) -> Result<Mode, String> {
    let text = std::str::from_utf8(raw).map_err(|_| "規則標記字碼無效")?;
    let mut quoted = false;
    let mut compact = String::new();
    for c in text.chars() {
        if c == '"' {
            quoted = !quoted;
        }
        if quoted || !c.is_ascii_whitespace() {
            compact.push(c);
        }
    }
    let body = compact
        .strip_prefix('{')
        .and_then(|s| s.strip_suffix('}'))
        .ok_or("規則標記格式無效")?;
    let mut fields = std::collections::BTreeMap::new();
    for part in body.split(',') {
        let (k, v) = part.split_once(':').ok_or("規則標記欄位無效")?;
        if fields.insert(k, v).is_some() {
            return Err("規則標記欄位重複".into());
        }
    }
    if fields.len() != 4 || fields.get("\"schema\"") != Some(&"1") {
        return Err("規則標記版本無效".into());
    }
    let value = |key: &str| fields.get(key).copied().ok_or("規則標記缺欄");
    let mode = value("\"rules\"")?
        .strip_prefix('"')
        .and_then(|s| s.strip_suffix('"'))
        .ok_or("規則標記模式無效")?;
    if value("\"save_bytes\"")? != data.len().to_string()
        || value("\"save_sha256\"")? != format!("\"{}\"", crate::sha256::hex(data))
    {
        return Err("規則標記與進度不符".into());
    }
    Mode::parse(mode)
}
pub(crate) fn read_marker(dir: &Path, name: &str, data: &[u8]) -> Result<Mode, String> {
    let path = dir.join(marker_name(name)?);
    match path.symlink_metadata() {
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(Mode::Native),
        Ok(st) if st.file_type().is_file() && st.len() <= LIMIT => {}
        _ => return Err("規則標記形態無效".into()),
    }
    let mut raw = Vec::new();
    fs::File::open(path)
        .map_err(|e| e.to_string())?
        .take(LIMIT + 1)
        .read_to_end(&mut raw)
        .map_err(|e| e.to_string())?;
    if raw.len() as u64 > LIMIT {
        return Err("規則標記過大".into());
    }
    parse(&raw, data)
}
pub(crate) fn write_marker(dir: &Path, name: &str, data: &[u8], mode: Mode) -> Result<(), String> {
    let path = dir.join(marker_name(name)?);
    match path.symlink_metadata() {
        Err(e) if e.kind() == std::io::ErrorKind::NotFound && mode == Mode::Native => return Ok(()),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
        Ok(st) if st.file_type().is_file() => {}
        _ => return Err("規則標記形態無效".into()),
    }
    if fs::read(dir.join(name)).map_err(|e| e.to_string())? != data {
        return Err("規則進度寫入未完成".into());
    }
    let raw = format!(
        "{{\"schema\":1,\"rules\":\"{}\",\"save_sha256\":\"{}\",\"save_bytes\":{}}}\n",
        mode.name(),
        crate::sha256::hex(data),
        data.len()
    );
    let temp = dir.join(format!(
        ".rules-{}-{}.tmp",
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
        f.write_all(raw.as_bytes())
            .and_then(|_| f.sync_all())
            .map_err(|e| e.to_string())?;
        drop(f);
        crate::platform::replace_file(&temp, &path).map_err(|e| e.to_string())?;
        crate::platform::sync_directory(dir).map_err(|e| e.to_string())
    })();
    if result.is_err() {
        let _ = fs::remove_file(temp);
    }
    result
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn fixed_go_rule_vectors() {
        let mut n = 0;
        for l in include_str!("../rules-reference.tsv")
            .lines()
            .filter(|l| !l.starts_with('#'))
        {
            let v: Vec<u64> = l.split('\t').map(|x| x.parse().unwrap()).collect();
            let s = scale(
                Mode::from_index(v[0] as usize),
                v[1] as usize,
                v[2] as u8,
                v[3] as u32,
                v[4] as usize,
                v[5] as u8,
                v[6] as u32,
                [v[7] as u32, v[8] as u32, v[9] as u32],
            );
            assert_eq!(s.apply(v[10]), v[11]);
            n += 1;
        }
        assert!(n >= 400);
    }
    #[test]
    fn marker_is_hash_bound_strict_and_native_can_replace_old_mode() {
        let dir = std::env::temp_dir().join(format!("8s-rules-{}", std::process::id()));
        fs::create_dir(&dir).unwrap();
        fs::write(dir.join("battle.chk"), b"old").unwrap();
        assert_eq!(
            read_marker(&dir, "battle.chk", b"old").unwrap(),
            Mode::Native
        );
        write_marker(&dir, "battle.chk", b"old", Mode::Tactics).unwrap();
        assert_eq!(
            read_marker(&dir, "battle.chk", b"old").unwrap(),
            Mode::Tactics
        );
        assert!(read_marker(&dir, "battle.chk", b"new").is_err());
        write_marker(&dir, "battle.chk", b"old", Mode::Native).unwrap();
        assert_eq!(
            read_marker(&dir, "battle.chk", b"old").unwrap(),
            Mode::Native
        );
        let p = dir.join("battle.chk.rules.json");
        fs::write(&p, b"{\"schema\":1,\"rules\":\"other\"}").unwrap();
        assert!(read_marker(&dir, "battle.chk", b"old").is_err());
        fs::remove_file(&p).unwrap();
        fs::create_dir(&p).unwrap();
        assert!(read_marker(&dir, "battle.chk", b"old").is_err());
        fs::remove_dir_all(dir).unwrap();
    }
}
