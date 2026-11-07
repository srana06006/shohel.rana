"""Render a silent 20-second research overview for the personal website.

Brief: show how signals from four application areas can be observed, put in
context, and used to support a decision that can be examined. No empirical
values or clinical/agricultural outcomes are shown.

Art direction: Swiss precision, matching the portfolio's ink, teal, coral,
blue, and warm-gold palette. Geometry represents abstract signal streams;
there is no narration or baked-in language, so the WebVTT caption tracks can
serve English, Bangla, Arabic, and Hindi visitors.

Timeline (24 fps, 20 seconds):
  0–4s   Four distinct signal patterns appear.
  4–8s   Paths connect those signals to a shared context.
  8–12s  A bounded signal is examined amid variation.
  12–16s Evidence resolves into a reviewable decision path.
  16–20s Hold on the complete, quiet composition.

Render: python3 tools/research_overview.py
"""

from __future__ import annotations

import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "dist" / "assets"
W, H = 1280, 720
FPS = 24
DURATION = 20
FRAMES = FPS * DURATION

INK = (17, 31, 48)
PAPER = (251, 250, 246)
GOLD = (239, 189, 97)
TEAL = (112, 208, 189)
CORAL = (233, 133, 104)
BLUE = (146, 185, 232)
MUTED = (151, 168, 181)


def clamp(x: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, x))


def smooth(x: float) -> float:
    x = clamp(x)
    return x * x * (3 - 2 * x)


def fade(time: float, start: float, end: float) -> float:
    return smooth((time - start) / max(0.001, end - start))


def cubic(p0, p1, p2, p3, steps=60):
    points = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        points.append((round(x), round(y)))
    return points


def alpha(color, amount):
    return (*color, round(255 * clamp(amount)))


def draw_grid(draw):
    for x in range(0, W + 1, 80):
        draw.line((x, 0, x, H), fill=(255, 255, 255, 10), width=1)
    for y in range(0, H + 1, 80):
        draw.line((0, y, W, y), fill=(255, 255, 255, 10), width=1)
    draw.line((80, 84, W - 80, 84), fill=(255, 255, 255, 22), width=1)
    draw.line((80, H - 82, W - 80, H - 82), fill=(255, 255, 255, 18), width=1)


def signal_wave(draw, box, color, phase, strength=1.0, alpha_value=1.0, cycles=2.0):
    x0, y0, x1, y1 = box
    points = []
    for i in range(151):
        p = i / 150
        x = x0 + p * (x1 - x0)
        envelope = 0.25 + 0.75 * (math.sin(math.pi * p) ** 0.7)
        y = (y0 + y1) / 2 + math.sin(p * math.pi * 2 * cycles + phase) * (y1 - y0) * 0.34 * envelope * strength
        points.append((round(x), round(y)))
    draw.line(points, fill=alpha(color, alpha_value), width=4, joint="curve")


def media_frames(draw, center, color, strength=1.0, alpha_value=1.0):
    cx, cy = center
    width = 92 * strength
    height = 62 * strength
    for offset, opacity in [(-13, .35), (0, .65), (13, 1.0)]:
        x0, y0 = cx - width / 2 + offset, cy - height / 2 + offset * .45
        x1, y1 = x0 + width, y0 + height
        draw.rounded_rectangle((x0, y0, x1, y1), radius=5 * strength,
                               outline=alpha(color, alpha_value * opacity), width=max(1, round(2 * strength)))
        draw.line((x0 + 9 * strength, y0 + 17 * strength, x1 - 9 * strength, y0 + 17 * strength),
                  fill=alpha(color, alpha_value * opacity), width=max(1, round(2 * strength)))
        draw.line((x0 + 9 * strength, y0 + 29 * strength, x0 + 43 * strength, y0 + 29 * strength),
                  fill=alpha(color, alpha_value * opacity), width=max(1, round(2 * strength)))


def spectrum(draw, box, color, alpha_value=1.0, phase=0.0):
    x0, y0, x1, y1 = box
    points = []
    for i in range(181):
        p = i / 180
        x = x0 + p * (x1 - x0)
        base = (y0 + y1) / 2
        wave = (math.sin(p * 11 + phase) * 0.10 + math.sin(p * 25 + phase * .5) * .05)
        peak1 = math.exp(-((p - .34) / .06) ** 2) * .42
        peak2 = math.exp(-((p - .70) / .11) ** 2) * .58
        y = base - (wave + peak1 + peak2) * (y1 - y0)
        points.append((round(x), round(y)))
    draw.line(points, fill=alpha(color, alpha_value), width=4, joint="curve")


def field_grid(draw, center, color, strength=1.0, alpha_value=1.0, phase=0.0):
    cx, cy = center
    spacing = 22 * strength
    for row in range(-2, 3):
        for col in range(-2, 3):
            x = cx + col * spacing
            y = cy + row * spacing
            intensity = .36 + .6 * ((math.sin(col * 1.2 + row + phase) + 1) / 2)
            radius = (2.2 + 2.8 * intensity) * strength
            draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                         fill=alpha(color, alpha_value * intensity))


def context_ring(draw, center, radius, color, alpha_value=1.0, width=2, dash=False):
    cx, cy = center
    box = (cx - radius, cy - radius, cx + radius, cy + radius)
    if not dash:
        draw.ellipse(box, outline=alpha(color, alpha_value), width=width)
        return
    for start in range(0, 360, 18):
        draw.arc(box, start=start, end=start + 9, fill=alpha(color, alpha_value), width=width)


def draw_source_paths(draw, time, opacity=1.0):
    center = (640, 355)
    routes = [
        ((245, 205), (360, 205), (440, 305), center, CORAL),
        ((245, 515), (365, 505), (450, 420), center, TEAL),
        ((1035, 205), (920, 200), (850, 300), center, BLUE),
        ((1035, 515), (920, 500), (835, 420), center, GOLD),
    ]
    progress = fade(time, 3.7, 7.0)
    for p0, p1, p2, p3, color in routes:
        path = cubic(p0, p1, p2, p3)
        n = max(2, round(len(path) * progress))
        draw.line(path[:n], fill=alpha(color, opacity * .65), width=3, joint="curve")
        if progress > 0:
            x, y = path[n - 1]
            r = 4 + 2 * progress
            draw.ellipse((x-r, y-r, x+r, y+r), fill=alpha(color, opacity))


def render_frame(frame):
    time = frame / FPS
    # Drawing RGBA overlays directly onto RGB composites their transparency.
    image = Image.new("RGB", (W, H), INK)
    draw = ImageDraw.Draw(image, "RGBA")
    draw_grid(draw)

    # Four distinct signal forms enter in sequence.
    source_alpha = 1 - fade(time, 3.8, 5.7) * .58
    reveal = [fade(time, .15, 1.2), fade(time, .55, 1.6), fade(time, .95, 2.0), fade(time, 1.35, 2.4)]
    media_frames(draw, (195, 195), CORAL, strength=.95, alpha_value=reveal[0] * source_alpha)
    signal_wave(draw, (105, 465, 285, 565), TEAL, phase=time * 1.8, strength=.85, alpha_value=reveal[1] * source_alpha, cycles=2.2)
    spectrum(draw, (930, 155, 1110, 255), BLUE, alpha_value=reveal[2] * source_alpha, phase=time * .5)
    field_grid(draw, (1080, 515), GOLD, strength=1.0, alpha_value=reveal[3] * source_alpha, phase=time * .4)

    # Each stream connects to a shared context, with endpoints clearly visible.
    draw_source_paths(draw, time)
    center = (640, 355)
    ring_alpha = fade(time, 4.9, 7.3)
    context_ring(draw, center, 152, TEAL, ring_alpha * .58, width=2, dash=True)
    context_ring(draw, center, 110, GOLD, ring_alpha * .42, width=1)

    # A band around one central trace suggests uncertainty without asserting values.
    band_alpha = fade(time, 7.8, 9.0) * (1 - fade(time, 11.2, 12.4))
    if band_alpha > .01:
        upper, lower = [], []
        for i in range(161):
            p = i / 160
            x = 490 + p * 300
            envelope = 10 + 18 * abs(math.sin(p * math.pi * 2.3 + .4))
            y = 355 + math.sin(p * math.pi * 2.3 + .35) * 52
            upper.append((round(x), round(y - envelope)))
            lower.append((round(x), round(y + envelope)))
        draw.polygon(upper + lower[::-1], fill=alpha(TEAL, band_alpha * .12))
        draw.line(upper, fill=alpha(TEAL, band_alpha * .46), width=2)
        draw.line(lower, fill=alpha(TEAL, band_alpha * .46), width=2)
        signal_wave(draw, (490, 310, 790, 400), PAPER, phase=.35, strength=.7, alpha_value=band_alpha, cycles=1.15)

    # Compact evidence marks remain around the context while the center is evaluated.
    context_alpha = fade(time, 8.4, 9.4) * (1 - fade(time, 11.5, 12.4))
    if context_alpha > .01:
        for i, angle in enumerate((0, 90, 180, 270)):
            rad = math.radians(angle - 90)
            x = center[0] + math.cos(rad) * 152
            y = center[1] + math.sin(rad) * 152
            color = (CORAL, TEAL, BLUE, GOLD)[i]
            r = 5 + 3 * (0.5 + 0.5 * math.sin(time * 1.5 + i))
            draw.ellipse((x-r, y-r, x+r, y+r), fill=alpha(color, context_alpha))

    # Evidence resolves into a reviewable route; movement ends in a stable hold.
    result_alpha = fade(time, 11.8, 13.4)
    if result_alpha > .01:
        path_y = 355
        left_x, right_x = 475, 805
        draw.line((left_x, path_y, right_x, path_y), fill=alpha(MUTED, result_alpha * .62), width=3)
        checkpoints = [500, 640, 790]
        for idx, x in enumerate(checkpoints):
            color = (GOLD, TEAL, BLUE)[idx]
            r = 14 if idx < 2 else 20
            draw.ellipse((x-r, path_y-r, x+r, path_y+r),
                         fill=alpha(INK, result_alpha), outline=alpha(color, result_alpha), width=3)
            if idx == 2:
                draw.line((x-8, path_y, x-2, path_y+7, x+10, path_y-8),
                          fill=alpha(PAPER, result_alpha), width=4, joint="curve")

        card_alpha = fade(time, 13.0, 14.6)
        if card_alpha > .01:
            x0, y0, x1, y1 = 885, 288, 1080, 422
            draw.rounded_rectangle((x0, y0, x1, y1), radius=12,
                                   fill=alpha((24, 47, 66), card_alpha),
                                   outline=alpha(TEAL, card_alpha * .72), width=2)
            for i, width in enumerate((108, 72, 126)):
                y = y0 + 37 + i * 25
                draw.rounded_rectangle((x0 + 22, y, x0 + 22 + width, y + 4), radius=2,
                                       fill=alpha((PAPER, MUTED, GOLD)[i], card_alpha * (.9 if i != 1 else .55)))
            draw.ellipse((x1 - 31, y0 + 21, x1 - 17, y0 + 35), fill=alpha(TEAL, card_alpha))

    # Final restrained composition: distinct evidence streams, connected and settled.
    finale = fade(time, 16.2, 17.4)
    if finale > .01:
        context_ring(draw, center, 150, TEAL, finale * .48, width=2, dash=True)
        context_ring(draw, center, 108, GOLD, finale * .3, width=1)
        signal_wave(draw, (510, 315, 770, 395), PAPER, phase=.35, strength=.7, alpha_value=finale, cycles=1.15)
        draw_source_paths(draw, 7.5)
        # The final connector has visible endpoints and a short directional marker.
        x0, y = 818, 355
        x1 = 875
        draw.line((x0, y, x1, y), fill=alpha(TEAL, finale), width=3)
        draw.line((x1-9, y-8, x1, y, x1-9, y+8), fill=alpha(TEAL, finale), width=3, joint="curve")
        draw.ellipse((x0-4, y-4, x0+4, y+4), fill=alpha(PAPER, finale))

    # Small, calm accent mark identifies the site palette without adding text.
    draw.ellipse((W - 108, 39, W - 96, 51), fill=alpha(GOLD, .85))
    return image


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    video_path = ASSETS / "research-overview.mp4"
    poster_path = ASSETS / "research-overview-poster.png"
    poster = render_frame(FPS * 18)
    poster.save(poster_path, optimize=True)

    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-crf", "21", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for frame in range(FRAMES):
            process.stdin.write(render_frame(frame).tobytes())
    finally:
        process.stdin.close()
    result = process.wait()
    if result:
        raise SystemExit(f"ffmpeg exited with status {result}")
    print(f"Rendered {video_path} ({video_path.stat().st_size:,} bytes)")
    print(f"Rendered {poster_path} ({poster_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
