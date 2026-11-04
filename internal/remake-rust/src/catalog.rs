use std::fmt;

const EXTRA_IDS: [&str; 8] = [
    "openkb:arcr",
    "openkb:pike",
    "openkb:wolf",
    "openkb:skel",
    "openkb:troll",
    "openkb:drui",
    "openkb:vamp",
    "openkb:drag",
];

/// A validated identity. Its storage code is private and is never a DOS kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct UnitId(u8);

impl UnitId {
    pub fn parse(text: &str) -> Result<Self, String> {
        if let Some(number) = text.strip_prefix("native:") {
            let kind: u8 = number.parse().map_err(|_| "兵種ID無效")?;
            if (1..=25).contains(&kind) && text == format!("native:{kind:02}") {
                return Ok(Self(kind));
            }
        }
        EXTRA_IDS
            .iter()
            .position(|id| *id == text)
            .map(|index| Self(26 + index as u8))
            .ok_or_else(|| "兵種ID無效".into())
    }

    pub fn native_kind(self) -> Option<u8> {
        (self.0 <= 25).then_some(self.0)
    }

    pub fn is_native_caster(self) -> bool {
        matches!(self.native_kind(), Some(10 | 12))
    }
    fn index(self) -> usize {
        usize::from(self.0 - 1)
    }
}

impl fmt::Display for UnitId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if let Some(kind) = self.native_kind() {
            write!(f, "native:{kind:02}")
        } else {
            f.write_str(EXTRA_IDS[usize::from(self.0 - 26)])
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnitProfile {
    pub id: UnitId,
    pub name: String,
    pub gold: u64,
    pub command: u64,
    pub rank: u8,
    pub attack: u64,
    pub hp: u64,
    pub ranged: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Catalog {
    profiles: [UnitProfile; 33],
}

impl Catalog {
    pub fn parse(text: &str) -> Result<Self, String> {
        let mut profiles: [Option<UnitProfile>; 33] = std::array::from_fn(|_| None);
        for (line, row) in text.lines().enumerate() {
            if row.starts_with('#') || row.trim().is_empty() {
                continue;
            }
            let fields: Vec<_> = row.split('\t').collect();
            let fail = || format!("兵種資料第 {} 行無效", line + 1);
            if fields.len() != 8 {
                return Err(fail());
            }
            let id = UnitId::parse(fields[0])?;
            let number = |at: usize| fields[at].parse::<u64>().map_err(|_| fail());
            let profile = UnitProfile {
                id,
                name: fields[1].into(),
                gold: number(2)?,
                command: number(3)?,
                rank: number(4)?.try_into().map_err(|_| fail())?,
                attack: number(5)?,
                hp: number(6)?,
                ranged: match fields[7] {
                    "0" => false,
                    "1" => true,
                    _ => return Err(fail()),
                },
            };
            if profiles[id.index()].is_some()
                || profile.name.is_empty()
                || profile.gold == 0
                || profile.command == 0
                || profile.attack == 0
                || profile.hp == 0
                || profile.rank > 5
            {
                return Err(fail());
            }
            profiles[id.index()] = Some(profile);
        }
        let values: Vec<_> = profiles
            .into_iter()
            .collect::<Option<Vec<_>>>()
            .ok_or("兵種資料必須包含完整33種ID")?;
        Ok(Self {
            profiles: values.try_into().map_err(|_| "兵種列數無效")?,
        })
    }

    pub fn builtin() -> Result<Self, String> {
        Self::parse(include_str!("../unit-catalog.tsv"))
    }
    pub fn get(&self, id: UnitId) -> &UnitProfile {
        &self.profiles[id.index()]
    }
    pub fn profiles(&self) -> &[UnitProfile; 33] {
        &self.profiles
    }
}
