use super::*;
#[test]
fn inherited_go_victory_retreat_and_promotion_receipts_match_resources_and_rule_rng() {
    let c = Catalog::builtin().unwrap();
    let mut count = 0;
    for l in include_str!("../settlement-reference.tsv")
        .lines()
        .filter(|l| !l.starts_with('#'))
    {
        let f: Vec<_> = l.split('\t').collect();
        let six = |s: &str| {
            s.split(',')
                .map(|n| n.parse::<u64>().unwrap())
                .collect::<Vec<_>>()
                .try_into()
                .unwrap()
        };
        let mut enemy = [Stack::default(); 6];
        for (i, s) in f[2].split(',').enumerate() {
            let (id, n) = s.split_once('=').unwrap();
            enemy[i] = Stack {
                unit: if id.is_empty() {
                    None
                } else {
                    Some(UnitId::parse(id).unwrap())
                },
                count: n.parse().unwrap(),
            };
        }
        let mut r = OriginalRng {
            seed: f[3].parse().unwrap(),
        };
        let result = settle_resources(
            &c,
            six(f[1]),
            enemy,
            if f[0] == "win" {
                Outcome::Win
            } else {
                Outcome::Retreat
            },
            &mut r,
        )
        .unwrap();
        assert_eq!(result, six(f[4]));
        assert_eq!(r.seed, f[5].parse::<u32>().unwrap());
        count += 1;
    }
    assert_eq!(count, 3);
}
#[test]
fn original_generator_320_cases_including_post_seed_and_discarded_duplicate_counts() {
    let mut count = 0;
    for line in include_str!("../generator-reference.tsv")
        .lines()
        .filter(|l| !l.starts_with('#'))
    {
        let f: Vec<_> = line.split('\t').collect();
        let n = |i: usize| f[i].parse::<u32>().unwrap();
        let mut r = OriginalRng { seed: n(3) };
        let army = generate(n(1) as u8, n(2) as u8, &mut r).unwrap();
        assert_eq!(r.seed, n(4), "{line}");
        for (i, s) in army.iter().enumerate() {
            assert_eq!(
                (
                    u32::from(s.unit.and_then(UnitId::native_kind).unwrap_or(0)),
                    s.count
                ),
                (n(5 + i * 2), n(6 + i * 2)),
                "{line}"
            );
        }
        count += 1;
    }
    assert_eq!(count, 320);
    let mut r = OriginalRng { seed: 2 };
    let a = generate(0, 1, &mut r).unwrap();
    assert_eq!(a[0].count, 20);
    assert_eq!(a.iter().filter(|s| s.count > 0).count(), 1);
    let old = r;
    assert!(generate(8, 1, &mut r).is_err());
    assert_eq!(r, old);
}
fn prompt<'a>(data: &WorldData) -> Journey<'a> {
    let mut j = Journey::new(data, 1);
    j.cue = Some(0);
    j
}
#[test]
fn refusal_has_one_roll_and_pursuit_starts_the_enemy_half_turn() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let mut j = prompt(&d);
    let seed = j.world.rng;
    let mut expected = seed;
    expected.next15();
    j.choose(&c, false).unwrap();
    assert_eq!(j.world.rng, expected);
    assert_eq!(j.phase(), "world");
    assert_eq!(j.resources, INITIAL);
    // Explicit inverse-LCG seed for next rand=9000 gives pursuit quotient one.
    let mut j = prompt(&d);
    j.world.rng.seed = 0xf5b8f641;
    let mut r = j.world.rng;
    assert_eq!(r.next15(), 9000);
    j.choose(&c, false).unwrap();
    assert!(j.enemy_first);
    assert_eq!(
        j.battle
            .as_mut()
            .unwrap()
            .controller
            .next_actor()
            .unwrap()
            .unwrap()
            .side,
        Side::Enemy
    );
}
#[test]
fn retreat_and_cold_battle_checkpoint_return_once_with_same_army_resources_and_seed() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let mut j = prompt(&d);
    j.choose(&c, true).unwrap();
    j.battle.as_mut().unwrap().controller.next_actor().unwrap();
    let raw = j.encode(&c, &d).unwrap();
    let mut cold = Journey::decode(&c, &d, &raw).unwrap();
    assert_eq!(cold, j);
    let mut r = j.battle.as_ref().unwrap().rng;
    let expected = 500 - 500 / (u64::from(r.next15()) / 2730 + 3);
    for s in [&mut j, &mut cold] {
        s.battle.as_mut().unwrap().controller.retreat().unwrap();
        s.finish(&c, &d, None).unwrap();
        assert_eq!(s.resources[3], expected);
        assert_eq!(s.world.rng, r);
        assert_eq!(s.army[0].count, 30);
        assert!(s.finish(&c, &d, None).is_err());
    }
    assert_eq!(j, cold);
    assert_eq!(
        Journey::decode(&c, &d, &j.encode(&c, &d).unwrap()).unwrap(),
        j
    );
}
#[test]
fn victory_and_annihilation_flow_through_the_real_controller_and_world_rules() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let mut win = prompt(&d);
    win.army[0] = Stack {
        unit: Some(UnitId::parse("openkb:wolf").unwrap()),
        count: 1000,
    };
    win.resources[1] = 2000;
    win.choose(&c, true).unwrap();
    let initial = win.enemy;
    let mut expected_gold = 500;
    let mut weight = 0;
    for s in initial {
        if let Some(id) = s.unit {
            expected_gold += c.get(id).gold * u64::from(s.count);
            weight += c.get(id).command * u64::from(s.count);
        }
    }
    for _ in 0..500 {
        let cp = win.battle.as_mut().unwrap();
        if cp.controller.battle().outcome().is_some() {
            break;
        }
        if let Some(a) = cp.controller.next_actor().unwrap() {
            if cp.controller.is_enemy_caster() {
                cp.controller.enemy_cast(&mut cp.rng).unwrap();
            } else {
                let target = if a.side == Side::Enemy {
                    cp.controller.enemy_target(&mut cp.rng).unwrap()
                } else {
                    cp.controller.legal_targets().unwrap()[0]
                };
                cp.controller.attack(target).unwrap();
            }
        }
    }
    assert_eq!(win.finish(&c, &d, None).unwrap(), Outcome::Win);
    assert_eq!(
        win.resources,
        [2, 2000 + weight / 2, 200, expected_gold, 200, 6]
    );
    assert_eq!(win.world.rank, 2);
    let mut loss = prompt(&d);
    loss.army[0].count = 1;
    loss.choose(&c, true).unwrap();
    for _ in 0..100 {
        let cp = loss.battle.as_mut().unwrap();
        if cp.controller.battle().outcome().is_some() {
            break;
        }
        if let Some(a) = cp.controller.next_actor().unwrap() {
            if a.side == Side::Player {
                cp.controller.skip().unwrap();
            } else if cp.controller.is_enemy_caster() {
                cp.controller.enemy_cast(&mut cp.rng).unwrap();
            } else {
                let t = cp.controller.enemy_target(&mut cp.rng).unwrap();
                cp.controller.attack(t).unwrap();
            }
        }
    }
    assert_eq!(
        loss.battle.as_ref().unwrap().controller.battle().outcome(),
        Some(Outcome::Loss)
    );
    assert!(loss.finish(&c, &d, None).is_err());
    let mut roam = loss.clone();
    loss.world.position = crate::world::Position { x: 9, y: 9 };
    roam.world.position = loss.world.position;
    loss.finish(&c, &d, Some(true)).unwrap();
    roam.finish(&c, &d, Some(false)).unwrap();
    assert_eq!(loss.world.position, d.starts[0]);
    assert_eq!(roam.world.position, crate::world::Position { x: 9, y: 9 });
    assert_eq!(loss.army, [Stack::default(); 6]);
    assert_eq!(roam.resources, INITIAL);
}
#[test]
fn journey_slot_rejects_corruption_bad_bindings_and_keeps_older_files() {
    let c = Catalog::builtin().unwrap();
    let d = WorldData::flat_fixture();
    let mut j = prompt(&d);
    j.choose(&c, true).unwrap();
    let raw = j.encode(&c, &d).unwrap();
    for n in [0, 7, 100, raw.len() - 1] {
        assert!(Journey::decode(&c, &d, &raw[..n]).is_err());
    }
    for at in [0, 8, 16, 5664, 5720] {
        let mut b = raw.clone();
        b[at] = 255;
        let end = b.len() - 8;
        let h = checksum(&b[..end]);
        b[end..].copy_from_slice(&h.to_le_bytes());
        assert!(Journey::decode(&c, &d, &b).is_err(), "{at}");
    }
    j.enemy[0].count += 1;
    assert!(j.encode(&c, &d).is_err());
    j.enemy[0].count -= 1;
    let dir = std::env::temp_dir().join(format!("8sword-journey-{}", std::process::id()));
    std::fs::create_dir(&dir).unwrap();
    std::fs::write(dir.join("battle.chk"), b"older battle").unwrap();
    j.save(&dir, &c, &d).unwrap();
    assert_eq!(Journey::load(&dir, &c, &d).unwrap(), j);
    assert_eq!(
        std::fs::read(dir.join("battle.chk")).unwrap(),
        b"older battle"
    );
    std::fs::write(dir.join("journey.chk"), b"broken").unwrap();
    assert!(j.save(&dir, &c, &d).is_err());
    std::fs::remove_dir_all(dir).unwrap();
}
