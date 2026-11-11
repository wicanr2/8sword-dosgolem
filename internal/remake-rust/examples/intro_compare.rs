use eightsword_remake::{intro::Pack, media_assets::checksum};
fn main() -> Result<(), String> {
    let args: Vec<_> = std::env::args().collect();
    let pack = Pack::load(std::path::Path::new(args.get(1).ok_or("缺少素材目錄")?))?;
    let mut n = 0;
    for line in include_str!("../intro-reference.tsv")
        .lines()
        .filter(|l| !l.starts_with('#'))
    {
        let v: Vec<_> = line.split('\t').collect();
        let index: usize = v[0].parse().map_err(|_| "參考索引錯誤")?;
        if pack.frames[index].stage != v[2] || pack.frames[index].ms.to_string() != v[1] {
            return Err("開場參考節點不符".into());
        }
        for mode in 0usize..4 {
            let pixels = pack.render(index, mode != 0, mode.saturating_sub(1))?;
            let got = format!("{:016x}", checksum(&pixels));
            if got != v[3 + mode] {
                return Err(format!(
                    "{} mode{} frame{} {} != {}",
                    v[2],
                    mode,
                    index,
                    got,
                    v[3 + mode]
                ));
            }
            println!("{}\t{}\t{}\t{}", v[2], index, mode, got);
            n += 1;
        }
    }
    if n != 72 {
        return Err("開場參考場景缺漏".into());
    }
    Ok(())
}
