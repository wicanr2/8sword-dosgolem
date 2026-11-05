//! Logical pointer actions shared by mouse and future touch frontends.
use crate::controller::POSITIONS;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Rect(pub i32, pub i32, pub i32, pub i32);
impl Rect {
    pub fn contains(self, x: i32, y: i32) -> bool {
        x >= self.0 && y >= self.1 && x < self.0 + self.2 && y < self.1 + self.3
    }
    pub fn array(self) -> [i32; 4] {
        [self.0, self.1, self.2, self.3]
    }
}
pub const FOOTER: [Rect; 4] = [
    Rect(24, 1272, 424, 48),
    Rect(480, 1272, 424, 48),
    Rect(936, 1272, 424, 48),
    Rect(1392, 1272, 504, 48),
];
pub fn army_box(i: usize) -> Rect {
    Rect(
        72 + (i / 3) as i32 * 696,
        126 + (i % 3) as i32 * 360,
        if i < 3 { 672 } else { 600 },
        300,
    )
}
pub fn offer_box(i: usize) -> Rect {
    Rect(
        384 + (i / 4) as i32 * 480,
        822 + (i % 4) as i32 * 84,
        456,
        72,
    )
}
pub const TABS: [Rect; 2] = [Rect(96, 738, 360, 60), Rect(480, 738, 360, 60)];
pub const CHOICES: [Rect; 2] = [Rect(144, 858, 432, 84), Rect(600, 858, 432, 84)];
pub fn digit_box(i: usize) -> Rect {
    Rect(
        1416 + (i % 3) as i32 * 156,
        360 + (i / 3) as i32 * 144,
        144,
        120,
    )
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Screen {
    World,
    Prompt,
    Army,
    Shop { extra: bool, quantity: bool },
    Battle { finished: bool },
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Action {
    Key(i32),
    Font(u8),
    Army(usize),
    Offer(usize),
    Target(usize),
    Choice(bool),
    Extra(bool),
}
pub fn normalized(x: f32, y: f32) -> Option<(i32, i32)> {
    if !x.is_finite() || !y.is_finite() || !(0.0..1.0).contains(&x) || !(0.0..1.0).contains(&y) {
        None
    } else {
        Some(((x * 1920.0) as i32, (y * 1320.0) as i32))
    }
}
pub fn hit(screen: Screen, x: i32, y: i32) -> Option<Action> {
    if !(0..1920).contains(&x) || !(0..1320).contains(&y) {
        return None;
    }
    for (i, r) in FOOTER.iter().enumerate() {
        if r.contains(x, y) {
            if screen == Screen::World {
                return Some(Action::Key([32, 27, 1073741883, 1073741888][i]));
            }
            if screen == Screen::Prompt && i == 1 {
                return Some(Action::Choice(true));
            }
            if matches!(screen, Screen::Battle { finished: true }) {
                return Some(Action::Key([13, 13, 1073741903, 1073741888][i]));
            }
            if matches!(screen, Screen::Shop { quantity: true, .. }) && i == 2 {
                return Some(Action::Key(127));
            }
            return Some(Action::Key([13, 27, 32, 1073741888][i]));
        }
    }
    if (2..46).contains(&y) {
        for i in 0..3 {
            if Rect(144 + i * 228, 2, 216, 44).contains(x, y) {
                return Some(Action::Font(i as u8));
            }
        }
        if Rect(920, 2, 232, 44).contains(x, y) {
            return Some(Action::Key(109));
        }
        if Rect(1480, 2, 232, 44).contains(x, y) {
            return Some(Action::Key(1073741888));
        }
    }
    match screen {
        Screen::World => {
            if Rect(1392, 120, 504, 1080).contains(x, y) {
                let row = (y - 120) / 162;
                return match row {
                    1 => Some(Action::Key(1073741883)),
                    2 => Some(Action::Key(1073741884)),
                    6 => Some(Action::Key(1073741888)),
                    _ => None,
                };
            }
            if Rect(24, 120, 1344, 1050).contains(x, y) {
                let dx = ((x - 24) / 192 - 3).signum();
                let dy = ((y - 120) / 150 - 3).signum();
                let key = match (dx, dy) {
                    (-1, -1) => 1073741898,
                    (0, -1) => 1073741906,
                    (1, -1) => 1073741899,
                    (-1, 0) => 1073741904,
                    (1, 0) => 1073741903,
                    (-1, 1) => 1073741901,
                    (0, 1) => 1073741905,
                    (1, 1) => 1073741902,
                    _ => 32,
                };
                return Some(Action::Key(key));
            }
        }
        Screen::Army => {
            for i in 0..6 {
                if army_box(i).contains(x, y) {
                    return Some(Action::Army(i));
                }
            }
        }
        Screen::Prompt => {
            for (i, r) in CHOICES.iter().enumerate() {
                if r.contains(x, y) {
                    return Some(Action::Choice(i == 1));
                }
            }
        }
        Screen::Shop { extra, quantity } => {
            if TABS[0].contains(x, y) {
                return Some(Action::Extra(false));
            }
            if TABS[1].contains(x, y) {
                return Some(Action::Extra(true));
            }
            if quantity {
                for i in 0..12 {
                    if digit_box(i).contains(x, y) {
                        return Some(Action::Key(
                            [49, 50, 51, 52, 53, 54, 55, 56, 57, 8, 48, 127][i],
                        ));
                    }
                }
            } else if extra {
                for i in 0..8 {
                    if offer_box(i).contains(x, y) {
                        return Some(Action::Offer(i));
                    }
                }
            }
        }
        Screen::Battle { finished } => {
            if finished {
                if Rect(1200, 2, 232, 44).contains(x, y) {
                    return Some(Action::Key(13));
                }
                if Rect(24, 1248, 1344, 24).contains(x, y) {
                    return Some(Action::Choice(x >= 696));
                }
            } else {
                for (slot, [left, top]) in POSITIONS[6..].iter().enumerate() {
                    if Rect(*left, *top + 48, 264, 300).contains(x, y) {
                        return Some(Action::Target(slot + 1));
                    }
                }
            }
        }
    }
    None
}
#[derive(Default)]
pub struct Pointer {
    pressed: Option<(Screen, Action)>,
}
impl Pointer {
    pub fn event(&mut self, screen: Screen, kind: u32, x: i32, y: i32) -> Option<Action> {
        let action = hit(screen, x, y);
        if kind == 0x401 {
            self.pressed = action.map(|a| (screen, a));
            None
        } else if kind == 0x402 {
            let before = self.pressed.take();
            action.filter(|a| before == Some((screen, *a)))
        } else {
            None
        }
    }
    pub fn cancel(&mut self) {
        self.pressed = None;
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn release_is_one_action_drag_and_duplicate_release_are_cancelled() {
        let mut p = Pointer::default();
        assert_eq!(p.event(Screen::World, 0x401, 500, 500), None);
        assert_eq!(
            p.event(Screen::World, 0x402, 500, 500),
            Some(Action::Key(1073741898))
        );
        assert_eq!(p.event(Screen::World, 0x402, 500, 500), None);
        p.event(Screen::Army, 0x401, 100, 200);
        assert_eq!(p.event(Screen::Army, 0x402, 800, 200), None);
        p.event(Screen::Army, 0x401, 100, 200);
        assert_eq!(p.event(Screen::World, 0x402, 100, 200), None);
    }
    #[test]
    fn normalized_points_and_every_control_share_their_visible_bounds() {
        assert_eq!(normalized(0.5, 0.5), Some((960, 660)));
        assert_eq!(normalized(f32::NAN, 0.0), None);
        assert_eq!(normalized(1.0, 0.5), None);
        for i in 0..6 {
            let r = army_box(i);
            assert_eq!(
                hit(Screen::Army, r.0 + r.2 / 2, r.1 + r.3 / 2),
                Some(Action::Army(i))
            );
        }
        for i in 0..12 {
            let r = digit_box(i);
            assert!(
                hit(
                    Screen::Shop {
                        extra: false,
                        quantity: true
                    },
                    r.0 + 20,
                    r.1 + 20
                )
                .is_some()
            );
        }
        assert_eq!(hit(Screen::World, -1, 50), None);
    }
}
