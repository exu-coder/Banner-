# by Saurabh 💀
# Flask Edition - Using jsDelivr CDN for images
# Tg-@Phantom4ura

import io
import os
import sys
import traceback
import requests
from flask import Flask, Response, request, jsonify
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

INFO_API_URL = "https://info-api-green-theta.vercel.app/info"

# ========== FONT SETUP ==========
FONT_PATHS = [
    "arial_unicode_bold.otf",
    "NotoSansCherokee.ttf",
    "/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/system/fonts/Roboto-Regular.ttf",
    "/system/fonts/Roboto-Bold.ttf",
    "/system/fonts/DroidSans.ttf",
    "/system/fonts/DroidSans-Bold.ttf",
]

def find_font():
    for path in FONT_PATHS:
        if os.path.exists(path):
            print(f"[OK] Font found: {path}")
            return path
    try:
        os.system("pkg install -y ttf-dejavu > /dev/null 2>&1")
        dejavu = "/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if os.path.exists(dejavu):
            return dejavu
    except:
        pass
    print("[WARN] No font found, using default")
    return None

FONT_FILE = find_font()

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Android; Mobile)"})

def load_font(size, font_file=None):
    try:
        if font_file and os.path.exists(font_file):
            return ImageFont.truetype(font_file, size)
        if FONT_FILE and os.path.exists(FONT_FILE):
            return ImageFont.truetype(FONT_FILE, size)
    except Exception as e:
        print(f"[FONT ERROR] {e}")
    return ImageFont.load_default()

# ========== FALLBACK IMAGES ==========
def create_fallback_avatar(size=300):
    img = Image.new("RGBA", (size, size), (30, 30, 30, 255))
    draw = ImageDraw.Draw(img)
    font = load_font(size // 3)
    text = "?"
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        tw, th = size // 3, size // 3
    draw.text(((size - tw) // 2, (size - th) // 2 - 10), text, font=font, fill=(200, 200, 200, 255))
    return img

def create_fallback_banner(width=600, height=300):
    img = Image.new("RGBA", (width, height), (40, 40, 40, 255))
    draw = ImageDraw.Draw(img)
    font = load_font(40)
    text = "NO BANNER"
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        tw, th = 200, 40
    draw.text(((width - tw) // 2, (height - th) // 2), text, font=font, fill=(100, 100, 100, 255))
    return img

# ========== IMAGE FETCHING via jsDelivr CDN ==========
# Format: https://cdn.jsdelivr.net/gh/{user}/{repo}@{branch}/PNG/{item_id}.png
CDN_BASE = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG"

def fetch_image_bytes(item_id, img_type="unknown"):
    if not item_id or str(item_id) == "0" or item_id is None:
        print(f"[SKIP] {img_type}: No item_id provided")
        return None

    item_id = str(item_id)
    print(f"[FETCH] {img_type}: id={item_id}")

    # Try multiple CDN sources
    urls = [
        f"{CDN_BASE}/{item_id}.png",
        # Add more repos here if needed
        # f"https://cdn.jsdelivr.net/gh/AnotherUser/repo@main/PNG/{item_id}.png",
    ]

    for url in urls:
        try:
            resp = session.get(url, timeout=10)
            if resp.status_code == 200:
                print(f"[OK] {img_type}: Loaded from {url}")
                return resp.content
            else:
                print(f"[ERR] {img_type}: {url} -> HTTP {resp.status_code}")
        except Exception as e:
            print(f"[ERR] {img_type}: {url} -> {e}")
            continue

    print(f"[FAIL] {img_type}: All CDN sources failed")
    return None

def bytes_to_image(img_bytes, fallback_fn, *args):
    if img_bytes:
        try:
            img = Image.open(io.BytesIO(img_bytes))
            if img.mode in ("P", "L"):
                img = img.convert("RGBA")
            elif img.mode != "RGBA":
                img = img.convert("RGBA")
            print(f"[OK] Image loaded: {img.size}")
            return img
        except Exception as e:
            print(f"[ERR] Image decode failed: {e}")
    return fallback_fn(*args)

# ========== TEXT DRAWING ==========
def is_cherokee(char):
    code = ord(char)
    return (0x13A0 <= code <= 0x13FF) or (0xAB70 <= code <= 0xABBF)

def draw_text_with_stroke(draw, x, y, text, font_main, size, stroke_col="black", text_col="white"):
    current_x = x
    for char in text:
        font = font_main
        for dx, dy in [(-size,0), (size,0), (0,-size), (0,size),
                       (-size,-size), (size,size), (-size,size), (size,-size)]:
            draw.text((current_x + dx, y + dy), char, font=font, fill=stroke_col)
        draw.text((current_x, y), char, font=font, fill=text_col)
        try:
            char_width = font.getlength(char)
        except:
            char_width = font_main.size * 0.6
        current_x += char_width

# ========== BANNER GENERATION ==========
def process_banner_image(data, avatar_bytes, banner_bytes, pin_bytes):
    level = str(data.get("AccountLevel", "0"))
    name = data.get("AccountName", "Unknown")
    guild = data.get("GuildName", "")

    print(f"[DATA] Name={name}, Guild={guild}, Level={level}")

    TARGET_HEIGHT = 300

    avatar_img = bytes_to_image(avatar_bytes, create_fallback_avatar, TARGET_HEIGHT)
    avatar_img = avatar_img.resize((TARGET_HEIGHT, TARGET_HEIGHT), Image.LANCZOS)

    banner_img = bytes_to_image(banner_bytes, create_fallback_banner, 600, TARGET_HEIGHT)

    b_w, b_h = banner_img.size
    if b_w > 50 and b_h > 50 and banner_bytes:
        banner_img = banner_img.rotate(3, resample=Image.BICUBIC, expand=True)
        b_w, b_h = banner_img.size

        crop_top, crop_bottom, crop_sides = 0.23, 0.32, 0.17
        left = b_w * crop_sides
        top = b_h * crop_top
        right = b_w * (1 - crop_sides)
        bottom = b_h * (1 - crop_bottom)
        banner_img = banner_img.crop((left, top, right, bottom))

    b_w, b_h = banner_img.size
    if b_h > 0:
        new_banner_w = int(TARGET_HEIGHT * (b_w / b_h) * 2.0)
        banner_img = banner_img.resize((new_banner_w, TARGET_HEIGHT), Image.LANCZOS)
    else:
        new_banner_w = 600
        banner_img = Image.new("RGBA", (new_banner_w, TARGET_HEIGHT), (50, 50, 50))

    final_w = TARGET_HEIGHT + new_banner_w
    final_h = TARGET_HEIGHT
    combined = Image.new("RGBA", (final_w, final_h), (20, 20, 20, 255))
    combined.paste(avatar_img, (0, 0))
    combined.paste(banner_img, (TARGET_HEIGHT, 0))

    draw = ImageDraw.Draw(combined)

    font_large = load_font(95)
    font_small = load_font(70)
    font_level = load_font(40)

    text_x = TARGET_HEIGHT + 30
    text_y = 30

    draw_text_with_stroke(draw, text_x + 20, text_y, name, font_large, 3)
    draw_text_with_stroke(draw, text_x + 20, text_y + 150, guild, font_small, 2)

    pin_img = bytes_to_image(pin_bytes, lambda: Image.new("RGBA", (1, 1), (0,0,0,0)))
    if pin_img and pin_img.size != (100, 100) and pin_img.size != (1, 1):
        pin_size = 100
        pin_img = pin_img.resize((pin_size, pin_size), Image.LANCZOS)
        combined.paste(pin_img, (0, TARGET_HEIGHT - pin_size), pin_img)

    level_txt = f"Lvl.{level}"
    try:
        bbox = draw.textbbox((0, 0), level_txt, font=font_level)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except:
        text_w = len(level_txt) * 15
        text_h = 30

    px, py = 20, 12
    box_x = final_w - (text_w + px * 2)
    box_y = final_h - (text_h + py * 2)

    draw.rectangle([box_x, box_y, final_w, final_h], fill="black")
    draw.text((box_x + px, box_y + py - 4), level_txt, font=font_level, fill="white")

    img_io = io.BytesIO()
    combined.save(img_io, "PNG", optimize=True)
    img_io.seek(0)
    return img_io

# ========== ROUTES ==========
@app.route("/")
def home():
    return jsonify({
        "message": "⚡ Ultra Fast Banner API Running",
        "Fix By": "SaUraBh 💀",
        "Telegram": "@Phantom4ura",
        "Your Info Api": INFO_API_URL,
        "Api Endpoint": "/profile?uid={uid}",
        "Note": "Join To @Phantom4ura For More 💝"
    })

@app.route("/profile")
def get_banner():
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "UID required"}), 400

    print(f"\n{'='*50}")
    print(f"[REQUEST] UID: {uid}")
    print(f"{'='*50}")

    try:
        resp = session.get(f"{INFO_API_URL}?uid={uid}", timeout=15)

        if resp.status_code != 200:
            print(f"[ERR] Info API returned {resp.status_code}")
            return jsonify({"error": "Info API Error", "status": resp.status_code}), 502

        data = resp.json()
        print(f"[OK] Info API data received")

        account_info = data.get("AccountInfo", {})
        profile_info = data.get("AccountProfileInfo", {})
        guild_info = data.get("GuildInfo", {})

        if not account_info:
            print("[ERR] No AccountInfo in response")
            return jsonify({"error": "Not Found"}), 404

        print(f"[DATA] AccountInfo keys: {list(account_info.keys())}")

        avatar_id = account_info.get("AccountAvatarId")
        banner_id = account_info.get("AccountBannerId")
        pin_id = profile_info.get("Title")

        print(f"[IDS] Avatar={avatar_id}, Banner={banner_id}, Pin={pin_id}")

        avatar_bytes = fetch_image_bytes(avatar_id, "AVATAR")
        banner_bytes = fetch_image_bytes(banner_id, "BANNER")
        pin_bytes = fetch_image_bytes(pin_id, "PIN") if (pin_id and str(pin_id) != "0") else None

        banner_data = {
            "AccountLevel": account_info.get("AccountLevel", "0"),
            "AccountName": account_info.get("AccountName", "Unknown"),
            "GuildName": guild_info.get("GuildName", "")
        }

        img_io = process_banner_image(banner_data, avatar_bytes, banner_bytes, pin_bytes)

        print(f"[OK] Banner generated successfully!")

        return Response(
            img_io.getvalue(),
            mimetype="image/png",
            headers={"Cache-Control": "public, max-age=300"}
        )

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("=" * 50)
    print("⚡ Banner API (Flask + jsDelivr CDN)")
    print("by Saurabh 💀 | @Phantom4ura")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=False)
