fn main() {
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 2 || args[1] != "--self-check" {
        eprintln!("用法：8sword-remake --self-check。此程式目前只驗證 Rust 原生戰鬥核心。");
        std::process::exit(2);
    }
    match eightsword_remake::check_reference(include_str!("../reference.tsv")) {
        Ok(count) => println!("Rust 原生戰鬥核心：{count} 組 Go 參考向量通過，執行期不需 DOS EXE。"),
        Err(err) => { eprintln!("{err}"); std::process::exit(1); }
    }
}
