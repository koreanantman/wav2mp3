# WAV2MP3 아이콘 생성: 둥근 사각형 + 파형 → 화살표 + "MP3"
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

S = 1024
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
font_path = next(p for p in FONT_CANDIDATES if os.path.exists(p))

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# 배경: 세로 그라데이션 (딥 네이비 → 인디고)
bg = Image.new("RGBA", (S, S))
top, bot = (28, 32, 58), (58, 40, 110)
px = bg.load()
for y in range(S):
    t = y / (S - 1)
    c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
    for x in range(S):
        px[x, y] = c
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([40, 40, S - 40, S - 40], radius=210, fill=255)
img.paste(bg, (0, 0), mask)

d = ImageDraw.Draw(img)

# 파형 바 (상단 영역)
cx0, cx1, cy = 150, S - 150, 390
n = 15
w = (cx1 - cx0) / n
for i in range(n):
    t = i / (n - 1)
    amp = (0.25 + 0.75 * abs(math.sin(t * math.pi * 2.3 + 0.4))) * (1 - 0.35 * abs(t - 0.5) * 2)
    h = 250 * amp
    x = cx0 + i * w + w * 0.18
    # 왼쪽 시안 → 오른쪽 마젠타
    col = (int(80 + 175 * t), int(220 - 120 * t), int(255 - 40 * t), 255)
    d.rounded_rectangle([x, cy - h, x + w * 0.64, cy + h], radius=w * 0.32, fill=col)

# "MP3" 텍스트
font = ImageFont.truetype(font_path, 250)
txt = "MP3"
bb = d.textbbox((0, 0), txt, font=font)
tw, th = bb[2] - bb[0], bb[3] - bb[1]
d.text(((S - tw) / 2 - bb[0], 735 - th / 2 - bb[1]), txt, font=font, fill=(255, 255, 255, 255))

out = sys.argv[1] if len(sys.argv) > 1 else "icon"
img.save(out + ".png")
img.save(out + ".ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)])
print("saved", out + ".ico")
