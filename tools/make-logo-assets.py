#!/usr/bin/env python3
"""
Пересобирает графику бренда из исходного логотипа.

Вход:  assets/img/logo-original.jpg  — логотип от заказчика (на белом фоне)
Выход: assets/img/logo-mark.png      — эмблема без фона, для хедера
       assets/img/logo.png           — полный лок-ап (эмблема + надпись + слоган), для футера
       assets/img/favicon.png        — иконка вкладки
       assets/img/apple-touch-icon.png — иконка для iOS (на белой плашке)
       assets/img/og.png             — превью для соцсетей 1200x630

Запуск (из корня проекта):  python3 tools/make-logo-assets.py
Нужны пакеты: pillow numpy fonttools brotli
"""

from collections import deque
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
FONTS = ROOT / "assets" / "fonts"

NAVY, TEAL, INK2, GOLDINK = (18, 60, 107), (17, 136, 143), (60, 68, 95), (150, 110, 30)

# Логотип разбит на три горизонтальные полосы: эмблема / надпись / слоган.
# Границы в пикселях исходника 1024x1024.
BAND_MARK = 140, 640
BAND_ALL = 140, 815


def cut_white_background(path):
    """Убирает белый фон, сохраняя мягкие края.

    Фоном считается только та почти-белая область, которая связана с краем кадра,
    поэтому белые детали внутри эмблемы остаются на месте. У пикселей на границе
    альфа берётся по удалению от белого, а из цвета вычитается примешанный белый —
    иначе на тёмном фоне вокруг логотипа видна светлая кайма.
    """
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
    h, w, _ = rgb.shape
    whiteish = (255 - rgb.min(axis=2)) <= 24

    bg = np.zeros((h, w), bool)
    dq = deque()
    border = [(y, x) for x in range(w) for y in (0, h - 1)]
    border += [(y, x) for y in range(h) for x in (0, w - 1)]
    for y, x in border:
        if whiteish[y, x] and not bg[y, x]:
            bg[y, x] = True
            dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and whiteish[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                dq.append((ny, nx))

    ring = bg.copy()
    for _ in range(5):
        s = ring.copy()
        s[1:, :] |= ring[:-1, :]
        s[:-1, :] |= ring[1:, :]
        s[:, 1:] |= ring[:, :-1]
        s[:, :-1] |= ring[:, 1:]
        ring = s
    edge = ring & ~bg

    alpha = np.where(bg, 0.0, 1.0)
    alpha[edge] = np.clip((255 - rgb.min(axis=2)) / 255 * 1.12, 0, 1)[edge]

    out = rgb.copy()
    m = edge & (alpha > 0.02)
    av = alpha[m][:, None]
    out[m] = np.clip((rgb[m] - (1 - av) * 255) / av, 0, 255)
    out[alpha <= 0.02] = 255

    data = np.dstack([out, alpha * 255]).round().clip(0, 255).astype(np.uint8)
    return Image.fromarray(data)


def fit(img, side):
    c = img.copy()
    c.thumbnail((side, side), Image.LANCZOS)
    return c


def crop_band(img, band):
    y0, y1 = band
    c = img.crop((0, y0, img.width, y1))
    return c.crop(c.getbbox())


def woff2_to_ttf(name, tmp):
    """PIL не читает woff2, поэтому распаковываем шрифт во временный ttf."""
    f = TTFont(FONTS / name)
    f.flavor = None
    path = str(tmp / name.replace(".woff2", ".ttf"))
    f.save(path)
    return path


class Text:
    """Рисует текст вариативным Manrope.

    Кириллица и латиница лежат в разных сабсетах шрифта, поэтому строку
    приходится разбивать на куски и для каждого брать файл с нужными глифами
    (цифры, «·», «—», «%» есть только в латинском).
    """

    def __init__(self, draw, tmp):
        self.d = draw
        self.paths = [woff2_to_ttf("manrope-cyrillic.woff2", tmp),
                      woff2_to_ttf("manrope-latin.woff2", tmp)]
        self.cov = [set(TTFont(p).getBestCmap()) for p in self.paths]
        self.cache = {}

    def _font(self, i, size, weight):
        key = (i, size, weight)
        if key not in self.cache:
            f = ImageFont.truetype(self.paths[i], size)
            f.set_variation_by_axes([weight])
            self.cache[key] = f
        return self.cache[key]

    def _runs(self, text):
        runs = []
        for ch in text:
            i = 0 if ord(ch) in self.cov[0] else 1
            if runs and runs[-1][0] == i:
                runs[-1][1] += ch
            else:
                runs.append([i, ch])
        return runs

    def width(self, text, size, weight):
        return sum(self.d.textlength(c, font=self._font(i, size, weight))
                   for i, c in self._runs(text))

    def draw(self, xy, text, size, weight, fill):
        x, y = xy
        for i, chunk in self._runs(text):
            f = self._font(i, size, weight)
            self.d.text((x, y), chunk, font=f, fill=fill)
            x += self.d.textlength(chunk, font=f)
        return x - xy[0]


def make_og(mark, tmp):
    W, H = 1200, 630
    col = np.linspace(0, 1, H)[:, None, None]
    bg = (255 + (np.array([237, 241, 249]) - 255) * col).astype(np.uint8).repeat(W, axis=1)
    gy, gx = np.mgrid[0:H, 0:W]
    glow = np.clip(1 - np.sqrt(((gx - 1010) / 430.) ** 2 + ((gy - 80) / 430.) ** 2), 0, 1) ** 2 * .28
    canvas = Image.fromarray(
        (bg * (1 - glow[..., None]) + np.array(TEAL) * glow[..., None]).astype(np.uint8)
    ).convert("RGBA")

    big = fit(mark, 286)
    canvas.alpha_composite(big, (866, 268))
    small = fit(mark, 66)
    canvas.alpha_composite(small, (80, 62))

    d = ImageDraw.Draw(canvas)
    t = Text(d, tmp)
    w = t.draw((160, 74), "Учебный ", 27, 800, NAVY)
    t.draw((160 + w, 74), "советник", 27, 800, TEAL)
    t.draw((80, 248), "Помогаем студентам", 61, 800, NAVY)
    t.draw((80, 324), "справляться с нагрузкой", 61, 800, TEAL)
    t.draw((80, 424), "Рефераты · контрольные · курсовые · ВКР · диссертации", 25, 500, INK2)

    x = 80
    for label, color in (("14 дней правок бесплатно", NAVY),
                         ("Оригинальность 60%+", TEAL),
                         ("Срочно — за сутки", GOLDINK)):
        pw = int(t.width(label, 21, 700)) + 52
        d.rounded_rectangle([x, 500, x + pw, 556], radius=28,
                            fill=(255, 255, 255), outline=color + (70,), width=2)
        t.draw((x + 26, 516), label, 21, 700, color)
        x += pw + 18

    d.rectangle([0, 0, W, 5], fill=NAVY)
    d.rectangle([0, 0, 420, 5], fill=TEAL)
    return canvas.convert("RGB")


def main():
    logo = cut_white_background(IMG / "logo-original.jpg")
    mark = crop_band(logo, BAND_MARK)
    full = crop_band(logo, BAND_ALL)

    saved = []
    def save(img, name, palette=True, **kw):
        # в логотипе плоские цвета, поэтому палитра из 256 оттенков даёт тот же
        # результат на глаз и файл в 4–5 раз меньше
        out = img.quantize(colors=256, method=Image.FASTOCTREE) if palette else img
        out.save(IMG / name, optimize=True, **kw)
        size_kb = (IMG / name).stat().st_size // 1024
        saved.append(f"{name} {img.size[0]}x{img.size[1]}, {size_kb} КБ")

    save(fit(mark, 160), "logo-mark.png")
    save(fit(full, 460), "logo.png")

    fav = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    m = fit(mark, 60)
    fav.paste(m, ((64 - m.width) // 2, (64 - m.height) // 2), m)
    save(fav, "favicon.png")

    touch = Image.new("RGB", (180, 180), (255, 255, 255))
    m = fit(mark, 140)
    touch.paste(m, ((180 - m.width) // 2, (180 - m.height) // 2 + 2), m)
    save(touch, "apple-touch-icon.png")

    with tempfile.TemporaryDirectory() as tmp:
        # у превью плавный градиент — палитра дала бы полосы
        save(make_og(mark, Path(tmp)), "og.png", palette=False)

    print("собрано:", *saved, sep="\n  ")


if __name__ == "__main__":
    main()
