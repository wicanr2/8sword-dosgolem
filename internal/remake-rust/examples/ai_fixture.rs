//! Explicit deterministic development checkpoint; not naturally acquired troops.
use eightsword_remake::{
    battle::{Modifiers, Side, Stack},
    catalog::{Catalog, UnitId},
    checkpoint_store,
    controller::{Checkpoint, Controller, OriginalRng, ViewState},
};
use std::path::PathBuf;
fn main() -> Result<(), String> {
    let out = PathBuf::from(std::env::args().nth(1).ok_or("output directory")?);
    checkpoint_store::check_directory(&out)?;
    let catalog = Catalog::builtin()?;
    let mut rows = [[Stack::default(); 6]; 2];
    for (side, raw, id, count) in [
        (0, 0, "native:06", 100),
        (0, 1, "native:11", 2),
        (1, 0, "openkb:arcr", 250),
    ] {
        rows[side][raw] = Stack {
            unit: Some(UnitId::parse(id)?),
            count,
        };
    }
    let c = Controller::new(&catalog, rows, Side::Player, Modifiers::default())
        .map_err(|e| format!("{e:?}"))?;
    let state = Checkpoint {
        controller: c,
        rng: OriginalRng { seed: 1 },
        view: ViewState::default(),
    };
    checkpoint_store::save(&out, &state)?;
    println!("Explicit troops:100 native06,2 native11 vs250 openkb arcr;seed1;firstPlayer");
    Ok(())
}
