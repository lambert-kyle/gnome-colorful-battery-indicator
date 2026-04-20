#!/usr/bin/env python3
"""
battery_svg.py — Generate battery icon SVGs from the command line.

Usage examples:
  python battery_svg.py --level 70
  python battery_svg.py --level 30 --bolt --bolt-color "#00e5ff"
  python battery_svg.py --level 100 --fill "#22d43a" --shell "#444444" --radius 2.5
  python battery_svg.py --level 50 --width-pct 90 --bolt --output my_battery.svg
  python battery_svg.py --level 0 --fill "transparent"
  python battery_svg.py --batch --output-dir ./icons
"""

import argparse
import math
import os
import sys


# ---------------------------------------------------------------------------
# Core geometry
# ---------------------------------------------------------------------------

def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def build_svg(
    level: float,          # 0–100 charge percent
    width_pct: float,      # how wide the battery is as % of 16px viewbox (e.g. 90)
    shell_color: str,      # color of the battery outline/shell
    shell_opacity: float,  # opacity of the ghost outline layer (0–1)
    fill_color: str,       # color of the charge indicator
    bolt: bool,            # whether to draw a lightning bolt
    bolt_color: str,       # color of the lightning bolt
    rx_body: float,        # corner radius of the battery body
    rx_nub: float,         # corner radius of the nub
) -> str:
    level = clamp(level, 0, 100)
    width_pct = clamp(width_pct, 20, 100)

    # --- Coordinate system ---
    # viewBox is always 0 0 16 16.
    # The battery is scaled horizontally to width_pct% of 16, then centered.
    # We work in "logical" units (as if 100% wide = 16px), then apply a
    # matrix transform: scaleX = width_pct/100, translateX = (16 - 16*scaleX)/2

    scale_x = width_pct / 100.0
    offset_x = (16 - 16 * scale_x) / 2.0

    # In logical space the battery occupies:
    #   body:  x=2, y=2, w=12, h=14   (full battery body)
    #   nub:   x=5, y=0, w=6,  h=2.5  (terminal nub at top)
    # The matrix transform handles the horizontal squish automatically,
    # so we specify all geometry in logical space and wrap in a <g transform>.

    transform = f"matrix({scale_x:.4f} 0 0 1 {offset_x:.4f} 0)"

    # --- Charge fill geometry ---
    # Body spans y=2 (top) to y=16 (bottom), total height=14.
    # 100% fill starts at y=2, 0% fill is empty (no rect drawn).
    body_top = 2.0
    body_bottom = 16.0
    body_height = body_bottom - body_top  # 14

    fill_height = body_height * (level / 100.0)
    fill_y = body_bottom - fill_height  # fills from the bottom up

    # rx in logical space: the matrix squishes x, so visual rx_x = rx * scale_x
    # We want the *visual* rx to match what the user asked for, so we pass
    # through as-is (horizontal squish makes corners slightly elliptical at
    # non-100% widths — acceptable and matches the originals).
    rx_b = rx_body
    rx_n = rx_nub

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">']
    lines.append(f'  <g transform="{transform}">')

    # --- Ghost shell (outline, semi-transparent) ---
    # Two rects: nub on top, body below.
    lines.append(
        f'    <rect x="5" y="0" width="6" height="2.5"'
        f' rx="{rx_n}" fill="{shell_color}" opacity="{shell_opacity}"/>'
    )
    lines.append(
        f'    <rect x="2" y="2" width="12" height="14"'
        f' rx="{rx_b}" fill="{shell_color}" opacity="{shell_opacity}"/>'
    )

    # --- Solid shell body (the unfilled portion) ---
    # Only draw if there's unfilled space above the charge level.
    if level < 100:
        lines.append(
            f'    <rect x="2" y="2" width="12" height="14"'
            f' rx="{rx_b}" fill="{shell_color}"/>'
        )

    # --- Charge fill ---
    if level > 0 and fill_color.lower() not in ("none", "transparent"):
        lines.append(
            f'    <rect x="2" y="{fill_y:.4f}" width="12" height="{fill_height:.4f}"'
            f' rx="{rx_b}" fill="{fill_color}"/>'
        )

    # --- Lightning bolt ---
    if bolt and bolt_color.lower() not in ("none", "transparent"):
        # Bolt path in logical space (same as the originals).
        # Classic battery bolt: top half → kink right → bottom half.
        # Simplified clean path: M10 3 L9 8 H12 L6 15 L7 10 H4 Z
        bolt_path = "M10 3 L9 8 H12 L6 15 L7 10 H4 Z"
        lines.append(
            f'    <path d="{bolt_path}" fill="{bolt_color}"/>'
        )

    lines.append('  </g>')
    lines.append('</svg>')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Batch mode: generate a standard set of icons
# ---------------------------------------------------------------------------

BATCH_ICONS = [
    # (name, level, bolt, fill_color)
    ("battery-100",             100, False, "#6ee89a"),
    ("battery-80",               80, False, "#b4f2d0"),
    ("battery-60",               60, False, "#dffaf0"),
    ("battery-40",               40, False, "#ffffff"),
    ("battery-20",               20, False, "#c8d8fc"),
    ("battery-10",               10, False, "#6080f4"),
    ("battery-caution",           5, False, "#6080f4"),
    ("battery-100-charging",    100,  True, "#6ee89a"),
    ("battery-80-charging",      80,  True, "#b4f2d0"),
    ("battery-60-charging",      60,  True, "#dffaf0"),
    ("battery-40-charging",      40,  True, "#ffffff"),
    ("battery-20-charging",      20,  True, "#c8d8fc"),
    ("battery-10-charging",      10,  True, "#6080f4"),
    ("battery-charging",        100,  True, "#2a10f8"),
]


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate battery SVG icons.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--batch",
        action="store_true",
        help="Generate a standard set of battery icons (ignores most other flags).",
    )

    p.add_argument(
        "--level",
        type=float,
        default=100,
        metavar="0-100",
        help="Charge level as a percentage (default: 100).",
    )
    p.add_argument(
        "--width-pct",
        type=float,
        default=90,
        metavar="PCT",
        dest="width_pct",
        help="Horizontal width as %% of the 16px viewbox (default: 90).",
    )
    p.add_argument(
        "--shell",
        default="#bebebe",
        metavar="COLOR",
        help="Shell/outline color (default: #bebebe).",
    )
    p.add_argument(
        "--shell-opacity",
        type=float,
        default=0.4,
        metavar="0-1",
        dest="shell_opacity",
        help="Opacity of the ghost outline layer (default: 0.4).",
    )
    p.add_argument(
        "--fill",
        default="#6ee89a",
        metavar="COLOR",
        help="Charge fill color (default: #6ee89a). Use 'none' or 'transparent' to skip.",
    )
    p.add_argument(
        "--bolt",
        action="store_true",
        help="Draw a lightning bolt over the battery.",
    )
    p.add_argument(
        "--bolt-color",
        default="#00e5ff",
        metavar="COLOR",
        dest="bolt_color",
        help="Lightning bolt fill color (default: #00e5ff). Use 'none' to hide.",
    )
    p.add_argument(
        "--radius",
        type=float,
        default=1.2,
        metavar="PX",
        help="Corner radius of the battery body (default: 1.2).",
    )
    p.add_argument(
        "--nub-radius",
        type=float,
        default=0.8,
        metavar="PX",
        dest="nub_radius",
        help="Corner radius of the nub/terminal (default: 0.8).",
    )
    p.add_argument(
        "--output", "-o",
        default=None,
        metavar="FILE",
        help="Output file path (default: stdout for single, required for --batch).",
    )
    p.add_argument(
        "--output-dir",
        default="./battery-icons",
        metavar="DIR",
        dest="output_dir",
        help="Output directory for --batch mode (default: ./battery-icons).",
    )
    p.add_argument(
        "--batch-bolt-color",
        default="#00e5ff",
        metavar="COLOR",
        dest="batch_bolt_color",
        help="Lightning bolt color for --batch mode (default: #00e5ff).",
    )
    p.add_argument(
        "--batch-shell",
        default="#bebebe",
        metavar="COLOR",
        dest="batch_shell",
        help="Shell color for --batch mode (default: #bebebe).",
    )

    return p


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = make_parser()
    args = parser.parse_args()

    if args.batch:
        out_dir = args.output_dir
        os.makedirs(out_dir, exist_ok=True)
        generated = []
        for name, level, has_bolt, fill in BATCH_ICONS:
            svg = build_svg(
                level=level,
                width_pct=args.width_pct,
                shell_color=args.batch_shell,
                shell_opacity=0.4,
                fill_color=fill,
                bolt=has_bolt,
                bolt_color=args.batch_bolt_color,
                rx_body=args.radius,
                rx_nub=args.nub_radius,
            )
            path = os.path.join(out_dir, f"{name}.svg")
            with open(path, "w") as f:
                f.write(svg)
            generated.append(path)

        print(f"Generated {len(generated)} icons in '{out_dir}/':")
        for p in generated:
            print(f"  {p}")
        return

    # Single icon mode
    svg = build_svg(
        level=args.level,
        width_pct=args.width_pct,
        shell_color=args.shell,
        shell_opacity=args.shell_opacity,
        fill_color=args.fill,
        bolt=args.bolt,
        bolt_color=args.bolt_color,
        rx_body=args.radius,
        rx_nub=args.nub_radius,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(svg)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(svg)


if __name__ == "__main__":
    main()