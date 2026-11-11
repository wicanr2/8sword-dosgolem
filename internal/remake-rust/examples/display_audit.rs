//! Validate every image in the original group and lossless HD round trips.
use eightsword_remake::{
    display,
    media_assets::{Image, checksum},
};
use std::{fs, path::PathBuf};
fn main() -> Result<(), String> {
    let root = PathBuf::from(std::env::args().nth(1).ok_or("assets directory")?);
    assert!(display::preflight(&root)?);
    println!("# name\thd\toriginal\thd-restored");
    let mut count = 0;
    for (name, (w, h)) in display::expected() {
        let mut im = Image::load_dual(&root.join(&name), w, h)?;
        let hd = checksum(&im.pixels);
        im.select(true)?;
        let original = Image::load(&root.join("original").join(&name), w, h)?;
        assert_eq!(im.pixels, original.pixels);
        let raw = checksum(&im.pixels);
        for _ in 0..8 {
            im.select(false)?;
            assert_eq!(checksum(&im.pixels), hd);
            im.select(true)?;
            assert_eq!(checksum(&im.pixels), raw);
        }
        im.select(false)?;
        assert_eq!(checksum(&im.pixels), hd);
        println!(
            "{name}\t{hd:016x}\t{raw:016x}\t{:016x}",
            checksum(&im.pixels)
        );
        count += 1;
    }
    assert_eq!(count, 127);
    let _ = fs::metadata(root).map_err(|e| e.to_string())?;
    Ok(())
}
