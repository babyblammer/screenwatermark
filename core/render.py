"""
ScreenWatermark Pro - Core Render Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

from datetime import datetime
from PIL import Image, ImageDraw

from core.constants import MUTED
from core.font_cache import load_font
from core.wm_cache import get_cached_watermark, _get_wm_resized
from core.utils import safe_hex_to_rgb, safe_strftime

def apply_watermark(img: "Image.Image", cfg: dict) -> "Image.Image":
    if not cfg.get("wm_enabled", True): return img
    wm = get_cached_watermark(cfg["watermark_path"])
    if wm is None: return img

    opacity = max(0.0, min(1.0, cfg["wm_opacity"] / 100.0))
    wm_mode = cfg.get("wm_mode", "normal")
    base    = img.convert("RGBA")

    def _apply_opacity(wm_img):
        r, g, b, a = wm_img.split()
        wm_img.putalpha(a.point(lambda p: int(p * opacity)))
        return wm_img

    if wm_mode == "full":
        iw, ih = img.size
        scale_f = max(iw / max(1, wm.width), ih / max(1, wm.height))
        new_w = max(1, int(wm.width  * scale_f))
        new_h = max(1, int(wm.height * scale_f))
        wm_r = _get_wm_resized(cfg["watermark_path"], new_w, new_h)
        if wm_r is None: return img
        wm_r = _apply_opacity(wm_r.copy())
        x = (iw - new_w) // 2
        y = (ih - new_h) // 2
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(wm_r, (x, y), wm_r)
        return Image.alpha_composite(base, layer).convert("RGB")

    if wm_mode == "pattern":
        pattern_gap = cfg.get("wm_pattern_gap", 20)
        iw, ih   = img.size
        scale    = max(5, cfg["wm_scale"])
        new_w    = max(1, int(iw * scale / 100))
        new_h    = max(1, int(wm.height * new_w / max(1, wm.width)))
        wm_r = _get_wm_resized(cfg["watermark_path"], new_w, new_h)
        if wm_r is None: return img
        wm_r = _apply_opacity(wm_r.copy())
        step_x = new_w  + pattern_gap
        step_y = new_h  + pattern_gap
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        y = 0
        while y < ih:
            x = 0
            while x < iw:
                layer.paste(wm_r, (x, y), wm_r)
                x += step_x
            y += step_y
        return Image.alpha_composite(base, layer).convert("RGB")

    scale = max(5, cfg["wm_scale"])
    margin = 24
    new_w = max(1, int(img.width * scale / 100))
    new_h = max(1, int(wm.height * new_w / max(1, wm.width)))
    max_w = max(1, img.width  - 2 * margin)
    max_h = max(1, img.height - 2 * margin)
    if new_w > max_w or new_h > max_h:
        scale_factor = min(max_w / max(1, new_w), max_h / max(1, new_h))
        new_w = max(1, int(new_w * scale_factor))
        new_h = max(1, int(new_h * scale_factor))
    wm_path = cfg["watermark_path"]
    wm_r = _get_wm_resized(wm_path, new_w, new_h)
    if wm_r is None:
        return img
    wm = wm_r
    wm = _apply_opacity(wm.copy())

    w, h   = img.size; ww, wh = wm.size
    coords = {
        "bottom-left":  (margin,       h-wh-margin),
        "bottom-right": (w-ww-margin,  h-wh-margin),
        "top-left":     (margin,        margin),
        "top-right":    (w-ww-margin,   margin),
        "center":       ((w-ww)//2,     (h-wh)//2),
    }
    x, y = coords.get(cfg["wm_position"], (margin, h-wh-margin))
    x = max(0, min(x, w-ww)); y = max(0, min(y, h-wh))
    layer = Image.new("RGBA", base.size, (0,0,0,0))
    layer.paste(wm, (x, y), wm)
    return Image.alpha_composite(base, layer).convert("RGB")

def apply_timestamp(img: "Image.Image", cfg: dict,
                    capture_time: "datetime | None" = None) -> "Image.Image":
    if not cfg["ts_enabled"]: return img
    ts_text = safe_strftime(cfg["ts_format"], capture_time or datetime.now())
    base_size = cfg["ts_font_size"]
    img_w = img.width
    dyn_size = max(10, min(base_size, img_w // 50))
    font = load_font(dyn_size, bold=cfg.get("ts_bold", False))

    draw_tmp = ImageDraw.Draw(Image.new("RGB", (1,1)))
    bbox = draw_tmp.textbbox((0,0), ts_text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    pad = 10
    strip_h = th + pad * 2 + 4
    w, h = img.size

    new_img = Image.new("RGB", (w, h + strip_h), (255, 255, 255))
    new_img.paste(img, (0, 0))
    strip_y = h

    draw = ImageDraw.Draw(new_img)
    tx = w - tw - pad - 10
    ty = strip_y + pad
    if cfg.get("ts_shadow"):
        draw.text((tx+1, ty+1), ts_text, font=font, fill=(180,180,180,255))
    draw.text((tx, ty), ts_text, font=font,
              fill=safe_hex_to_rgb(cfg["ts_color"]) + (255,))
    return new_img
