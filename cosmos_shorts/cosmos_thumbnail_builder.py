import os
import sys
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MPT_DIR = os.path.join(BASE_DIR, "MoneyPrinterTurbo")
HINDI_FONT_PATH = os.path.join(MPT_DIR, "resource", "fonts", "Nirmala.ttc")
ENGLISH_FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf"

def get_font(font_path: str, size: int):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        try:
            return ImageFont.truetype(HINDI_FONT_PATH, size)
        except Exception:
            return ImageFont.load_default()

def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    clean = hex_code.lstrip('#')
    if len(clean) == 3:
        clean = ''.join(c * 2 for c in clean)
    try:
        return tuple(int(clean[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (0, 255, 102)

def create_cosmos_thumbnail(
    bg_image_path: Optional[str],
    output_path: str,
    headline_hi: str = "दुनिया की सबसे रहस्यमयी जगहें!",
    subtext: str = "क्या ये सच है?",
    brand_name: str = "COSMOS",
    badge_color_hex: str = "#00FF66",
    badge_text_color_hex: str = "#000000"
) -> str:
    """
    Creates a professional vertical 1080x1920 YouTube Shorts thumbnail with theme-coordinated styling.
    """
    width, height = 1080, 1920

    # 1. Base Image
    if bg_image_path and os.path.exists(bg_image_path):
        base_img = Image.open(bg_image_path).convert("RGB")
        # Resize & crop to 1080x1920 center-crop
        img_ratio = base_img.width / base_img.height
        target_ratio = width / height
        if img_ratio > target_ratio:
            new_height = height
            new_width = int(height * img_ratio)
        else:
            new_width = width
            new_height = int(width / img_ratio)
        base_img = base_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - width) // 2
        top = (new_height - height) // 2
        img = base_img.crop((left, top, left + width, top + height))
    else:
        # Fallback dark cosmic gradient
        img = Image.new("RGB", (width, height), color=(10, 10, 25))

    draw = ImageDraw.Draw(img, "RGBA")

    # 2. Add Top & Bottom Dark Gradient Overlay for text readability
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Top gradient for channel badge
    for y in range(350):
        alpha = int(180 * (1.0 - (y / 350.0)))
        overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))

    # Bottom gradient for headline and hook
    for y in range(height - 850, height):
        progress = (y - (height - 850)) / 850.0
        alpha = int(220 * progress)
        overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))

    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay), (0, 0))
    draw = ImageDraw.Draw(img)

    # 3. Top-Left Channel Badge: "🔴 COSMOS"
    badge_x, badge_y = 60, 80
    badge_w, badge_h = 280, 70
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
        radius=35,
        fill=(0, 0, 0, 200),
        outline=(255, 255, 255, 180),
        width=3
    )
    # Red record dot
    draw.ellipse([(badge_x + 25, badge_y + 25), (badge_x + 45, badge_y + 45)], fill=(255, 40, 40))
    # Brand text
    brand_font = get_font(ENGLISH_FONT_PATH, 36)
    draw.text((badge_x + 60, badge_y + 12), brand_name, font=brand_font, fill=(255, 255, 255))

    # 4. Big Bold Hindi Headline near the middle-bottom
    text_font = get_font(HINDI_FONT_PATH, 80)
    sub_font = get_font(HINDI_FONT_PATH, 55)

    # Wrap Hindi text if needed
    words = headline_hi.split()
    lines = []
    current_line = []
    for w in words:
        test_line = " ".join(current_line + [w])
        bbox = draw.textbbox((0, 0), test_line, font=text_font)
        if bbox[2] - bbox[0] < width - 120:
            current_line.append(w)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [w]
    if current_line:
        lines.append(" ".join(current_line))

    start_y = height - 600
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=text_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2

        # Draw thick black outline
        stroke_width = 8
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx * dx + dy * dy <= stroke_width * stroke_width:
                    draw.text((x + dx, start_y + dy), line, font=text_font, fill=(0, 0, 0))

        # Vibrant Yellow text
        draw.text((x, start_y), line, font=text_font, fill=(255, 230, 0))
        start_y += text_h + 35

    # 5. Callout Badge for subtext matching the Video Theme Color
    if subtext:
        sub_bbox = draw.textbbox((0, 0), subtext, font=sub_font)
        sub_w = sub_bbox[2] - sub_bbox[0]
        sub_h = sub_bbox[3] - sub_bbox[1]
        pad_x, pad_y = 40, 20
        box_x = (width - sub_w - pad_x * 2) // 2
        box_y = start_y + 20

        bg_rgb = hex_to_rgb(badge_color_hex)
        txt_rgb = hex_to_rgb(badge_text_color_hex)

        # Rounded theme badge
        draw.rounded_rectangle(
            [(box_x, box_y), (box_x + sub_w + pad_x * 2, box_y + sub_h + pad_y * 2)],
            radius=20,
            fill=bg_rgb
        )
        # Bold themed subtext
        draw.text((box_x + pad_x, box_y + pad_y - 5), subtext, font=sub_font, fill=txt_rgb)

    # Save PNG and optimized JPG
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, quality=95)
    
    # Also save .jpg version for YouTube API compatibility
    jpg_path = os.path.splitext(output_path)[0] + ".jpg"
    img.convert("RGB").save(jpg_path, "JPEG", quality=90)

    return output_path
