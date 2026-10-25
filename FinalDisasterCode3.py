# ============================================================
# RAKSHAK v3
# Autonomous Search & Rescue Intelligence Prototype
#
# YOLOv8 + ByteTrack + Fire/Smoke Detection
# + Survivor Risk Engine + Tactical Command Dashboard
# ============================================================

import cv2
import math
import time
import tkinter as tk
from ultralytics import YOLO


# ============================================================
# CONFIGURATION
# ============================================================

PERSON_MODEL = "yolov8n.pt"

# IMPORTANT:
# Put the SAME fire/smoke model that is already working.
HAZARD_MODEL = "fire_smoke.pt"

# Your video / webcam
VIDEO_SOURCE = r"C://Users//Aditya//Downloads//WhatsApp Video 2026-08-31 at 00.20.20.mp4"
# Example webcam:
# VIDEO_SOURCE = 0


# ------------------------------------------------------------
# PERSON DETECTION
# ------------------------------------------------------------

PERSON_CONF = 0.30
PERSON_IMGSZ = 640


# ------------------------------------------------------------
# FIRE / SMOKE
# ------------------------------------------------------------

HAZARD_CONF = 0.20
HAZARD_IMGSZ = 640


# ------------------------------------------------------------
# TRACK MEMORY
# ------------------------------------------------------------

# How long a survivor remains in the system after disappearing
MAX_MISSING_TIME = 8.0


# ------------------------------------------------------------
# HAZARD DISTANCE
# ------------------------------------------------------------

CRITICAL_DISTANCE = 100
HIGH_DISTANCE = 200
MEDIUM_DISTANCE = 350


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------

DASHBOARD_WIDTH = 620
DASHBOARD_HEIGHT = 850

VIDEO_WIDTH = 1000
VIDEO_HEIGHT = 760


# ============================================================
# RAKSHAK COLOURS
# ============================================================

BG = "#080c10"
PANEL = "#0d1319"
PANEL_2 = "#111820"
BORDER = "#202b34"

TEXT = "#e8eef2"
MUTED = "#7d8a94"

GREEN = "#42f59b"
RED = "#ff4d5e"
ORANGE = "#ffad42"
YELLOW = "#f5d76e"
BLUE = "#54b8ff"
CYAN = "#55e6e6"


# ============================================================
# INITIALIZATION
# ============================================================

print()
print("================================================")
print("              RAKSHAK v3")
print("     RESCUE INTELLIGENCE SYSTEM")
print("================================================")
print()

print("[SYSTEM] Loading survivor model...")

person_model = YOLO(PERSON_MODEL)

print("[SYSTEM] Loading hazard model...")

hazard_model = YOLO(HAZARD_MODEL)

print("[SYSTEM] Models loaded.")
print()


# ============================================================
# VIDEO
# ============================================================

cap = cv2.VideoCapture(VIDEO_SOURCE)

if not cap.isOpened():

    print("[ERROR] Could not open video source.")

    raise SystemExit


video_fps = cap.get(cv2.CAP_PROP_FPS)

if video_fps <= 0:

    video_fps = 30


# ============================================================
# GLOBAL DATA
# ============================================================

persons = {}

total_people_seen = 0

mission_start = time.time()

selected_id = None

frame_count = 0

fps_counter = 0

fps_timer = time.time()

display_fps = 0.0


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clamp(value, minimum, maximum):

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


def distance_between(x1, y1, x2, y2):

    return math.sqrt(
        (x1 - x2) ** 2 +
        (y1 - y2) ** 2
    )


def format_time(seconds):

    seconds = int(seconds)

    minutes = seconds // 60

    seconds = seconds % 60

    return f"{minutes:02d}:{seconds:02d}"


# ============================================================
# RISK ENGINE
# ============================================================

def calculate_risk(person, hazards):

    """
    RAKSHAK Rescue Risk Engine

    Factors:

        Hazard proximity       40%
        Hazard severity        20%
        Survivor state         15%
        Detection confidence   10%
        Visibility             15%

    Returns:

        risk
        priority
        nearest hazard
        nearest distance
    """

    px = person["cx"]
    py = person["cy"]

    nearest_distance = float("inf")

    nearest_hazard = "NONE"

    # --------------------------------------------------------
    # FIND NEAREST HAZARD
    # --------------------------------------------------------

    for hazard in hazards:

        distance = distance_between(
            px,
            py,
            hazard["cx"],
            hazard["cy"]
        )

        if distance < nearest_distance:

            nearest_distance = distance

            nearest_hazard = hazard["type"]


    # --------------------------------------------------------
    # HAZARD PROXIMITY
    # --------------------------------------------------------

    if nearest_hazard == "NONE":

        proximity_score = 0

    elif nearest_distance <= CRITICAL_DISTANCE:

        proximity_score = 100

    elif nearest_distance <= HIGH_DISTANCE:

        proximity_score = 75

    elif nearest_distance <= MEDIUM_DISTANCE:

        proximity_score = 45

    else:

        proximity_score = 10


    # --------------------------------------------------------
    # HAZARD SEVERITY
    # --------------------------------------------------------

    if nearest_hazard == "FIRE":

        severity_score = 100

    elif nearest_hazard == "SMOKE":

        severity_score = 65

    else:

        severity_score = 0


    # --------------------------------------------------------
    # SURVIVOR STATE
    # --------------------------------------------------------

    if person["stationary"]:

        state_score = 100

    else:

        state_score = 25


    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence_score = (
        person["confidence"] * 100
    )


    # --------------------------------------------------------
    # VISIBILITY
    # --------------------------------------------------------

    missing_time = (
        time.time() -
        person["last_seen"]
    )

    if missing_time <= 1:

        visibility_score = 0

    elif missing_time <= 3:

        visibility_score = 25

    elif missing_time <= 5:

        visibility_score = 60

    else:

        visibility_score = 100


    # --------------------------------------------------------
    # BASE HAZARD RISK
    # --------------------------------------------------------

    hazard_risk = (

        proximity_score * 0.40 +

        severity_score * 0.20

    )


    # --------------------------------------------------------
    # FINAL RISK
    # --------------------------------------------------------

    risk = (

        hazard_risk +

        state_score * 0.15 +

        confidence_score * 0.10 +

        visibility_score * 0.15

    )


    risk = int(
        clamp(
            risk,
            0,
            100
        )
    )


    # --------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------

    if risk >= 80:

        priority = "CRITICAL"

    elif risk >= 60:

        priority = "HIGH"

    elif risk >= 35:

        priority = "MEDIUM"

    else:

        priority = "LOW"


    return (
        risk,
        priority,
        nearest_hazard,
        nearest_distance
    )


# ============================================================
# TKINTER ROOT
# ============================================================

root = tk.Tk()

root.title(
    "RAKSHAK | Rescue Intelligence Command Center"
)

root.configure(
    bg=BG
)

root.geometry(
    f"{DASHBOARD_WIDTH}x{DASHBOARD_HEIGHT}"
)

root.resizable(
    False,
    False
)


# ============================================================
# SCREEN POSITION
# ============================================================

root.update_idletasks()

screen_width = root.winfo_screenwidth()

screen_height = root.winfo_screenheight()

total_width = (
    VIDEO_WIDTH +
    DASHBOARD_WIDTH
)

start_x = (
    screen_width -
    total_width
) // 2

if start_x < 0:

    start_x = 0

start_y = max(
    0,
    (
        screen_height -
        DASHBOARD_HEIGHT
    ) // 2
)


# ============================================================
# MOVE DASHBOARD
# ============================================================

root.geometry(
    f"{DASHBOARD_WIDTH}x{DASHBOARD_HEIGHT}+"
    f"{start_x + VIDEO_WIDTH}+{start_y}"
)


# ============================================================
# STYLE HELPERS
# ============================================================

def label(
    parent,
    text,
    size=10,
    weight="normal",
    color=TEXT,
    bg=BG,
    anchor="w"
):

    return tk.Label(
        parent,
        text=text,
        font=("Segoe UI", size, weight),
        fg=color,
        bg=bg,
        anchor=anchor
    )


def panel(parent, bg=PANEL):

    return tk.Frame(
        parent,
        bg=bg,
        highlightbackground=BORDER,
        highlightthickness=1
    )


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    root,
    bg=BG
)

header.pack(
    fill="x",
    padx=24,
    pady=(22, 10)
)


title_frame = tk.Frame(
    header,
    bg=BG
)

title_frame.pack(
    side="left"
)


label(
    title_frame,
    "RAKSHAK",
    25,
    "bold",
    TEXT,
    BG
).pack(
    anchor="w"
)


label(
    title_frame,
    "AUTONOMOUS SEARCH & RESCUE INTELLIGENCE",
    8,
    "bold",
    MUTED,
    BG
).pack(
    anchor="w",
    pady=(1, 0)
)


# ------------------------------------------------------------
# LIVE STATUS
# ------------------------------------------------------------

status_frame = tk.Frame(
    header,
    bg=BG
)

status_frame.pack(
    side="right",
    anchor="n"
)


status_dot = tk.Label(
    status_frame,
    text="●",
    font=("Segoe UI", 13),
    fg=GREEN,
    bg=BG
)

status_dot.pack(
    side="left"
)


status_text = label(
    status_frame,
    " SYSTEM ONLINE",
    9,
    "bold",
    GREEN,
    BG
)

status_text.pack(
    side="left"
)


# ============================================================
# MISSION BAR
# ============================================================

mission_bar = tk.Frame(
    root,
    bg=PANEL_2,
    height=48
)

mission_bar.pack(
    fill="x",
    padx=20,
    pady=(0, 12)
)

mission_bar.pack_propagate(
    False
)


label(
    mission_bar,
    "●  MISSION ACTIVE",
    9,
    "bold",
    GREEN,
    PANEL_2
).pack(
    side="left",
    padx=14
)


label(
    mission_bar,
    "UAV-01",
    9,
    "bold",
    BLUE,
    PANEL_2
).pack(
    side="right",
    padx=14
)


mission_time_label = label(
    mission_bar,
    "00:00",
    9,
    "bold",
    TEXT,
    PANEL_2
)

mission_time_label.pack(
    side="right",
    padx=12
)


# ============================================================
# OVERVIEW
# ============================================================

label(
    root,
    "MISSION OVERVIEW",
    9,
    "bold",
    MUTED,
    BG
).pack(
    anchor="w",
    padx=24,
    pady=(2, 7)
)


overview = tk.Frame(
    root,
    bg=BG
)

overview.pack(
    fill="x",
    padx=20
)


def create_metric(parent, name):

    frame = tk.Frame(
        parent,
        bg=PANEL,
        height=72
    )

    frame.pack(
        side="left",
        fill="x",
        expand=True,
        padx=3
    )

    frame.pack_propagate(False)

    tk.Label(
        frame,
        text=name,
        font=("Segoe UI", 7, "bold"),
        fg=MUTED,
        bg=PANEL
    ).pack(
        anchor="w",
        padx=10,
        pady=(9, 0)
    )

    value = tk.Label(
        frame,
        text="0",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT,
        bg=PANEL
    )

    value.pack(
        anchor="w",
        padx=10
    )

    return value


active_label = create_metric(
    overview,
    "ACTIVE"
)

critical_label = create_metric(
    overview,
    "CRITICAL"
)

fire_label = create_metric(
    overview,
    "FIRE"
)

smoke_label = create_metric(
    overview,
    "SMOKE"
)


# ============================================================
# PRIORITY HEADER
# ============================================================

label(
    root,
    "RESCUE PRIORITY",
    9,
    "bold",
    MUTED,
    BG
).pack(
    anchor="w",
    padx=24,
    pady=(18, 7)
)


priority_container = tk.Frame(
    root,
    bg=BG
)

priority_container.pack(
    fill="x",
    padx=20
)


# ============================================================
# SELECTED SURVIVOR
# ============================================================

label(
    root,
    "SURVIVOR INTELLIGENCE",
    9,
    "bold",
    MUTED,
    BG
).pack(
    anchor="w",
    padx=24,
    pady=(18, 7)
)


selected_panel = panel(
    root,
    PANEL
)

selected_panel.pack(
    fill="x",
    padx=20
)


# ------------------------------------------------------------
# SELECTED HEADER
# ------------------------------------------------------------

selected_header = tk.Frame(
    selected_panel,
    bg=PANEL
)

selected_header.pack(
    fill="x",
    padx=14,
    pady=(12, 8)
)


selected_name = label(
    selected_header,
    "NO SURVIVOR SELECTED",
    15,
    "bold",
    TEXT,
    PANEL
)

selected_name.pack(
    side="left"
)


selected_priority = label(
    selected_header,
    "—",
    8,
    "bold",
    MUTED,
    PANEL
)

selected_priority.pack(
    side="right"
)


# ------------------------------------------------------------
# RISK BAR
# ------------------------------------------------------------

risk_frame = tk.Frame(
    selected_panel,
    bg=PANEL
)

risk_frame.pack(
    fill="x",
    padx=14
)


risk_canvas = tk.Canvas(
    risk_frame,
    height=12,
    bg="#202830",
    highlightthickness=0
)

risk_canvas.pack(
    fill="x",
    side="left",
    expand=True
)


risk_value_label = label(
    risk_frame,
    "0",
    17,
    "bold",
    TEXT,
    PANEL
)

risk_value_label.pack(
    side="right",
    padx=(12, 0)
)


# ------------------------------------------------------------
# SURVIVOR DATA
# ------------------------------------------------------------

info_frame = tk.Frame(
    selected_panel,
    bg=PANEL
)

info_frame.pack(
    fill="x",
    padx=14,
    pady=12
)


selected_threat = label(
    info_frame,
    "THREAT       —",
    9,
    "bold",
    TEXT,
    PANEL
)

selected_threat.pack(
    anchor="w",
    pady=2
)


selected_distance = label(
    info_frame,
    "PROXIMITY    —",
    9,
    "bold",
    TEXT,
    PANEL
)

selected_distance.pack(
    anchor="w",
    pady=2
)


selected_state = label(
    info_frame,
    "STATE        —",
    9,
    "bold",
    TEXT,
    PANEL
)

selected_state.pack(
    anchor="w",
    pady=2
)


selected_conf = label(
    info_frame,
    "CONFIDENCE   —",
    9,
    "bold",
    TEXT,
    PANEL
)

selected_conf.pack(
    anchor="w",
    pady=2
)


selected_last_seen = label(
    info_frame,
    "LAST SEEN    —",
    9,
    "bold",
    TEXT,
    PANEL
)

selected_last_seen.pack(
    anchor="w",
    pady=2
)


# ============================================================
# SYSTEM STATUS
# ============================================================

label(
    root,
    "SYSTEM TELEMETRY",
    9,
    "bold",
    MUTED,
    BG
).pack(
    anchor="w",
    padx=24,
    pady=(18, 7)
)


telemetry = panel(
    root,
    PANEL
)

telemetry.pack(
    fill="x",
    padx=20
)


telemetry_left = tk.Frame(
    telemetry,
    bg=PANEL
)

telemetry_left.pack(
    side="left",
    padx=14,
    pady=10
)


telemetry_right = tk.Frame(
    telemetry,
    bg=PANEL
)

telemetry_right.pack(
    side="right",
    padx=14,
    pady=10
)


tracking_status = label(
    telemetry_left,
    "TRACKING       ACTIVE",
    8,
    "bold",
    GREEN,
    PANEL
)

tracking_status.pack(
    anchor="w"
)


person_status = label(
    telemetry_left,
    "PERSON AI      ONLINE",
    8,
    "bold",
    GREEN,
    PANEL
)

person_status.pack(
    anchor="w",
    pady=(5, 0)
)


hazard_status = label(
    telemetry_right,
    "HAZARD AI      ONLINE",
    8,
    "bold",
    GREEN,
    PANEL
)

hazard_status.pack(
    anchor="w"
)


fps_status = label(
    telemetry_right,
    "PROCESSING     0 FPS",
    8,
    "bold",
    TEXT,
    PANEL
)

fps_status.pack(
    anchor="w",
    pady=(5, 0)
)


# ============================================================
# CLICKABLE SURVIVOR CARD
# ============================================================

def create_survivor_card(pid, person):

    risk = person["risk"]

    priority = person["priority"]

    hazard = person["hazard"]

    # --------------------------------------------------------
    # PRIORITY COLOUR
    # --------------------------------------------------------

    if priority == "CRITICAL":

        accent = RED

    elif priority == "HIGH":

        accent = ORANGE

    elif priority == "MEDIUM":

        accent = YELLOW

    else:

        accent = GREEN


    # --------------------------------------------------------
    # CARD
    # --------------------------------------------------------

    card = tk.Frame(
        priority_container,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1,
        height=54,
        cursor="hand2"
    )

    card.pack(
        fill="x",
        pady=2
    )

    card.pack_propagate(
        False
    )


    # --------------------------------------------------------
    # ACCENT
    # --------------------------------------------------------

    accent_frame = tk.Frame(
        card,
        bg=accent,
        width=4
    )

    accent_frame.pack(
        side="left",
        fill="y"
    )


    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    id_label = tk.Label(
        card,
        text=f"S{pid}",
        font=("Segoe UI", 11, "bold"),
        fg=TEXT,
        bg=PANEL,
        width=5,
        anchor="w"
    )

    id_label.pack(
        side="left",
        padx=(12, 0)
    )


    # --------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------

    priority_label = tk.Label(
        card,
        text=priority,
        font=("Segoe UI", 7, "bold"),
        fg=accent,
        bg=PANEL,
        width=11,
        anchor="w"
    )

    priority_label.pack(
        side="left"
    )


    # --------------------------------------------------------
    # HAZARD
    # --------------------------------------------------------

    hazard_label = tk.Label(
        card,
        text=hazard,
        font=("Segoe UI", 7, "bold"),
        fg=MUTED,
        bg=PANEL,
        width=9,
        anchor="w"
    )

    hazard_label.pack(
        side="left"
    )


    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    risk_label = tk.Label(
        card,
        text=f"{risk}",
        font=("Segoe UI", 12, "bold"),
        fg=accent,
        bg=PANEL,
        width=5,
        anchor="e"
    )

    risk_label.pack(
        side="right",
        padx=12
    )


    # --------------------------------------------------------
    # CLICK
    # --------------------------------------------------------

    widgets = [
        card,
        accent_frame,
        id_label,
        priority_label,
        hazard_label,
        risk_label
    ]


    def select(event=None):

        global selected_id

        selected_id = pid

        update_selected_survivor()


    for widget in widgets:

        widget.bind(
            "<Button-1>",
            select
        )


# ============================================================
# UPDATE SELECTED SURVIVOR
# ============================================================

def update_selected_survivor():

    if selected_id is None:

        return

    if selected_id not in persons:

        return

    person = persons[selected_id]

    priority = person["priority"]

    risk = person["risk"]


    # --------------------------------------------------------
    # COLOUR
    # --------------------------------------------------------

    if priority == "CRITICAL":

        accent = RED

    elif priority == "HIGH":

        accent = ORANGE

    elif priority == "MEDIUM":

        accent = YELLOW

    else:

        accent = GREEN


    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    selected_name.config(
        text=f"SURVIVOR  S{selected_id}"
    )

    selected_priority.config(
        text=priority,
        fg=accent
    )


    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    risk_value_label.config(
        text=f"{risk}/100",
        fg=accent
    )


    # --------------------------------------------------------
    # RISK BAR
    # --------------------------------------------------------

    risk_canvas.delete(
        "all"
    )

    width = risk_canvas.winfo_width()

    if width <= 1:

        width = 350

    fill_width = int(
        width *
        risk /
        100
    )

    risk_canvas.create_rectangle(
        0,
        0,
        fill_width,
        12,
        fill=accent,
        outline=""
    )


    # --------------------------------------------------------
    # THREAT
    # --------------------------------------------------------

    selected_threat.config(
        text=f"THREAT       {person['hazard']}"
    )


    # --------------------------------------------------------
    # DISTANCE
    # --------------------------------------------------------

    if person["distance"] == float("inf"):

        distance_text = "—"

    else:

        distance_text = (
            f"{person['distance']:.0f} px"
        )


    selected_distance.config(
        text=f"PROXIMITY    {distance_text}"
    )


    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    if person["stationary"]:

        state = "STATIONARY"

    else:

        state = "MOVING"


    selected_state.config(
        text=f"STATE        {state}"
    )


    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    selected_conf.config(
        text=(
            f"CONFIDENCE   "
            f"{person['confidence']:.2f}"
        )
    )


    # --------------------------------------------------------
    # LAST SEEN
    # --------------------------------------------------------

    missing = (
        time.time() -
        person["last_seen"]
    )


    if missing < 1:

        last_seen = "NOW"

    else:

        last_seen = f"{missing:.1f}s ago"


    selected_last_seen.config(
        text=f"LAST SEEN    {last_seen}"
    )


# ============================================================
# UPDATE PRIORITY QUEUE
# ============================================================

def update_priority_queue():

    # --------------------------------------------------------
    # CLEAR OLD CARDS
    # --------------------------------------------------------

    for widget in priority_container.winfo_children():

        widget.destroy()


    # --------------------------------------------------------
    # COLLECT ACTIVE
    # --------------------------------------------------------

    active = []

    now = time.time()

    for pid, person in persons.items():

        if (
            now -
            person["last_seen"]
        ) <= MAX_MISSING_TIME:

            active.append(
                (
                    pid,
                    person
                )
            )


    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    active.sort(
        key=lambda item:
        item[1]["risk"],
        reverse=True
    )


    # --------------------------------------------------------
    # LIMIT DISPLAY
    # --------------------------------------------------------

    display_people = active[:8]


    # --------------------------------------------------------
    # CARDS
    # --------------------------------------------------------

    for pid, person in display_people:

        create_survivor_card(
            pid,
            person
        )


    # --------------------------------------------------------
    # EMPTY
    # --------------------------------------------------------

    if not display_people:

        empty = label(
            priority_container,
            "NO ACTIVE SURVIVORS",
            9,
            "bold",
            MUTED,
            BG
        )

        empty.pack(
            pady=18
        )


# ============================================================
# UPDATE DASHBOARD
# ============================================================

def update_dashboard(
    fire_count,
    smoke_count
):

    global selected_id


    # --------------------------------------------------------
    # CURRENT TIME
    # --------------------------------------------------------

    now = time.time()


    # --------------------------------------------------------
    # ACTIVE PEOPLE
    # --------------------------------------------------------

    active_people = []

    for pid, person in persons.items():

        if (
            now -
            person["last_seen"]
        ) <= MAX_MISSING_TIME:

            active_people.append(
                person
            )


    # --------------------------------------------------------
    # CRITICAL
    # --------------------------------------------------------

    critical = 0

    for person in active_people:

        if person["priority"] == "CRITICAL":

            critical += 1


    # --------------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------------

    active_label.config(
        text=str(
            len(active_people)
        )
    )

    critical_label.config(
        text=str(
            critical
        )
    )

    fire_label.config(
        text=str(
            fire_count
        )
    )

    smoke_label.config(
        text=str(
            smoke_count
        )
    )


    # --------------------------------------------------------
    # MISSION TIMER
    # --------------------------------------------------------

    mission_time_label.config(
        text=format_time(
            time.time() -
            mission_start
        )
    )


    # --------------------------------------------------------
    # FPS
    # --------------------------------------------------------

    fps_status.config(
        text=(
            f"PROCESSING     "
            f"{display_fps:.1f} FPS"
        )
    )


    # --------------------------------------------------------
    # HAZARD STATUS
    # --------------------------------------------------------

    if fire_count > 0 or smoke_count > 0:

        hazard_status.config(
            text="HAZARD AI      THREAT DETECTED",
            fg=RED
        )

    else:

        hazard_status.config(
            text="HAZARD AI      NO THREATS",
            fg=GREEN
        )


    # --------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------

    update_priority_queue()


    # --------------------------------------------------------
    # SELECTED
    # --------------------------------------------------------

    if selected_id is not None:

        if selected_id in persons:

            update_selected_survivor()


    # --------------------------------------------------------
    # ROOT UPDATE
    # --------------------------------------------------------

    root.update_idletasks()

    root.update()


# ============================================================
# OPENCV WINDOW
# ============================================================

cv2.namedWindow(
    "RAKSHAK | LIVE UAV FEED",
    cv2.WINDOW_NORMAL
)

cv2.resizeWindow(
    "RAKSHAK | LIVE UAV FEED",
    VIDEO_WIDTH,
    VIDEO_HEIGHT
)

cv2.moveWindow(
    "RAKSHAK | LIVE UAV FEED",
    start_x,
    start_y
)


# ============================================================
# MAIN PROCESSING LOOP
# ============================================================

while True:

    ret, frame = cap.read()


    # --------------------------------------------------------
    # VIDEO END
    # --------------------------------------------------------

    if not ret:

        print("[SYSTEM] Video finished.")

        break


    frame_count += 1

    fps_counter += 1


    current_time = time.time()


    # ========================================================
    # PERSON DETECTION + BYTE TRACK
    # ========================================================

    person_results = person_model.track(

        frame,

        persist=True,

        tracker="bytetrack.yaml",

        classes=[0],

        conf=PERSON_CONF,

        imgsz=PERSON_IMGSZ,

        verbose=False

    )


    person_result = person_results[0]


    # ========================================================
    # HAZARD DETECTION
    # ========================================================

    hazard_results = hazard_model.predict(

        frame,

        conf=HAZARD_CONF,

        imgsz=HAZARD_IMGSZ,

        verbose=False

    )


    hazard_result = hazard_results[0]


    # ========================================================
    # HAZARD LIST
    # ========================================================

    hazards = []

    fire_count = 0

    smoke_count = 0


    # ========================================================
    # PROCESS HAZARDS
    # ========================================================

    if hazard_result.boxes is not None:

        for box in hazard_result.boxes:

            confidence = float(
                box.conf[0]
            )


            cls = int(
                box.cls[0]
            )


            name = (
                hazard_model.names[cls]
                .lower()
            )


            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )


            cx = int(
                (x1 + x2) / 2
            )


            cy = int(
                (y1 + y2) / 2
            )


            # ------------------------------------------------
            # CLASSIFY
            # ------------------------------------------------

            if "fire" in name:

                hazard_type = "FIRE"

                fire_count += 1

            elif "smoke" in name:

                hazard_type = "SMOKE"

                smoke_count += 1

            else:

                hazard_type = name.upper()


            hazards.append({

                "type": hazard_type,

                "cx": cx,

                "cy": cy,

                "conf": confidence,

                "box": (
                    x1,
                    y1,
                    x2,
                    y2
                )

            })


    # ========================================================
    # DRAW HAZARDS
    # ========================================================

    for hazard in hazards:

        x1, y1, x2, y2 = hazard["box"]


        if hazard["type"] == "FIRE":

            box_color = (
                0,
                0,
                255
            )

        elif hazard["type"] == "SMOKE":

            box_color = (
                255,
                170,
                0
            )

        else:

            box_color = (
                255,
                255,
                255
            )


        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            box_color,

            2

        )


        cv2.putText(

            frame,

            (
                f"{hazard['type']} "
                f"{hazard['conf']:.2f}"
            ),

            (
                x1,
                max(
                    22,
                    y1 - 8
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.6,

            box_color,

            2

        )


        cv2.circle(

            frame,

            (
                hazard["cx"],
                hazard["cy"]
            ),

            5,

            box_color,

            -1

        )


    # ========================================================
    # PERSON TRACKING
    # ========================================================

    if person_result.boxes is not None:

        boxes = person_result.boxes


        if boxes.id is not None:

            ids = (
                boxes.id
                .int()
                .cpu()
                .tolist()
            )


            coordinates = (
                boxes.xyxy
                .cpu()
                .tolist()
            )


            confidences = (
                boxes.conf
                .cpu()
                .tolist()
            )


            for pid, coords, confidence in zip(

                ids,

                coordinates,

                confidences

            ):

                x1, y1, x2, y2 = map(
                    int,
                    coords
                )


                cx = int(
                    (x1 + x2) / 2
                )


                cy = int(
                    (y1 + y2) / 2
                )


                # =================================================
                # NEW SURVIVOR
                # =================================================

                if pid not in persons:

                    persons[pid] = {

                        "cx": cx,

                        "cy": cy,

                        "previous_cx": cx,

                        "previous_cy": cy,

                        "last_seen": current_time,

                        "confidence": confidence,

                        "risk": 10,

                        "priority": "LOW",

                        "hazard": "NONE",

                        "distance": float("inf"),

                        "stationary": False

                    }


                    total_people_seen += 1


                else:

                    person = persons[pid]


                    # ------------------------------------------------
                    # MOVEMENT
                    # ------------------------------------------------

                    movement = distance_between(

                        cx,

                        cy,

                        person["previous_cx"],

                        person["previous_cy"]

                    )


                    person["stationary"] = (
                        movement < 5
                    )


                    person["previous_cx"] = cx

                    person["previous_cy"] = cy

                    person["cx"] = cx

                    person["cy"] = cy

                    person["last_seen"] = current_time

                    person["confidence"] = confidence


                # =================================================
                # RISK
                # =================================================

                person = persons[pid]


                (
                    risk,
                    priority,
                    nearest_hazard,
                    nearest_distance

                ) = calculate_risk(

                    person,

                    hazards

                )


                person["risk"] = risk

                person["priority"] = priority

                person["hazard"] = nearest_hazard

                person["distance"] = nearest_distance


                # =================================================
                # DRAW SURVIVOR
                # =================================================

                if priority == "CRITICAL":

                    color = (
                        0,
                        0,
                        255
                    )

                elif priority == "HIGH":

                    color = (
                        0,
                        165,
                        255
                    )

                elif priority == "MEDIUM":

                    color = (
                        0,
                        220,
                        255
                    )

                else:

                    color = (
                        0,
                        255,
                        120
                    )


                cv2.rectangle(

                    frame,

                    (x1, y1),

                    (x2, y2),

                    color,

                    2

                )


                # =================================================
                # SURVIVOR LABEL
                # =================================================

                cv2.rectangle(

                    frame,

                    (
                        x1,
                        max(
                            0,
                            y1 - 30
                        )
                    ),

                    (
                        x1 + 170,
                        y1
                    ),

                    color,

                    -1

                )


                cv2.putText(

                    frame,

                    (
                        f"S{pid}  "
                        f"{priority}"
                    ),

                    (
                        x1 + 5,
                        y1 - 10
                    ),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.52,

                    (
                        0,
                        0,
                        0
                    ),

                    2

                )


                # =================================================
                # RISK
                # =================================================

                cv2.putText(

                    frame,

                    f"RISK {risk}",

                    (
                        x1,
                        y2 + 22
                    ),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.55,

                    color,

                    2

                )


                # =================================================
                # CLOSEST HAZARD CONNECTION
                # =================================================

                closest_hazard = None

                closest_distance = float("inf")


                for hazard in hazards:

                    d = distance_between(

                        cx,

                        cy,

                        hazard["cx"],

                        hazard["cy"]

                    )


                    if d < closest_distance:

                        closest_distance = d

                        closest_hazard = hazard


                if (

                    closest_hazard is not None

                    and

                    closest_distance <= MEDIUM_DISTANCE

                ):

                    hx = closest_hazard["cx"]

                    hy = closest_hazard["cy"]


                    cv2.line(

                        frame,

                        (cx, cy),

                        (hx, hy),

                        (
                            0,
                            165,
                            255
                        ),

                        1

                    )


                    mid_x = int(
                        (cx + hx) / 2
                    )

                    mid_y = int(
                        (cy + hy) / 2
                    )


                    cv2.putText(

                        frame,

                        f"{closest_distance:.0f}px",

                        (
                            mid_x,
                            mid_y
                        ),

                        cv2.FONT_HERSHEY_SIMPLEX,

                        0.42,

                        (
                            0,
                            165,
                            255
                        ),

                        1

                    )


    # ========================================================
    # VIDEO TELEMETRY HEADER
    # ========================================================

    overlay_height = 76


    overlay = frame[
        0:overlay_height,
        0:frame.shape[1]
    ]


    dark_overlay = overlay.copy()


    cv2.rectangle(

        dark_overlay,

        (0, 0),

        (
            frame.shape[1],
            overlay_height
        ),

        (
            10,
            15,
            20
        ),

        -1

    )


    cv2.addWeighted(

        dark_overlay,

        0.90,

        overlay,

        0.10,

        0,

        overlay

    )


    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "RAKSHAK",

        (20, 28),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.75,

        (
            255,
            255,
            255
        ),

        2

    )


    cv2.putText(

        frame,

        "LIVE UAV FEED",

        (20, 52),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.42,

        (
            160,
            175,
            185
        ),

        1

    )


    # --------------------------------------------------------
    # COUNTERS
    # --------------------------------------------------------

    cv2.putText(

        frame,

        f"SURVIVORS {len(persons)}",

        (260, 30),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.48,

        (
            0,
            255,
            120
        ),

        2

    )


    cv2.putText(

        frame,

        f"FIRE {fire_count}",

        (420, 30),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.48,

        (
            0,
            0,
            255
        ),

        2

    )


    cv2.putText(

        frame,

        f"SMOKE {smoke_count}",

        (520, 30),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.48,

        (
            255,
            170,
            0
        ),

        2

    )


    cv2.putText(

        frame,

        f"{display_fps:.1f} FPS",

        (260, 54),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.42,

        (
            220,
            230,
            235
        ),

        1

    )


    # ========================================================
    # FPS CALCULATION
    # ========================================================

    elapsed_fps = (
        time.time() -
        fps_timer
    )


    if elapsed_fps >= 1:

        display_fps = (
            fps_counter /
            elapsed_fps
        )

        fps_counter = 0

        fps_timer = time.time()


    # ========================================================
    # DISPLAY
    # ========================================================

    cv2.imshow(

        "RAKSHAK | LIVE UAV FEED",

        frame

    )


    # ========================================================
    # DASHBOARD
    # ========================================================

    update_dashboard(

        fire_count,

        smoke_count

    )


    # ========================================================
    # KEYBOARD
    # ========================================================

    key = cv2.waitKey(1) & 0xFF


    if key == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()

try:

    root.destroy()

except:

    pass


print()
print("================================================")
print("        RAKSHAK MISSION TERMINATED")
print("================================================")
print(
    f"Total survivors detected: "
    f"{total_people_seen}"
)
print("================================================")