//! Self-owned native development checkpoint. Not a Go/DOS save converter.
use super::*;
use crate::battle::Stack;
use crate::catalog::UnitId;
use crate::media_assets::checksum;

pub const LIMIT: usize = 4096;
const MAGIC: &[u8; 8] = b"8SBCHK01";
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ViewState {
    pub font: u8,
    pub music: bool,
    pub cursor: u8,
    pub spell_cursor: u8,
    // weak=1, player spells=2, taoist=4, enemy spells=8; explicit demo only.
    pub scenario: u8,
}
impl Default for ViewState {
    fn default() -> Self {
        Self {
            font: 0,
            music: true,
            cursor: 1,
            spell_cursor: 0,
            scenario: 0,
        }
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Checkpoint<'a> {
    pub controller: Controller<'a>,
    pub rng: OriginalRng,
    pub view: ViewState,
}
fn fingerprint(c: &Catalog) -> u64 {
    let mut data = String::new();
    for p in c.profiles() {
        data.push_str(&format!(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n",
            p.id,
            p.name,
            p.gold,
            p.command,
            p.rank,
            p.attack,
            p.hp,
            u8::from(p.ranged)
        ));
    }
    checksum(data.as_bytes())
}
struct Writer(Vec<u8>);
impl Writer {
    fn b(&mut self, v: u8) {
        self.0.push(v);
    }
    fn flag(&mut self, v: bool) {
        self.b(u8::from(v));
    }
    fn w(&mut self, v: u16) {
        self.0.extend(v.to_le_bytes());
    }
    fn d(&mut self, v: u32) {
        self.0.extend(v.to_le_bytes());
    }
    fn q(&mut self, v: u64) {
        self.0.extend(v.to_le_bytes());
    }
}
struct Reader<'b> {
    data: &'b [u8],
    at: usize,
}
impl Reader<'_> {
    fn bytes(&mut self, n: usize) -> Result<&[u8], String> {
        let end = self.at.checked_add(n).ok_or("檢查點長度錯誤")?;
        let v = self.data.get(self.at..end).ok_or("檢查點截斷")?;
        self.at = end;
        Ok(v)
    }
    fn b(&mut self) -> Result<u8, String> {
        Ok(self.bytes(1)?[0])
    }
    fn flag(&mut self) -> Result<bool, String> {
        match self.b()? {
            0 => Ok(false),
            1 => Ok(true),
            _ => Err("檢查點旗標錯誤".into()),
        }
    }
    fn w(&mut self) -> Result<u16, String> {
        Ok(u16::from_le_bytes(
            self.bytes(2)?.try_into().map_err(|_| "word截斷")?,
        ))
    }
    fn d(&mut self) -> Result<u32, String> {
        Ok(u32::from_le_bytes(
            self.bytes(4)?.try_into().map_err(|_| "dword截斷")?,
        ))
    }
    fn q(&mut self) -> Result<u64, String> {
        Ok(u64::from_le_bytes(
            self.bytes(8)?.try_into().map_err(|_| "qword截斷")?,
        ))
    }
    fn side(&mut self) -> Result<Side, String> {
        match self.b()? {
            0 => Ok(Side::Player),
            1 => Ok(Side::Enemy),
            _ => Err("檢查點陣營錯誤".into()),
        }
    }
}
impl<'a> Checkpoint<'a> {
    pub(crate) fn catalog(&self) -> &'a Catalog {
        self.controller.catalog
    }
    fn validate(&self) -> Result<(), String> {
        let c = &self.controller;
        let bad = || "檢查點狀態不合法".to_owned();
        if (self.view.scenario & 2 != 0) != c.book.is_some()
            || (self.view.scenario & 8 != 0) != c.enemy_config.is_some()
        {
            return Err(bad());
        }
        if self.view.font >= 3
            || !(1..=12).contains(&self.view.cursor)
            || self.view.spell_cursor >= 8
            || self.view.scenario > 15
            || self.view.scenario & 4 != 0 && self.view.scenario & 2 == 0
            || c.half_turn == 0
            || c.scan.front > 3
            || !(3..=6).contains(&c.scan.rear)
            || c.scan.front < 3 && c.scan.rear != 3
            || c.modifiers.player_attack >= 5
            || c.modifiers.player_boost == 65535
            || c.modifiers.enemy_defense > 65530
        {
            return Err(bad());
        }
        Battle::restore_native(
            c.catalog,
            *c.battle.rows(),
            *c.battle.hp(),
            c.battle.sequence(),
            c.battle.retreated(),
        )
        .map_err(|_| bad())?;
        if c.book.as_ref().is_some_and(|b| b.stat_26ae > 6552)
            || c.enemy_config
                .is_some_and(|e| e.stat_26ae > 6552 || e.shifted_alias >= 12)
        {
            return Err(bad());
        }
        for side in 0..2 {
            let mut occurrence = [0u8; 6];
            for raw in c.slots[side] {
                if raw >= 6 {
                    return Err(bad());
                }
                occurrence[usize::from(raw)] += 1;
            }
            for (raw, row) in c.battle.rows()[side].iter().enumerate() {
                if row.count > 0 && occurrence[raw] != 1 {
                    return Err(bad());
                }
                if row.unit.is_some_and(|id| id.is_native_caster())
                    && if side == 0 {
                        c.book.is_none()
                    } else {
                        c.enemy_config.is_none()
                    }
                {
                    return Err(bad());
                }
                if side == 1
                    && c.enemy_config.is_some()
                    && row.count > 0
                    && row.unit.is_some_and(|id| id.native_kind().is_none())
                {
                    return Err(bad());
                }
            }
        }
        if let Some(a) = c.actor {
            if a.side != c.side
                || a.slot >= 6
                || a.raw >= 6
                || usize::from(c.slots[a.side.index()][a.slot]) != a.raw
            {
                return Err(bad());
            }
            let row = c.battle.rows()[a.side.index()][a.raw];
            let id = row.unit.ok_or_else(bad)?;
            if row.count == 0
                || a.ranged != c.catalog.get(id).ranged
                || c.battle.outcome().is_some()
                || if a.slot < 3 {
                    c.scan.front != a.slot
                } else {
                    c.scan.front != 3
                        || c.scan.rear != a.slot
                        || !(a.ranged || id.is_native_caster())
                }
            {
                return Err(bad());
            }
        }
        if c.selected_spell.is_some()
            && (!c.is_caster() || c.book.as_ref().is_none_or(|b| !b.enabled))
        {
            return Err(bad());
        }
        if c.selected_spell.is_some_and(|s| !s.targeted()) {
            return Err(bad());
        }
        if c.battle.outcome().is_some() && (c.actor.is_some() || c.selected_spell.is_some()) {
            return Err(bad());
        }
        Ok(())
    }
    pub fn encode(&self) -> Result<Vec<u8>, String> {
        self.validate()?;
        let c = &self.controller;
        let mut w = Writer(Vec::new());
        w.q(fingerprint(c.catalog));
        for side in 0..2 {
            for raw in 0..6 {
                let row = c.battle.rows()[side][raw];
                let id = row.unit.map(|id| id.to_string()).unwrap_or_default();
                w.b(id.len() as u8);
                w.0.extend(id.as_bytes());
                w.d(row.count);
                w.q(c.battle.hp()[side][raw]);
            }
        }
        w.q(c.battle.sequence());
        w.flag(c.battle.retreated());
        for side in 0..2 {
            for raw in c.slots[side] {
                w.b(raw);
            }
            for n in c.remaining[side] {
                w.w(n);
            }
        }
        w.b(c.side.index() as u8);
        w.flag(c.actor.is_some());
        if let Some(a) = c.actor {
            w.b(a.side.index() as u8);
            w.b(a.slot as u8);
            w.b(a.raw as u8);
            w.flag(a.ranged);
        }
        w.b(c.scan.front as u8);
        w.b(c.scan.rear as u8);
        w.flag(c.scan.activity);
        w.q(c.half_turn);
        w.w(c.modifiers.player_attack);
        w.w(c.modifiers.player_boost);
        w.w(c.modifiers.enemy_defense);
        w.flag(c.book.is_some());
        if let Some(b) = &c.book {
            w.flag(b.enabled);
            for n in b.charges {
                w.w(n);
            }
            w.w(b.stat_26b0);
            w.w(b.stat_26ae);
        }
        w.b(c.selected_spell.map(|s| s.index() as u8).unwrap_or(255));
        w.q(c.spell_returns);
        w.flag(c.enemy_config.is_some());
        if let Some(e) = c.enemy_config {
            w.w(e.stat_26ae);
            w.b(e.shifted_alias);
        }
        w.q(c.enemy_returns);
        w.d(self.rng.seed);
        w.b(self.view.font);
        w.flag(self.view.music);
        w.b(self.view.cursor);
        w.b(self.view.spell_cursor);
        w.b(self.view.scenario);
        let mut out = MAGIC.to_vec();
        out.extend((w.0.len() as u32).to_le_bytes());
        out.extend(w.0);
        out.extend(checksum(&out).to_le_bytes());
        if out.len() > LIMIT {
            return Err("檢查點超過上限".into());
        }
        Ok(out)
    }
    pub fn decode(catalog: &'a Catalog, bytes: &[u8]) -> Result<Self, String> {
        if bytes.len() < 28 || bytes.len() > LIMIT || &bytes[..8] != MAGIC {
            return Err("檢查點格式或版本錯誤".into());
        }
        let end = bytes.len() - 8;
        if u64::from_le_bytes(bytes[end..].try_into().map_err(|_| "校驗截斷")?)
            != checksum(&bytes[..end])
            || u32::from_le_bytes(bytes[8..12].try_into().map_err(|_| "長度截斷")?) as usize
                != end - 12
        {
            return Err("檢查點長度或校驗錯誤".into());
        }
        let mut r = Reader {
            data: &bytes[12..end],
            at: 0,
        };
        if r.q()? != fingerprint(catalog) {
            return Err("檢查點兵種資料不相容".into());
        }
        let mut rows = [[Stack::default(); 6]; 2];
        let mut hp = [[0; 6]; 2];
        for side in 0..2 {
            for raw in 0..6 {
                let len = usize::from(r.b()?);
                if len > 16 {
                    return Err("檢查點ID過長".into());
                }
                let text = std::str::from_utf8(r.bytes(len)?).map_err(|_| "檢查點ID編碼錯誤")?;
                let unit = if text.is_empty() {
                    None
                } else {
                    Some(UnitId::parse(text)?)
                };
                rows[side][raw] = Stack {
                    unit,
                    count: r.d()?,
                };
                hp[side][raw] = r.q()?;
            }
        }
        let sequence = r.q()?;
        let retreat = r.flag()?;
        let battle = Battle::restore_native(catalog, rows, hp, sequence, retreat)
            .map_err(|e| format!("檢查點軍隊錯誤：{e:?}"))?;
        let mut slots = [[0; 6]; 2];
        let mut remaining = [[0; 6]; 2];
        for side in 0..2 {
            for n in &mut slots[side] {
                *n = r.b()?;
            }
            for n in &mut remaining[side] {
                *n = r.w()?;
            }
        }
        let side = r.side()?;
        let actor = if r.flag()? {
            Some(Actor {
                side: r.side()?,
                slot: usize::from(r.b()?),
                raw: usize::from(r.b()?),
                ranged: r.flag()?,
            })
        } else {
            None
        };
        let scan = Scan {
            front: usize::from(r.b()?),
            rear: usize::from(r.b()?),
            activity: r.flag()?,
        };
        let half_turn = r.q()?;
        let modifiers = Modifiers {
            player_attack: r.w()?,
            player_boost: r.w()?,
            enemy_defense: r.w()?,
        };
        let book = if r.flag()? {
            let enabled = r.flag()?;
            let mut charges = [0; 8];
            for n in &mut charges {
                *n = r.w()?;
            }
            Some(SpellBook {
                enabled,
                charges,
                stat_26b0: r.w()?,
                stat_26ae: r.w()?,
            })
        } else {
            None
        };
        let selected_spell = match r.b()? {
            255 => None,
            n => Some(*Spell::ALL.get(usize::from(n)).ok_or("檢查點法術錯誤")?),
        };
        let spell_returns = r.q()?;
        let enemy_config = if r.flag()? {
            Some(EnemyConfig {
                stat_26ae: r.w()?,
                shifted_alias: r.b()?,
            })
        } else {
            None
        };
        let enemy_returns = r.q()?;
        let rng = OriginalRng { seed: r.d()? };
        let view = ViewState {
            font: r.b()?,
            music: r.flag()?,
            cursor: r.b()?,
            spell_cursor: r.b()?,
            scenario: r.b()?,
        };
        if r.at != r.data.len() {
            return Err("檢查點有多餘資料".into());
        }
        let controller = Controller {
            catalog,
            battle,
            slots,
            remaining,
            side,
            actor,
            scan,
            half_turn,
            modifiers,
            book,
            selected_spell,
            spell_returns,
            enemy_config,
            enemy_returns,
        };
        let value = Self {
            controller,
            rng,
            view,
        };
        value.validate()?;
        Ok(value)
    }
}

#[cfg(test)]
#[path = "checkpoint_tests.rs"]
mod tests;
