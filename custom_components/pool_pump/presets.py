"""Curated catalog of common Intex / Bestway / generic in-ground pool models.

Each preset carries enough geometry to derive the thermal time constant of
the lumped first-order model used by the coordinator. Dimensions come from
manufacturer catalogs (intex.fr, bestway.com) and major French retailers
(boulanger, leroy merlin, manomano).

The thermal time constant is computed empirically:

    tau_hours = depth_m * exposure_factor * cover_factor * 20

where exposure_factor reflects how exposed the pool is (aboveground frame
pools are wind-exposed and conductive — factor 0.8; in-ground pools are
sheltered and lossier through soil — factor 1.2). cover_factor is 1.0 by
default and the user can multiply by ~2.5 manually if a cover is installed.

The formula is a heuristic. Users should fine-tune tau after a week or two
of observation.
"""
from __future__ import annotations

from typing import Final, Literal

ShapeKind = Literal["round", "rect", "oval"]


POOL_PRESETS: Final[list[dict]] = [
    # ---- Intex Easy Set (round, inflatable top ring) — 80% fill ----
    {"slug": "intex_easy_set_244_61",  "name": "Intex Easy Set 244×61 cm",  "shape": "round", "volume_m3": 1.94,  "surface_m2": 4.67,  "depth_m": 0.51, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_305_61",  "name": "Intex Easy Set 305×61 cm",  "shape": "round", "volume_m3": 3.08,  "surface_m2": 7.30,  "depth_m": 0.51, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_305_76",  "name": "Intex Easy Set 305×76 cm",  "shape": "round", "volume_m3": 3.85,  "surface_m2": 7.30,  "depth_m": 0.66, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_366_76",  "name": "Intex Easy Set 366×76 cm",  "shape": "round", "volume_m3": 5.62,  "surface_m2": 10.52, "depth_m": 0.61, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_396_84",  "name": "Intex Easy Set 396×84 cm",  "shape": "round", "volume_m3": 7.29,  "surface_m2": 12.32, "depth_m": 0.74, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_457_107", "name": "Intex Easy Set 457×107 cm", "shape": "round", "volume_m3": 12.43, "surface_m2": 16.40, "depth_m": 0.94, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_457_122", "name": "Intex Easy Set 457×122 cm", "shape": "round", "volume_m3": 14.14, "surface_m2": 16.40, "depth_m": 0.87, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_549_122", "name": "Intex Easy Set 549×122 cm", "shape": "round", "volume_m3": 20.65, "surface_m2": 23.66, "depth_m": 1.07, "manufacturer": "Intex"},

    # ---- Intex Metal Frame / Prism Frame (round) — 90% fill ----
    {"slug": "intex_metal_frame_305_76",  "name": "Intex Metal Frame 305×76 cm",  "shape": "round", "volume_m3": 4.49,  "surface_m2": 7.30,  "depth_m": 0.66, "manufacturer": "Intex"},
    {"slug": "intex_metal_frame_366_76",  "name": "Intex Metal Frame 366×76 cm",  "shape": "round", "volume_m3": 6.50,  "surface_m2": 10.52, "depth_m": 0.66, "manufacturer": "Intex"},
    {"slug": "intex_prism_frame_366_99",  "name": "Intex Prism Frame 366×99 cm",  "shape": "round", "volume_m3": 8.59,  "surface_m2": 10.52, "depth_m": 0.84, "manufacturer": "Intex"},
    {"slug": "intex_prism_frame_457_107", "name": "Intex Prism Frame 457×107 cm", "shape": "round", "volume_m3": 14.61, "surface_m2": 16.40, "depth_m": 0.94, "manufacturer": "Intex"},
    {"slug": "intex_prism_frame_457_122", "name": "Intex Prism Frame 457×122 cm", "shape": "round", "volume_m3": 16.81, "surface_m2": 16.40, "depth_m": 1.07, "manufacturer": "Intex"},
    {"slug": "intex_prism_frame_549_122", "name": "Intex Prism Frame 549×122 cm", "shape": "round", "volume_m3": 24.31, "surface_m2": 23.66, "depth_m": 1.07, "manufacturer": "Intex"},

    # ---- Intex Rectangular Frame / Prism Frame Rectangular — 90% fill ----
    {"slug": "intex_rect_frame_220_150_60",  "name": "Intex Frame 220×150×60 cm",        "shape": "rect", "volume_m3": 1.66, "surface_m2": 3.30, "depth_m": 0.51, "manufacturer": "Intex"},
    {"slug": "intex_rect_frame_300_200_75",  "name": "Intex Frame 300×200×75 cm",        "shape": "rect", "volume_m3": 3.83, "surface_m2": 6.00, "depth_m": 0.65, "manufacturer": "Intex"},
    {"slug": "intex_prism_rect_400_200_100", "name": "Intex Prism Frame 400×200×100 cm", "shape": "rect", "volume_m3": 6.84, "surface_m2": 8.00, "depth_m": 0.84, "manufacturer": "Intex"},
    {"slug": "intex_prism_rect_400_200_122", "name": "Intex Prism Frame 400×200×122 cm", "shape": "rect", "volume_m3": 8.42, "surface_m2": 8.00, "depth_m": 1.07, "manufacturer": "Intex"},
    {"slug": "intex_rect_frame_450_220_84",  "name": "Intex Frame 450×220×84 cm",        "shape": "rect", "volume_m3": 7.13, "surface_m2": 9.90, "depth_m": 0.72, "manufacturer": "Intex"},

    # ---- Intex Ultra XTR Frame (round & rectangular) — 90% fill ----
    {"slug": "intex_ultra_xtr_488_122",          "name": "Intex Ultra XTR 488×122 cm",        "shape": "round", "volume_m3": 19.16, "surface_m2": 18.70, "depth_m": 1.07, "manufacturer": "Intex"},
    {"slug": "intex_ultra_xtr_549_132",          "name": "Intex Ultra XTR 549×132 cm",        "shape": "round", "volume_m3": 26.42, "surface_m2": 23.66, "depth_m": 1.17, "manufacturer": "Intex"},
    {"slug": "intex_ultra_xtr_rect_549_274_132", "name": "Intex Ultra XTR 549×274×132 cm",    "shape": "rect",  "volume_m3": 17.20, "surface_m2": 15.04, "depth_m": 1.17, "manufacturer": "Intex"},
    {"slug": "intex_ultra_xtr_rect_732_366_132", "name": "Intex Ultra XTR 732×366×132 cm",    "shape": "rect",  "volume_m3": 31.81, "surface_m2": 26.79, "depth_m": 1.17, "manufacturer": "Intex"},

    # ---- Bestway Steel Pro / Steel Pro Max (round) — 90% fill ----
    {"slug": "bestway_steel_pro_244_61",      "name": "Bestway Steel Pro 244×61 cm",      "shape": "round", "volume_m3": 1.88,  "surface_m2": 4.67,  "depth_m": 0.51, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_366_76",      "name": "Bestway Steel Pro 366×76 cm",      "shape": "round", "volume_m3": 6.47,  "surface_m2": 10.52, "depth_m": 0.66, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_305_76",  "name": "Bestway Steel Pro Max 305×76 cm",  "shape": "round", "volume_m3": 4.68,  "surface_m2": 7.30,  "depth_m": 0.66, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_366_122", "name": "Bestway Steel Pro Max 366×122 cm", "shape": "round", "volume_m3": 10.25, "surface_m2": 10.52, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_427_84",  "name": "Bestway Steel Pro Max 427×84 cm",  "shape": "round", "volume_m3": 10.22, "surface_m2": 14.32, "depth_m": 0.72, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_427_122", "name": "Bestway Steel Pro Max 427×122 cm", "shape": "round", "volume_m3": 15.23, "surface_m2": 14.32, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_457_122", "name": "Bestway Steel Pro Max 457×122 cm", "shape": "round", "volume_m3": 16.02, "surface_m2": 16.40, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_488_122", "name": "Bestway Steel Pro Max 488×122 cm", "shape": "round", "volume_m3": 19.48, "surface_m2": 18.70, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_549_122", "name": "Bestway Steel Pro Max 549×122 cm", "shape": "round", "volume_m3": 23.06, "surface_m2": 23.66, "depth_m": 1.07, "manufacturer": "Bestway"},

    # ---- Bestway Power Steel (rectangular & oval) — 90% fill ----
    {"slug": "bestway_power_steel_404_201_100",      "name": "Bestway Power Steel 404×201×100 cm",      "shape": "rect", "volume_m3": 6.48,  "surface_m2": 8.12,  "depth_m": 0.84, "manufacturer": "Bestway"},
    {"slug": "bestway_power_steel_488_244_122",      "name": "Bestway Power Steel 488×244×122 cm",      "shape": "rect", "volume_m3": 11.53, "surface_m2": 11.91, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_power_steel_oval_549_274_122", "name": "Bestway Power Steel Oval 549×274×122 cm", "shape": "oval", "volume_m3": 13.43, "surface_m2": 11.81, "depth_m": 1.07, "manufacturer": "Bestway"},

    # ---- Bestway Hydrium (steel wall) — 90% fill ----
    {"slug": "bestway_hydrium_360_120",          "name": "Bestway Hydrium 360×120 cm",          "shape": "round", "volume_m3": 10.99, "surface_m2": 10.18, "depth_m": 1.10, "manufacturer": "Bestway"},
    {"slug": "bestway_hydrium_460_120",          "name": "Bestway Hydrium 460×120 cm",          "shape": "round", "volume_m3": 17.43, "surface_m2": 16.62, "depth_m": 1.10, "manufacturer": "Bestway"},
    {"slug": "bestway_hydrium_oval_610_360_120", "name": "Bestway Hydrium Oval 610×360×120 cm", "shape": "oval",  "volume_m3": 19.93, "surface_m2": 17.25, "depth_m": 1.10, "manufacturer": "Bestway"},

    # ---- Generic in-ground pools ----
    {"slug": "inground_small_25",  "name": "Piscine enterrée ~25 m³ (6×3×1.4)",  "shape": "rect", "volume_m3": 25.0, "surface_m2": 18.0, "depth_m": 1.40, "manufacturer": "Generic"},
    {"slug": "inground_med_40",    "name": "Piscine enterrée ~40 m³ (8×4×1.4)",  "shape": "rect", "volume_m3": 40.0, "surface_m2": 32.0, "depth_m": 1.40, "manufacturer": "Generic"},
    {"slug": "inground_large_60",  "name": "Piscine enterrée ~60 m³ (10×5×1.5)", "shape": "rect", "volume_m3": 60.0, "surface_m2": 50.0, "depth_m": 1.50, "manufacturer": "Generic"},
    {"slug": "inground_xl_90",     "name": "Piscine enterrée ~90 m³ (12×6×1.5)", "shape": "rect", "volume_m3": 90.0, "surface_m2": 72.0, "depth_m": 1.60, "manufacturer": "Generic"},
    {"slug": "inground_round_30",  "name": "Piscine ronde enterrée 6×1.4 m",     "shape": "round","volume_m3": 28.3, "surface_m2": 28.3, "depth_m": 1.40, "manufacturer": "Generic"},

    # ---- Custom (geometry-only; user provides volume/surface/depth) ----
    # Custom is handled separately in the config flow — not in this list.
]

PRESET_CUSTOM = "custom"


def get_preset(slug: str) -> dict | None:
    for p in POOL_PRESETS:
        if p["slug"] == slug:
            return p
    return None


def compute_tau_hours(preset: dict, *, with_cover: bool = False) -> float:
    """Empirical tau (hours) for the lumped 1st-order thermal model.

    The dominant heat exchange mode for residential outdoor pools is
    evaporation, which scales roughly with the water surface area. The
    thermal capacity scales with volume. A useful proxy is the depth
    (volume / surface), capturing how "thick" the water layer is.

    Aboveground frame pools are wind-exposed and conductive through thin
    vinyl/steel walls (factor 0.8). In-ground pools are sheltered and
    lossy through soil (factor 1.2). Generic in-ground presets use the
    higher factor.
    """
    depth = float(preset["depth_m"])
    mfr = preset.get("manufacturer", "")
    exposure_factor = 1.2 if mfr == "Generic" else 0.8
    cover_factor = 2.5 if with_cover else 1.0
    return depth * exposure_factor * cover_factor * 20.0


def render_pool_svg(
    preset: dict,
    *,
    state: str = "idle",  # idle | running | forced_off | unavailable
    temperature: float | None = None,
    duration_hours: float | None = None,
    width: int = 360,
    height: int = 200,
) -> str:
    """Render an inline SVG for the dashboard card.

    The shape (round/rect/oval) and aspect ratio are taken from the preset.
    Color reflects pump state. Labels show the model name and key facts.
    """
    shape: ShapeKind = preset.get("shape", "rect")  # type: ignore[assignment]
    name = preset.get("name", "Piscine")
    volume = preset.get("volume_m3")
    depth = preset.get("depth_m")

    palette = {
        "idle": ("#7BC1E5", "#4A90B8"),
        "running": ("#1FA0E3", "#0B5C8A"),
        "forced_off": ("#9AA7B0", "#5C6B73"),
        "unavailable": ("#D4D7DA", "#6B7178"),
    }
    fill, stroke = palette.get(state, palette["idle"])

    pad = 24
    inner_w = width - 2 * pad
    inner_h = height - 2 * pad - 36  # leave 36px at bottom for labels

    # Compute the drawable shape so the bounding box matches dimensions.
    elem = ""
    if shape == "round":
        radius = min(inner_w, inner_h) / 2
        cx, cy = width / 2, pad + radius
        elem = (
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
            f'fill="url(#water)" stroke="{stroke}" stroke-width="3" />'
        )
    elif shape == "oval":
        rx = inner_w / 2
        ry = inner_h / 2
        cx, cy = width / 2, pad + ry
        elem = (
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'fill="url(#water)" stroke="{stroke}" stroke-width="3" />'
        )
    else:  # rect
        # Use a slightly rounded rectangle for visual softness.
        x, y = pad, pad
        elem = (
            f'<rect x="{x}" y="{y}" width="{inner_w}" height="{inner_h}" '
            f'rx="14" ry="14" fill="url(#water)" stroke="{stroke}" stroke-width="3" />'
        )

    # Ripple lines when running.
    ripples = ""
    if state == "running":
        for i, (frac_y, w_frac) in enumerate(((0.35, 0.55), (0.55, 0.45), (0.75, 0.35))):
            cy = pad + inner_h * frac_y
            cx = width / 2
            half = inner_w * w_frac / 2
            ripples += (
                f'<path d="M {cx-half:.1f} {cy:.1f} '
                f'q {half/2:.1f} -6 {half:.1f} 0 '
                f't {half:.1f} 0" '
                f'stroke="#FFFFFFAA" stroke-width="2" fill="none" />'
            )

    # State badge.
    badge_text = {
        "running": "POMPE",
        "idle": "veille",
        "forced_off": "ARRÊT",
        "unavailable": "?",
    }.get(state, "veille")
    badge_color = {
        "running": "#1FA0E3",
        "idle": "#7BC1E5",
        "forced_off": "#6B7178",
        "unavailable": "#9AA7B0",
    }.get(state, "#7BC1E5")

    # Bottom labels.
    label_y = height - 14
    vol_text = f"{volume:.1f} m³" if isinstance(volume, (int, float)) else "?"
    depth_text = f"{depth:.2f} m" if isinstance(depth, (int, float)) else "?"
    temp_text = f"{temperature:.1f}°C" if isinstance(temperature, (int, float)) else "—"
    dur_text = (
        f"{duration_hours:.1f} h"
        if isinstance(duration_hours, (int, float))
        else "—"
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" preserveAspectRatio="xMidYMid meet">
  <defs>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{fill}" />
      <stop offset="100%" stop-color="{stroke}" />
    </linearGradient>
  </defs>
  <text x="{pad}" y="18" font-family="sans-serif" font-size="13" font-weight="600" fill="#222">{name}</text>
  {elem}
  {ripples}
  <rect x="{width - pad - 64}" y="6" width="64" height="20" rx="10" fill="{badge_color}" />
  <text x="{width - pad - 32}" y="20" text-anchor="middle" font-family="sans-serif" font-size="11" fill="white" font-weight="700">{badge_text}</text>
  <text x="{pad}" y="{label_y}" font-family="sans-serif" font-size="11" fill="#444">Vol: {vol_text} · Prof: {depth_text} · T° eau: {temp_text} · Filt: {dur_text}</text>
</svg>'''
