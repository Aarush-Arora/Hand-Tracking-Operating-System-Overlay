import cv2
import mediapipe as mp
import pyautogui
import time
import math
import tkinter as tk
import threading

# ---------- PERFORMANCE ----------
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# ---------- OVERLAY STATE ----------
ring_trigger = False
cursor_pos = (0, 0)
overlay_lock = threading.Lock()

def create_overlay():
    global ring_trigger, cursor_pos
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", "white")
    root.attributes("-alpha", 0.8)
    root.wm_attributes("-disabled", True)

    canvas = tk.Canvas(root, width=100, height=100, bg="white", highlightthickness=0)
    canvas.pack()

    def update_overlay():
        global ring_trigger
        with overlay_lock:
            trigger = ring_trigger
            pos = cursor_pos

        if trigger:
            root.geometry(f"100x100+{pos[0]-50}+{pos[1]-50}")
            root.deiconify()
            for i in range(1, 11):
                canvas.delete("all")
                r = 5 + i * 3
                canvas.create_oval(50-r, 50-r, 50+r, 50+r, outline="#00FF00", width=3)
                root.update()
                time.sleep(0.01)
            canvas.delete("all")
            with overlay_lock:
                ring_trigger = False
            root.withdraw()

        root.after(10, update_overlay)

    root.withdraw()
    update_overlay()
    root.mainloop()

threading.Thread(target=create_overlay, daemon=True).start()

# ---------- MEDIAPIPE ----------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0)

screen_w, screen_h = pyautogui.size()

# ---------- TUNING ----------
TRACKPAD_SCALE = 0.5
TRACKPAD_BUFFER = 0.12
SMOOTHING = 0.18
PIXEL_DEADZONE = 2

LEFT_PINCH_CLOSE = 0.30
LEFT_PINCH_OPEN = 0.45

RIGHT_PINCH_CLOSE = 0.28
RIGHT_PINCH_OPEN = 0.43

GRAB_HOLD_TIME = 0.35

PINCH_STABLE_FRAMES = 2
RELEASE_STABLE_FRAMES = 3

# Scroll settings - RELAXED for easier detection
SCROLL_THRESHOLD = 10        # Pixels to move before scrolling
SCROLL_SPEED = 40.0           # Scroll multiplier
TWO_FINGER_DISTANCE_MAX = 0.20  # Max distance between fingers (INCREASED)
FINGER_EXTENDED_THRESHOLD = 0.075  # Lower threshold (RELAXED)

DEBUG_MODE = True

# ---------- STATE ----------
prev_x, prev_y = 0, 0
pinch_start_time = None
grab_active = False
left_clicked = False
right_active = False

grab_ref_x = grab_ref_y = None

left_pinch_counter = 0
left_release_counter = 0
right_pinch_counter = 0
right_release_counter = 0

scroll_active = False
scroll_ref_y = None

last_frame_time = time.time()
target_fps = 60

def dist3(a, b):
    return math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

print("=" * 60)
print("Hand Gesture Control Started - TWO HAND MODE")
print("=" * 60)
print("LEFT HAND:")
print("  📍 Index finger alone        = Move cursor")
print("  👆 Index + Thumb quick pinch = Left click")
print("  👆 Index + Thumb HOLD (0.35s)= Grab & drag")
print("  ☝️  Middle + Thumb pinch      = Right click")
print("")
print("RIGHT HAND:")
print("  ✌️  Index + Middle extended  = Scroll (move up/down)")
print("=" * 60)
print("TIP: Use BOTH hands simultaneously for best experience!")
print("=" * 60)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    screen_ratio = screen_w / screen_h
    box_h = int(h * TRACKPAD_SCALE)
    box_w = int(box_h * screen_ratio)
    x1, y1 = (w-box_w)//2, (h-box_h)//2

    box_color = (0, 255, 0) if grab_active else (255, 0, 255)
    cv2.rectangle(frame, (x1, y1), (x1+box_w, y1+box_h), box_color, 2)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    left_hand_lm = None
    right_hand_lm = None

    if res.multi_hand_landmarks and res.multi_handedness:
        for idx, hand_landmarks in enumerate(res.multi_hand_landmarks):
            handedness = res.multi_handedness[idx].classification[0].label
            # MediaPipe labels are flipped in mirror view
            if handedness == "Right":  # Actually left hand in mirror
                left_hand_lm = hand_landmarks.landmark
            else:  # Actually right hand in mirror
                right_hand_lm = hand_landmarks.landmark

    # ================= RIGHT HAND: SCROLL =================
    if right_hand_lm is not None:
        lm = right_hand_lm
        index = lm[8]
        middle = lm[12]
        index_mcp = lm[5]
        middle_mcp = lm[9]
        
        # Check finger extension
        index_len = dist3(index, index_mcp)
        middle_len = dist3(middle, middle_mcp)
        
        index_extended = index_len > FINGER_EXTENDED_THRESHOLD
        middle_extended = middle_len > FINGER_EXTENDED_THRESHOLD
        
        # Distance between fingertips
        two_finger_dist = dist3(index, middle)
        two_fingers_together = two_finger_dist < TWO_FINGER_DISTANCE_MAX
        
        # Average Y position for scroll tracking
        avg_fy = (int(index.y * h) + int(middle.y * h)) // 2
        
        # DEBUG: Show detection values
        if DEBUG_MODE:
            cv2.putText(frame, f"R: Idx:{index_len:.3f} Mid:{middle_len:.3f} Dist:{two_finger_dist:.3f}", 
                        (10, h-60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            cv2.putText(frame, f"R: Extended I:{int(index_extended)} M:{int(middle_extended)} Together:{int(two_fingers_together)}", 
                        (10, h-40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        
        if index_extended and middle_extended and two_fingers_together:
            # SCROLL MODE
            if not scroll_active:
                scroll_active = True
                scroll_ref_y = avg_fy
                print(f"RIGHT HAND: SCROLL ACTIVATED - idx:{index_len:.3f} mid:{middle_len:.3f} dist:{two_finger_dist:.3f}")
            else:
                # Perform scroll
                dy = avg_fy - scroll_ref_y
                if abs(dy) > SCROLL_THRESHOLD:
                    scroll_amount = int(-dy / SCROLL_THRESHOLD * SCROLL_SPEED)
                    pyautogui.scroll(scroll_amount)
                    scroll_ref_y = avg_fy
                    print(f"RIGHT HAND: Scrolling {scroll_amount} (dy={dy})")
        else:
            if scroll_active:
                scroll_active = False
                scroll_ref_y = None
                print(f"RIGHT HAND: SCROLL DEACTIVATED")

    # ================= LEFT HAND: CURSOR & CLICKS =================
    if left_hand_lm is not None:
        lm = left_hand_lm
        index, middle, thumb = lm[8], lm[12], lm[4]
        index_mcp, middle_mcp = lm[5], lm[9]

        fx, fy = int(index.x*w), int(index.y*h)

        index_len = dist3(index, index_mcp)
        middle_len = dist3(middle, middle_mcp)

        # ================= CURSOR =================
        if grab_active:
            # DRAG MODE
            dx = (fx - grab_ref_x) * 1.2
            dy = (fy - grab_ref_y) * 1.2
            pyautogui.moveRel(int(dx), int(dy))
            grab_ref_x, grab_ref_y = fx, fy
            with overlay_lock:
                cursor_pos = pyautogui.position()
        else:
            # NORMAL MODE
            rel_x = clamp((fx-x1)/box_w, -TRACKPAD_BUFFER, 1+TRACKPAD_BUFFER)
            rel_y = clamp((fy-y1)/box_h, -TRACKPAD_BUFFER, 1+TRACKPAD_BUFFER)
            rel_x, rel_y = clamp(rel_x, 0, 1), clamp(rel_y, 0, 1)

            tx, ty = rel_x*screen_w, rel_y*screen_h
            
            if prev_x == 0 and prev_y == 0:
                prev_x, prev_y = tx, ty
            
            dx = tx - prev_x
            dy = ty - prev_y
            if abs(dx) < PIXEL_DEADZONE and abs(dy) < PIXEL_DEADZONE:
                tx, ty = prev_x, prev_y
            
            curr_x = prev_x + (tx - prev_x) * SMOOTHING
            curr_y = prev_y + (ty - prev_y) * SMOOTHING
            
            pyautogui.moveTo(int(curr_x), int(curr_y))
            prev_x, prev_y = curr_x, curr_y
            with overlay_lock:
                cursor_pos = (int(curr_x), int(curr_y))

        # ================= LEFT CLICK / GRAB =================
        left_ratio = dist3(index, thumb) / max(index_len, 1e-6)
        left_pinching = left_ratio < LEFT_PINCH_CLOSE
        left_released = left_ratio > LEFT_PINCH_OPEN
        now = time.time()

        if left_pinching:
            left_pinch_counter += 1
            left_release_counter = 0
        elif left_released:
            left_release_counter += 1
            left_pinch_counter = 0

        if left_pinch_counter >= PINCH_STABLE_FRAMES and pinch_start_time is None:
            pinch_start_time = now
            if DEBUG_MODE:
                print(f"LEFT HAND: Pinch detected - {left_ratio:.3f}")

        if pinch_start_time is not None and not grab_active:
            if (now - pinch_start_time) > GRAB_HOLD_TIME and left_pinch_counter >= PINCH_STABLE_FRAMES:
                pyautogui.mouseDown()
                grab_active = True
                grab_ref_x, grab_ref_y = fx, fy
                print(f"LEFT HAND: GRAB STARTED")

        if left_release_counter >= RELEASE_STABLE_FRAMES:
            if grab_active:
                pyautogui.mouseUp()
                grab_active = False
                print(f"LEFT HAND: GRAB RELEASED")
                left_release_counter = 0
            elif pinch_start_time is not None and not left_clicked:
                pyautogui.click()
                with overlay_lock:
                    ring_trigger = True
                    cursor_pos = pyautogui.position()
                if DEBUG_MODE:
                    print(f"LEFT HAND: LEFT CLICK")
                left_clicked = True
                left_release_counter = 0
            
            pinch_start_time = None
            left_clicked = False

        # ================= RIGHT CLICK =================
        right_ratio = dist3(middle, thumb) / max(middle_len, 1e-6)
        right_pinching = right_ratio < RIGHT_PINCH_CLOSE
        right_released = right_ratio > RIGHT_PINCH_OPEN

        if right_pinching:
            right_pinch_counter += 1
            right_release_counter = 0
        elif right_released:
            right_release_counter += 1
            right_pinch_counter = 0

        if right_pinch_counter >= PINCH_STABLE_FRAMES and not right_active:
            pyautogui.click(button="right")
            with overlay_lock:
                ring_trigger = True
                cursor_pos = pyautogui.position()
            right_active = True
            if DEBUG_MODE:
                print(f"LEFT HAND: RIGHT CLICK")

        if right_release_counter >= RELEASE_STABLE_FRAMES and right_active:
            right_active = False
            right_release_counter = 0

    # ================= DEBUG INFO =================
    if DEBUG_MODE:
        y_offset = 60
        
        # Show which hands are detected
        hands_detected = []
        if left_hand_lm is not None:
            hands_detected.append("LEFT")
        if right_hand_lm is not None:
            hands_detected.append("RIGHT")
        
        hands_text = " + ".join(hands_detected) if hands_detected else "NONE"
        cv2.putText(frame, f"Hands: {hands_text}", 
                    (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 25
        
        # Right hand - scroll info
        if right_hand_lm is not None:
            if scroll_active:
                cv2.putText(frame, "RIGHT HAND: SCROLLING ACTIVE", 
                            (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "RIGHT HAND: Hold 2 fingers together", 
                            (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
            y_offset += 30
        
        # Left hand - control info
        if left_hand_lm is not None:
            left_ratio = dist3(index, thumb) / max(index_len, 1e-6)
            left_color = (0, 255, 0) if left_pinch_counter >= PINCH_STABLE_FRAMES else (100, 100, 100)
            status_text = "DETECTED ✓" if left_pinch_counter >= PINCH_STABLE_FRAMES else f"{left_pinch_counter}/{PINCH_STABLE_FRAMES}"
            cv2.putText(frame, f"LEFT L (I+T): {left_ratio:.3f} < {LEFT_PINCH_CLOSE} | {status_text}", 
                        (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, left_color, 2 if left_pinch_counter >= PINCH_STABLE_FRAMES else 1)
            y_offset += 25
            
            right_ratio = dist3(middle, thumb) / max(middle_len, 1e-6)
            right_color = (0, 255, 0) if right_pinch_counter >= PINCH_STABLE_FRAMES else (100, 100, 100)
            status_text = "DETECTED ✓" if right_pinch_counter >= PINCH_STABLE_FRAMES else f"{right_pinch_counter}/{PINCH_STABLE_FRAMES}"
            cv2.putText(frame, f"LEFT R (M+T): {right_ratio:.3f} < {RIGHT_PINCH_CLOSE} | {status_text}", 
                        (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, right_color, 2 if right_pinch_counter >= PINCH_STABLE_FRAMES else 1)
            y_offset += 25
            
            if pinch_start_time is not None and not grab_active:
                hold_time = time.time() - pinch_start_time
                timer_color = (0, 255, 255) if hold_time < GRAB_HOLD_TIME else (0, 255, 0)
                progress = int((hold_time / GRAB_HOLD_TIME) * 20)
                bar = "█" * progress + "░" * (20 - progress)
                cv2.putText(frame, f"Hold: {hold_time:.2f}s [{bar}]", 
                            (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, timer_color, 1)
                y_offset += 25
            
            if grab_active and left_release_counter > 0:
                cv2.putText(frame, f"Release countdown: {left_release_counter}/{RELEASE_STABLE_FRAMES}", 
                            (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    # Status display
    status = []
    if scroll_active:
        status.append("RIGHT: SCROLLING")
    if grab_active:
        status.append("LEFT: GRABBING")
    elif left_pinch_counter >= PINCH_STABLE_FRAMES and left_hand_lm is not None:
        status.append("LEFT: L-PINCH")
    if right_active:
        status.append("LEFT: R-CLICK")
    
    status_text = " | ".join(status) if status else "READY"
    cv2.putText(frame, status_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # No hands - reset
    if left_hand_lm is None:
        if grab_active:
            pyautogui.mouseUp()
            grab_active = False
        left_pinch_counter = 0
        right_pinch_counter = 0
    
    if right_hand_lm is None:
        if scroll_active:
            scroll_active = False
            scroll_ref_y = None

    cv2.imshow("Hand Gesture Control", frame)

    # Frame rate control
    current_time = time.time()
    elapsed = current_time - last_frame_time
    if elapsed < 1/target_fps:
        time.sleep(1/target_fps - elapsed)
    last_frame_time = time.time()

    if cv2.waitKey(1) == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
print("\nHand Gesture Control Stopped")
