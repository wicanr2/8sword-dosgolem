fn main() {
    let args: Vec<_> = std::env::args().collect();
    if args.get(1).is_some_and(|arg| arg == "--battle") {
        #[cfg(feature = "desktop")]
        if let Err(err) = eightsword_remake::desktop::run(&args[2..]) {
            eprintln!("{err}");
            std::process::exit(1);
        }
        #[cfg(not(feature = "desktop"))]
        {
            eprintln!("此建置未包含desktop功能");
            std::process::exit(2);
        }
        return;
    }
    if args.len() != 2 || args[1] != "--self-check" {
        eprintln!("用法：8sword-remake --self-check 或 --battle --assets <素材目錄>。");
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
    let controller = eightsword_remake::replay::check_controller(
        &catalog,
        include_str!("../controller-reference.tsv"),
    )?;
    println!(
        "Rust 原生核心：{}種兵種、{arithmetic}組算式、{}組陣位／補位／換位通過。",
        catalog.profiles().len(),
        models.setup + models.sort + models.motion
    );
    println!(
        "{}場戰鬥的{}個普通行動通過；勝利{}、全滅{}、撤退{}。執行期不需DOS EXE。",
        battles.battles, battles.actions, battles.wins, battles.losses, battles.retreats
    );
    println!(
        "原生普通回合：{}場、{}次選隊、{}次攻擊、{}次略過通過。",
        controller.battles, controller.offers, controller.actions, controller.skips
    );
    println!("--battle 啟動原生普通戰鬥樣本；世界流程、法術與存檔待接。");
    Ok(())
}
