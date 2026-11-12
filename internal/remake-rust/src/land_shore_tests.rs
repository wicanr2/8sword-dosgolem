use crate::{
    catalog::Catalog,
    journey::Journey,
    world::{self, Position, WorldData},
};
fn site(tile: u8) -> (u8, Position) {
    match tile {
        49 | 50 => {
            let s = crate::world_exits::exits()
                .iter()
                .find(|s| s.tile == tile)
                .unwrap();
            (s.area, s.position)
        }
        51 => {
            let s = crate::map_notice::sites()[0];
            (s.area, s.position)
        }
        53 => {
            let s = crate::world_magic::shops()[0];
            (s.area, Position { x: s.x, y: s.y })
        }
        54..=58 => {
            let (_, s) = crate::management::camps()
                .iter()
                .enumerate()
                .find(|(i, s)| i / 24 == usize::from(tile - 54) && s.kind > 0)
                .unwrap();
            (s.area, Position { x: s.x, y: s.y })
        }
        59 => {
            let s = crate::treasure::sites()[0];
            (s.area, Position { x: s.x, y: s.y })
        }
        65 => {
            let s = crate::guards::sites()[0];
            (s.area, s.position)
        }
        _ => panic!("tile"),
    }
}
#[test]
fn space_on_special_sites_stays_an_atomic_boundary() {
    let d = WorldData::land_shore_fixture();
    let c = Catalog::builtin().unwrap();
    for tile in [49, 50, 51, 53, 54, 55, 56, 57, 58, 59, 65] {
        let (area, position) = site(tile);
        let mut j = Journey::new(&d, 1);
        j.world.area = area;
        j.world.position = position;
        j.world.boat = 2;
        let before = j.clone();
        assert_eq!(
            j.travel(&d, 0x3920, &c).unwrap(),
            Some(world::Boundary::BoatExit)
        );
        assert_eq!(j, before);
        assert!(j.encode(&c, &d).is_ok());
    }
}
fn cold<'a>(j: &Journey<'a>, c: &'a Catalog, d: &WorldData) -> Journey<'a> {
    let s = Journey::decode(c, d, &j.encode(c, d).unwrap()).unwrap();
    assert_eq!(&s, j);
    s
}
#[test]
fn all_352_original_post_choice_vectors_continue_from_land_and_cold_each_modal() {
    let d = WorldData::land_shore_fixture();
    let c = Catalog::builtin().unwrap();
    let mut count = 0;
    for line in include_str!("../land-shore-reference.tsv")
        .lines()
        .filter(|s| s.starts_with("FLOW\t"))
    {
        let f: Vec<u16> = line
            .split('\t')
            .skip(1)
            .map(|v| v.parse().unwrap())
            .collect();
        let tile = f[0] as u8;
        let yes = f[1] == 1;
        let key = f[2];
        let remaining = f[3];
        let (area, target) = site(tile);
        let from = world::motion(target, key, 3, true).unwrap().0;
        let mut j = Journey::new(&d, 1);
        j.world.area = area;
        j.world.position = from;
        j.world.boat = 2;
        j.world.remaining = remaining;
        j.magic.book = true;
        j.resources[5] = 3;
        assert!(!matches!(d.tile(area, from).unwrap(), 2 | 11..=14));
        assert_eq!(j.travel(&d, key, &c).unwrap(), None);
        if tile == 51 {
            assert_eq!(j.phase(), "map-notice");
            j = cold(&j, &c, &d);
            j.close_map_notice(&d, &c).unwrap();
        }
        assert_eq!(j.phase(), "shore");
        assert_eq!(j.world.position, from);
        assert_eq!(j.world.remaining, remaining);
        j.select_shore(yes).unwrap();
        j = cold(&j, &c, &d);
        j.finish_shore(&d, &c).unwrap();
        assert_eq!(j.world.boat, f[6] as u8);
        // Deferred native modals commit the source step only when closed.
        for _ in 0..5 {
            j = cold(&j, &c, &d);
            match j.phase() {
                "magic-shop" => {
                    if !yes {
                        assert_eq!(j.magic_offer().unwrap(), 0);
                    }
                    j.close_magic_shop(&c, &d).unwrap();
                }
                "camp" => {
                    j.close_camp(&d, &c).unwrap();
                }
                "treasure" => {
                    j.finish_treasure(&c, &d, false).unwrap();
                }
                "guard" => {
                    j.close_guard(&d, &c).unwrap();
                }
                _ => break,
            }
        }
        if f[9] == 0 {
            assert_eq!(j.phase(), "monthly");
            j = cold(&j, &c, &d);
            j.close_month(&d).unwrap();
            assert_eq!(j.world.remaining, 324);
        } else {
            assert_eq!(j.world.remaining, f[9]);
        }
        assert_eq!(j.world.boat, f[6] as u8);
        assert!(j.encode(&c, &d).is_ok());
        count += 1;
    }
    assert_eq!(count, 352);
}
#[test]
fn refused_shop_on_land_keeps_original_fallback_and_buy_once_after_cold() {
    let d = WorldData::land_shore_fixture();
    let c = Catalog::builtin().unwrap();
    let s = crate::world_magic::shops()[1];
    assert_eq!(s.offer, 8);
    let mut j = Journey::new(&d, 1);
    j.world.area = s.area;
    j.world.position = Position { x: s.x, y: s.y - 1 };
    j.world.boat = 2;
    j.magic.book = true;
    j.resources[5] = 3;
    j.travel(&d, 0x5000, &c).unwrap();
    j.select_shore(false).unwrap();
    j.finish_shore(&d, &c).unwrap();
    assert_eq!(j.magic_offer().unwrap(), 0);
    j = cold(&j, &c, &d);
    j.buy_world_spell().unwrap();
    assert_eq!(
        (
            j.resources[3],
            j.magic.charges[0],
            j.magic.battle_charges[0]
        ),
        (490, 1, 0)
    );
    j.close_magic_shop(&c, &d).unwrap();
    assert_eq!((j.world.boat, j.world.remaining), (2, 324));
    cold(&j, &c, &d);
}
#[test]
fn declining_original_exit_can_reach_nonwater_boat2_then_next_site_transaction() {
    let d = WorldData::land_shore_fixture();
    let c = Catalog::builtin().unwrap();
    let e = crate::world_exits::exits()
        .iter()
        .find(|e| e.tile == 49)
        .unwrap();
    let mut j = Journey::new(&d, 1);
    j.world.area = e.area;
    j.world.position = world::motion(e.position, 0x4800, 3, true).unwrap().0;
    j.world.boat = 2;
    j.travel(&d, 0x4800, &c).unwrap();
    j.select_shore(false).unwrap();
    j.finish_shore(&d, &c).unwrap();
    assert_eq!(j.world.boat, 2);
    assert!(!matches!(
        d.tile(j.world.area, j.world.position).unwrap(),
        2 | 11..=14
    ));
    cold(&j, &c, &d);
}
