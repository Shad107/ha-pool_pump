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


def compute_solar_coefficient(preset: dict | None) -> float | None:
    """Physics-derived k_sun (°C / hour at full sun) for the preset.

    From the energy balance: at peak solar input (~800 W/m² absorbed),
    a pool warms at:

        dT/dt = (irradiance × surface × absorptivity) / (volume × ρ × c)
              = (800 × surface × 0.8) / (volume × 1000 × 4180)  [°C/s]
              ≈ 0.69 × surface_m² / volume_m³                     [°C/h]

    Returns None if the preset lacks volume_m3 or surface_m2 (custom
    pools without geometry), so the caller can fall back to a sane
    default such as 0.6 °C/h.
    """
    if not preset:
        return None
    vol = preset.get("volume_m3")
    surf = preset.get("surface_m2")
    if not (isinstance(vol, (int, float)) and isinstance(surf, (int, float))):
        return None
    if vol <= 0 or surf <= 0:
        return None
    return round(0.69 * surf / vol, 3)




def _project_3q(x: float, y: float, z: float, scale: float) -> tuple[float, float]:
    """Axonometric 3/4 view projection.

    World coords:
        x = length along the long axis (right)
        y = width / depth into screen (away from viewer, top-left in image)
        z = vertical drop into the pool from water surface (down)

    Returns (screen_x, screen_y) in pixels, before any canvas offset.
    Viewer is at upper-front-right corner of the pool, so we see:
      - top water surface (parallelogram)
      - front face (rectangle)
      - left side wall (parallelogram)
    The right side and the back walls are hidden.
    """
    sx = (x - 0.5 * y) * scale
    sy = (z - 0.4 * y) * scale
    return sx, sy


def _pool_real_dims(preset: dict) -> tuple[float, float, float]:
    """Return (length_m, width_m, depth_m) for the preset.

    For round pools, length=width=diameter; depth from preset.
    For rect/oval, uses length_m/width_m if present, else derives an
    L:W ratio of 1.77 from surface_m2.
    """
    shape = preset.get("shape", "rect")
    depth = float(preset.get("depth_m") or 1.0)
    L = float(preset.get("length_m") or 0)
    W = float(preset.get("width_m") or 0)
    if L > 0 and W > 0:
        return L, W, depth
    surf = float(preset.get("surface_m2") or 0)
    if shape == "round" and surf > 0:
        from math import pi, sqrt
        d = 2 * sqrt(surf / pi)
        return d, d, depth
    # Fallback: assume 1.77:1
    if surf > 0:
        # surf = L · W = L · L/1.77 → L = sqrt(surf · 1.77)
        from math import sqrt
        L = sqrt(surf * 1.77)
        W = L / 1.77
        return L, W, depth
    return 4.0, 2.0, depth


def render_pool_svg(
    preset: dict,
    *,
    state: str = "idle",
    temperature: float | None = None,
    duration_hours: float | None = None,
    width: int = 360,
    height: int = 220,
) -> str:
    """Render an axonometric 3/4 view of the pool.

    The pool is drawn as if seen from the upper-front-right of a
    poolside terrace: top water surface as a parallelogram (or
    foreshortened ellipse for round pools), front wall as a vertical
    rectangle, and the left side wall visible as another parallelogram.
    For round/oval pools the surface is an ellipse with horizontal
    radius unchanged and vertical radius squashed by perspective.
    """
    shape = preset.get("shape", "rect")
    volume = preset.get("volume_m3")
    depth = preset.get("depth_m")
    mfr = preset.get("manufacturer", "")
    aboveground = mfr in ("Intex", "Bestway")
    slug = preset.get("slug", "")

    # Frame style derived from slug/manufacturer — drives the look:
    #   inflatable_ring: Intex Easy Set — blue donut on the rim, vinyl wall
    #   metal_frame:     Intex Frame/Prism/Ultra XTR + Bestway Steel/Power/Hydrium
    #                    — silver top rail + visible vertical posts
    #   stone_coping:    in-ground — stone rim, no aboveground wall
    if "easy_set" in slug:
        frame_style = "inflatable_ring"
    elif aboveground:
        frame_style = "metal_frame"
    else:
        frame_style = "stone_coping"

    # Wall colors per frame style:
    # - inflatable_ring (Easy Set): vinyl bleu marine
    # - metal_frame (Frame / Ultra XTR / Steel Pro / Power Steel): vinyl
    #   navy + montants silver
    # - stone_coping (in-ground): pierre crème
    if frame_style == "inflatable_ring":
        wall_top = "#1A4A7A"
        wall_bot = "#0B2748"
        wall_side_bot = "#061730"
    elif frame_style == "metal_frame":
        wall_top = "#1F2E4A"
        wall_bot = "#0B1424"
        wall_side_bot = "#050B16"
    else:
        wall_top = "#D8D2C2"
        wall_bot = "#9A937F"
        wall_side_bot = "#7A7466"

    palette = {
        "idle":        {"top": "#7BC1E5", "mid": "#2F95C8", "bot": "#0F4A78", "tile": "#3a8fc5", "highlight": "#FFFFFFAA"},
        "running":     {"top": "#5FB5E5", "mid": "#1F90D6", "bot": "#0A4B7A", "tile": "#1F84BD", "highlight": "#FFFFFFDD"},
        "forced_off":  {"top": "#B0BCC4", "mid": "#7E8C95", "bot": "#4A555C", "tile": "#5d6970", "highlight": "#FFFFFF66"},
        "unavailable": {"top": "#D4D7DA", "mid": "#9aa0a4", "bot": "#5C6268", "tile": "#7e858a", "highlight": "#FFFFFF55"},
    }
    pal = palette.get(state, palette["idle"])
    pal = {**pal, "wall_top": wall_top, "wall_bot": wall_bot, "wall_side_bot": wall_side_bot}

    pad_x = 22
    pad_top = 20
    pad_bot = 30

    L, W, D = _pool_real_dims(preset)

    # Compute scale so the projected pool fits in the inner canvas
    proj_w = L + 0.5 * W   # x-extent of the projected box
    proj_h = D + 0.4 * W   # y-extent
    inner_w = width - 2 * pad_x
    inner_h = height - pad_top - pad_bot
    scale = min(inner_w / proj_w, inner_h / proj_h) * 0.92

    # Center the projected pool in the canvas
    proj_w_px = proj_w * scale
    proj_h_px = proj_h * scale
    origin_x = (width - proj_w_px) / 2 + 0.5 * W * scale  # back-top-left has x = +0.5W·scale
    origin_y = pad_top + 0.4 * W * scale

    def P(x, y, z):
        sx, sy = _project_3q(x, y, z, scale)
        return origin_x + sx, origin_y + sy

    # 8 corners of the pool box
    # x ∈ [0,L], y ∈ [0,W], z ∈ [0,D]; z=0 is water surface, z=D is floor
    FTL = P(0, 0, 0)     # Front-Top-Left
    FTR = P(L, 0, 0)
    BTL = P(0, W, 0)     # Back-Top-Left
    BTR = P(L, W, 0)
    FBL = P(0, 0, D)
    FBR = P(L, 0, D)
    BBL = P(0, W, D)
    BBR = P(L, W, D)

    # Surface paths
    if shape == "round" or shape == "oval":
        # Top water: ellipse with rx = L/2 · scale, ry = (W/2) · 0.4 · scale  (squashed)
        cx_top = (FTL[0] + BTR[0]) / 2  # rough center
        cy_top = (FTL[1] + BTR[1]) / 2
        rx_top = (L / 2) * scale
        ry_top = (W / 2) * 0.4 * scale
        water_surface = (
            f'<ellipse class="pool-water" cx="{cx_top:.1f}" cy="{cy_top:.1f}" '
            f'rx="{rx_top:.1f}" ry="{ry_top:.1f}" fill="url(#water)" />'
        )
        # Front-curved wall: ellipse arc going from the front-bottom edge of the surface to the floor
        front_y = cy_top + ry_top
        floor_y = front_y + D * scale
        # Cylinder side: draw a path from (cx-rx, front_y) down to (cx-rx, floor_y) arc to (cx+rx, floor_y) up to (cx+rx, front_y)
        # Use an arc for the bottom curve too
        side_wall = (
            f'<path d="M {cx_top-rx_top:.1f} {front_y:.1f} '
            f'L {cx_top-rx_top:.1f} {floor_y:.1f} '
            f'A {rx_top:.1f} {ry_top:.1f} 0 0 0 {cx_top+rx_top:.1f} {floor_y:.1f} '
            f'L {cx_top+rx_top:.1f} {front_y:.1f} '
            f'A {rx_top:.1f} {ry_top:.1f} 0 0 1 {cx_top-rx_top:.1f} {front_y:.1f} Z" '
            f'fill="url(#wall_grad)" />'
        )
        coping_shape = (
            f'<ellipse cx="{cx_top:.1f}" cy="{cy_top:.1f}" '
            f'rx="{rx_top+3:.1f}" ry="{ry_top+1.5:.1f}" '
            f'fill="none" stroke="url(#coping)" stroke-width="4" />'
        )
        tile_band = (
            f'<ellipse cx="{cx_top:.1f}" cy="{cy_top:.1f}" '
            f'rx="{rx_top-3:.1f}" ry="{ry_top-1.5:.1f}" '
            f'fill="none" stroke="{pal["tile"]}" stroke-width="2.5" '
            f'stroke-dasharray="5 2" opacity="0.85" />'
        )
        bbox = (cx_top - rx_top, cy_top - ry_top, cx_top + rx_top, cy_top + ry_top)
    else:
        # Rectangular: water surface as a parallelogram polygon
        water_surface = (
            f'<polygon class="pool-water" '
            f'points="{BTL[0]:.1f},{BTL[1]:.1f} '
            f'{BTR[0]:.1f},{BTR[1]:.1f} '
            f'{FTR[0]:.1f},{FTR[1]:.1f} '
            f'{FTL[0]:.1f},{FTL[1]:.1f}" '
            f'fill="url(#water)" />'
        )
        # Front wall: vertical rectangle (visible face)
        # Left side wall: parallelogram (BTL → FTL → FBL → BBL)
        side_wall = (
            f'<polygon points="'
            f'{FTL[0]:.1f},{FTL[1]:.1f} '
            f'{FTR[0]:.1f},{FTR[1]:.1f} '
            f'{FBR[0]:.1f},{FBR[1]:.1f} '
            f'{FBL[0]:.1f},{FBL[1]:.1f}" '
            f'fill="url(#wall_grad)" />'
            f'<polygon points="'
            f'{BTL[0]:.1f},{BTL[1]:.1f} '
            f'{FTL[0]:.1f},{FTL[1]:.1f} '
            f'{FBL[0]:.1f},{FBL[1]:.1f} '
            f'{BBL[0]:.1f},{BBL[1]:.1f}" '
            f'fill="url(#wall_grad_side)" opacity="0.85" />'
        )
        # Coping (white rim) — drawn as a slightly larger parallelogram outline behind the water
        ext = 3 * scale / 50
        coping_shape = (
            f'<polygon points="'
            f'{BTL[0]-ext:.1f},{BTL[1]-ext:.1f} '
            f'{BTR[0]+ext:.1f},{BTR[1]-ext:.1f} '
            f'{FTR[0]+ext:.1f},{FTR[1]+ext:.1f} '
            f'{FTL[0]-ext:.1f},{FTL[1]+ext:.1f}" '
            f'fill="none" stroke="url(#coping)" stroke-width="4" />'
        )
        # Tile band: smaller parallelogram inside
        inset = max(3.0, 6 * scale / 100)
        tile_band = (
            f'<polygon points="'
            f'{BTL[0]+inset:.1f},{BTL[1]+inset*0.5:.1f} '
            f'{BTR[0]-inset:.1f},{BTR[1]+inset*0.5:.1f} '
            f'{FTR[0]-inset:.1f},{FTR[1]-inset*0.5:.1f} '
            f'{FTL[0]+inset:.1f},{FTL[1]-inset*0.5:.1f}" '
            f'fill="none" stroke="{pal["tile"]}" stroke-width="2" '
            f'stroke-dasharray="5 2" opacity="0.85" />'
        )
        bbox = (
            min(BTL[0], FTL[0]),
            BTL[1],
            max(BTR[0], FTR[0]),
            FTR[1],
        )

    # Ripples on the water surface — running state
    ripples = ""
    if state == "running":
        bl, bt, br, bb = bbox
        wbox = br - bl
        hbox = max(bb - bt, 1)
        cxw = (bl + br) / 2
        for fy, fw in ((0.42, 0.55), (0.62, 0.45), (0.80, 0.35)):
            ry_pos = bt + hbox * fy
            half = wbox * fw / 2
            ripples += (
                f'<path d="M {cxw-half:.1f} {ry_pos:.1f} '
                f'q {half/2:.1f} -3 {half:.1f} 0 '
                f't {half:.1f} 0" '
                f'stroke="{pal["highlight"]}" stroke-width="1.6" '
                f'fill="none" stroke-linecap="round" />'
            )

    # Sun glint on the surface
    glint_cx = (bbox[0] + bbox[2]) / 2 - (bbox[2] - bbox[0]) * 0.18
    glint_cy = (bbox[1] + bbox[3]) / 2 - (bbox[3] - bbox[1]) * 0.20
    glint = (
        f'<ellipse cx="{glint_cx:.1f}" cy="{glint_cy:.1f}" '
        f'rx="{(bbox[2]-bbox[0])*0.14:.1f}" ry="{(bbox[3]-bbox[1])*0.06:.1f}" '
        f'fill="#FFFFFF" opacity="0.35" transform="rotate(-12 {glint_cx:.1f} {glint_cy:.1f})" />'
    )

    # Product-specific frame overlay
    frame_overlay = ""
    if frame_style == "inflatable_ring":
        # Intex Easy Set: blue inflated tube around the rim. Drawn as a
        # thick rounded outline ABOVE the coping, with a lighter highlight
        # on top to suggest the tube's roundness.
        if shape == "round" or shape == "oval":
            ring_rx = (bbox[2] - bbox[0]) / 2
            ring_ry = (bbox[3] - bbox[1]) / 2
            ring_cx = (bbox[0] + bbox[2]) / 2
            ring_cy = (bbox[1] + bbox[3]) / 2
            frame_overlay = (
                f'<ellipse cx="{ring_cx:.1f}" cy="{ring_cy:.1f}" '
                f'rx="{ring_rx+4:.1f}" ry="{ring_ry+2:.1f}" '
                f'fill="none" stroke="#1E5AA6" stroke-width="5" stroke-linecap="round" />'
                f'<ellipse cx="{ring_cx:.1f}" cy="{ring_cy:.1f}" '
                f'rx="{ring_rx+4:.1f}" ry="{ring_ry+2:.1f}" '
                f'fill="none" stroke="#7AB3E0" stroke-width="1.5" stroke-dasharray="20 80" stroke-linecap="round" />'
            )
        else:
            # rectangular Easy Set is rare but we still handle it
            frame_overlay = (
                f'<polygon points="'
                f'{BTL[0]-3:.1f},{BTL[1]-2:.1f} '
                f'{BTR[0]+3:.1f},{BTR[1]-2:.1f} '
                f'{FTR[0]+3:.1f},{FTR[1]+2:.1f} '
                f'{FTL[0]-3:.1f},{FTL[1]+2:.1f}" '
                f'fill="none" stroke="#1E5AA6" stroke-width="5" stroke-linejoin="round" />'
            )
    elif frame_style == "metal_frame":
        # Silver top rail + vertical posts at corners + middle of long sides.
        # The rail sits ON the coping; posts go from the rail to the floor.
        post_color = "#C8CDD3"
        post_stroke = "#7A8088"
        rail_color = "#D9DCE0"
        if shape == "round" or shape == "oval":
            ring_rx = (bbox[2] - bbox[0]) / 2
            ring_ry = (bbox[3] - bbox[1]) / 2
            ring_cx = (bbox[0] + bbox[2]) / 2
            ring_cy = (bbox[1] + bbox[3]) / 2
            # Top rail = a slightly thicker ellipse stroke outside the coping
            frame_overlay = (
                f'<ellipse cx="{ring_cx:.1f}" cy="{ring_cy:.1f}" '
                f'rx="{ring_rx+2:.1f}" ry="{ring_ry+1:.1f}" '
                f'fill="none" stroke="{rail_color}" stroke-width="2.5" />'
            )
            # 4 visible vertical posts (front, left, right, and the back is hidden)
            floor_y = ring_cy + ring_ry + D * scale
            for fx in (-0.95, -0.5, 0.4, 0.85):
                post_top_x = ring_cx + ring_rx * fx
                # approximate y on the ellipse at this x
                # (x/rx)² + (y/ry)² = 1 → y = ry × √(1 - (x/rx)²)
                from math import sqrt
                t = (fx) ** 2
                if t >= 1:
                    continue
                post_top_y = ring_cy + ring_ry * sqrt(1 - t)
                post_bot_y = post_top_y + D * scale
                frame_overlay += (
                    f'<line x1="{post_top_x:.1f}" y1="{post_top_y:.1f}" '
                    f'x2="{post_top_x:.1f}" y2="{post_bot_y:.1f}" '
                    f'stroke="{post_color}" stroke-width="2.2" stroke-linecap="round" />'
                )
        else:
            # Rectangular frame: rail along the top edges + 4 corner posts
            # + middle posts on long sides
            frame_overlay = (
                f'<polyline points="'
                f'{BTL[0]:.1f},{BTL[1]:.1f} '
                f'{BTR[0]:.1f},{BTR[1]:.1f} '
                f'{FTR[0]:.1f},{FTR[1]:.1f} '
                f'{FTL[0]:.1f},{FTL[1]:.1f} '
                f'{BTL[0]:.1f},{BTL[1]:.1f}" '
                f'fill="none" stroke="{rail_color}" stroke-width="2.5" stroke-linejoin="round" />'
            )
            # Corner posts (4 visible)
            for top, bot in [(FTL, FBL), (FTR, FBR), (BTL, BBL)]:
                frame_overlay += (
                    f'<line x1="{top[0]:.1f}" y1="{top[1]:.1f}" '
                    f'x2="{bot[0]:.1f}" y2="{bot[1]:.1f}" '
                    f'stroke="{post_color}" stroke-width="2.4" stroke-linecap="round" />'
                )
            # Mid post on the long front edge for big pools
            if L > 4:
                mid_top_x = (FTL[0] + FTR[0]) / 2
                mid_top_y = (FTL[1] + FTR[1]) / 2
                mid_bot_x = (FBL[0] + FBR[0]) / 2
                mid_bot_y = (FBL[1] + FBR[1]) / 2
                frame_overlay += (
                    f'<line x1="{mid_top_x:.1f}" y1="{mid_top_y:.1f}" '
                    f'x2="{mid_bot_x:.1f}" y2="{mid_bot_y:.1f}" '
                    f'stroke="{post_color}" stroke-width="2.4" stroke-linecap="round" />'
                )

    # Aboveground ladder, drawn on the right side of the front wall going down
    ladder = ""
    if aboveground and shape != "round" and shape != "oval":
        lx = FTR[0] - 16
        ly_top = FTR[1] - 3
        ly_bot = FBR[1] + 3
        ladder = f'''
        <g stroke="#D5D8DC" stroke-width="1.8" fill="none" stroke-linecap="round" filter="url(#ladder_shadow)">
          <line x1="{lx:.1f}" y1="{ly_top:.1f}" x2="{lx:.1f}" y2="{ly_bot:.1f}"/>
          <line x1="{lx + 6:.1f}" y1="{ly_top:.1f}" x2="{lx + 6:.1f}" y2="{ly_bot:.1f}"/>
          <line x1="{lx:.1f}" y1="{ly_top + 4:.1f}" x2="{lx + 6:.1f}" y2="{ly_top + 4:.1f}"/>
          <line x1="{lx:.1f}" y1="{(ly_top + ly_bot)/2:.1f}" x2="{lx + 6:.1f}" y2="{(ly_top + ly_bot)/2:.1f}"/>
          <line x1="{lx:.1f}" y1="{ly_bot - 4:.1f}" x2="{lx + 6:.1f}" y2="{ly_bot - 4:.1f}"/>
        </g>'''
    elif aboveground:
        # Round/oval: ladder on the right of the cylinder
        bl, bt, br, bb = bbox
        lx = br - 6
        ly_top = bt + (bb - bt) * 0.5
        ly_bot = bb + D * scale * 0.9
        ladder = f'''
        <g stroke="#D5D8DC" stroke-width="1.8" fill="none" stroke-linecap="round" filter="url(#ladder_shadow)">
          <line x1="{lx:.1f}" y1="{ly_top:.1f}" x2="{lx:.1f}" y2="{ly_bot:.1f}"/>
          <line x1="{lx + 6:.1f}" y1="{ly_top:.1f}" x2="{lx + 6:.1f}" y2="{ly_bot:.1f}"/>
          <line x1="{lx:.1f}" y1="{ly_top + 6:.1f}" x2="{lx + 6:.1f}" y2="{ly_top + 6:.1f}"/>
          <line x1="{lx:.1f}" y1="{(ly_top + ly_bot)/2:.1f}" x2="{lx + 6:.1f}" y2="{(ly_top + ly_bot)/2:.1f}"/>
          <line x1="{lx:.1f}" y1="{ly_bot - 6:.1f}" x2="{lx + 6:.1f}" y2="{ly_bot - 6:.1f}"/>
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
    <linearGradient id="wall_grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="{pal["wall_top"]}" />
      <stop offset="100%" stop-color="{pal["wall_bot"]}" />
    </linearGradient>
    <linearGradient id="wall_grad_side" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"  stop-color="{pal["wall_top"]}" />
      <stop offset="100%" stop-color="{pal["wall_side_bot"]}" />
    </linearGradient>
    <linearGradient id="grass_grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="#7FB85A" />
      <stop offset="100%" stop-color="#4F8E3A" />
    </linearGradient>
    <pattern id="grass" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
      <rect width="24" height="24" fill="url(#grass_grad)" />
      <line x1="3" y1="24" x2="3" y2="18" stroke="#9CC369" stroke-opacity="0.7" stroke-width="0.6" stroke-linecap="round"/>
      <line x1="7" y1="24" x2="7" y2="20" stroke="#3E7A28" stroke-opacity="0.6" stroke-width="0.6" stroke-linecap="round"/>
      <line x1="11" y1="24" x2="11" y2="17" stroke="#A6CD7B" stroke-opacity="0.65" stroke-width="0.6" stroke-linecap="round"/>
      <line x1="15" y1="24" x2="15" y2="19" stroke="#5B9842" stroke-opacity="0.7" stroke-width="0.6" stroke-linecap="round"/>
      <line x1="19" y1="24" x2="19" y2="20" stroke="#85B860" stroke-opacity="0.6" stroke-width="0.6" stroke-linecap="round"/>
      <line x1="22" y1="24" x2="22" y2="18" stroke="#4A8633" stroke-opacity="0.65" stroke-width="0.6" stroke-linecap="round"/>
      <line x1="1" y1="12" x2="1" y2="7" stroke="#6BAA4E" stroke-opacity="0.55" stroke-width="0.5" stroke-linecap="round"/>
      <line x1="9" y1="11" x2="9" y2="6" stroke="#8FBD6B" stroke-opacity="0.55" stroke-width="0.5" stroke-linecap="round"/>
      <line x1="17" y1="13" x2="17" y2="7" stroke="#4F8E3A" stroke-opacity="0.5" stroke-width="0.5" stroke-linecap="round"/>
    </pattern>
    <filter id="ladder_shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0.5" dy="1" stdDeviation="0.6" flood-opacity="0.35" />
    </filter>
  </defs>

  <rect x="0" y="0" width="{width}" height="{height}" fill="url(#grass)" rx="12" ry="12" />
  <rect x="0" y="0" width="{width}" height="{height}" fill="none" stroke="#3E7A28" stroke-opacity="0.45" stroke-width="1" rx="12" ry="12" />

  <!-- Visible side wall + front face (drawn first, behind the water rim) -->
  {side_wall}

  <!-- Concrete coping outline -->
  {coping_shape}

  <!-- Water surface -->
  {water_surface}

  <!-- Tile band inside the water -->
  {tile_band}

  <!-- Sun glint and ripples -->
  {glint}
  {ripples}

  <!-- Product-specific frame overlay (top rail + posts, or inflatable ring) -->
  {frame_overlay}

  <!-- Ladder for aboveground pools -->
  {ladder}

  <!-- State badge (top-right) -->
  <rect x="{width - pad_x - 64}" y="8" width="64" height="20" rx="10" fill="{badge_color}" />
  <text x="{width - pad_x - 32}" y="22" text-anchor="middle" font-family="sans-serif" font-size="10.5" fill="white" font-weight="700">{badge_text}</text>

  <!-- Compact bottom label -->
  <text x="{width / 2:.1f}" y="{label_y}" text-anchor="middle" font-family="sans-serif" font-size="10.5" fill="white" stroke="#1f3d12" stroke-width="0.4" font-weight="600" opacity="0.95">{bottom_label}</text>
</svg>'''
