use std::ffi::{CStr, CString, c_char, c_int, c_void};
use std::ptr;

const RGBA32: u32 = 0x16762004;
#[repr(C)]
#[derive(Clone, Copy)]
struct AudioSpec {
    freq: i32,
    format: u16,
    channels: u8,
    silence: u8,
    samples: u16,
    padding: u16,
    size: u32,
    callback: Option<unsafe extern "C" fn(*mut c_void, *mut u8, i32)>,
    userdata: *mut c_void,
}
#[repr(C, align(8))]
pub struct Event {
    pub bytes: [u8; 56],
}
#[link(name = "SDL2")]
unsafe extern "C" {
    fn SDL_Init(flags: u32) -> c_int;
    fn SDL_Quit();
    fn SDL_GetError() -> *const c_char;
    fn SDL_CreateWindow(
        title: *const c_char,
        x: c_int,
        y: c_int,
        w: c_int,
        h: c_int,
        flags: u32,
    ) -> *mut c_void;
    fn SDL_DestroyWindow(window: *mut c_void);
    fn SDL_CreateRenderer(window: *mut c_void, index: c_int, flags: u32) -> *mut c_void;
    fn SDL_DestroyRenderer(renderer: *mut c_void);
    fn SDL_RenderSetLogicalSize(renderer: *mut c_void, w: c_int, h: c_int) -> c_int;
    fn SDL_GetRendererOutputSize(renderer: *mut c_void, w: *mut c_int, h: *mut c_int) -> c_int;
    fn SDL_CreateTexture(
        renderer: *mut c_void,
        format: u32,
        access: c_int,
        w: c_int,
        h: c_int,
    ) -> *mut c_void;
    fn SDL_DestroyTexture(texture: *mut c_void);
    fn SDL_LockTexture(
        texture: *mut c_void,
        rect: *const c_void,
        pixels: *mut *mut c_void,
        pitch: *mut c_int,
    ) -> c_int;
    fn SDL_UnlockTexture(texture: *mut c_void);
    fn SDL_RenderClear(renderer: *mut c_void) -> c_int;
    fn SDL_RenderCopy(
        renderer: *mut c_void,
        texture: *mut c_void,
        src: *const c_void,
        dst: *const c_void,
    ) -> c_int;
    fn SDL_RenderPresent(renderer: *mut c_void);
    fn SDL_RenderReadPixels(
        renderer: *mut c_void,
        rect: *const c_void,
        format: u32,
        pixels: *mut c_void,
        pitch: c_int,
    ) -> c_int;
    fn SDL_PollEvent(event: *mut Event) -> c_int;
    fn SDL_OpenAudioDevice(
        device: *const c_char,
        capture: c_int,
        want: *const AudioSpec,
        have: *mut AudioSpec,
        allowed: c_int,
    ) -> u32;
    fn SDL_CloseAudioDevice(device: u32);
    fn SDL_PauseAudioDevice(device: u32, pause: c_int);
    fn SDL_QueueAudio(device: u32, data: *const c_void, len: u32) -> c_int;
    fn SDL_GetQueuedAudioSize(device: u32) -> u32;
}
fn error() -> String {
    unsafe {
        let p = SDL_GetError();
        if p.is_null() {
            "SDL錯誤".into()
        } else {
            CStr::from_ptr(p).to_string_lossy().into_owned()
        }
    }
}
pub struct Sdl {
    window: *mut c_void,
    renderer: *mut c_void,
    texture: *mut c_void,
    audio: u32,
    pub width: usize,
    pub height: usize,
}
impl Sdl {
    pub fn open(width: usize, height: usize, scale: f64, mute: bool) -> Result<Self, String> {
        Self::open_named(width, height, scale, mute, "神州八劍・Rust 原生普通戰鬥")
    }
    pub fn open_named(
        width: usize,
        height: usize,
        scale: f64,
        mute: bool,
        title: &str,
    ) -> Result<Self, String> {
        unsafe {
            if SDL_Init(0x20 | if mute { 0 } else { 0x10 }) != 0 {
                return Err(error());
            }
            let mut s = Self {
                window: ptr::null_mut(),
                renderer: ptr::null_mut(),
                texture: ptr::null_mut(),
                audio: 0,
                width,
                height,
            };
            let title = CString::new(title).map_err(|e| e.to_string())?;
            s.window = SDL_CreateWindow(
                title.as_ptr(),
                0x2fff0000,
                0x2fff0000,
                (width as f64 * scale) as i32,
                (height as f64 * scale) as i32,
                0x24,
            );
            if s.window.is_null() {
                return Err(error());
            }
            s.renderer = SDL_CreateRenderer(s.window, -1, 0);
            if s.renderer.is_null() {
                return Err(error());
            }
            if SDL_RenderSetLogicalSize(s.renderer, width as i32, height as i32) != 0 {
                return Err(error());
            }
            s.texture = SDL_CreateTexture(s.renderer, RGBA32, 1, width as i32, height as i32);
            if s.texture.is_null() {
                return Err(error());
            }
            if !mute {
                let want = AudioSpec {
                    freq: 48000,
                    format: 0x8010,
                    channels: 2,
                    silence: 0,
                    samples: 1024,
                    padding: 0,
                    size: 0,
                    callback: None,
                    userdata: ptr::null_mut(),
                };
                let mut have = want;
                s.audio = SDL_OpenAudioDevice(ptr::null(), 0, &want, &mut have, 0);
                if s.audio == 0 {
                    return Err(error());
                }
                if (have.freq, have.format, have.channels) != (48000, 0x8010, 2) {
                    return Err("音訊裝置格式不符".into());
                }
                SDL_PauseAudioDevice(s.audio, 0);
            }
            Ok(s)
        }
    }
    pub fn events(&self) -> Vec<Event> {
        let mut out = Vec::new();
        unsafe {
            loop {
                let mut e = Event { bytes: [0; 56] };
                if SDL_PollEvent(&mut e) == 0 {
                    break;
                }
                out.push(e)
            }
        }
        out
    }
    pub fn draw(&self, pixels: &[u8], capture: bool) -> Result<Option<Vec<u8>>, String> {
        if pixels.len() != self.width * self.height * 4 {
            return Err("畫布長度不符".into());
        }
        unsafe {
            let mut target = ptr::null_mut();
            let mut pitch = 0;
            if SDL_LockTexture(self.texture, ptr::null(), &mut target, &mut pitch) != 0 {
                return Err(error());
            }
            if pitch < self.width as i32 * 4 || target.is_null() {
                SDL_UnlockTexture(self.texture);
                return Err("紋理步幅無效".into());
            }
            for y in 0..self.height {
                ptr::copy_nonoverlapping(
                    pixels.as_ptr().add(y * self.width * 4),
                    target.cast::<u8>().add(y * pitch as usize),
                    self.width * 4,
                )
            }
            SDL_UnlockTexture(self.texture);
            if SDL_RenderClear(self.renderer) != 0
                || SDL_RenderCopy(self.renderer, self.texture, ptr::null(), ptr::null()) != 0
            {
                return Err(error());
            }
            let readback = if capture {
                let (mut width, mut height) = (0, 0);
                if SDL_GetRendererOutputSize(self.renderer, &mut width, &mut height) != 0 {
                    return Err(error());
                }
                if width != self.width as i32 || height != self.height as i32 {
                    return Err("擷取時視窗尺寸須等於原生畫布".into());
                }
                let mut data = vec![0u8; pixels.len()];
                if SDL_RenderReadPixels(
                    self.renderer,
                    ptr::null(),
                    RGBA32,
                    data.as_mut_ptr().cast(),
                    (self.width * 4) as i32,
                ) != 0
                {
                    return Err(error());
                }
                Some(data)
            } else {
                None
            };
            SDL_RenderPresent(self.renderer);
            Ok(readback)
        }
    }
    pub fn queued(&self) -> u32 {
        if self.audio == 0 {
            0
        } else {
            unsafe { SDL_GetQueuedAudioSize(self.audio) }
        }
    }
    pub fn queue(&self, bytes: &[u8]) -> Result<(), String> {
        if self.audio == 0 {
            return Ok(());
        }
        let len: u32 = bytes.len().try_into().map_err(|_| "音訊區塊過大")?;
        unsafe {
            if SDL_QueueAudio(self.audio, bytes.as_ptr().cast(), len) != 0 {
                return Err(error());
            }
        }
        Ok(())
    }
    pub fn pause_music(&self, paused: bool) {
        if self.audio != 0 {
            unsafe { SDL_PauseAudioDevice(self.audio, i32::from(paused)) }
        }
    }
}
impl Drop for Sdl {
    fn drop(&mut self) {
        unsafe {
            if self.audio != 0 {
                SDL_CloseAudioDevice(self.audio)
            }
            if !self.texture.is_null() {
                SDL_DestroyTexture(self.texture)
            }
            if !self.renderer.is_null() {
                SDL_DestroyRenderer(self.renderer)
            }
            if !self.window.is_null() {
                SDL_DestroyWindow(self.window)
            }
            SDL_Quit()
        }
    }
}
