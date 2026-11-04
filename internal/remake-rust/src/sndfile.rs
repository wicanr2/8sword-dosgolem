//! libsndfile's documented SF_INFO and frame-oriented read API.
//! https://libsndfile.github.io/libsndfile/api.html
use crate::media_assets::Music;
use std::ffi::{CStr, c_char, c_int, c_void};
use std::fs::File;
use std::io::{Read, Seek};
use std::os::fd::AsRawFd;
use std::path::Path;

#[repr(C)]
#[derive(Default)]
struct Info {
    frames: i64,
    rate: c_int,
    channels: c_int,
    format: c_int,
    sections: c_int,
    seekable: c_int,
}
#[link(name = ":libsndfile.so.1")]
unsafe extern "C" {
    fn sf_open_fd(fd: c_int, mode: c_int, info: *mut Info, close_desc: c_int) -> *mut c_void;
    fn sf_readf_short(file: *mut c_void, ptr: *mut i16, frames: i64) -> i64;
    fn sf_error(file: *mut c_void) -> c_int;
    fn sf_strerror(file: *mut c_void) -> *const c_char;
    fn sf_close(file: *mut c_void) -> c_int;
}
struct Sound(*mut c_void);
impl Drop for Sound {
    fn drop(&mut self) {
        unsafe {
            sf_close(self.0);
        }
    }
}
pub fn decode(path: &Path) -> Result<Music, String> {
    let meta = path.symlink_metadata().map_err(|e| e.to_string())?;
    if !meta.file_type().is_file() || meta.len() > 32 << 20 {
        return Err("音樂檔案無效".into());
    }
    let mut file = File::open(path).map_err(|e| e.to_string())?;
    let mut magic = [0u8; 4];
    file.read_exact(&mut magic).map_err(|e| e.to_string())?;
    if &magic != b"OggS" {
        return Err("音樂必須使用OGG".into());
    }
    file.rewind().map_err(|e| e.to_string())?;
    // Rust retains ownership of fd.
    let mut info = Info::default();
    let raw = unsafe { sf_open_fd(file.as_raw_fd(), 0x10, &mut info, 0) };
    if raw.is_null() {
        return Err(unsafe { CStr::from_ptr(sf_strerror(raw)) }
            .to_string_lossy()
            .into_owned());
    }
    let sound = Sound(raw);
    if info.rate != 48000
        || info.channels != 2
        || info.format & 0x0fff_ffff != 0x20_0060
        || info.frames <= 0
        || info.frames > 48000 * 600
    {
        return Err("音樂格式須為48kHz雙聲道OGG Vorbis且不超過十分鐘".into());
    }
    let mut samples = vec![0i16; info.frames as usize * 2];
    let mut done = 0i64;
    while done < info.frames {
        let got = unsafe {
            sf_readf_short(
                sound.0,
                samples[done as usize * 2..].as_mut_ptr(),
                info.frames - done,
            )
        };
        if got <= 0 || got > info.frames - done {
            return Err("音樂資料截斷".into());
        }
        done += got;
    }
    if unsafe { sf_error(sound.0) } != 0 {
        return Err("音樂解碼失敗".into());
    }
    let pcm = samples.into_iter().flat_map(i16::to_le_bytes).collect();
    Ok(Music {
        pcm,
        frames: done as u64,
    })
}
