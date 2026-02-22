# Gesture-Controlled Operating System Interface

> **⚠️ WORK IN PROGRESS**: This is an actively developed prototype for a gesture-based OS input layer. It is NOT production-ready and should be considered experimental software.

## 🎯 Project Vision

This is **not a demo or script**. This is the foundation for a **gesture-based Operating System input layer** intended to replace or augment traditional input devices:
- Mouse
- Trackpad  
- Scroll wheel

The goal is **OS-level interaction**, not application-specific hacks. This system aims to behave like a native input device that works seamlessly across all applications.

---

## 📋 Current Status

### ✅ What Works
- **Two-hand gesture system**
  - Left hand: Cursor control, left/right click, drag & drop
  - Right hand: Two-finger scroll
- **Real-time hand tracking** using MediaPipe
- **Smooth cursor movement** with interpolation and deadzone filtering
- **Stable gesture detection** with frame confirmation to prevent false triggers
- **Visual feedback** with green ring overlay on clicks
- **Debug mode** with real-time detection values

### ⚠️ Known Limitations
- **Uses `pyautogui`** - High latency (~100ms), not true OS-level integration
- **Single-threaded** - Overlay can block main loop
- **No calibration system** - Fixed thresholds may not work for all hand sizes
- **Camera-dependent** - Performance varies with lighting and camera quality
- **No failsafe mechanism** - Can't easily disable if gestures go haywire
- **No multi-monitor optimization**
- **No persistence** - Settings reset on restart

### 🚧 In Development
- Migration to native input APIs (`pynput` for Windows, `evdev` for Linux)
- Gesture state machine for deterministic behavior
- Kalman filtering for ultra-smooth cursor tracking
- Auto-calibration system
- System service/daemon architecture
- Multi-monitor support
- Settings UI and system tray integration

---

## 🛠️ Technical Architecture

### Current Implementation

```
┌─────────────────────────────────────────┐
│         Camera Feed (60 FPS)            │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    MediaPipe Hand Tracking              │
│    - Detects up to 2 hands              │
│    - 21 landmarks per hand              │
│    - Classifies left/right hand         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Gesture Recognition                │
│    - Pinch detection (distance ratios)  │
│    - Finger extension detection         │
│    - Stability counters (debouncing)    │
│    - Hold timers for grab vs click      │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│       PyAutoGUI (Current)               │
│    ⚠️  High latency, not OS-native      │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Operating System                │
└─────────────────────────────────────────┘
```

### Target Architecture (Future)

```
┌─────────────────────────────────────────┐
│      Camera Feed (120+ FPS)             │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    MediaPipe (GPU Accelerated)          │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    Gesture State Machine                │
│    - Intent prediction                  │
│    - Kalman filtering                   │
│    - Adaptive thresholds                │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    Native Input APIs (<10ms latency)    │
│    - Windows: SendInput / pynput        │
│    - Linux: evdev virtual HID           │
│    - macOS: Quartz Events               │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Operating System                │
└─────────────────────────────────────────┘
```

---

## 📦 Requirements

### Hardware
- **Webcam** - 720p or higher recommended, 60 FPS preferred
- **CPU** - Intel i5/AMD Ryzen 5 or better (for real-time processing)
- **RAM** - 4GB minimum, 8GB recommended
- **OS** - Windows 10/11, Ubuntu 20.04+, or macOS 10.15+

### Software Dependencies

```bash
# Core dependencies
pip install opencv-python
pip install mediapipe
pip install pyautogui  # Will be replaced with pynput

# Optional (for future native input)
pip install pynput     # Windows/macOS/Linux
pip install evdev      # Linux only - for virtual HID device
```

### Python Version
- **Python 3.8+** required
- **Python 3.10+** recommended

---

## 🚀 Installation & Usage

### Quick Start

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd gesture-control
   ```

2. **Install dependencies**
   ```bash
   pip install opencv-python mediapipe pyautogui
   ```

3. **Run the application**
   ```bash
   python hand_mouse.py
   ```

4. **Position your hands**
   - **Left hand**: Controls cursor and clicks
   - **Right hand**: Controls scrolling

5. **Exit**
   - Press `ESC` key to quit

### System Setup Notes

#### Windows
- No special permissions required (currently)
- Camera access permission needed
- Future versions will require elevated privileges for native input

#### Linux (WSL2)
- Camera access in WSL2 is complex - requires USB passthrough or network streaming
- **Recommended**: Run natively in Ubuntu, not through WSL2
- For virtual HID device (future), need root permissions

#### macOS
- Camera permission required in System Preferences
- Accessibility permissions required for input control
- May need to disable System Integrity Protection for low-level input

---

## 🎮 Gesture Guide

### Left Hand (Control Hand)

| Gesture | Action | How To |
|---------|--------|--------|
| 📍 **Index finger extended** | Move cursor | Point and move your finger within the tracking box |
| 👆 **Index + Thumb pinch (quick)** | Left click | Touch index and thumb together briefly |
| 👆 **Index + Thumb pinch (hold 0.35s)** | Grab & drag | Touch and hold, then move hand to drag |
| ☝️ **Middle + Thumb pinch** | Right click | Touch middle finger and thumb together |

### Right Hand (Scroll Hand)

| Gesture | Action | How To |
|---------|--------|--------|
| ✌️ **Index + Middle extended** | Scroll | Extend both fingers together, move hand up/down |

### Visual Feedback

- **Purple box** = Normal mode, cursor active
- **Green box** = Grab mode, dragging active
- **Green ring** = Click registered (expands from cursor position)
- **Status text** = Shows current gesture state

---

## ⚙️ Configuration & Tuning

### Key Parameters (in code)

```python
# Cursor Control
SMOOTHING = 0.18              # Lower = more responsive, higher = smoother
PIXEL_DEADZONE = 2            # Ignore movements smaller than this
TRACKPAD_SCALE = 0.5          # Size of tracking area (0.5 = 50% of frame)

# Gesture Detection
LEFT_PINCH_CLOSE = 0.30       # Threshold for index+thumb pinch
RIGHT_PINCH_CLOSE = 0.28      # Threshold for middle+thumb pinch
GRAB_HOLD_TIME = 0.35         # Seconds to hold pinch before drag activates

# Scroll
SCROLL_THRESHOLD = 10         # Pixels to move before scrolling
SCROLL_SPEED = 2.0            # Scroll multiplier (higher = faster)
TWO_FINGER_DISTANCE_MAX = 0.20  # Max distance between scroll fingers

# Stability
PINCH_STABLE_FRAMES = 2       # Frames needed to confirm pinch
RELEASE_STABLE_FRAMES = 3     # Frames needed to confirm release
```

### Tuning Tips

**Cursor too fast/slow?**
```python
SMOOTHING = 0.25  # Increase for slower, smoother cursor
SMOOTHING = 0.12  # Decrease for faster, more responsive cursor
```

**False clicks?**
```python
LEFT_PINCH_CLOSE = 0.25  # Make tighter (fingers must be closer)
PINCH_STABLE_FRAMES = 3  # Require more confirmation frames
```

**Scroll not detecting?**
```python
FINGER_EXTENDED_THRESHOLD = 0.065  # Lower threshold (easier to detect)
TWO_FINGER_DISTANCE_MAX = 0.25     # Allow fingers to be farther apart
```

**Grab activating too fast?**
```python
GRAB_HOLD_TIME = 0.5  # Increase hold time before drag starts
```

---

## 🐛 Troubleshooting

### Camera Issues

**Problem**: "NO HAND DETECTED" constantly
- **Solution**: 
  - Check camera is working (test in other apps)
  - Ensure hands are within camera view
  - Improve lighting (face a window or add desk lamp)
  - Lower detection confidence: `min_detection_confidence=0.6`

**Problem**: Laggy/choppy video
- **Solution**:
  - Close other camera apps
  - Lower resolution if needed
  - Check CPU usage (close background apps)

### Gesture Detection Issues

**Problem**: Clicks happening without pinching
- **Solution**:
  - Tighten thresholds: `LEFT_PINCH_CLOSE = 0.25`
  - Increase confirmation: `PINCH_STABLE_FRAMES = 3`
  - Check debug values to see actual pinch ratios

**Problem**: Pinch not detecting
- **Solution**:
  - Relax thresholds: `LEFT_PINCH_CLOSE = 0.35`
  - Watch debug output to see current ratio values
  - Ensure fingers are fully visible to camera

**Problem**: Cursor is jittery
- **Solution**:
  - Increase smoothing: `SMOOTHING = 0.30`
  - Increase deadzone: `PIXEL_DEADZONE = 5`
  - Stabilize camera (mount on tripod/stand)

**Problem**: Grab releases unexpectedly
- **Solution**:
  - Increase release frames: `RELEASE_STABLE_FRAMES = 5`
  - Check lighting (shadows can confuse tracking)

### Performance Issues

**Problem**: Low FPS, system lag
- **Solution**:
  - Close other applications
  - Disable debug mode: `DEBUG_MODE = False`
  - Use better camera with hardware encoding
  - Consider GPU acceleration (CUDA for MediaPipe)

---

## 📊 Debug Mode

Enable detailed debugging:
```python
DEBUG_MODE = True
```

### Debug Display Shows:

**Top Bar**:
- Current hands detected (LEFT, RIGHT, or both)
- Active gestures and states

**Middle Section** (per hand):
- Pinch detection ratios and thresholds
- Frame counters for stability
- "DETECTED ✓" when gesture confirmed
- Hold timer progress bar for grab

**Bottom Section** (Right hand):
- Finger extension values
- Two-finger distance
- Extended/Together status

**Console Output**:
- Gesture activation/deactivation events
- Click confirmations
- Scroll events with amounts
- Pinch detection with ratio values

---

## 🗺️ Roadmap

### Phase 1: Native Input Layer ✅ (Next Priority)
- [ ] Replace `pyautogui` with `pynput` (Windows)
- [ ] Implement `evdev` virtual HID (Linux)
- [ ] Add Quartz Events support (macOS)
- [ ] Target <10ms input latency
- [ ] Measure and optimize performance

### Phase 2: Gesture State Machine
- [ ] Implement proper FSM for gesture states
- [ ] Add hysteresis to prevent state flickering
- [ ] Intent prediction for smoother interactions
- [ ] Gesture chaining (combine multiple gestures)

### Phase 3: Advanced Filtering
- [ ] Kalman filter for cursor smoothing
- [ ] Predictive cursor movement
- [ ] Adaptive deadzone based on velocity
- [ ] Hand pose prediction (1-2 frames ahead)

### Phase 4: Calibration System
- [ ] Auto-detect hand size
- [ ] Workspace boundary calibration
- [ ] Personalized gesture thresholds
- [ ] Save/load user profiles

### Phase 5: System Integration
- [ ] System service/daemon (auto-start)
- [ ] System tray icon and controls
- [ ] Settings UI (web-based or native)
- [ ] Gesture overlay toggle
- [ ] Emergency disable (panic key)
- [ ] Multi-monitor support

### Phase 6: Advanced Features
- [ ] Three-finger gestures (swipes, pinch-zoom)
- [ ] Custom gesture macros
- [ ] Voice commands integration
- [ ] Haptic feedback (via phone/watch)
- [ ] ML-based gesture learning

---

## Development History

### Iteration Process

This project evolved through multiple iterations addressing real usability issues:

1. **Initial Implementation**
   - Single-hand control with multiple gestures
   - **Problem**: Gestures conflicted with each other (scroll vs click)
   
2. **Sensitivity Tuning**
   - Added threshold parameters
   - **Problem**: Too sensitive (false clicks) or too insensitive (missed clicks)
   
3. **Stability System**
   - Added frame counters and confirmation delays
   - **Problem**: Still jittery, grab released prematurely
   
4. **Two-Hand Separation**
   - Split gestures across left/right hands
   - **Problem**: Scroll detection was unreliable (tried fist, then two-finger)
   
5. **Current Version**
   - Refined two-hand system with better debug feedback
   - Relaxed detection thresholds
   - **Still needs**: Native input APIs, calibration, state machine

### Key Lessons Learned

- **Debouncing is critical** - Raw sensor data needs heavy filtering
- **Visual feedback matters** - Users need to see what system detects
- **Gesture separation** - Don't overload one hand with too many gestures
- **Threshold tuning is hard** - One-size-fits-all values don't exist
- **Latency kills UX** - Even 100ms feels sluggish for cursor control

---

## 📝 Code Structure

### Main Files

- `hand_mouse.py` - Latest with improved scroll detection

### Key Components

```python
# Gesture Detection
- dist3(a, b)              # 3D Euclidean distance between landmarks
- clamp(v, lo, hi)         # Value clamping utility

# State Variables
- left_pinch_counter       # Stability counter for left pinch
- right_pinch_counter      # Stability counter for right pinch
- grab_active              # Drag mode flag
- scroll_active            # Scroll mode flag
- pinch_start_time         # Timer for grab vs click distinction

# Tunable Parameters
- SMOOTHING                # Cursor interpolation factor
- PINCH_STABLE_FRAMES      # Confirmation frames needed
- GRAB_HOLD_TIME           # Hold duration for drag
```

---

## ⚠️ Important Notes

### This is NOT Production Software

- **No warranty** - Use at your own risk
- **No accessibility compliance** - Not tested for users with disabilities
- **No security audit** - Camera access without encryption
- **No error recovery** - Crashes may leave mouse in weird state
- **No documentation** - Code comments are minimal

### Known Bugs

- Cursor can jump when hand briefly leaves frame
- Multi-monitor cursor can get stuck at screen edges
- Overlay sometimes doesn't disappear after click
- Debug text can overlap and become unreadable
- No graceful degradation if camera access fails

### Privacy & Security

- **Camera access** - System has full access to webcam feed
- **No recording** - Video is processed in real-time, not saved
- **No network** - All processing happens locally
- **Input injection** - Future versions will inject OS-level input events

---

## Credits & Inspiration

### Core Technologies
- **MediaPipe** (Google) - Hand tracking and landmark detection
- **OpenCV** - Computer vision and camera handling  
- **PyAutoGUI** - Current input injection (to be replaced)

### Inspiration
- Apple Vision Pro hand tracking
- Leap Motion gesture control
- Microsoft Kinect
- VR/AR hand gesture systems

---

## 📄 License

[License information to be added]

---

## 📧 Contact & Contributions

email: aarush.narora@gmail.com

---

## 🔗 Resources

### Documentation
- [MediaPipe Hands Documentation](https://google.github.io/mediapipe/solutions/hands.html)
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)

### Related Projects
- [Leap Motion SDK](https://developer.leapmotion.com/)
- [Google MediaPipe Examples](https://github.com/google/mediapipe/tree/master/mediapipe/examples)

### Research Papers
- MediaPipe Hands: On-device Real-time Hand Tracking (Google AI Blog)
- Real-time Hand Tracking for Human-Computer Interaction

---

**Last Updated**: January 2025  
**Version**: 0.1.0-alpha  
**Status**: 🚧 Experimental / Work in Progress
