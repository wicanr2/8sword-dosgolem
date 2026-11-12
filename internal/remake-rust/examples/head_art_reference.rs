//! 057: regenerate only HD story hashes; reject changes to every other sample.
use eightsword_remake::{intro::Pack, media_assets::checksum};
fn main() -> Result<(), String> {
    let args: Vec<_> = std::env::args().collect();
    let pack = Pack::load(std::path::Path::new(args.get(1).ok_or("缺素材")?))?;
    let mut changed = 0;
    for line in include_str!("../intro-reference.tsv").lines() {
        if line.starts_with('#') {
            println!("{line}");
            continue;
        }
        let mut v: Vec<String> = line.split('\t').map(str::to_owned).collect();
        let index: usize = v[0].parse().map_err(|_| "索引錯誤")?;
        for mode in 0usize..4 {
            let pixels = pack.render(index, mode != 0, mode.saturating_sub(1))?;
            let hash = format!("{:016x}", checksum(&pixels));
            if hash != v[3 + mode] {
                if mode == 0 || !v[2].starts_with("story-") {
                    return Err(format!("非目標畫面改變：{} mode{mode}", v[2]));
                }
                changed += 1;
                v[3 + mode] = hash;
            }
        }
        println!("{}", v.join("\t"));
    }
    eprintln!("changed_hd_story_samples={changed}; all_other_samples_unchanged");
    Ok(())
}
