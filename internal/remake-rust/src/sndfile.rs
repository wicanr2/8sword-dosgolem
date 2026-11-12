//! libsndfile's documented SF_INFO and frame-oriented read API.
//! https://libsndfile.github.io/libsndfile/api.html
use crate::media_assets::Music;
use std::ffi::{CStr, c_char, c_int, c_void};
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
#[repr(C)]
struct VirtualIo {
    length: unsafe extern "C" fn(*mut c_void) -> i64,
    seek: unsafe extern "C" fn(i64, c_int, *mut c_void) -> i64,
    read: unsafe extern "C" fn(*mut c_void, i64, *mut c_void) -> i64,
    write: unsafe extern "C" fn(*const c_void, i64, *mut c_void) -> i64,
    tell: unsafe extern "C" fn(*mut c_void) -> i64,
}
struct Input {
    bytes: Vec<u8>,
    pos: usize,
}
unsafe extern "C" fn length(data: *mut c_void) -> i64 {
    unsafe { (&*(data as *const Input)).bytes.len() as i64 }
}
unsafe extern "C" fn seek(offset: i64, whence: c_int, data: *mut c_void) -> i64 {
    let input = unsafe { &mut *(data as *mut Input) };
    let base = match whence {
        0 => 0,
        1 => input.pos as i64,
        2 => input.bytes.len() as i64,
        _ => return -1,
    };
    match base.checked_add(offset) {
        Some(p) if p >= 0 && p <= input.bytes.len() as i64 => {
            input.pos = p as usize;
            p
        }
        _ => -1,
    }
}
unsafe extern "C" fn read(out: *mut c_void, count: i64, data: *mut c_void) -> i64 {
    if count <= 0 || out.is_null() {
        return 0;
    }
    let input = unsafe { &mut *(data as *mut Input) };
    let n = (count as u64).min((input.bytes.len() - input.pos) as u64) as usize;
    unsafe {
        std::ptr::copy_nonoverlapping(input.bytes.as_ptr().add(input.pos), out.cast(), n);
    }
    input.pos += n;
    n as i64
}
unsafe extern "C" fn write(_: *const c_void, _: i64, _: *mut c_void) -> i64 {
    0
}
unsafe extern "C" fn tell(data: *mut c_void) -> i64 {
    unsafe { (&*(data as *const Input)).pos as i64 }
}

#[cfg_attr(target_os = "linux", link(name = ":libsndfile.so.1"))]
#[cfg_attr(not(target_os = "linux"), link(name = "sndfile"))]
unsafe extern "C" {
    fn sf_open_virtual(
        io: *const VirtualIo,
        mode: c_int,
        info: *mut Info,
        data: *mut c_void,
    ) -> *mut c_void;
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
    let bytes = std::fs::read(path).map_err(|e| e.to_string())?;
    if bytes.len() > 32 << 20 || !bytes.starts_with(b"OggS") {
        return Err("音樂必須使用OGG".into());
    }
    // The buffer and callback table outlive Sound, including early returns.
    let mut input = Input { bytes, pos: 0 };
    let io = VirtualIo {
        length,
        seek,
        read,
        write,
        tell,
    };
    let mut info = Info::default();
    let raw = unsafe { sf_open_virtual(&io, 0x10, &mut info, (&mut input as *mut Input).cast()) };
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

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn virtual_io_bounds_and_seek_failures() {
        let mut input = Input {
            bytes: b"OggS".to_vec(),
            pos: 0,
        };
        let p = (&mut input as *mut Input).cast();
        let mut out = [0u8; 8];
        unsafe {
            assert_eq!(length(p), 4);
            assert_eq!(seek(-1, 0, p), -1);
            assert_eq!(seek(i64::MAX, 2, p), -1);
            assert_eq!(tell(p), 0);
            assert_eq!(read(out.as_mut_ptr().cast(), 8, p), 4);
            assert_eq!(&out[..4], b"OggS");
            assert_eq!(read(out.as_mut_ptr().cast(), 1, p), 0);
            assert_eq!(seek(-2, 2, p), 2);
            assert_eq!(read(out.as_mut_ptr().cast(), 1, p), 1);
            assert_eq!(out[0], b'g');
            assert_eq!(write(out.as_ptr().cast(), 1, p), 0);
        }
    }
}
