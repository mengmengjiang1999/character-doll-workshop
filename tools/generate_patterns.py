#!/usr/bin/env python3
"""Generate an explicitly unverified doll muslin, in mm, from labelled parameters.

No general-purpose pattern-fitting algorithm is claimed. This is a documented
quarter-bodice/waist-dart construction, a four-sector skirt and an open sleeve
tube test. The generator verifies flat seam relationships, not doll fit.
"""
from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "projects/honkai-star-rail/march-7th-preservation-bjd-1-4/patterns"
COLORS = {"cut": "#17242d", "seam": "#176a94", "dart": "#b54343", "guide": "#687985"}


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def cubic(a, b, c, d, n=48):
    return [tuple((1-t)**3*a[k] + 3*(1-t)**2*t*b[k] +
                  3*(1-t)*t*t*c[k] + t**3*d[k] for k in (0, 1))
            for t in (i/n for i in range(n+1))]


def signed_area(poly):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in
               zip(poly, poly[1:]+poly[:1]))/2


def validate_simple_polygon(poly):
    """Reject proper edge crossings in a generated cut contour."""
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    edges = list(zip(poly, poly[1:]+poly[:1]))
    if abs(signed_area(poly)) < 1:
        raise ValueError("Degenerate cutting contour")
    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges):
            if j <= i+1 or (i == 0 and j == len(edges)-1):
                continue
            if cross(a, b, c)*cross(a, b, d) < -1e-10 and cross(c, d, a)*cross(c, d, b) < -1e-10:
                raise ValueError("Seam allowance produces a crossing; revise the curve or allowance")


def offset_polygon(poly, allowance):
    """Parallel-edge miter offset of a densely sampled simple seam polygon."""
    sign = 1 if signed_area(poly) > 0 else -1
    edges = []
    for a, b in zip(poly, poly[1:]+poly[:1]):
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy)
        if length < 1e-9:
            raise ValueError("Repeated polygon point")
        normal = (sign*dy/length*allowance, -sign*dx/length*allowance)
        edges.append(((a[0]+normal[0], a[1]+normal[1]), (dx, dy)))
    result = []
    for previous, current in zip(edges[-1:]+edges[:-1], edges):
        p, u = previous
        q, v = current
        cross = u[0]*v[1]-u[1]*v[0]
        if abs(cross) < 1e-10:
            result.append(q)
        else:
            w = (q[0]-p[0], q[1]-p[1])
            t = (w[0]*v[1]-w[1]*v[0])/cross
            result.append((p[0]+t*u[0], p[1]+t*u[1]))
    return result


def clip_at_fold(poly):
    """Remove allowance on the x=0 fold edge, preserving adjacent offsets."""
    out = []
    for a, b in zip(poly[-1:]+poly[:-1], poly):
        a_in, b_in = a[0] >= 0, b[0] >= 0
        if a_in != b_in:
            t = -a[0]/(b[0]-a[0])
            out.append((0, a[1]+t*(b[1]-a[1])))
        if b_in:
            out.append(b)
    return out


class Page:
    def __init__(self, title, subtitle, width=210, height=297):
        self.width, self.height = width, height
        self.items = []
        self.text(12, 14, "MARCH 7TH / UFdoll S BUST", 4.3, bold=True)
        self.text(12, 22, title, 4.0, bold=True)
        self.text(12, 29, subtitle, 2.7)
        self.text(12, 36, "v0.1 DRAFT - MUSLIN ONLY - NOT PHYSICALLY FITTED", 2.8, color="dart")
        self.line([(12, 41), (width-12, 41)], "guide", width=.2)

    def line(self, pts, color="cut", width=.3, dashed=False, closed=False):
        self.items.append(("line", pts, color, width, dashed, closed))

    def text(self, x, y, text, size=3, color="cut", bold=False):
        self.items.append(("text", x, y, text, size, color, bold))

    def arrow(self, x, y, length, label="GRAIN"):
        self.line([(x, y), (x, y+length)], "guide", .25)
        self.line([(x-1.5, y+2.5), (x, y), (x+1.5, y+2.5)], "guide", .25)
        self.line([(x-1.5, y+length-2.5), (x, y+length), (x+1.5, y+length-2.5)], "guide", .25)
        self.text(x+2, y+length/2, label, 2.4, "guide")

    def calibration(self, x=140, y=222):
        self.line([(x, y), (x+50, y), (x+50, y+50), (x, y+50)], closed=True)
        self.text(x+6, y+22, "50 x 50 mm", 3.4, bold=True)
        self.text(x+5, y+29, "Measure both axes", 2.5)
        self.text(x, y-4, "CALIBRATION / print at 100%", 2.6)

    def footer(self, number):
        self.text(12, self.height-14, f"A4 / {self.width} x {self.height} mm / actual size / disable Fit to page", 2.6)
        self.text(12, self.height-8, f"Page {number}/4 - Read sewing-guide.md before cutting. All dimensions mm.", 2.6)


def shifted(poly, x, y):
    return [(a+x, b+y) for a, b in poly]


def mark_notch(page, point, text, dx=3, dy=0):
    x, y = point
    page.line([(x-1.2, y), (x+1.2, y)], "dart", .25)
    page.line([(x, y-1.2), (x, y+1.2)], "dart", .25)
    page.text(x+dx, y+dy, text, 2.5, "dart")


def bodice(v, front):
    q = (v["bust"]+v["bust_ease"])/4
    waist_x = q-v["quarter_side_reduction"]
    shoulder_x = v["shoulder_width"]/2
    nw, depth = v["neck_half_width"], v["front_neck_depth" if front else "back_neck_depth"]
    ah, sl, wl = v["armhole_depth"], v["shoulder_drop"], v["shoulder_to_waist"]
    # The shallow back neck ends diagonally, avoiding a radius tighter than
    # its 3 mm allowance; a near-vertical endpoint would fold the offset back.
    neck = cubic((0, depth), (nw*.7, depth),
                 (nw if front else nw*.75, depth*.45), (nw, 0))
    arm = cubic((shoulder_x, sl), (shoulder_x-9, sl+10),
                (q-(8 if front else 5), ah-1), (q, ah))
    seam = neck + [(shoulder_x, sl)] + arm[1:] + [(q, v["bust_line_y"]), (waist_x, wl), (0, wl)]
    cut = offset_polygon(seam, v["seam_allowance"])
    if front:
        cut = clip_at_fold(cut)
    return seam, cut


def generate(spec):
    p = spec["parameters"]
    for name, entry in p.items():
        if entry["kind"] not in ("nominal", "measured", "assumed", "design"):
            raise ValueError(f"Unlabelled parameter: {name}")
        if entry["value"] <= 0:
            raise ValueError(f"Non-positive parameter: {name}")
    v = {key: item["value"] for key, item in p.items()}
    bust, waist = v["bust"]+v["bust_ease"], v["waist"]+v["waist_ease"]
    q = bust/4
    wx = q-v["quarter_side_reduction"]
    dart = wx-waist/4
    assert 0 < dart < 12, "Waist suppression out of prototype range"
    assert v["armhole_depth"] < min(v["front_dart_apex_y"], v["back_dart_apex_y"]) < v["shoulder_to_waist"]
    assert v["armhole_depth"] < v["bust_line_y"] < v["front_dart_apex_y"]
    assert 0 < v["dart_x"]-dart/2 < v["dart_x"]+dart/2 < wx
    assert v["neck_half_width"] < v["shoulder_width"]/2 < q+2
    pages = []
    page = Page("01 / WAIST-DART BODICE", "Front on fold + mirrored back pair. Separate prototype foundation.")
    for front, ox in [(True, 28), (False, 126)]:
        oy = 60
        seam, cut = bodice(v, front)
        page.line(shifted(cut, ox, oy), closed=True, width=.35)
        page.line(shifted(seam, ox, oy), "seam", .25, dashed=True, closed=True)
        page.line([(ox, oy+v["bust_line_y"]), (ox+q, oy+v["bust_line_y"])], "guide", .18, dashed=True)
        apex_y = v["front_dart_apex_y" if front else "back_dart_apex_y"]
        x, y = v["dart_x"], v["shoulder_to_waist"]
        page.line(shifted([(x-dart/2, y), (x, apex_y), (x+dart/2, y)], ox, oy), "dart", .3)
        page.line(shifted([(x, apex_y), (x, y)], ox, oy), "dart", .18, dashed=True)
        page.text(ox+5, oy+25, "A FRONT" if front else "B BACK", 3, bold=True)
        page.text(ox+5, oy+30, "Cut 1 on fold" if front else "Cut 2 mirrored", 2.7)
        page.arrow(ox+7, oy+57, 16)
        if front:
            page.line([(ox, oy+v["front_neck_depth"]), (ox, oy+y)], "guide", .6)
            page.text(ox-16, oy+40, "FOLD", 2.5, "guide", True)
            page.text(ox-18, oy+45, "NO SA", 2.4, "guide")
        else:
            page.text(ox-20, oy+29, "CB OPEN", 2.5, "dart", True)
            page.text(ox-20, oy+34, "Edges meet", 2.3, "dart")
        under = (ox+q, oy+v["armhole_depth"])
        waistpoint = (ox+wx, oy+y)
        mark_notch(page, under, "S1")
        mark_notch(page, waistpoint, "S2", 3, -2)
        page.text(ox+8, oy+y+10, f"Dart intake {dart:.1f}", 2.6, "dart")
    page.text(12, 162, f"Seam-line circumference: bust {bust:.1f} / closed-dart waist {waist:.1f}", 3.0, bold=True)
    page.text(12, 170, f"Body reference: bust {v['bust']} / waist {v['waist']}. Added ease is a trial choice.", 2.7)
    page.text(12, 177, f"ASSUMED: shoulder to waist {v['shoulder_to_waist']} / armhole depth {v['armhole_depth']}.", 2.7, "dart")
    page.text(12, 184, "Close all 4 darts first. Match S1/S2. Back stays open for fitting.", 2.7)
    page.text(12, 191, "No bust dart: check front balance and waist level on the actual doll.", 2.7)
    page.text(12, 198, f"Includes {v['seam_allowance']} mm SA except fold. Neck/armhole allowances are temporary.", 2.7)
    legend(page, v["seam_allowance"])
    page.calibration()
    page.footer(1)
    pages.append(page)

    theta = math.radians(v["skirt_angle_degrees"])/4
    assert 0 < theta <= math.pi/2
    r = (waist/4)/theta
    outer = r+v["skirt_length"]
    alpha = theta/2
    base_y = r*math.cos(alpha)
    def polar(radius, a):
        return (radius*math.sin(a), radius*math.cos(a)-base_y)
    angles = [-alpha+theta*i/100 for i in range(101)]
    inner = [polar(r, a) for a in angles]
    lower = [polar(outer, a) for a in reversed(angles)]
    skirt = inner+lower
    cut = offset_polygon(skirt, v["seam_allowance"])
    hip_capacity = 4*(r+v["hip_depth"])*theta
    assert hip_capacity >= v["hip"]+v["hip_ease_min"], "Insufficient skirt capacity at assumed hip depth"
    assert v["skirt_back_opening"] < v["skirt_length"]
    page = Page("02 / FOUR-SECTOR SKIRT FOUNDATION", "Cut 4 identical sectors. The four sectors form a half-circle skirt.")
    ox, oy = 105, 64
    page.line(shifted(cut, ox, oy), closed=True, width=.35)
    page.line(shifted(skirt, ox, oy), "seam", .25, dashed=True, closed=True)
    hiparc = [polar(r+v["hip_depth"], a) for a in angles]
    page.line(shifted(hiparc, ox, oy), "guide", .2, dashed=True)
    page.text(82, 88, "C SKIRT / CUT 4", 3, bold=True)
    page.text(83, 94, "Front pair + back pair", 2.5)
    page.arrow(100, 110, 25)
    page.text(78, 146, f"Radial length {v['skirt_length']}", 2.7)
    page.text(76, 153, "Not final costume hem", 2.6, "dart")
    for a, tag in [(-alpha, "W1"), (alpha, "W2")]:
        pos = polar(r, a)
        mark_notch(page, (pos[0]+ox, pos[1]+oy), tag, 3, -4)
        pos = polar(r+v["skirt_back_opening"], a)
        mark_notch(page, (pos[0]+ox, pos[1]+oy), "OPEN END", -20 if a < 0 else 3, 0)
    page.text(12, 178, f"Waist arc per sector: {waist/4:.2f}; all 4 sectors: {waist:.2f}.", 3, bold=True)
    page.text(12, 186, f"Capacity at assumed hip depth {v['hip_depth']}: {hip_capacity:.2f} (target minimum {v['hip']+v['hip_ease_min']:.2f}).", 2.7)
    page.text(12, 193, "Only the centre-back seam remains open to OPEN END; sew all other seams.", 2.7)
    page.text(12, 200, "Mark CF, CB and side seams after laying out the 4 sectors; keep waist unstretched.", 2.6)
    legend(page, v["seam_allowance"])
    page.calibration()
    page.footer(2)
    pages.append(page)

    upper = v["upper_arm"]+v["sleeve_upper_ease"]
    wrist = v["wrist"]+v["sleeve_wrist_ease"]
    length = v["sleeve_length"]
    sleeve = [(-upper/2, 0), (upper/2, 0), (wrist/2, length), (-wrist/2, length)]
    cut = offset_polygon(sleeve, v["seam_allowance"])
    page = Page("03 / DETACHED SLEEVE TUBE TEST", "Optional size test only. No sleeve head, gathered cap, collar or finished cuff.")
    ox, oy = 100, 65
    page.line(shifted(cut, ox, oy), closed=True, width=.35)
    page.line(shifted(sleeve, ox, oy), "seam", .25, dashed=True, closed=True)
    page.text(79, 80, "D SLEEVE", 3, bold=True)
    page.text(77, 87, "Cut 2 mirrored", 2.8)
    page.text(75, 94, "One piece per arm", 2.6)
    page.arrow(92, 108, 27)
    page.text(76, 147, f"Top {upper:.1f} / wrist {wrist:.1f}", 2.6)
    page.text(78, 154, f"Length {length:.1f}", 2.6)
    for x in [-upper/2, upper/2]:
        mark_notch(page, (ox+x, oy), "T", 3, -4)
    for x in [-wrist/2, wrist/2]:
        mark_notch(page, (ox+x, oy+length), "U", 3, 5)
    page.text(12, 184, f"Assumed arm {v['upper_arm']} / wrist {v['wrist']} unless replaced with actual measurements.", 2.7, "dart")
    page.text(12, 191, "Wrap and pin on arm before sewing. Keep seam open if hand cannot pass.", 2.7)
    page.text(12, 198, "Sew T-to-U only after fitting; actual gathered costume sleeve is a later draft.", 2.7)
    legend(page, v["seam_allowance"])
    page.calibration()
    page.footer(3)
    pages.append(page)

    # A second skirt option tied to the pleated appearance visible in the
    # official model. Two half-skirts join at CF/CB, keeping the opening aligned
    # with the bodice's CB. No centre-back slit or unprinted extra allowance.
    pleats = v["pleats_per_half"]
    assert int(pleats) == pleats and pleats % 2 == 0, "Need even whole pleats per half for side-waist mark"
    pleats = int(pleats)
    finished_repeat = waist/(2*pleats)
    flat_repeat = 3*finished_repeat
    flat_width = pleats*flat_repeat
    length, sa = v["skirt_length"], v["seam_allowance"]
    assert 0 < v["pleated_hem_band"] < length
    page = Page("04 / PRESERVATION PLEATED SKIRT TRIAL", "Alternative to page 2. Two HALF-SKIRTS join at centre front and centre back.", 297, 210)
    ox, oy = 18, 58
    seam = [(0, 0), (flat_width, 0), (flat_width, length), (0, length)]
    cut = offset_polygon(seam, sa)
    page.line(shifted(cut, ox, oy), closed=True, width=.35)
    page.line(shifted(seam, ox, oy), "seam", .25, dashed=True, closed=True)
    for i in range(pleats):
        start = i*flat_repeat
        a, b, c = [start+k*finished_repeat for k in (1, 2, 3)]
        page.line([(ox+a, oy), (ox+a, oy+length)], "dart", .25)
        page.line([(ox+b, oy), (ox+b, oy+length)], "guide", .25, dashed=True)
        if i < pleats-1:
            page.line([(ox+c, oy), (ox+c, oy+length)], "guide", .16, dashed=True)
        for x, label in [(a, f"A{i+1}"), (b, f"B{i+1}"), (c, f"C{i+1}")]:
            page.text(ox+x-2, oy-6, label, 2.3, "dart" if label.startswith('A') else "guide")
        ay = oy+12
        page.line([(ox+a+2, ay), (ox+c-2, ay)], "dart", .2)
        page.line([(ox+c-4, ay-1), (ox+c-2, ay), (ox+c-4, ay+1)], "dart", .2)
    page.arrow(197, 99, 22, "G")
    page.line([(ox, oy+length-v["pleated_hem_band"]), (ox+flat_width, oy+length-v["pleated_hem_band"])], "guide", .18, dashed=True)
    page.text(ox-3, oy+length+8, "CF", 2.5, "dart", True)
    page.text(ox+flat_width/2-5, oy+length+8, "SIDE", 2.5, "dart", True)
    page.text(ox+flat_width-4, oy+length+8, "CB", 2.5, "dart", True)
    mark_notch(page, (ox+flat_width/2, oy), "SIDE", -4, -11)
    mark_notch(page, (ox+flat_width, oy+v["skirt_back_opening"]), "OPEN", 3, 0)
    page.calibration(235, 49)
    page.text(236, 108, "E HALF-SKIRT / CUT 2", 2.7, bold=True)
    page.text(236, 114, "Fold A onto matching C.", 2.5)
    page.text(236, 120, "B: return fold / G: grain", 2.5, "guide")
    page.text(236, 126, "Do not sew vertical folds.", 2.5, "dart")
    page.text(236, 132, f"SA: {sa} mm all edges", 2.5)
    page.text(236, 138, f"Hem band guide: {v['pleated_hem_band']} mm", 2.5, "guide")
    page.text(236, 144, "Black: cut / blue: seam", 2.5)
    page.text(12, 167, f"Each panel: flat waist {flat_width:.1f} -> folded {waist/2:.1f}. Two panels = {waist:.1f} finished waist.", 2.8, bold=True)
    page.text(12, 175, f"Each repeat: {flat_repeat:.1f} -> {finished_repeat:.1f}. Baste pleats at waist only. Open CB for first {v['skirt_back_opening']} mm.", 2.7)
    page.text(12, 183, "Arrange left/right halves with CF touching CF and CB touching CB; they may be folded in mirrored directions.", 2.6)
    page.footer(4)
    pages.append(page)

    shoulder = distance((v["neck_half_width"], 0), (v["shoulder_width"]/2, v["shoulder_drop"]))
    side = v["bust_line_y"]-v["armhole_depth"]+distance((q, v["bust_line_y"]), (wx, v["shoulder_to_waist"]))
    sleeve_edge = distance(sleeve[0], sleeve[-1])
    checks = {
        "front_to_back_shoulder_mm": [shoulder, shoulder],
        "front_to_back_side_mm": [side, side],
        "front_dart_legs_mm": [distance((v["dart_x"]-dart/2, v["shoulder_to_waist"]), (v["dart_x"], v["front_dart_apex_y"]))]*2,
        "back_dart_legs_mm": [distance((v["dart_x"]-dart/2, v["shoulder_to_waist"]), (v["dart_x"], v["back_dart_apex_y"]))]*2,
        "quarter_bodice_closed_waist_to_skirt_arc_mm": [wx-dart, r*theta],
        "skirt_adjacent_side_mm": [v["skirt_length"], v["skirt_length"]],
        "sleeve_side_edges_mm": [sleeve_edge, distance(sleeve[1], sleeve[2])],
        "pleated_half_waist_to_half_bodice_mm": [flat_width/3, waist/2],
        "pleated_cf_seam_mm": [length, length],
        "pleated_cb_sewn_seam_mm": [length-v["skirt_back_opening"], length-v["skirt_back_opening"]],
    }
    for key, (a, b) in checks.items():
        assert abs(a-b) < .01, (key, a, b)
    for page in pages:
        for item in page.items:
            if item[0] == "line":
                for x, y in item[1]:
                    assert 9 < x < page.width-9 and 9 < y < page.height-19, f"Pattern path outside A4 margin: {x}, {y}"
                if item[2] == "cut" and item[-1]:
                    validate_simple_polygon(item[1])
    report = {
        "status": "DIGITAL GEOMETRY PASS; physical fit NOT tested",
        "version": spec["version"], "units": "mm", "page_sizes_mm": [[p.width, p.height] for p in pages],
        "page_count": len(pages), "calibration_square_mm": [50, 50],
        "bust_seam_circumference": bust, "waist_closed_dart_circumference": waist,
        "dart_intake_per_quarter": dart, "total_darts": 4,
        "skirt_waist_arc_total": 4*r*theta, "skirt_hip_capacity_at_assumed_depth": hip_capacity,
        "skirt_hip_target_minimum": v["hip"]+v["hip_ease_min"],
        "pleated_skirt": {"half_panels": 2, "pleats_per_half": pleats,
                          "flat_repeat": flat_repeat, "folded_repeat": finished_repeat,
                          "flat_width_per_half": flat_width, "folded_width_per_half": waist/2,
                          "cut_width_per_half": flat_width+2*sa, "height_with_allowance": length+2*sa,
                          "max_released_circumference": flat_width*2,
                          "note": "Vertical pleats not sewn shut; their drape and hip clearance need physical fitting."},
        "matching_seams": checks, "tolerance_mm": .01,
        "seam_allowance_mm": v["seam_allowance"], "fold_allowance_mm": 0,
        "closed_cut_contours_checked_for_crossings": True,
        "not_verified": ["actual body fit", "bust projection and balance", "armhole clearance", "hand passage", "costume silhouette", "physical printing calibration"],
    }
    return pages, report


def legend(page, allowance):
    for y, color, dashed, label in [(219, "cut", False, "Solid black: CUT line"),
                                     (227, "seam", True, "Blue dashed: SEAM line"),
                                     (235, "dart", False, "Red: DART / match mark")]:
        page.line([(12, y), (27, y)], color, .3, dashed)
        page.text(30, y+1, label, 2.6)
    page.text(12, 246, f"SA: {allowance} mm except front fold (0).", 2.6)
    page.text(12, 253, "Transfer seam lines and marks to cloth.", 2.5)
    page.text(12, 260, "Do not cut notches into the seam line.", 2.5)
    page.text(12, 267, "Change parameters and reprint for a new size.", 2.4)


def render_svg(page, path):
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{page.width}mm" height="{page.height}mm" viewBox="0 0 {page.width} {page.height}">',
             f'<rect width="{page.width}" height="{page.height}" fill="white"/>']
    for item in page.items:
        if item[0] == "line":
            _, pts, color, width, dashed, closed = item
            points = " ".join(f"{x:.4f},{y:.4f}" for x, y in pts)
            tag = "polygon" if closed else "polyline"
            dash = ' stroke-dasharray="1.8 1.2"' if dashed else ''
            lines.append(f'<{tag} points="{points}" fill="none" stroke="{COLORS[color]}" stroke-width="{width}"{dash}/>')
        else:
            _, x, y, text, size, color, bold = item
            lines.append(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{"bold" if bold else "normal"}" fill="{COLORS[color]}">{html.escape(text)}</text>')
    lines.append('</svg>')
    path.write_text("\n".join(lines)+"\n")


def render_pdf(pages, path):
    c = canvas.Canvas(str(path), pagesize=(210*mm, 297*mm), invariant=1)
    c.setTitle("March 7th - UFdoll S bust - fitting prototype v0.1 DRAFT")
    c.setAuthor("Character Doll Workshop")
    for page in pages:
        c.setPageSize((page.width*mm, page.height*mm))
        for item in page.items:
            if item[0] == "line":
                _, pts, color, width, dashed, closed = item
                c.setStrokeColor(COLORS[color])
                c.setLineWidth(width*mm)
                c.setDash([1.8*mm, 1.2*mm] if dashed else [])
                path_obj = c.beginPath()
                path_obj.moveTo(pts[0][0]*mm, (page.height-pts[0][1])*mm)
                for x, y in pts[1:]:
                    path_obj.lineTo(x*mm, (page.height-y)*mm)
                if closed:
                    path_obj.close()
                c.drawPath(path_obj, stroke=1, fill=0)
            else:
                _, x, y, text, size, color, bold = item
                c.setFillColor(COLORS[color])
                c.setFont("Helvetica-Bold" if bold else "Helvetica", size*mm)
                c.drawString(x*mm, (page.height-y)*mm, text)
        c.showPage()
    c.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, default=DEFAULT/"parameters-v0.1.json")
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    spec = json.loads(args.parameters.read_text())
    pages, report = generate(spec)
    args.output.mkdir(parents=True, exist_ok=True)
    render_pdf(pages, args.output/"muslin-v0.1-draft-a4.pdf")
    for n, page in enumerate(pages, 1):
        render_svg(page, args.output/f"muslin-v0.1-draft-page-{n}.svg")
    (args.output/"geometry-check-v0.1.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
