"""One-time asset-prep script: extract the V-106 valve icon (green, open
state) from images/rtd/rtd_normal_operation.svg into a standalone overlay
SVG with the same viewBox, so the RTD diagram widget can paint it on top of
any cip_r10x.svg (where V-106 is baked in red/closed) to flash the valve
green during an injection.

Each valve icon is a single matplotlib <path> using fill-rule:evenodd (the
"bowtie" of two triangles is one self-intersecting path) at a fixed
transform="matrix(...,tx,ty)" -- the same 8 (tx, ty) positions recur
identically across rtd_normal_operation.svg and every cip_r10x.svg, since
only the fill color changes between plant-feed (green) and CIP (red) modes.

Two valves (V-106, feed; V-113, product outlet) are red in *every* CIP
variant, unlike the four reactor-branch valves which are red in some CIP
variants and green in others (open only for the reactor currently under
CIP). Locating V-106 among those two: it's the smaller translate-x (it
sits near TK-104 on the left; V-113 sits near AT-101 on the right).

Run: python scripts/extract_v106_overlay.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_SVG = ROOT / "images" / "rtd" / "rtd_normal_operation.svg"
CIP_SVGS = [ROOT / "images" / "rtd" / f"cip_r10{n}.svg" for n in (2, 3, 4)]
OUT_SVG = ROOT / "images" / "rtd" / "overlay_v106_green.svg"

_GREEN = "fill:rgb(0%,68.627451%,32.941176%)"
_RED = "fill:rgb(100%,7.843137%,9.411765%)"

_PATH_RE = re.compile(
    r'<path style="([^"]*{color}[^"]*)" d="([^"]*)" transform="matrix\(([^)]+)\)"/>'
)


def _valve_paths(svg_text: str, color: str) -> dict[str, tuple[str, str, str]]:
    """Map transform string -> (style, d, transform) for every valve path of
    the given fill color."""
    pattern = re.compile(_PATH_RE.pattern.format(color=re.escape(color)))
    return {m.group(3): m.groups() for m in pattern.finditer(svg_text)}


def main() -> None:
    base_text = BASE_SVG.read_text(encoding="utf-8")
    green_valves = _valve_paths(base_text, _GREEN)

    # Positions red in every CIP variant (V-106 and V-113 only).
    always_red = set(green_valves)
    for cip_svg in CIP_SVGS:
        red_here = set(_valve_paths(cip_svg.read_text(encoding="utf-8"), _RED))
        always_red &= red_here

    if len(always_red) != 2:
        raise SystemExit(
            f"Expected exactly two always-red valve positions (V-106, V-113), "
            f"found {len(always_red)}: {always_red}. Diagram assets may have "
            f"changed -- update this script's matching logic."
        )

    # V-106 (feed, near TK-104) has the smaller translate-x than V-113
    # (product outlet, near AT-101).
    def tx(transform: str) -> float:
        return float(transform.split(",")[4])

    transform = min(always_red, key=tx)
    style, d, _ = green_valves[transform]

    vb_match = re.search(r'viewBox="([^"]+)"', base_text)
    w_match = re.search(r'width="([^"]+)"', base_text)
    h_match = re.search(r'height="([^"]+)"', base_text)
    if not (vb_match and w_match and h_match):
        raise SystemExit(f"Could not read viewBox/width/height from {BASE_SVG}")

    out = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_match.group(1)}" '
        f'height="{h_match.group(1)}" viewBox="{vb_match.group(1)}" version="1.1">\n'
        f'<path style="{style}" d="{d}" transform="matrix({transform})"/>\n'
        "</svg>\n"
    )
    OUT_SVG.write_text(out, encoding="utf-8")
    print(f"Wrote {OUT_SVG} (V-106 transform={transform})")


if __name__ == "__main__":
    main()
