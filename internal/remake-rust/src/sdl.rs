use std::ffi::{CStr, CString, c_char, c_int, c_void};
use std::ptr;
use std::{
    cell::{Cell, RefCell},
    path::{Path, PathBuf},
};

const RGBA32: u32 = 0x16762004;
#[repr(C)]
struct DisplayRect {
    x: i32,
    y: i32,
    w: i32,
    h: i32,
}
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
    fn SDL_SetMainReady();
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
    fn SDL_SetWindowSize(window: *mut c_void, w: c_int, h: c_int);
    fn SDL_SetWindowPosition(window: *mut c_void, x: c_int, y: c_int);
    fn SDL_GetDisplayUsableBounds(display: c_int, rect: *mut DisplayRect) -> c_int;
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
    fn SDL_ClearQueuedAudio(device: u32);
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
    poster: RefCell<Option<crate::poster::Shell>>,
    capture: Option<PathBuf>,
    capture_index: Cell<u32>,
    ai_mode: Cell<crate::ai::Mode>,
    rule_mode: Cell<crate::rules::Mode>,
    rules_selected: Cell<bool>,
    rules_locked: Cell<bool>,
    display_fallback: RefCell<crate::display::Settings>,
    ai_trace: RefCell<Vec<crate::ai::Decision>>,
    ai_decisions: Cell<u64>,
    ai_changed: Cell<u64>,
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
            SDL_SetMainReady();
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
                poster: RefCell::new(None),
                capture: None,
                capture_index: Cell::new(0),
                ai_mode: Cell::new(crate::ai::Mode::Native),
                rule_mode: Cell::new(crate::rules::Mode::Native),
                rules_selected: Cell::new(false),
                rules_locked: Cell::new(false),
                display_fallback: RefCell::new(crate::display::Settings::default()),
                ai_trace: RefCell::new(Vec::new()),
                ai_decisions: Cell::new(0),
                ai_changed: Cell::new(0),
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
                if let Some(shell) = self.poster.borrow_mut().as_mut() {
                    if shell.event(&mut e.bytes) {
                        continue;
                    }
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
        let shell = self.poster.borrow();
        let full = shell
            .as_ref()
            .map(|s| s.compose(pixels, s.elapsed()))
            .transpose()?;
        let presented = full.as_deref().unwrap_or(pixels);
        let canvas_width = if full.is_some() {
            crate::poster::WIDTH
        } else {
            self.width
        };
        unsafe {
            let mut target = ptr::null_mut();
            let mut pitch = 0;
            if SDL_LockTexture(self.texture, ptr::null(), &mut target, &mut pitch) != 0 {
                return Err(error());
            }
            if pitch < canvas_width as i32 * 4 || target.is_null() {
                SDL_UnlockTexture(self.texture);
                return Err("紋理步幅無效".into());
            }
            for y in 0..self.height {
                ptr::copy_nonoverlapping(
                    presented.as_ptr().add(y * canvas_width * 4),
                    target.cast::<u8>().add(y * pitch as usize),
                    canvas_width * 4,
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
                if width != canvas_width as i32 || height != self.height as i32 {
                    return Err("擷取時視窗尺寸須等於原生畫布".into());
                }
                let mut data = vec![0u8; presented.len()];
                if SDL_RenderReadPixels(
                    self.renderer,
                    ptr::null(),
                    RGBA32,
                    data.as_mut_ptr().cast(),
                    (canvas_width * 4) as i32,
                ) != 0
                {
                    return Err(error());
                }
                if let Some(s) = shell.as_ref() {
                    if data != presented {
                        return Err("海報全幅SDL讀回不符".into());
                    }
                    if let Some(dir) = &self.capture {
                        let n = self.capture_index.get() + 1;
                        self.capture_index.set(n);
                        Self::ppm(
                            &dir.join(format!("shell-frame-{n:03}.ppm")),
                            presented,
                            canvas_width,
                            self.height,
                        )?;
                        Self::ppm(
                            &dir.join(format!("shell-readback-{n:03}.ppm")),
                            &data,
                            canvas_width,
                            self.height,
                        )?;
                        std::fs::write(
                            dir.join(format!("shell-{n:03}.tsv")),
                            format!("{}{}", s.status(), self.ai_status()),
                        )
                        .map_err(|e| e.to_string())?;
                    }
                    let mut center = Vec::with_capacity(pixels.len());
                    for y in 0..self.height {
                        center.extend_from_slice(
                            &data[(y * canvas_width + 512) * 4..(y * canvas_width + 2432) * 4],
                        );
                    }
                    Some(center)
                } else {
                    Some(data)
                }
            } else {
                None
            };
            SDL_RenderPresent(self.renderer);
            Ok(readback)
        }
    }
    fn ppm(path: &Path, pixels: &[u8], width: usize, height: usize) -> Result<(), String> {
        use std::io::Write;
        let f = std::fs::File::create(path).map_err(|e| e.to_string())?;
        let mut out = std::io::BufWriter::new(f);
        write!(out, "P6\n{width} {height}\n255\n").map_err(|e| e.to_string())?;
        for p in pixels.chunks_exact(4) {
            out.write_all(&p[..3]).map_err(|e| e.to_string())?;
        }
        out.flush().map_err(|e| e.to_string())
    }
    pub fn configure_poster(
        &mut self,
        root: &Path,
        store: Option<&Path>,
        capture: Option<&Path>,
        scale: f64,
    ) -> Result<(), String> {
        let settings = crate::display::Settings::load(root, store)?;
        let mut shell = match crate::poster::Shell::load(root, store) {
            Ok(v) => v,
            Err(e) => {
                eprintln!("海報工具列：{e}");
                None
            }
        };
        if let Some(s) = shell.as_mut() {
            s.display = settings;
        } else {
            *self.display_fallback.borrow_mut() = settings;
            return Ok(());
        }

        unsafe {
            let new = SDL_CreateTexture(
                self.renderer,
                RGBA32,
                1,
                crate::poster::WIDTH as i32,
                self.height as i32,
            );
            if new.is_null() {
                return Err(error());
            }
            if SDL_RenderSetLogicalSize(
                self.renderer,
                crate::poster::WIDTH as i32,
                self.height as i32,
            ) != 0
            {
                SDL_DestroyTexture(new);
                return Err(error());
            }
            SDL_DestroyTexture(self.texture);
            self.texture = new;
            let mut bounds = DisplayRect {
                x: 0,
                y: 0,
                w: 0,
                h: 0,
            };
            let fitted = if capture.is_none()
                && SDL_GetDisplayUsableBounds(0, &mut bounds) == 0
                && bounds.w > 0
                && bounds.h > 0
            {
                scale
                    .min(f64::from(bounds.w) / crate::poster::WIDTH as f64)
                    .min(f64::from(bounds.h) / self.height as f64)
            } else {
                scale
            };
            SDL_SetWindowSize(
                self.window,
                (crate::poster::WIDTH as f64 * fitted) as i32,
                (self.height as f64 * fitted) as i32,
            );
            SDL_SetWindowPosition(self.window, 0x2fff0000, 0x2fff0000);
        }
        *self.poster.borrow_mut() = shell;
        self.capture = capture.map(Path::to_path_buf);
        Ok(())
    }
    pub fn display_mode(&self) -> crate::display::Mode {
        self.poster
            .borrow()
            .as_ref()
            .map_or_else(|| self.display_fallback.borrow().mode, |s| s.display.mode)
    }
    pub fn display_configured(&self) -> bool {
        self.poster.borrow().as_ref().map_or_else(
            || self.display_fallback.borrow().configured,
            |s| s.display.configured,
        )
    }
    pub fn set_display(&self, mode: crate::display::Mode, persist: bool) -> Result<(), String> {
        if let Some(s) = self.poster.borrow_mut().as_mut() {
            s.display.choose(mode, persist)?;
            s.display.configured = true;
        } else {
            let mut s = self.display_fallback.borrow_mut();
            s.choose(mode, persist)?;
            s.configured = true;
        }
        Ok(())
    }
    pub fn toggle_display(&self) -> Result<(), String> {
        let mode = if self.display_mode().original() {
            crate::display::Mode::Hd
        } else {
            crate::display::Mode::Original
        };
        self.set_display(mode, true)
    }
    pub fn set_rules(&self, mode: crate::rules::Mode, selected: bool) {
        self.rule_mode.set(mode);
        self.rules_selected.set(selected);
        if let Some(s) = self.poster.borrow_mut().as_mut() {
            s.rules = mode;
            s.rules_selected = selected;
        }
    }
    pub fn rule_mode(&self) -> crate::rules::Mode {
        self.poster
            .borrow()
            .as_ref()
            .map_or(self.rule_mode.get(), |s| s.rules)
    }
    pub fn rules_selected(&self) -> bool {
        self.poster
            .borrow()
            .as_ref()
            .map_or(self.rules_selected.get(), |s| s.rules_selected)
    }
    pub fn lock_rules(&self, locked: bool) {
        self.rules_locked.set(locked);
        if let Some(s) = self.poster.borrow_mut().as_mut() {
            s.rules_locked = locked;
            if locked {
                s.close_rules_menu();
            }
        }
    }
    pub fn set_battle_ai(&self, mode: crate::ai::Mode) {
        self.ai_mode.set(mode);
        if let Some(shell) = self.poster.borrow_mut().as_mut() {
            shell.ai = mode;
        }
    }
    pub fn battle_ai(&self) -> crate::ai::Mode {
        self.poster
            .borrow()
            .as_ref()
            .map_or(self.ai_mode.get(), |s| s.ai)
    }
    pub fn record_ai(&self, decision: Option<crate::ai::Decision>) {
        if let Some(d) = decision {
            self.ai_decisions.set(self.ai_decisions.get() + 1);
            if d.original != d.selected {
                self.ai_changed.set(self.ai_changed.get() + 1);
            }
            let mut trace = self.ai_trace.borrow_mut();
            trace.push(d);
            if trace.len() > 32 {
                trace.remove(0);
            }
        }
    }
    pub fn ai_status(&self) -> String {
        let trace = self.ai_trace.borrow();
        let last = trace.last();
        let base = format!(
            "battle_ai\t{}\nai_decisions\t{}\nai_changed\t{}\nai_original_slot\t{}\nai_selected_slot\t{}\nai_route\t{}\nai_reason\t{}\n",
            self.battle_ai().name(),
            self.ai_decisions.get(),
            self.ai_changed.get(),
            last.map_or(-1, |d| d.original as i32),
            last.map_or(-1, |d| d.selected as i32),
            last.map_or("none", |d| d.route.name()),
            last.map_or("none", |d| d.reason)
        );
        let candidates = last
            .map(|d| {
                d.candidates
                    .iter()
                    .map(|c| format!("{}:{}/{}:{}", c.slot, c.loss, c.count, c.amount))
                    .collect::<Vec<_>>()
                    .join(",")
            })
            .unwrap_or_default();
        let recent = trace
            .iter()
            .map(|d| format!("{}:{}>{}", d.route.name(), d.original, d.selected))
            .collect::<Vec<_>>()
            .join(";");
        let settings = self.poster.borrow();
        let settings = settings.as_ref().map(|s| &s.display);
        let fallback = self.display_fallback.borrow();
        let settings = settings.unwrap_or(&fallback);
        let display = format!(
            "display_mode\t{}\ndisplay_available\t{}\ndisplay_configured\t{}\n",
            settings.mode.name(),
            settings.available,
            settings.configured
        );
        format!(
            "{display}{base}ai_candidates\t{candidates}\nai_recent\t{recent}\nbattle_rules\t{}\nrules_locked\t{}\n",
            self.rule_mode().name(),
            self.rules_locked.get()
        )
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
    pub fn clear_music(&self) {
        if self.audio != 0 {
            unsafe { SDL_ClearQueuedAudio(self.audio) }
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
