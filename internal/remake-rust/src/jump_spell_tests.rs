use super::*;
use crate::{catalog::Catalog, media_assets::checksum, world::WorldState};
fn ready<'a>(d: &WorldData) -> Journey<'a> {
    let mut j = Journey::new(d, 1);
    j.magic.book = true;
    j.magic.charges[3] = 2;
    j.resources[5] = 3;
    j
}
#[test]
fn original_1445_arm_move_landing_and_reveal_vectors_match() {
    let mut count = 0;
    for l in include_str!("../jump-reference.tsv")
        .lines()
        .filter(|s| !s.starts_with('#'))
    {
        let fields: Vec<_> = l.split('\t').collect();
        let f: Vec<u16> = fields[..11].iter().map(|s| s.parse().unwrap()).collect();
        let d = WorldData::jump_fixture(f[2] as u8);
        let mut s = WorldState::new(&d, 1);
        s.position = Position {
            x: f[4] as u8,
            y: f[5] as u8,
        };
        s.explored[0].fill(0);
        s.reveal();
        let jump = if f[0] == 1 {
            Jump::Ready
        } else {
            Jump::Flying { key: f[1] }
        };
        let (p, face, state, regular) = plan(jump, s.position, 3, f[1], f[10] as u8).unwrap();
        s.position = p;
        s.facing = face;
        s.reveal();
        let flag = match state {
            Jump::Idle => 0,
            Jump::Ready => 1,
            Jump::Flying { .. } => 2,
        };
        assert_eq!(
            (p.x, p.y, face, flag),
            (f[6] as u8, f[7] as u8, f[8] as u8, f[9]),
            "{l}"
        );
        assert_eq!(regular, f[1] == 0x3920);
        assert_eq!(
            format!("{:016x}", checksum(&s.explored[0])),
            fields[11],
            "{l}"
        );
        count += 1;
    }
    assert_eq!(count, 1445);
}
#[test]
fn jumps_bypass_terrain_events_clock_and_boat_but_run_encounter_tail() {
    let c = Catalog::builtin().unwrap();
    for tile in [2, 11, 15, 46, 49, 52, 53, 60, 65] {
        let d = WorldData::jump_fixture(tile);
        let mut j = ready(&d);
        j.world.boat = 2;
        j.world.remaining = 1;
        let old = j.world.clone();
        j.cast_jump().unwrap();
        j.travel(&d, 0x4d00, &c).unwrap();
        assert_eq!(j.phase(), "jump-flight");
        j.advance_jump(&d).unwrap();
        assert_eq!(j.world.position.x, 42);
        assert_ne!(j.world.rng, old.rng);
        assert_eq!(j.world.remaining, 1);
        assert_eq!(j.world.actions, old.actions + 2);
        assert_eq!(j.world.boat, 2);
        assert!(j.month.pending.is_none());
        assert!(j.cue.is_none());
    }
    let d = WorldData::magic_fixture(5);
    let mut j = ready(&d);
    j.magic.bridges = vec![40 * 70 + 40];
    j.world.position.x = 39;
    j.cast_jump().unwrap();
    j.travel(&d, 0x4d00, &c).unwrap();
    assert!(matches!(j.travel_spell.jump, Jump::Flying { .. }));
    for _ in 0..3 {
        j.advance_jump(&d).unwrap();
    }
    assert_eq!(j.world.position.x, 43);
    assert_eq!(j.travel_spell.jump, Jump::Idle);
}
#[test]
fn no_landing_keeps_wrapping_without_inventing_an_escape_or_spending() {
    let d = WorldData::jump_fixture(15);
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    // Empty army keeps this bounded movement stress case outside battle prompts.
    j.army = [crate::battle::Stack::default(); 6];
    let old = j.world.clone();
    j.cast_jump().unwrap();
    j.travel(&d, 0x4900, &c).unwrap();
    for _ in 1..560 {
        j.advance_jump(&d).unwrap();
    }
    assert_eq!(j.world.position, old.position);
    assert_eq!(j.world.remaining, old.remaining);
    assert_ne!(j.world.rng, old.rng);
    assert_eq!(j.world.actions, old.actions + 560);
    assert!(matches!(j.travel_spell.jump, Jump::Flying { key: 0x4900 }));
    assert_eq!(j.magic.charges[3], 1);
    assert_eq!(
        j.world.explored[0]
            .iter()
            .map(|n| n.count_ones())
            .sum::<u32>(),
        2800
    );
}
#[test]
fn space_preserves_ready_and_uses_existing_event_tail_recast_spends_once() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    j.cast_jump().unwrap();
    let old = j.world.clone();
    j.travel(&d, 0x3920, &c).unwrap();
    assert_eq!(j.travel_spell.jump, Jump::Ready);
    assert_eq!(j.world.remaining, old.remaining);
    assert_eq!(j.world.position, old.position);
    assert_eq!(j.world.actions, old.actions + 1);
    assert_ne!(j.world.rng, old.rng);
    j.cast_jump().unwrap();
    assert_eq!(j.magic.charges[3], 0);
    let before = j.clone();
    assert!(j.cast_jump().is_err());
    assert_eq!(j, before);
    j.travel(&d, 0x4d00, &c).unwrap();
    assert_eq!(j.travel_spell.jump, Jump::Idle);
    assert_eq!(j.world.remaining, old.remaining);
}
#[test]
fn cold_flying_preserves_key_and_rejects_malformed_phases_and_reads_v9() {
    let d = WorldData::jump_fixture(15);
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    j.magic.charges[3] = 0;
    let mut raw = j.encode(&c, &d).unwrap();
    raw.truncate(raw.len() - 11);
    raw[..8].copy_from_slice(b"8SJRN009");
    raw.extend(checksum(&raw).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &raw).unwrap(), j);
    j.magic.charges[3] = 1;
    j.cast_jump().unwrap();
    let mut cold = Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap();
    cold.travel(&d, 0x4800, &c).unwrap();
    let mut j = Journey::decode(&c, &d, &cold.encode(&c, &d).unwrap()).unwrap();
    let old = j.clone();
    assert!(j.cast_water().is_err());
    assert!(j.dismiss(0).is_err());
    assert!(j.travel(&d, 0x4d00, &c).is_err());
    assert!(j.begin_teleport().is_err());
    assert_eq!(j, old);
    j.advance_jump(&d).unwrap();
    assert_eq!(j.world.position, Position { x: 40, y: 38 });
    assert_eq!(j.magic.charges[3], 0);
    for n in 0..6 {
        let mut b = j.clone();
        match n {
            0 => b.magic.book = false,
            1 => b.magic.direction = true,
            2 => b.survey.bird = true,
            3 => b.world.facing = 2,
            4 => b.travel_spell.jump = Jump::Flying { key: 0x3920 },
            _ => b.travel_spell.teleport = Some(0),
        };
        assert!(b.encode(&c, &d).is_err(), "{n}");
    }
    let mut raw = j.encode(&c, &d).unwrap();
    let at = raw.len() - 11;
    raw[at] = 3;
    let n = raw.len() - 8;
    let h = checksum(&raw[..n]);
    raw[n..].copy_from_slice(&h.to_le_bytes());
    assert!(Journey::decode(&c, &d, &raw).is_err());
}
#[test]
fn full_chest_is_crossed_but_empty_chest_is_a_landing_without_rewards() {
    let d = WorldData::treasure_fixture();
    let c = Catalog::builtin().unwrap();
    let site = crate::treasure::sites()[0];
    for empty in [false, true] {
        let mut j = ready(&d);
        j.world.area = site.area;
        j.world.position = Position {
            x: site.x - 1,
            y: site.y,
        };
        if empty {
            j.treasure.amounts[0] = 0;
        }
        let money = j.resources;
        j.cast_jump().unwrap();
        j.travel(&d, 0x4d00, &c).unwrap();
        assert_eq!(
            j.world.position,
            Position {
                x: site.x,
                y: site.y
            }
        );
        assert_eq!(j.travel_spell.jump == Jump::Idle, empty);
        assert_eq!(j.resources, money);
        assert!(j.treasure.pending.is_none());
        if !empty {
            j.advance_jump(&d).unwrap();
            assert_eq!(j.travel_spell.jump, Jump::Idle);
        }
        j.encode(&c, &d).unwrap();
    }
}
#[cfg(feature = "desktop")]
#[test]
fn original_f4_and_flying_ui_ignore_gameplay_inputs_until_landing() {
    use crate::management_ui::{Manager, Page};
    let d = WorldData::jump_fixture(15);
    let c = Catalog::builtin().unwrap();
    let mut j = ready(&d);
    let mut ui = Manager::default();
    ui.key(1073741885, &mut j, &c, &d);
    ui.selected = 3;
    ui.key(13, &mut j, &c, &d);
    assert_eq!(j.travel_spell.jump, Jump::Ready);
    j.travel(&d, 0x4b00, &c).unwrap();
    ui.sync(&j);
    assert_eq!(ui.page, Page::Flight);
    let before = j.clone();
    for k in [13, 27, 32, 1073741903, 1073741885] {
        ui.key(k, &mut j, &c, &d);
        assert_eq!(j, before);
    }
    assert_eq!(ui.page, Page::Flight);
    j.travel_spell.jump = Jump::Idle;
    ui.sync(&j);
    assert_eq!(ui.page, Page::World);
    assert_eq!(j.phase(), "world");
}
