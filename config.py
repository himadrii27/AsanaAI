# ── FormFix AI · Global Configuration ────────────────────────────────────────

# ── Camera ────────────────────────────────────────────────────────────────────
CAMERA_INDEX      = 0        # 0 = default webcam; change to video file path for testing
FRAME_WIDTH       = 1280
FRAME_HEIGHT      = 720
TARGET_FPS        = 30

# ── MediaPipe Pose ─────────────────────────────────────────────────────────────
MP_MODEL_COMPLEXITY      = 1     # 0=lite  1=full  2=heavy
MP_SMOOTH_LANDMARKS      = True
MP_MIN_DETECTION_CONF    = 0.7
MP_MIN_TRACKING_CONF     = 0.6

# ── Feedback ───────────────────────────────────────────────────────────────────
FEEDBACK_COOLDOWN_SEC    = 2.5   # seconds between repeated voice cues
VOICE_ENABLED            = True
VOICE_RATE               = 160   # words per minute

# ── Overlay colours (BGR) ─────────────────────────────────────────────────────
COLOR_CORRECT   = (0,   220,  60)   # green
COLOR_INCORRECT = (0,    60, 255)   # red
COLOR_NEUTRAL   = (220, 220, 220)   # light grey
COLOR_TEXT_BG   = (20,   20,  20)   # near-black
COLOR_ACCENT    = (255, 165,   0)   # orange

# ── Rep counter ───────────────────────────────────────────────────────────────
REP_SMOOTHING_FRAMES     = 5     # frames to smooth angle signal before counting

# ── Sessions / persistence ────────────────────────────────────────────────────
SESSIONS_DIR    = "data/sessions"
MAX_SESSIONS    = 50             # keep the last N sessions on disk
