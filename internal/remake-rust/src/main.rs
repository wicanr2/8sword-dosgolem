fn main() {
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 2 || args[1] != "--self-check" {
        eprintln!("用法：8sword-remake --self-check。此程式目前驗證 Rust 原生戰鬥核心。");
        std::process::exit(2);
    }
    if let Err(err) = verify() {
        eprintln!("{err}");
        std::process::exit(1);
    }
}

fn verify() -> Result<(), String> {
    let catalog = eightsword_remake::catalog::Catalog::builtin()?;
    let arithmetic = eightsword_remake::check_reference(include_str!("../reference.tsv"))?;
    let models =
        eightsword_remake::replay::check_models(&catalog, include_str!("../battle-models.tsv"))?;
    let battles =
        eightsword_remake::replay::check_battles(&catalog, include_str!("../battle-replay.tsv"))?;
    println!(
        "Rust 原生核心：{}種兵種、{arithmetic}組算式、{}組陣位／補位／換位通過。",
        catalog.profiles().len(),
        models.setup + models.sort + models.motion
    );
    println!(
        "{}場戰鬥的{}個普通行動通過；勝利{}、全滅{}、撤退{}。執行期不需DOS EXE。",
        battles.battles, battles.actions, battles.wins, battles.losses, battles.retreats
    );
    println!("目前按既有記錄的選隊順序重播，原生回合控制、操作介面與存檔待接。");
    Ok(())
}
