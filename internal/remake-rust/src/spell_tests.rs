use crate::battle::{Modifiers, Outcome, Side, Stack};
use crate::catalog::{Catalog, UnitId};
use crate::controller::{Controller, OriginalRng};
use crate::spells::{Spell, SpellBook};
fn row(id: &str, n: u32) -> Stack {
    Stack {
        unit: Some(UnitId::parse(id).unwrap()),
        count: n,
    }
}
fn setup(c: &Catalog, kind: u8) -> Controller<'_> {
    let mut rows = [[Stack::default(); 6]; 2];
    rows[0][0] = row("native:01", 30);
    rows[0][1] = row(&format!("native:{kind:02}"), 2);
    rows[1][0] = row("native:06", 11);
    rows[1][1] = row("native:16", 35);
    rows[1][2] = row("native:11", 29);
    let mut ctl = Controller::with_spells(
        c,
        rows,
        Side::Player,
        Modifiers::default(),
        SpellBook {
            enabled: true,
            charges: [3; 8],
            stat_26b0: 2,
            stat_26ae: 4,
        },
    )
    .unwrap();
    ctl.next_actor().unwrap();
    ctl.attack(0).unwrap();
    let actor = ctl.next_actor().unwrap().unwrap();
    assert_eq!(actor.slot, 5);
    ctl
}
#[test]
fn all_eight_spells_preserve_pending_hp_and_ordinary_sequence() {
    let catalog = Catalog::builtin().unwrap();
    for spell in Spell::ALL {
        let mut c = setup(&catalog, 12);
        let hp = *c.battle().hp();
        let seq = c.battle().sequence();
        let mut rng = OriginalRng { seed: 123 };
        if c.select_spell(spell).unwrap().is_none() {
            c.target_spell(if spell == Spell::Clone { 0 } else { 1 }, &mut rng)
                .unwrap();
        }
        assert_eq!(c.battle().hp(), &hp);
        assert_eq!(c.battle().sequence(), seq);
        assert_eq!(c.spell_book().unwrap().charges[spell.index()], 2);
        assert_eq!(c.spell_returns(), 1);
    }
}
#[test]
fn target_wait_invalid_input_and_space_refund_are_atomic() {
    let catalog = Catalog::builtin().unwrap();
    let mut c = setup(&catalog, 12);
    c.select_spell(Spell::Fireball).unwrap();
    let before = c.clone();
    let mut rng = OriginalRng { seed: 77 };
    let seed = rng.seed;
    assert!(c.target_spell(6, &mut rng).is_err());
    assert_eq!(c, before);
    assert_eq!(rng.seed, seed);
    assert!(c.select_spell(Spell::Fireball).is_err());
    assert_eq!(c, before);
    assert_eq!(c.next_actor().unwrap(), before.current());
    assert_eq!(c, before);
    c.cancel_spell_target(false).unwrap();
    assert_eq!(c.spell_book().unwrap().charges, [3; 8]);
    let mut c = setup(&catalog, 12);
    c.select_spell(Spell::Fireball).unwrap();
    c.cancel_spell_target(true).unwrap();
    assert_eq!(c.battle().outcome(), Some(Outcome::Retreat));
    assert_eq!(c.spell_book().unwrap().charges[0], 2);
}
#[test]
fn freeze_keeps_duplicate_empty_rows_and_returns_extra_actions() {
    let catalog = Catalog::builtin().unwrap();
    let mut c = setup(&catalog, 12);
    assert_eq!(c.remaining()[0], [0, 0, 1, 1, 1, 1]);
    c.select_spell(Spell::Freeze).unwrap();
    assert_eq!(c.remaining()[0], [1, 1, 1, 1, 1, 5]);
    assert_eq!(c.next_actor().unwrap().unwrap().raw, 0);
    c.skip().unwrap();
    assert_eq!(c.next_actor().unwrap().unwrap().raw, 1);
    assert!(c.is_caster());
}
#[test]
fn caster_without_charges_moves_to_front_when_alone() {
    let catalog = Catalog::builtin().unwrap();
    let mut rows = [[Stack::default(); 6]; 2];
    rows[0][0] = row("native:10", 30);
    rows[1][0] = row("native:01", 1);
    let mut c = Controller::with_spells(
        &catalog,
        rows,
        Side::Enemy,
        Modifiers::default(),
        SpellBook {
            enabled: true,
            charges: [0; 8],
            stat_26b0: 2,
            stat_26ae: 4,
        },
    )
    .unwrap();
    let mut rng = OriginalRng { seed: 42 };
    c.next_actor().unwrap();
    let t = c.enemy_target(&mut rng).unwrap();
    c.attack(t).unwrap();
    let actor = c.next_actor().unwrap().unwrap();
    assert_eq!(actor.side, Side::Player);
    assert!(actor.slot < 3);
    assert!(!c.is_caster());
    c.attack(0).unwrap();
}

#[test]
fn verified_spell_models_and_original_interface_receipts() {
    let catalog = Catalog::builtin().unwrap();
    let result = crate::replay::check_spells(&catalog, include_str!("../spell-reference.tsv"));
    assert!(result.is_ok(), "{result:?}");
    assert_eq!(result.unwrap().1, 15);
}
