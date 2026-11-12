fn main() {
    let args: Vec<_> = std::env::args().collect();
    if args.len() == 2 && args[1] == "--version" {
        println!("{}", eightsword_remake::platform::VERSION);
        return;
    }
    if args.len() == 1
        || args.get(1).is_some_and(|a| {
            matches!(
                a.as_str(),
                "--play"
                    | "--assets"
                    | "--save-dir"
                    | "--capture-dir"
                    | "--scale"
                    | "--seed"
                    | "--mute"
                    | "--skip-intro"
                    | "--battle-ai"
                    | "--battle-rules"
                    | "--display"
            )
        })
    {
        #[cfg(feature = "desktop")]
        {
            let mut play = vec!["--start-menu".to_string()];
            let first = if args.get(1).is_some_and(|a| a == "--play") {
                2
            } else {
                1
            };
            play.extend_from_slice(&args[first..]);
            if let Err(e) = eightsword_remake::journey_desktop::run(&play) {
                eprintln!("{e}");
                std::process::exit(1);
            }
        }
        #[cfg(not(feature = "desktop"))]
        {
            eprintln!("此建置未包含desktop功能");
            std::process::exit(2);
        }
        return;
    }
    if args.get(1).is_some_and(|arg| arg == "--journey") {
        #[cfg(feature = "desktop")]
        if let Err(e) = eightsword_remake::journey_desktop::run(&args[2..]) {
            eprintln!("{e}");
            std::process::exit(1);
        }
        #[cfg(not(feature = "desktop"))]
        {
            eprintln!("此建置未包含desktop功能");
            std::process::exit(2);
        }
        return;
    }
    if args.get(1).is_some_and(|arg| arg == "--world-preview") {
        #[cfg(feature = "desktop")]
        if let Err(err) = eightsword_remake::world_desktop::run(&args[2..]) {
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
        eprintln!(
            "用法：8sword-remake [--play] [--assets <素材目錄>] [--save-dir <既有目錄>]；--self-check核對核心。"
        );
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
    println!("--play 啟動開始選單與原生世界；--battle 保留戰鬥樣本。");
    let (models, cases) =
        eightsword_remake::replay::check_spells(&catalog, include_str!("../spell-reference.tsv"))?;
    println!(
        "玩家八術：{models}組模型、{cases}份既有原版介面收據通過；--battle --spells啟動施法樣本。"
    );
    let (models, cases) =
        eightsword_remake::replay::check_enemy(&catalog, include_str!("../enemy-reference.tsv"))?;
    println!(
        "敵方八分派：{models}組模型、{cases}份既有原版介面收據通過；--battle --enemy-spells啟動敵術樣本。"
    );
    println!(
        "原生戰中檢查點：--save-dir <既有目錄>，F7存檔；--continue由保存的戰鬥續接。舊Go／世界進度不變。"
    );
    println!("--world-preview保留八圖預覽；--play可新建或繼續原生旅程，存檔格式v18。");
    Ok(())
}
