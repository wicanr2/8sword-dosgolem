use super::*;
use crate::{
    battle::Stack,
    catalog::{Catalog, UnitId},
    controller::OriginalRng,
    world::{Position, WorldData},
};
fn grant(j: &mut Journey<'_>, i: usize) {
    match i {
        0 => j.magic.book = true,
        5 => j.world.bamboo = true,
        6 => j.world.mountain = true,
        _ => j.artifacts |= 1 << i,
    }
}
#[test]
fn original_32_searches_preserve_position_clock_resources_and_one_rng_call() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut count = 0;
    for line in include_str!("../items-reference.tsv")
        .lines()
        .filter(|l| !l.starts_with('#'))
    {
        let v: Vec<u32> = line
            .split_whitespace()
            .map(|s| s.parse().unwrap())
            .collect();
        let item = crate::world_magic::items()[v[0] as usize];
        let mut j = Journey::new(&d, 0x12345678);
        j.world.area = item[1];
        j.world.position = Position {
            x: item[2],
            y: item[3],
        };
        j.resources[5] = 9;
        match v[1] {
            1 => j.world.position.x += 1,
            2 => j.world.area = (j.world.area + 1) % 8,
            3 => grant(&mut j, v[0] as usize),
            _ => {}
        }
        let old = j.clone();
        assert_eq!(j.search_item().unwrap(), (v[2] == 1).then_some(v[0] as u8));
        assert_eq!(j.world.rng.seed, v[4]);
        assert_eq!(j.resources[5], u64::from(v[3]));
        assert_eq!(j.world.position, old.world.position);
        assert_eq!(j.world.remaining, old.world.remaining);
        assert_eq!(j.world.actions, old.world.actions);
        assert_eq!(j.army, old.army);
        assert_eq!(j.resources[..5], old.resources[..5]);
        for i in 0..8 {
            assert_eq!(
                j.has_item(i),
                old.has_item(i) || (v[2] == 1 && i == v[0] as usize)
            );
        }
        assert_eq!(
            Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap(),
            j
        );
        count += 1;
    }
    assert_eq!(count, 32);
}
#[test]
fn original_192_token_quotients_keep_post_division_shift_and_safe_domain() {
    let mut count = 0;
    for l in include_str!("../recruit-token-reference.tsv")
        .lines()
        .filter(|l| !l.starts_with('#'))
    {
        let v: Vec<i64> = l.split_whitespace().map(|s| s.parse().unwrap()).collect();
        let got = recruit_ceiling(v[0] as u64, v[1] as u64, v[2] as u64, v[3] == 1);
        if v[1] > v[0] {
            assert!(got.is_err());
        } else {
            assert_eq!(got.unwrap(), v[4].max(0) as u64, "{l}");
        }
        count += 1;
    }
    assert_eq!(count, 192);
    assert_eq!(recruit_ceiling(100, 30, 3, true).unwrap(), 46);
    assert_eq!(recruit_ceiling(30000, 0, 1, true).unwrap(), 0); // Original signed word wrap.
    assert!(recruit_ceiling(100, 0, 0, true).is_err());
}
#[test]
fn all_items_cold_resume_bind_battle_modifiers_and_both_entry_paths() {
    let d = WorldData::guards_fixture(false);
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 1);
    for i in 0..8 {
        grant(&mut j, i);
    }
    j.resources[5] = 3;
    assert_eq!(
        j.item_modifiers(),
        Modifiers {
            player_attack: 1,
            player_boost: 1,
            enemy_defense: 1
        }
    );
    j.army[1] = Stack {
        unit: Some(UnitId::parse("native:12").unwrap()),
        count: 1,
    };
    let mut random = j.clone();
    random.cue = Some(1);
    random.choose(&c, true).unwrap();
    let cp = random.battle.as_ref().unwrap();
    assert_eq!(cp.controller.modifiers(), j.item_modifiers());
    assert_eq!(cp.controller.spell_book().unwrap().stat_26b0, 1);
    assert_eq!(cp.controller.spell_book().unwrap().stat_26ae, 1);
    assert_eq!(cp.controller.enemy_config().unwrap().stat_26ae, 1);
    assert_eq!(
        Journey::decode(&c, &d, &random.encode(&c, &d).unwrap()).unwrap(),
        random
    );
    let site = crate::guards::sites()[0];
    j.world.area = site.area;
    j.world.position = Position {
        x: site.position.x,
        y: site.position.y + 1,
    };
    j.travel(&d, 0x4800, &c).unwrap();
    j.choose_guard(&d, &c, true).unwrap();
    assert_eq!(
        j.battle.as_ref().unwrap().controller.modifiers(),
        j.item_modifiers()
    );
    assert_eq!(
        Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap(),
        j
    );
    let old = j.clone();
    assert!(j.search_item().is_err());
    assert_eq!(j, old);
    j.artifacts ^= 1 << 4;
    assert!(j.encode(&c, &d).is_err());
}
#[test]
fn original_item_bonuses_reach_resource_spells_recruitment_and_base_leadership() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 1);
    j.magic.book = true;
    j.resources[5] = 3;
    j.magic.charges = [0, 1, 1, 0, 0, 0, 0, 0];
    grant(&mut j, 2);
    grant(&mut j, 3);
    grant(&mut j, 7);
    let mut rng = OriginalRng { seed: 1 };
    let expected = crate::resource_spells::alchemy_amount(rng.next15(), true).unwrap();
    j.cast_resource(&c, 1).unwrap();
    assert_eq!(
        j.resource_notice
            .as_ref()
            .unwrap()
            .effect(&j, &c)
            .unwrap()
            .amount,
        expected
    );
    j.close_resource_notice(&c).unwrap();
    j.resources[4] = 1000;
    j.cast_resource(&c, 2).unwrap();
    assert_eq!(
        j.resource_notice
            .as_ref()
            .unwrap()
            .effect(&j, &c)
            .unwrap()
            .count,
        30
    );
    j.close_resource_notice(&c).unwrap();
    assert_eq!(j.resources[4], 1000);
    assert_eq!(j.displayed_leadership(), 2000);
    j.camps.pending = Some(1);
    j.resources[3] = 10000;
    let without = {
        let mut s = j.clone();
        s.artifacts &= !(1 << 7);
        s.maximum(&c, None).unwrap()
    };
    assert_eq!(j.maximum(&c, None).unwrap(), without * 2);
}
#[test]
fn v15_migration_unknown_flags_and_changed_data_are_checked() {
    let d = WorldData::flat_fixture();
    let c = Catalog::builtin().unwrap();
    let mut j = Journey::new(&d, 1);
    j.magic.book = true;
    j.resources[5] = 3;
    j.world.mountain = true;
    let mut old = j.encode(&c, &d).unwrap();
    old.truncate(old.len() - crate::space_events::SUFFIX - 16 - 8 - SUFFIX);
    old[..8].copy_from_slice(b"8SJRN015");
    old.extend(checksum(&old).to_le_bytes());
    assert_eq!(Journey::decode(&c, &d, &old).unwrap(), j);
    j.artifacts = MASK;
    let raw = j.encode(&c, &d).unwrap();
    assert_eq!(&raw[..8], b"8SJRN018");
    for offset in [9, 10] {
        let mut bad = raw.clone();
        let n = bad.len();
        bad[n - crate::space_events::SUFFIX - 16 - offset] ^= if offset == 9 { 1 } else { 2 };
        let sum = checksum(&bad[..n - 8]);
        bad[n - 8..].copy_from_slice(&sum.to_le_bytes());
        assert!(Journey::decode(&c, &d, &bad).is_err());
    }
}
#[test]
fn item_names_and_two_column_text_rectangles_are_bounded() {
    let names = names();
    assert_eq!(names[7], "黃金令牌");
    for (i, n) in names.iter().enumerate() {
        assert!(n.chars().count() <= 4);
        let x = 648 + (i / 4) * 324;
        let y = 444 + (i % 4) * 156;
        assert!(x + 96 + n.chars().count() * 48 <= 1368);
        assert!(y + 96 <= 1164);
    }
}

#[test]
fn found_movement_items_survive_cold_load_and_enable_existing_terrain_rules() {
    let c = Catalog::builtin().unwrap();
    for (item, terrain) in [(5, 46), (6, 15)] {
        let d = WorldData::jump_fixture(terrain);
        let mut j = Journey::new(&d, 1);
        let site = crate::world_magic::items()[item];
        j.world.area = site[1];
        j.world.position = Position {
            x: site[2],
            y: site[3],
        };
        assert_eq!(j.search_item().unwrap(), Some(item as u8));
        let raw = j.encode(&c, &d).unwrap();
        let mut cold = Journey::decode(&c, &d, &raw).unwrap();
        assert!(cold.has_item(item));
        // An explicit terrain fixture isolates the item flag's existing consumer.
        cold.world.area = 0;
        cold.world.position = Position { x: 40, y: 40 };
        cold.world.rng.seed = 1;
        assert_eq!(cold.travel(&d, 0x4d00, &c).unwrap(), None);
        assert_eq!(cold.world.position.x, 41);
        let mut absent = Journey::new(&d, 1);
        absent.travel(&d, 0x4d00, &c).unwrap();
        assert_eq!(absent.world.position.x, 40);
    }
}
