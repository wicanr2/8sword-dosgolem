//! Original sub_16058:54 travel cells;Survey owns the stop-time flag and divisor.
pub const X: usize = 48;
pub const Y: usize = 1206;
pub const WIDTH: usize = 1296;
pub const HEIGHT: usize = 18;
pub fn cells(remaining: u16, tempo: u8) -> Result<u8, String> {
    if tempo == 0 {
        return Err("行程條比率不能為零".into());
    }
    Ok(u32::from(remaining).div_ceil(u32::from(tempo)).min(54) as u8)
}
fn paint(out: &mut [u8], stride: usize, x: usize, y: usize, n: u8, stopped: bool) {
    let rows = if stopped {
        [[255, 85, 85], [255, 255, 85], [255, 85, 255]]
    } else {
        [[0, 170, 0], [255, 255, 85], [85, 255, 85]]
    };
    for row in 0..HEIGHT {
        for col in 0..WIDTH {
            let color = if col < usize::from(n) * 24 {
                rows[row / 6]
            } else {
                [0, 0, 0]
            };
            let at = ((y + row) * stride + x + col) * 4;
            out[at..at + 3].copy_from_slice(&color);
            out[at + 3] = 255;
        }
    }
}
pub fn strip(remaining: u16, tempo: u8, stopped: bool) -> Result<Vec<u8>, String> {
    let mut out = vec![0; WIDTH * HEIGHT * 4];
    paint(&mut out, WIDTH, 0, 0, cells(remaining, tempo)?, stopped);
    Ok(out)
}
#[cfg(feature = "desktop")]
pub(crate) fn draw(out: &mut [u8], remaining: u16, tempo: u8, stopped: bool) -> Result<(), String> {
    if out.len() != 1920 * 1320 * 4 {
        return Err("行程條畫布尺寸錯誤".into());
    }
    paint(out, 1920, X, Y, cells(remaining, tempo)?, stopped);
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn original_84_call_sequences_and_three_color_rows_match() {
        let mut n = 0;
        for line in include_str!("../travelbar-reference.tsv")
            .lines()
            .filter(|l| !l.starts_with('#'))
        {
            let v: Vec<_> = line.split('\t').collect();
            let r = v[0].parse().unwrap();
            let t = v[1].parse().unwrap();
            let stopped = v[2] == "1";
            let filled = cells(r, t).unwrap();
            assert_eq!(filled.to_string(), v[3]);
            assert_eq!((54 - filled).to_string(), v[4]);
            assert_eq!(&v[5..8], &["2", "55", "193"]);
            assert_eq!(
                format!(
                    "{:016x}",
                    crate::media_assets::checksum(&strip(r, t, stopped).unwrap())
                ),
                v[8]
            );
            n += 1;
        }
        assert_eq!(n, 84);
    }
    #[test]
    fn shortening_clears_tail_and_oversized_state_cannot_escape_bar() {
        assert_eq!(cells(u16::MAX, 6).unwrap(), 54);
        assert!(cells(1, 0).is_err());
        let full = strip(324, 6, false).unwrap();
        let short = strip(318, 6, false).unwrap();
        for y in 0..HEIGHT {
            let start = (y * WIDTH + 53 * 24) * 4;
            assert!(
                short[start..start + 24 * 4]
                    .chunks_exact(4)
                    .all(|p| p == [0, 0, 0, 255])
            );
            assert_ne!(&full[start..start + 24 * 4], &short[start..start + 24 * 4]);
        }
        assert!(X + WIDTH <= 1368 && Y + HEIGHT < 1248);
    }
}
