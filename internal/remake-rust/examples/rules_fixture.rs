//! Explicit representative troops, not naturally acquired. The game performs all actions.
use eightsword_remake::{
    battle::{Modifiers, Side, Stack},
    catalog::{Catalog, UnitId},
    checkpoint_store,
    controller::{Checkpoint, Controller, OriginalRng, ViewState},
    rules::Mode,
};
use std::{fs, path::PathBuf};
fn main() -> Result<(), String> {
    let root = PathBuf::from(std::env::args().nth(1).ok_or("output directory")?);
    checkpoint_store::check_directory(&root)?;
    let c = Catalog::builtin()?;
    for mode in [Mode::Native, Mode::Formation, Mode::Tactics] {
        let dir = root.join(mode.name());
        fs::create_dir(&dir).map_err(|e| e.to_string())?;
        let mut rows = [[Stack::default(); 6]; 2];
        for (side, raw, id, count) in [
            (0, 0, "native:01", 100),
            (0, 1, "native:21", 100),
            (1, 0, "native:03", 50),
        ] {
            rows[side][raw] = Stack {
                unit: Some(UnitId::parse(id)?),
                count,
            };
        }
        let controller = Controller::new(&c, rows, Side::Player, Modifiers::default())
            .and_then(|c| c.with_rule_mode(mode))
            .map_err(|e| format!("{e:?}"))?;
        checkpoint_store::save(
            &dir,
            &Checkpoint {
                controller,
                rng: OriginalRng { seed: 1 },
                view: ViewState::default(),
            },
        )?;
    }
    println!(
        "Controlled:100 militia+100 native21 vs50 native archers;seed1;firstPlayer;no runtime injection"
    );
    Ok(())
}
