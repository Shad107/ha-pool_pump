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
    {"slug": "intex_easy_set_244_61",  "name": "Intex Easy Set 244×61 cm (ronde)", "shape": "round", "volume_m3": 1.94,  "surface_m2": 4.67,  "depth_m": 0.51, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_305_61",  "name": "Intex Easy Set 305×61 cm (ronde)", "shape": "round", "volume_m3": 3.08,  "surface_m2": 7.30,  "depth_m": 0.51, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_305_76",  "name": "Intex Easy Set 305×76 cm (ronde)", "shape": "round", "volume_m3": 3.85,  "surface_m2": 7.30,  "depth_m": 0.66, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_366_76",  "name": "Intex Easy Set 366×76 cm (ronde)", "shape": "round", "volume_m3": 5.62,  "surface_m2": 10.52, "depth_m": 0.61, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_396_84",  "name": "Intex Easy Set 396×84 cm (ronde)", "shape": "round", "volume_m3": 7.29,  "surface_m2": 12.32, "depth_m": 0.74, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_457_107", "name": "Intex Easy Set 457×107 cm (ronde)", "shape": "round", "volume_m3": 12.43, "surface_m2": 16.40, "depth_m": 0.94, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_457_122", "name": "Intex Easy Set 457×122 cm (ronde)", "shape": "round", "volume_m3": 14.14, "surface_m2": 16.40, "depth_m": 0.87, "manufacturer": "Intex"},
    {"slug": "intex_easy_set_549_122", "name": "Intex Easy Set 549×122 cm (ronde)", "shape": "round", "volume_m3": 20.65, "surface_m2": 23.66, "depth_m": 1.07, "manufacturer": "Intex"},

    # ---- Intex Metal Frame / Prism Frame (round) — 90% fill ----
    {"slug": "intex_metal_frame_305_76",  "name": "Intex Metal Frame 305×76 cm (ronde)", "shape": "round", "volume_m3": 4.49,  "surface_m2": 7.30,  "depth_m": 0.66, "manufacturer": "Intex"},
    {"slug": "intex_metal_frame_366_76",  "name": "Intex Metal Frame 366×76 cm (ronde)", "shape": "round", "volume_m3": 6.50,  "surface_m2": 10.52, "depth_m": 0.66, "manufacturer": "Intex"},
    {"slug": "intex_prism_frame_366_99",  "name": "Intex Prism Frame 366×99 cm (ronde)", "shape": "round", "volume_m3": 8.59,  "surface_m2": 10.52, "depth_m": 0.84, "manufacturer": "Intex"},
    {"slug": "intex_prism_frame_457_107", "name": "Intex Prism Frame 457×107 cm (ronde)", "shape": "round", "volume_m3": 14.61, "surface_m2": 16.40, "depth_m": 0.94, "manufacturer": "Intex"},
    {"slug": "intex_prism_frame_457_122", "name": "Intex Prism Frame 457×122 cm (ronde)", "shape": "round", "volume_m3": 16.81, "surface_m2": 16.40, "depth_m": 1.07, "manufacturer": "Intex"},
    {"slug": "intex_prism_frame_549_122", "name": "Intex Prism Frame 549×122 cm (ronde)", "shape": "round", "volume_m3": 24.31, "surface_m2": 23.66, "depth_m": 1.07, "manufacturer": "Intex"},

    # ---- Intex Rectangular Frame / Prism Frame Rectangular — 90% fill ----
    {"slug": "intex_rect_frame_220_150_60",  "name": "Intex Frame 220×150×60 cm (rect.)", "shape": "rect", "volume_m3": 1.66, "surface_m2": 3.30, "length_m": 2.20, "width_m": 1.50, "depth_m": 0.51, "manufacturer": "Intex"},
    {"slug": "intex_rect_frame_300_200_75",  "name": "Intex Frame 300×200×75 cm (rect.)", "shape": "rect", "volume_m3": 3.83, "surface_m2": 6.00, "length_m": 3.00, "width_m": 2.00, "depth_m": 0.65, "manufacturer": "Intex"},
    {"slug": "intex_prism_rect_400_200_100", "name": "Intex Prism Frame 400×200×100 cm (rect.)", "shape": "rect", "volume_m3": 6.84, "surface_m2": 8.00, "length_m": 4.00, "width_m": 2.00, "depth_m": 0.84, "manufacturer": "Intex"},
    {"slug": "intex_prism_rect_400_200_122", "name": "Intex Prism Frame 400×200×122 cm (rect.)", "shape": "rect", "volume_m3": 8.42, "surface_m2": 8.00, "length_m": 4.00, "width_m": 2.00, "depth_m": 1.07, "manufacturer": "Intex"},
    {"slug": "intex_rect_frame_450_220_84",  "name": "Intex Frame 450×220×84 cm (rect.)", "shape": "rect", "volume_m3": 7.13, "surface_m2": 9.90, "length_m": 4.50, "width_m": 2.20, "depth_m": 0.72, "manufacturer": "Intex"},

    # ---- Intex Ultra XTR Frame (round & rectangular) — 90% fill ----
    {"slug": "intex_ultra_xtr_488_122",          "name": "Intex Ultra XTR 488×122 cm (ronde)", "shape": "round", "volume_m3": 19.16, "surface_m2": 18.70, "depth_m": 1.07, "manufacturer": "Intex"},
    {"slug": "intex_ultra_xtr_549_132",          "name": "Intex Ultra XTR 549×132 cm (ronde)", "shape": "round", "volume_m3": 26.42, "surface_m2": 23.66, "depth_m": 1.17, "manufacturer": "Intex"},
    {"slug": "intex_ultra_xtr_rect_549_274_132", "name": "Intex Ultra XTR 549×274×132 cm (rect.)", "shape": "rect",  "volume_m3": 17.20, "surface_m2": 15.04, "length_m": 5.49, "width_m": 2.74, "depth_m": 1.17, "manufacturer": "Intex"},
    {"slug": "intex_ultra_xtr_rect_732_366_132", "name": "Intex Ultra XTR 732×366×132 cm (rect.)", "shape": "rect",  "volume_m3": 31.81, "surface_m2": 26.79, "length_m": 7.32, "width_m": 3.66, "depth_m": 1.17, "manufacturer": "Intex"},

    # ---- Bestway Steel Pro / Steel Pro Max (round) — 90% fill ----
    {"slug": "bestway_steel_pro_244_61",      "name": "Bestway Steel Pro 244×61 cm (ronde)", "shape": "round", "volume_m3": 1.88,  "surface_m2": 4.67,  "depth_m": 0.51, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_366_76",      "name": "Bestway Steel Pro 366×76 cm (ronde)", "shape": "round", "volume_m3": 6.47,  "surface_m2": 10.52, "depth_m": 0.66, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_305_76",  "name": "Bestway Steel Pro Max 305×76 cm (ronde)", "shape": "round", "volume_m3": 4.68,  "surface_m2": 7.30,  "depth_m": 0.66, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_366_122", "name": "Bestway Steel Pro Max 366×122 cm (ronde)", "shape": "round", "volume_m3": 10.25, "surface_m2": 10.52, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_427_84",  "name": "Bestway Steel Pro Max 427×84 cm (ronde)", "shape": "round", "volume_m3": 10.22, "surface_m2": 14.32, "depth_m": 0.72, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_427_122", "name": "Bestway Steel Pro Max 427×122 cm (ronde)", "shape": "round", "volume_m3": 15.23, "surface_m2": 14.32, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_457_122", "name": "Bestway Steel Pro Max 457×122 cm (ronde)", "shape": "round", "volume_m3": 16.02, "surface_m2": 16.40, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_488_122", "name": "Bestway Steel Pro Max 488×122 cm (ronde)", "shape": "round", "volume_m3": 19.48, "surface_m2": 18.70, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_steel_pro_max_549_122", "name": "Bestway Steel Pro Max 549×122 cm (ronde)", "shape": "round", "volume_m3": 23.06, "surface_m2": 23.66, "depth_m": 1.07, "manufacturer": "Bestway"},

    # ---- Bestway Power Steel (rectangular & oval) — 90% fill ----
    {"slug": "bestway_power_steel_404_201_100",      "name": "Bestway Power Steel 404×201×100 cm (rect.)", "shape": "rect", "volume_m3": 6.48,  "surface_m2": 8.12,  "length_m": 4.04, "width_m": 2.01, "depth_m": 0.84, "manufacturer": "Bestway"},
    {"slug": "bestway_power_steel_488_244_122",      "name": "Bestway Power Steel 488×244×122 cm (rect.)", "shape": "rect", "volume_m3": 11.53, "surface_m2": 11.91, "length_m": 4.88, "width_m": 2.44, "depth_m": 1.07, "manufacturer": "Bestway"},
    {"slug": "bestway_power_steel_oval_549_274_122", "name": "Bestway Power Steel Oval 549×274×122 cm (ovale)", "shape": "oval", "volume_m3": 13.43, "surface_m2": 11.81, "length_m": 5.49, "width_m": 2.74, "depth_m": 1.07, "manufacturer": "Bestway"},

    # ---- Bestway Hydrium (steel wall) — 90% fill ----
    {"slug": "bestway_hydrium_360_120",          "name": "Bestway Hydrium 360×120 cm (ronde)", "shape": "round", "volume_m3": 10.99, "surface_m2": 10.18, "depth_m": 1.10, "manufacturer": "Bestway"},
    {"slug": "bestway_hydrium_460_120",          "name": "Bestway Hydrium 460×120 cm (ronde)", "shape": "round", "volume_m3": 17.43, "surface_m2": 16.62, "depth_m": 1.10, "manufacturer": "Bestway"},
    {"slug": "bestway_hydrium_oval_610_360_120", "name": "Bestway Hydrium Oval 610×360×120 cm (ovale)", "shape": "oval",  "volume_m3": 19.93, "surface_m2": 17.25, "length_m": 6.10, "width_m": 3.60, "depth_m": 1.10, "manufacturer": "Bestway"},

    # ---- Generic in-ground pools ----
    {"slug": "inground_small_25",  "name": "Piscine enterrée ~25 m³ (6×3×1.4) (rect.)", "shape": "rect", "volume_m3": 25.0, "surface_m2": 18.0, "length_m": 6.00, "width_m": 3.00, "depth_m": 1.40, "manufacturer": "Generic"},
    {"slug": "inground_med_40",    "name": "Piscine enterrée ~40 m³ (8×4×1.4) (rect.)", "shape": "rect", "volume_m3": 40.0, "surface_m2": 32.0, "length_m": 8.00, "width_m": 4.00, "depth_m": 1.40, "manufacturer": "Generic"},
    {"slug": "inground_large_60",  "name": "Piscine enterrée ~60 m³ (10×5×1.5) (rect.)", "shape": "rect", "volume_m3": 60.0, "surface_m2": 50.0, "length_m": 10.00, "width_m": 5.00, "depth_m": 1.50, "manufacturer": "Generic"},
    {"slug": "inground_xl_90",     "name": "Piscine enterrée ~90 m³ (12×6×1.5) (rect.)", "shape": "rect", "volume_m3": 90.0, "surface_m2": 72.0, "length_m": 12.00, "width_m": 6.00, "depth_m": 1.60, "manufacturer": "Generic"},
    {"slug": "inground_round_30",  "name": "Piscine ronde enterrée 6×1.4 m (ronde)", "shape": "round","volume_m3": 28.3, "surface_m2": 28.3, "depth_m": 1.40, "manufacturer": "Generic"},

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



def _pool_geometry(
    preset: dict,
    *,
    canvas_w: int,
    canvas_h: int,
    coping_w: int,
    wall_h: int,
    pad_x: int,
    pad_top: int,
    pad_bot: int,
) -> tuple[str, float, float, float, float, float, float]:
    """Compute the water/coping bounding box honoring real aspect ratio.

    For round pools the box is a square (matches the diameter). For
    rect/oval pools, if ``length_m`` and ``width_m`` are present in the
    preset, the box is sized to the real ratio length/width, fitted
    inside the available canvas area.
    """
    shape: str = preset.get("shape", "rect")
    inner_w = canvas_w - 2 * pad_x
    inner_h = canvas_h - pad_top - pad_bot - wall_h

    if shape == "round":
        radius = min(inner_w, inner_h) / 2 - coping_w
        cx, cy = canvas_w / 2, pad_top + radius + coping_w
        return shape, cx - radius, cy - radius, cx + radius, cy + radius, cx, cy

    length = float(preset.get("length_m") or 0)
    width = float(preset.get("width_m") or 0)
    ratio = (length / width) if (length > 0 and width > 0) else 1.77

    available_w = inner_w - 2 * coping_w
    available_h = inner_h - 2 * coping_w
    if available_w / max(available_h, 1) > ratio:
        rect_h = available_h
        rect_w = rect_h * ratio
    else:
        rect_w = available_w
        rect_h = rect_w / ratio

    x = (canvas_w - rect_w) / 2
    y = pad_top + coping_w + (available_h - rect_h) / 2
    return shape, x, y, x + rect_w, y + rect_h, x + rect_w / 2, y + rect_h / 2


def render_pool_svg(
    preset: dict,
    *,
    state: str = "idle",
    temperature: float | None = None,
    duration_hours: float | None = None,
    width: int = 360,
    height: int = 220,
) -> str:
    """Render a "looks like a real pool" inline SVG of the chosen preset.

    Includes a wooden deck background with subtle plank lines, a white
    concrete coping, a blue mosaic tile band hugging the water edge,
    caustic light patterns inside the water, a sun glint, pool stairs in
    the upper-right corner, and a side wall + ladder for aboveground
    (Intex/Bestway) pools. Real aspect ratio is honored for rect/oval
    presets that carry length_m/width_m.
    """
    volume = preset.get("volume_m3")
    depth = preset.get("depth_m")
    mfr = preset.get("manufacturer", "")
    aboveground = mfr in ("Intex", "Bestway")

    palette = {
        "idle":        {"top": "#7BC1E5", "mid": "#2F95C8", "bot": "#0F4A78", "tile": "#3a8fc5", "highlight": "#FFFFFFAA"},
        "running":     {"top": "#5FB5E5", "mid": "#1F90D6", "bot": "#0A4B7A", "tile": "#1F84BD", "highlight": "#FFFFFFDD"},
        "forced_off":  {"top": "#B0BCC4", "mid": "#7E8C95", "bot": "#4A555C", "tile": "#5d6970", "highlight": "#FFFFFF66"},
        "unavailable": {"top": "#D4D7DA", "mid": "#9aa0a4", "bot": "#5C6268", "tile": "#7e858a", "highlight": "#FFFFFF55"},
    }
    pal = palette.get(state, palette["idle"])

    pad_x = 22
    pad_top = 14
    pad_bot = 30
    coping_w = 6
    wall_h = 14 if aboveground else 0

    shape_kind, bl, bt, br, bb, cx, cy = _pool_geometry(
        preset,
        canvas_w=width,
        canvas_h=height,
        coping_w=coping_w,
        wall_h=wall_h,
        pad_x=pad_x,
        pad_top=pad_top,
        pad_bot=pad_bot,
    )
    wbox = br - bl
    hbox = bb - bt

    # Pool shapes
    if shape_kind == "round":
        r = wbox / 2
        water_shape = f'<circle class="pool-water" cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#water)" />'
        coping_shape = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r + coping_w:.1f}" fill="none" stroke="url(#coping)" stroke-width="{coping_w*2}" />'
        tile_band = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - 2:.1f}" fill="none" stroke="{pal["tile"]}" stroke-width="3" stroke-dasharray="6 2" opacity="0.85" />'
    elif shape_kind == "oval":
        rx = wbox / 2
        ry = hbox / 2
        water_shape = f'<ellipse class="pool-water" cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="url(#water)" />'
        coping_shape = f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx + coping_w:.1f}" ry="{ry + coping_w:.1f}" fill="none" stroke="url(#coping)" stroke-width="{coping_w*2}" />'
        tile_band = f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx - 2:.1f}" ry="{ry - 2:.1f}" fill="none" stroke="{pal["tile"]}" stroke-width="3" stroke-dasharray="6 2" opacity="0.85" />'
    else:
        rxc = 8
        water_shape = f'<rect class="pool-water" x="{bl:.1f}" y="{bt:.1f}" width="{wbox:.1f}" height="{hbox:.1f}" rx="{rxc}" ry="{rxc}" fill="url(#water)" />'
        coping_shape = f'<rect x="{bl - coping_w:.1f}" y="{bt - coping_w:.1f}" width="{wbox + 2*coping_w:.1f}" height="{hbox + 2*coping_w:.1f}" rx="{rxc + coping_w}" ry="{rxc + coping_w}" fill="none" stroke="url(#coping)" stroke-width="{coping_w*2}" />'
        tile_band = f'<rect x="{bl + 3:.1f}" y="{bt + 3:.1f}" width="{wbox - 6:.1f}" height="{hbox - 6:.1f}" rx="{rxc - 2}" ry="{rxc - 2}" fill="none" stroke="{pal["tile"]}" stroke-width="3" stroke-dasharray="6 2" opacity="0.85" />'

    wall = ""
    if aboveground:
        if shape_kind == "round":
            r = wbox / 2
            wall = (
                f'<path d="M {cx - r - coping_w:.1f} {cy:.1f} '
                f'A {r + coping_w:.1f} {r + coping_w:.1f} 0 0 0 '
                f'{cx + r + coping_w:.1f} {cy:.1f} '
                f'L {cx + r + coping_w:.1f} {cy + wall_h:.1f} '
                f'A {r + coping_w:.1f} {(r + coping_w) * 0.45:.1f} 0 0 1 '
                f'{cx - r - coping_w:.1f} {cy + wall_h:.1f} Z" '
                f'fill="url(#wall)" />'
            )
        elif shape_kind == "oval":
            rx = wbox / 2
            ry = hbox / 2
            wall = (
                f'<path d="M {cx - rx - coping_w:.1f} {cy:.1f} '
                f'A {rx + coping_w:.1f} {ry + coping_w:.1f} 0 0 0 '
                f'{cx + rx + coping_w:.1f} {cy:.1f} '
                f'L {cx + rx + coping_w:.1f} {cy + wall_h:.1f} '
                f'A {rx + coping_w:.1f} {(ry + coping_w) * 0.45:.1f} 0 0 1 '
                f'{cx - rx - coping_w:.1f} {cy + wall_h:.1f} Z" '
                f'fill="url(#wall)" />'
            )
        else:
            wall = f'<rect x="{bl - coping_w:.1f}" y="{bb + coping_w:.1f}" width="{wbox + 2*coping_w:.1f}" height="{wall_h}" rx="2" ry="2" fill="url(#wall)" />'

    # Caustic light patterns inside the water
    caustics = ""
    n_caustics = 6 if state == "running" else 4
    for i in range(n_caustics):
        frac_x = 0.18 + (i % 3) * 0.30
        frac_y = 0.28 + (i // 3) * 0.32 + (i % 2) * 0.08
        cxc = bl + wbox * frac_x
        cyc = bt + hbox * frac_y
        lc = wbox * (0.10 + (i % 2) * 0.04)
        caustics += (
            f'<path d="M {cxc:.1f} {cyc:.1f} '
            f'q {lc/3:.1f} -3 {lc*2/3:.1f} 0 '
            f't {lc:.1f} 0" '
            f'stroke="{pal["highlight"]}" stroke-width="1.2" '
            f'fill="none" stroke-linecap="round" opacity="0.45" />'
        )

    # Surface ripples (running only)
    ripples = ""
    if state == "running":
        cxw = (bl + br) / 2
        for fy, fw in ((0.40, 0.42), (0.58, 0.36), (0.76, 0.28)):
            ry_pos = bt + hbox * fy
            half = wbox * fw / 2
            ripples += (
                f'<path d="M {cxw-half:.1f} {ry_pos:.1f} '
                f'q {half/2:.1f} -4 {half:.1f} 0 '
                f't {half:.1f} 0" '
                f'stroke="{pal["highlight"]}" stroke-width="2" '
                f'fill="none" stroke-linecap="round" />'
            )

    # Pool stairs — top-right corner of the water
    stairs = ""
    if wbox > 60 and hbox > 40:
        sx = br - wbox * 0.16
        sy = bt + hbox * 0.10
        step_w = wbox * 0.12
        for i in range(3):
            stairs += (
                f'<rect x="{sx:.1f}" y="{sy + i * 4:.1f}" '
                f'width="{step_w:.1f}" height="3" '
                f'rx="1.5" ry="1.5" fill="#FFFFFFAA" stroke="#FFFFFFDD" stroke-width="0.5" />'
            )

    # Sun glint — softer ellipse with a secondary sparkle
    gx = bl + wbox * 0.20
    gy = bt + hbox * 0.22
    glint = (
        f'<ellipse cx="{gx:.1f}" cy="{gy:.1f}" '
        f'rx="{wbox * 0.16:.1f}" ry="{hbox * 0.07:.1f}" '
        f'fill="#FFFFFF" opacity="0.30" transform="rotate(-22 {gx:.1f} {gy:.1f})" />'
        f'<ellipse cx="{gx - 8:.1f}" cy="{gy - 4:.1f}" '
        f'rx="{wbox * 0.05:.1f}" ry="{hbox * 0.03:.1f}" '
        f'fill="#FFFFFF" opacity="0.55" transform="rotate(-22 {gx:.1f} {gy:.1f})" />'
    )

    # Ladder for aboveground pools — small chrome rails on the right
    ladder = ""
    if aboveground:
        lx = br + coping_w - 2
        ly_top = bt - 4
        ly_bot = bb + (wall_h if shape_kind == "rect" else wall_h - 2)
        ladder = f'''
        <g stroke="#D5D8DC" stroke-width="2.2" fill="none" stroke-linecap="round" filter="url(#ladder_shadow)">
          <line x1="{lx:.1f}" y1="{ly_top:.1f}" x2="{lx:.1f}" y2="{ly_bot:.1f}"/>
          <line x1="{lx + 7:.1f}" y1="{ly_top:.1f}" x2="{lx + 7:.1f}" y2="{ly_bot:.1f}"/>
          <line x1="{lx:.1f}" y1="{ly_top + 6:.1f}" x2="{lx + 7:.1f}" y2="{ly_top + 6:.1f}"/>
          <line x1="{lx:.1f}" y1="{ly_top + 18:.1f}" x2="{lx + 7:.1f}" y2="{ly_top + 18:.1f}"/>
          <line x1="{lx:.1f}" y1="{ly_top + 30:.1f}" x2="{lx + 7:.1f}" y2="{ly_top + 30:.1f}"/>
        </g>'''

    badge_text = {"running": "POMPE", "idle": "veille", "forced_off": "ARRÊT", "unavailable": "?"}.get(state, "veille")
    badge_color = {"running": "#1FA0E3", "idle": "#A0BFCF", "forced_off": "#6B7178", "unavailable": "#9AA7B0"}.get(state, "#A0BFCF")

    parts = []
    if isinstance(volume, (int, float)):
        parts.append(f"{volume:.1f} m³")
    if isinstance(depth, (int, float)):
        parts.append(f"prof. {depth:.2f} m")
    bottom_label = " · ".join(parts) if parts else ""
    label_y = height - 10

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" preserveAspectRatio="xMidYMid meet">
  <defs>
    <radialGradient id="water" cx="35%" cy="30%" r="80%">
      <stop offset="0%"  stop-color="{pal["top"]}" />
      <stop offset="45%" stop-color="{pal["mid"]}" />
      <stop offset="100%" stop-color="{pal["bot"]}" />
    </radialGradient>
    <linearGradient id="coping" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="#FAF8F2" />
      <stop offset="100%" stop-color="#E8E4D8" />
    </linearGradient>
    <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="#D8CCB8" />
      <stop offset="100%" stop-color="#9E8B73" />
    </linearGradient>
    <linearGradient id="deck" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="#EADFC7" />
      <stop offset="100%" stop-color="#C9B48E" />
    </linearGradient>
    <pattern id="planks" x="0" y="0" width="44" height="240" patternUnits="userSpaceOnUse">
      <rect width="44" height="240" fill="url(#deck)" />
      <line x1="44" y1="0" x2="44" y2="240" stroke="#A99270" stroke-opacity="0.35" stroke-width="0.6" />
      <line x1="0" y1="0" x2="0" y2="240" stroke="#FFFFFF" stroke-opacity="0.15" stroke-width="0.5" />
    </pattern>
    <radialGradient id="deck_shadow" cx="50%" cy="50%" r="55%">
      <stop offset="0%"  stop-color="#000000" stop-opacity="0.18" />
      <stop offset="80%" stop-color="#000000" stop-opacity="0" />
    </radialGradient>
    <filter id="ladder_shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0.5" dy="1" stdDeviation="0.6" flood-opacity="0.35" />
    </filter>
  </defs>

  <rect x="0" y="0" width="{width}" height="{height}" fill="url(#planks)" rx="12" ry="12" />
  <rect x="0" y="0" width="{width}" height="{height}" fill="none" stroke="#A99270" stroke-opacity="0.3" stroke-width="1" rx="12" ry="12" />

  <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{wbox*0.62:.1f}" ry="{hbox*0.62:.1f}" fill="url(#deck_shadow)" />

  {wall}
  {coping_shape}
  {water_shape}
  {tile_band}
  {caustics}
  {glint}
  {stairs}
  {ripples}
  {ladder}

  <rect x="{width - pad_x - 64}" y="8" width="64" height="20" rx="10" fill="{badge_color}" />
  <text x="{width - pad_x - 32}" y="22" text-anchor="middle" font-family="sans-serif" font-size="10.5" fill="white" font-weight="700">{badge_text}</text>
  <text x="{width / 2:.1f}" y="{label_y}" text-anchor="middle" font-family="sans-serif" font-size="10.5" fill="#7a6743" font-weight="500" opacity="0.85">{bottom_label}</text>
</svg>'''
