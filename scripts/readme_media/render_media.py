"""Render README media from a recorded session. Needs only Python and Pillow.

    python3 scripts/readme_media/render_media.py docs/media/demo_session.csv docs/media

Writes:
  handpilot_demo.gif  animation drawn from recorded ControllerStatus samples
  ik_branches.svg     animated two-branch IK illustration (computed geometry)
  pipeline.svg        animated command-flow diagram
Link lengths below must match the configuration used for the recording.
"""

import csv
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

L1, L2 = 0.30, 0.25
TIMEOUT = 0.25
JOINT_LIMIT = 2.8
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

BG = (13, 17, 23)
PANEL = (22, 27, 34)
GRID = (33, 40, 49)
MUTED = (139, 148, 158)
TEXT = (230, 237, 243)
TEAL = (20, 184, 166)
SILVER = (175, 184, 193)
ORANGE = (245, 166, 35)
BLUE = (88, 166, 255)
STATE_NAME = {0: "DISENGAGED", 1: "ENGAGED", 2: "HOLD", 3: "FAULT"}
STATE_COLOR = {0: (110, 118, 129), 1: (46, 160, 67), 2: (210, 153, 34), 3: (218, 54, 51)}
CAPTION = {
    "pre-engage": ("Commands arrive, robot not engaged", "Receiving input must never start motion."),
    "engage": ("Explicit engage service call", "Engaging syncs the target; no jump."),
    "circle": ("Velocity commands trace a circle", "target = achieved + v * dt, every 20 ms."),
    "reach-limit": ("Operator pushes past full reach", "IK rejects the step; joints stay valid."),
    "silence": ("Operator goes silent", "Watchdog: command age > 0.25 s -> HOLD."),
}


def font(size, bold=False, mono=False):
    name = "DejaVuSansMono" if mono else "DejaVuSans"
    name += "-Bold" if bold else ""
    try:
        return ImageFont.truetype(str(FONT_DIR / f"{name}.ttf"), size)
    except OSError:
        return ImageFont.load_default()


def load(path):
    with open(path, encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key in ("t", "sent_vx", "sent_vy", "req_x", "req_y", "ach_x", "ach_y", "q1", "q2", "age"):
            row[key] = float(row[key])
        for key in ("state", "limited", "rejected", "age_valid", "sending"):
            row[key] = int(row[key])
    return rows


def render_gif(rows, output):
    width, height, scale = 820, 470, 600
    origin = (48, 392)
    f_title, f_big = font(17, bold=True), font(20, bold=True)
    f_body, f_small, f_mono = font(13), font(11), font(13, mono=True)
    f_reason = font(12, mono=True)

    def px(x, y):
        return origin[0] + x * scale, origin[1] - y * scale

    base = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(base)
    for step in range(-1, 13):
        gx = origin[0] + step * 0.05 * scale
        gy = origin[1] - step * 0.05 * scale
        draw.line([(gx, 0), (gx, height - 53)], fill=GRID)
        draw.line([(0, gy), (429, gy)], fill=GRID)
    outer, inner = (L1 + L2) * scale, abs(L1 - L2) * scale
    draw.ellipse([origin[0] - outer, origin[1] - outer, origin[0] + outer, origin[1] + outer],
                 outline=(48, 64, 82), width=2)
    draw.ellipse([origin[0] - inner, origin[1] - inner, origin[0] + inner, origin[1] + inner],
                 outline=(48, 64, 82), width=1)
    draw.text((origin[0] + outer * 0.80 + 4, origin[1] - outer * 0.60 + 4), "reach\nlimit",
              font=f_small, fill=MUTED)
    draw.text((origin[0] + 18, origin[1] + 8), "base_link   grid = 5 cm", font=f_small, fill=MUTED)
    draw.rectangle([430, 0, width, height - 52], fill=PANEL)
    draw.text((448, 18), "HandPilot  -  real controller output", font=f_title, fill=TEXT)
    draw.text((448, 42), "rendered from recorded controller/status", font=f_small, fill=MUTED)
    total = rows[-1]["t"]
    bar_x0, bar_x1, bar_y = 20, width - 20, height - 30
    for index, row in enumerate(rows[:-1]):
        x0 = bar_x0 + (bar_x1 - bar_x0) * row["t"] / total
        x1 = bar_x0 + (bar_x1 - bar_x0) * rows[index + 1]["t"] / total
        draw.rectangle([x0, bar_y, x1 + 1, bar_y + 10], fill=STATE_COLOR[row["state"]])
    draw.text((bar_x0, bar_y - 18), "state timeline", font=f_small, fill=MUTED)

    frames, trail = [], []
    picks = list(range(0, len(rows), 3))
    for index, sample in enumerate(picks):
        row = rows[sample]
        trail.append(px(row["ach_x"], row["ach_y"]))
        frame = base.copy()
        d = ImageDraw.Draw(frame)
        if len(trail) > 1:
            d.line(trail, fill=(36, 99, 140), width=3)
        elbow = px(L1 * math.cos(row["q1"]), L1 * math.sin(row["q1"]))
        tool = px(row["ach_x"], row["ach_y"])
        d.line([origin, elbow], fill=TEAL, width=13)
        d.line([elbow, tool], fill=SILVER, width=10)
        for point, radius, colour in ((origin, 11, SILVER), (elbow, 7, TEXT), (tool, 8, ORANGE)):
            d.ellipse([point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius],
                      fill=colour)
        if row["sending"]:
            target = px(row["req_x"], row["req_y"])
            vx, vy = row["sent_vx"], row["sent_vy"]
            if math.hypot(vx, vy) > 0:
                end = (tool[0] + vx * 900, tool[1] - vy * 900)
                d.line([tool, end], fill=BLUE, width=3)
                d.ellipse([end[0] - 3, end[1] - 3, end[0] + 3, end[1] + 3], fill=BLUE)
            if row["rejected"]:
                d.ellipse([target[0] - 11, target[1] - 11, target[0] + 11, target[1] + 11],
                          outline=STATE_COLOR[3], width=3)
        colour = STATE_COLOR[row["state"]]
        d.rounded_rectangle([448, 70, 640, 106], radius=18, fill=colour)
        name = STATE_NAME[row["state"]]
        d.text((544 - d.textlength(name, font=f_big) / 2, 76), name, font=f_big, fill=(255, 255, 255))
        d.text((654, 80), f"t = {row['t']:5.2f} s", font=f_mono, fill=MUTED)
        title, detail = CAPTION[row["phase"]]
        d.text((448, 122), title, font=f_body, fill=TEXT)
        d.text((448, 141), detail, font=f_small, fill=MUTED)
        d.text((448, 166), "reason:", font=f_small, fill=MUTED)
        d.text((498, 166), row["reason"][:40], font=f_reason, fill=TEXT)
        for line, (label, value) in enumerate((("shoulder", row["q1"]), ("elbow", row["q2"]))):
            y = 200 + line * 38
            d.text((448, y), f"{label:<8} {value:+.3f} rad", font=f_mono, fill=TEXT)
            x0, x1 = 448, 790
            d.rectangle([x0, y + 19, x1, y + 25], fill=GRID)
            centre = x0 + (x1 - x0) * (value + JOINT_LIMIT) / (2 * JOINT_LIMIT)
            d.rectangle([x0 + (x1 - x0) / 2, y + 19, centre, y + 25] if centre >= x0 + (x1 - x0) / 2
                        else [centre, y + 19, x0 + (x1 - x0) / 2, y + 25], fill=TEAL)
        d.text((448, 280), "joint limits +/-2.8 rad", font=f_small, fill=MUTED)
        age = row["age"] if row["age_valid"] else 0.0
        d.text((448, 306), f"command age  {age * 1000:6.1f} ms", font=f_mono, fill=TEXT)
        x0, x1, span = 448, 790, 0.30
        d.rectangle([x0, 326, x1, 340], fill=GRID)
        d.rectangle([x0, 326, x0 + (x1 - x0) * min(age, span) / span, 340],
                    fill=STATE_COLOR[2] if age > TIMEOUT else BLUE)
        limit_x = x0 + (x1 - x0) * TIMEOUT / span
        d.line([(limit_x, 320), (limit_x, 346)], fill=STATE_COLOR[3], width=2)
        d.text((limit_x - 52, 348), "timeout 250 ms", font=f_small, fill=MUTED)
        flags = [("limited", row["limited"], STATE_COLOR[2]), ("rejected", row["rejected"], STATE_COLOR[3]),
                 ("input", row["sending"], BLUE)]
        for slot, (label, on, flag_colour) in enumerate(flags):
            x = 448 + slot * 112
            d.rounded_rectangle([x, 376, x + 100, 400], radius=12,
                                fill=flag_colour if on else GRID)
            d.text((x + 50 - d.textlength(label, font=f_small) / 2, 381), label, font=f_small,
                   fill=(255, 255, 255) if on else MUTED)
        head = bar_x0 + (bar_x1 - bar_x0) * row["t"] / total
        d.polygon([(head - 6, bar_y - 4), (head + 6, bar_y - 4), (head, bar_y + 3)], fill=TEXT)
        frames.append(frame)

    palette_source = Image.new("RGB", (width, height * 3))
    for slot, sample in enumerate((0, len(frames) // 2, len(frames) - 1)):
        palette_source.paste(frames[sample], (0, height * slot))
    palette = palette_source.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    durations = [60] * len(indexed)
    durations[-1] = 2500
    indexed[0].save(output, save_all=True, append_images=indexed[1:], duration=durations,
                    loop=0, optimize=True, disposal=1)


def render_ik_svg(output):
    target = (0.36, 0.22)
    radius = math.hypot(*target)
    cosine = (radius ** 2 - L1 ** 2 - L2 ** 2) / (2 * L1 * L2)
    scale, ox, oy = 420, 70, 300

    def p(x, y):
        return f"{ox + x * scale:.1f},{oy - y * scale:.1f}"

    branches = []
    for sign in (1, -1):
        q2 = sign * math.acos(cosine)
        q1 = math.atan2(target[1], target[0]) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
        branches.append((q1, q2, (L1 * math.cos(q1), L1 * math.sin(q1))))
    (_, _, e_down), (_, _, e_up) = branches
    tx, ty = p(*target).split(",")
    up, down = p(*e_up), p(*e_down)
    return output.write_text(f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 340" width="640" height="340" font-family="DejaVu Sans, Segoe UI, Helvetica, Arial, sans-serif">
  <rect width="640" height="340" rx="14" fill="#0d1117"/>
  <circle cx="{ox}" cy="{oy}" r="{(L1 + L2) * scale:.1f}" fill="none" stroke="#30405a" stroke-width="2" stroke-dasharray="6 6"/>
  <circle cx="{ox}" cy="{oy}" r="{abs(L1 - L2) * scale:.1f}" fill="#30405a" fill-opacity="0.5"/>
  <line x1="{ox}" y1="{oy}" x2="{down.split(',')[0]}" y2="{down.split(',')[1]}" stroke="#14b8a6" stroke-opacity="0.18" stroke-width="10" stroke-linecap="round"/>
  <line x1="{down.split(',')[0]}" y1="{down.split(',')[1]}" x2="{tx}" y2="{ty}" stroke="#afb8c1" stroke-opacity="0.18" stroke-width="8" stroke-linecap="round"/>
  <line x1="{ox}" y1="{oy}" x2="{up.split(',')[0]}" y2="{up.split(',')[1]}" stroke="#14b8a6" stroke-opacity="0.18" stroke-width="10" stroke-linecap="round"/>
  <line x1="{up.split(',')[0]}" y1="{up.split(',')[1]}" x2="{tx}" y2="{ty}" stroke="#afb8c1" stroke-opacity="0.18" stroke-width="8" stroke-linecap="round"/>
  <line x1="{ox}" y1="{oy}" x2="{up.split(',')[0]}" y2="{up.split(',')[1]}" stroke="#14b8a6" stroke-width="10" stroke-linecap="round">
    <animate attributeName="x2" values="{up.split(',')[0]};{up.split(',')[0]};{down.split(',')[0]};{down.split(',')[0]};{up.split(',')[0]}" keyTimes="0;0.35;0.5;0.85;1" dur="5s" repeatCount="indefinite"/>
    <animate attributeName="y2" values="{up.split(',')[1]};{up.split(',')[1]};{down.split(',')[1]};{down.split(',')[1]};{up.split(',')[1]}" keyTimes="0;0.35;0.5;0.85;1" dur="5s" repeatCount="indefinite"/>
  </line>
  <line x1="{up.split(',')[0]}" y1="{up.split(',')[1]}" x2="{tx}" y2="{ty}" stroke="#afb8c1" stroke-width="8" stroke-linecap="round">
    <animate attributeName="x1" values="{up.split(',')[0]};{up.split(',')[0]};{down.split(',')[0]};{down.split(',')[0]};{up.split(',')[0]}" keyTimes="0;0.35;0.5;0.85;1" dur="5s" repeatCount="indefinite"/>
    <animate attributeName="y1" values="{up.split(',')[1]};{up.split(',')[1]};{down.split(',')[1]};{down.split(',')[1]};{up.split(',')[1]}" keyTimes="0;0.35;0.5;0.85;1" dur="5s" repeatCount="indefinite"/>
  </line>
  <circle cx="{ox}" cy="{oy}" r="10" fill="#afb8c1"/>
  <circle cx="{tx}" cy="{ty}" r="9" fill="#f5a623"/>
  <circle cx="{tx}" cy="{ty}" r="16" fill="none" stroke="#f5a623" stroke-width="2">
    <animate attributeName="r" values="10;20;10" dur="1.6s" repeatCount="indefinite"/>
    <animate attributeName="stroke-opacity" values="1;0;1" dur="1.6s" repeatCount="indefinite"/>
  </circle>
  <text x="{float(tx) + 16:.1f}" y="{float(ty) + 5:.1f}" fill="#e6edf3" font-size="13">target (0.36, 0.22) m</text>
  <text x="{ox - 30}" y="{oy + 26}" fill="#8b949e" font-size="12">base_link</text>
  <text x="372" y="40" fill="#e6edf3" font-size="17" font-weight="bold">One point, two arm poses</text>
  <text x="372" y="66" fill="#8b949e" font-size="13">q2 = +/- acos(c),</text>
  <text x="372" y="84" fill="#8b949e" font-size="13">c = (r^2 - L1^2 - L2^2) / (2 L1 L2)</text>
  <text x="372" y="118" fill="#14b8a6" font-size="13">elbow-down  q2 = {branches[0][1]:+.2f} rad</text>
  <text x="372" y="138" fill="#14b8a6" font-size="13">elbow-up    q2 = {branches[1][1]:+.2f} rad</text>
  <text x="372" y="172" fill="#8b949e" font-size="12">HandPilot keeps the branch nearest the</text>
  <text x="372" y="189" fill="#8b949e" font-size="12">current joints, inside hard limits.</text>
  <text x="372" y="223" fill="#8b949e" font-size="12">Dashed ring: |r| &gt; L1 + L2 is unreachable.</text>
  <text x="372" y="240" fill="#8b949e" font-size="12">Filled disc: |r| &lt; |L1 - L2| is unreachable.</text>
  <text x="372" y="274" fill="#6e7681" font-size="11">Geometry computed from L1 = 0.30 m, L2 = 0.25 m</text>
</svg>
""", encoding="utf-8")


def render_pipeline_svg(output):
    stages = [("Keyboard", "w a s d e", "#58a6ff"), ("TeleopCommand", "teleop/command", "#a371f7"),
              ("Gates", "engaged? fresh? finite?", "#d29922"), ("IK + limits", "pure C++ core", "#14b8a6"),
              ("JointState", "joint_states", "#2ea043"), ("TF", "robot_state_publisher", "#f5a623")]
    boxes, dots = [], []
    for index, (title, detail, colour) in enumerate(stages):
        x = 20 + index * 136
        boxes.append(f"""  <rect x="{x}" y="50" width="118" height="70" rx="10" fill="#161b22" stroke="{colour}" stroke-width="2"/>
  <text x="{x + 59}" y="80" text-anchor="middle" fill="#e6edf3" font-size="13" font-weight="bold">{title}</text>
  <text x="{x + 59}" y="100" text-anchor="middle" fill="#8b949e" font-size="10">{detail}</text>""")
        if index < len(stages) - 1:
            boxes.append(f'  <line x1="{x + 120}" y1="85" x2="{x + 134}" y2="85" stroke="#30363d" stroke-width="2"/>')
    for offset in range(3):
        dots.append(f"""  <circle r="5" cy="85" fill="#f5a623">
    <animate attributeName="cx" values="20;816" dur="4.5s" begin="{offset * 1.5}s" repeatCount="indefinite"/>
    <animate attributeName="fill" values="#58a6ff;#a371f7;#d29922;#14b8a6;#2ea043;#f5a623" dur="4.5s" begin="{offset * 1.5}s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0;1;1;1;1;0" dur="4.5s" begin="{offset * 1.5}s" repeatCount="indefinite"/>
  </circle>""")
    output.write_text(f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 836 170" width="836" height="170" font-family="DejaVu Sans, Segoe UI, Helvetica, Arial, sans-serif">
  <rect width="836" height="170" rx="14" fill="#0d1117"/>
  <text x="20" y="32" fill="#e6edf3" font-size="15" font-weight="bold">One key press, end to end</text>
{chr(10).join(boxes)}
{chr(10).join(dots)}
  <text x="20" y="150" fill="#8b949e" font-size="11">Keyboard: Python node (publishes at 50 Hz)   ·   controller: C++ node, 50 Hz timer   ·   a stale or missing command stops motion at the gates</text>
</svg>
""", encoding="utf-8")


def main():
    recording = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/media/demo_session.csv")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "docs/media")
    out.mkdir(parents=True, exist_ok=True)
    render_gif(load(recording), out / "handpilot_demo.gif")
    render_ik_svg(out / "ik_branches.svg")
    render_pipeline_svg(out / "pipeline.svg")
    for name in ("handpilot_demo.gif", "ik_branches.svg", "pipeline.svg"):
        print(f"{name}: {(out / name).stat().st_size / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
