use eightsword_remake::{ending::Pack, media_assets::checksum};
fn main() -> Result<(), String> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() != 3 {
        return Err("assets output".into());
    }
    let p = Pack::load(std::path::Path::new(&a[1]))?;
    let mut log = String::new();
    let mut n = 0;
    for line in include_str!("../ending-reference.tsv")
        .lines()
        .filter(|l| !l.starts_with('#'))
    {
        let f: Vec<_> = line.split('\t').collect();
        let index = f[0].parse::<usize>().map_err(|e| e.to_string())?;
        assert_eq!(p.frame_index(f[1].parse().unwrap()), index);
        for mode in 0usize..4 {
            let pixels = p.render(index, mode != 0, mode.saturating_sub(1))?;
            let got = checksum(&pixels);
            let expected = u64::from_str_radix(f[mode + 3], 16).map_err(|e| e.to_string())?;
            if got != expected {
                std::fs::write(std::path::Path::new(&a[2]).join("failed.rgba"), pixels)
                    .map_err(|e| e.to_string())?;
                return Err(format!("{} mode{mode} {got:016x}!={expected:016x}", f[2]));
            }
            log += &format!("{}\t{index}\t{mode}\t{got:016x}\n", f[2]);
            n += 1
        }
    }
    assert_eq!(n, 36);
    std::fs::write(std::path::Path::new(&a[2]).join("ending-renders.tsv"), log)
        .map_err(|e| e.to_string())?;
    println!("36 ending renders matched / {} frames", p.frames.len());
    Ok(())
}
