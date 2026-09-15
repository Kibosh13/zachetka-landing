#!/usr/bin/env python3
"""
Собирает страницу договора-оферты из исходного .docx заказчика.

Вход:  assets/docs/dogovor-oferta.docx — документ от заказчика
Выход: oferta.html                     — страница договора на сайте

Текст переносится дословно, без правок формулировок, сумм, дат и географии:
изменения вносятся в .docx, после чего страница пересобирается.

Запуск (из корня проекта):  python3 tools/make-oferta.py
Зависимостей нет, только стандартная библиотека.
"""

from html import escape
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "docs" / "dogovor-oferta.docx"
OUT = ROOT / "oferta.html"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Два пункта в .docx пронумерованы автосписком Word: самих цифр в тексте нет,
# Word подставляет их при отрисовке. Переносим номера явно, иначе на странице
# получится разрыв нумерации (7.2 → 7.4, 8.3 → приложение).
AUTO_NUMS = {"13": "7.3.", "14": "8.4."}
BULLET_LIST = "8"  # маркированный список гарантий в приложении

REQUISITE_CODES = re.compile(r"(ОГРНИП|ИНН|ОКАТО|ОКТМО|ОКПО)\s+(\d+)")
CLAUSE = re.compile(r"^(\d+(?:\.\d+)*\.?)\s+(.+)$", re.S)
URL = re.compile(r"https?://[^\s<>«»]+")


def esc(text):
    return escape(text, quote=False)


def body_html(text):
    """Экранирует текст абзаца и делает адреса сайта кликабельными."""

    def link(m):
        url, tail = m.group(0), ""
        while url and url[-1] in ".,;:":
            url, tail = url[:-1], url[-1] + tail
        return f'<a href="{url}">{url}</a>{tail}'

    return URL.sub(link, esc(text))


def clean(text):
    """Схлопывает переносы и двойные пробелы из Word в обычный пробел."""
    return re.sub(r"\s+", " ", text).strip()


def cell_paragraphs(tc):
    out = [clean("".join(t.text or "" for t in p.iter(f"{W}t"))) for p in tc.findall(f"{W}p")]
    return [p for p in out if p]


def read_blocks(path):
    """Разбирает документ в поток блоков: ('p', текст, numId) и ('tbl', строки)."""
    body = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml")).find(f"{W}body")
    blocks = []
    for el in body:
        tag = el.tag.split("}")[1]
        if tag == "p":
            text = clean("".join(t.text or "" for t in el.iter(f"{W}t")))
            if not text:
                continue
            num = el.find(f"{W}pPr/{W}numPr/{W}numId")
            blocks.append(("p", text, num.get(f"{W}val") if num is not None else None))
        elif tag == "tbl":
            rows = [[cell_paragraphs(tc) for tc in tr.findall(f"{W}tc")] for tr in el.findall(f"{W}tr")]
            blocks.append(("tbl", rows, None))
    return blocks


def is_section_heading(text):
    """Заголовки разделов в документе набраны капсом: «5. ОТВЕТСТВЕННОСТЬ СТОРОН»."""
    return bool(re.match(r"^\d+\.\s", text)) and text == text.upper()


def clause(text):
    """Выделяет номер пункта, чтобы он читался отдельно от текста."""
    m = CLAUSE.match(text)
    if not m:
        return f"<p>{body_html(text)}</p>"
    return f'<p class="dc"><b>{esc(m.group(1))}</b> {body_html(m.group(2))}</p>'


def render_table(rows):
    cols = [" ".join(c) for c in rows[0]]
    html = ['<div class="doc-table-wrap">', '<table class="doc-table">', "<thead><tr>"]
    for i, col in enumerate(cols):
        cls = ' class="dt-n"' if i == 0 else ""
        html.append(f"<th{cls}>{esc(col)}</th>")
    html.append("</tr></thead><tbody>")

    for row in rows[1:]:
        filled = [c for c in row if c]
        if len(filled) == 1:  # строка-раздел прайса: «3. Курсовые работы»
            html.append(f'<tr class="dt-group"><td colspan="{len(cols)}">{esc(" ".join(filled[0]))}</td></tr>')
            continue

        html.append("<tr>")
        for i, cell in enumerate(row):
            main, *rest = cell or ["—"]
            extra = "".join(f"<small>{esc(p)}</small>" for p in rest)
            cls = ("dt-n", "dt-name")[i] if i < 2 else "dt-cell"
            html.append(f'<td class="{cls}" data-label="{esc(cols[i])}">{esc(main)}{extra}</td>')
        html.append("</tr>")

    html += ["</tbody>", "</table>", "</div>"]
    return html


def render(blocks, skip):
    """Превращает поток блоков в тело статьи и собирает оглавление.

    skip — строки шапки документа (название, город, дата): они выводятся в hero.
    """
    html, toc, bullets, requisites = [], [], [], []
    mode = "preamble"

    def flush_bullets():
        if bullets:
            html.append('<ul class="doc-list">' + "".join(f"<li>{body_html(b)}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    def flush_requisites():
        if not requisites:
            return
        name, *codes = requisites
        pairs = [m for line in codes for m in REQUISITE_CODES.findall(line)]
        html.append('<div class="doc-req">')
        html.append(f"<b>{esc(name)}</b>")
        html.append("<dl>" + "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in pairs) + "</dl>")
        html.append("</div>")
        requisites.clear()

    for kind, payload, num in blocks:
        if kind == "tbl":
            flush_bullets()
            html += render_table(payload)
            continue

        text = payload
        if text in skip:
            continue

        if is_section_heading(text):
            flush_bullets()
            flush_requisites()
            anchor = "s" + re.match(r"^(\d+)", text).group(1)
            mode = "requisites" if "РЕКВИЗИТЫ" in text else "body"
            toc.append((anchor, text))
            html.append(f'<h2 id="{anchor}">{esc(text)}</h2>')
            continue

        if text.startswith("Приложение"):
            flush_bullets()
            flush_requisites()
            mode = "appendix"
            if num == "14":  # ссылка на приложение из раздела 8 — это пункт 8.4
                html.append(clause(f"{AUTO_NUMS[num]} {text}"))
                continue
            toc.append(("pril", "Приложение № 1. Прайс-лист"))
            html.append(f'<h2 id="pril">{esc(text)}</h2>')
            continue

        if mode == "requisites":
            requisites.append(text)
            continue

        if text.startswith("●"):
            bullets.append(text.lstrip("● ").strip())
            continue
        if num == BULLET_LIST:
            bullets.append(text)
            continue
        flush_bullets()

        if num in AUTO_NUMS:
            html.append(clause(f"{AUTO_NUMS[num]} {text}"))
            continue

        if mode == "preamble":
            # Ключевой абзац преамбулы — условие акцепта: выносим в плашку
            cls = "doc-callout" if text.startswith("Полным и безоговорочным акцептом") else "doc-intro"
            html.append(f'<p class="{cls}">{body_html(text)}</p>')
            continue

        if mode == "appendix" and not CLAUSE.match(text):
            if text.startswith("Прайс-лист"):
                html.append(f"<h3>{esc(text)}</h3>")
            else:
                cls = "dc-note" if text.startswith("*") else "dc-lead"
                html.append(f'<p class="{cls}">{body_html(text)}</p>')
            continue

        html.append(clause(text))

    flush_bullets()
    flush_requisites()
    return html, toc


NAV = """    <nav class="nav" id="nav" aria-label="Основная навигация">
      <a href="index.html#services">Услуги</a>
      <a href="index.html#process">Как работаем</a>
      <a href="index.html#pricing">Прайс</a>
      <a href="index.html#calc">Калькулятор</a>
      <a href="index.html#faq">Вопросы</a>
      <a class="btn btn-primary nav-cta" href="index.html#order">Оставить заявку</a>
    </nav>"""

PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Договор-оферта — Учебный советник</title>
<meta name="description" content="Публичная оферта на оказание информационно-консультационных услуг ИП Подойниковой Е. А.: предмет договора, порядок оплаты, права и обязанности сторон, прайс-лист.">
<meta name="theme-color" content="#123c6b">
<link rel="canonical" href="https://uchebnyisovetnik.ru/oferta.html">

<meta property="og:type" content="article">
<meta property="og:site_name" content="Учебный советник">
<meta property="og:title" content="Договор-оферта — Учебный советник">
<meta property="og:description" content="Публичная оферта на оказание информационно-консультационных услуг: условия, оплата, сроки и прайс-лист.">
<meta property="og:url" content="https://uchebnyisovetnik.ru/oferta.html">
<meta property="og:image" content="https://uchebnyisovetnik.ru/assets/img/og.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">

<link rel="icon" href="assets/img/favicon.png" type="image/png" sizes="64x64">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="preload" href="assets/fonts/manrope-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/css/fonts.css">
<!-- ?v= сбрасывает недельный кэш из .htaccess: меняем при правке стилей и скрипта -->
<link rel="stylesheet" href="assets/css/styles.css?v=2">
</head>
<body>

<div class="scroll-progress" aria-hidden="true"><span id="scrollBar"></span></div>

<a class="skip-link" href="#doc">Перейти к тексту договора</a>

<!-- ============ HEADER ============ -->
<header class="site-header" id="header">
  <div class="wrap header-inner">
    <a class="logo" href="index.html" aria-label="Учебный советник — на главную">
      <img class="logo-mark" src="assets/img/logo-mark.png" width="40" height="40" alt="" aria-hidden="true">
      <span class="logo-text">Учебный <i>советник</i></span>
    </a>

{nav}

    <div class="header-actions">
      <a class="btn btn-primary btn-sm" href="index.html#order">Оставить заявку</a>
      <button class="burger" id="burger" type="button" aria-label="Меню" aria-expanded="false"><span></span><span></span></button>
    </div>
  </div>
</header>

<main>

<!-- ============ ШАПКА ДОКУМЕНТА ============ -->
<section class="doc-hero">
  <div class="hero-glow" aria-hidden="true"></div>

  <div class="wrap doc-hero-inner">
    <nav class="crumbs" aria-label="Хлебные крошки">
      <a href="index.html">Главная</a>
      <span aria-hidden="true">/</span>
      <span aria-current="page">Договор-оферта</span>
    </nav>

    <h1>{title}<span>{subtitle}</span></h1>

    <dl class="doc-place">
      <div><dt>Место заключения</dt><dd>{city}<span>{region}</span></dd></div>
      <div><dt>Дата</dt><dd>{date}</dd></div>
    </dl>

    <div class="doc-actions">
      <a class="btn btn-primary" href="assets/docs/dogovor-oferta.docx" download>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M8 11l4 4 4-4M5 19h14"/></svg>
        Скачать .docx
      </a>
      <button class="btn btn-ghost" id="docPrint" type="button">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M7 9V4h10v5M7 17H5v-6h14v6h-2M7 14h10v6H7z"/></svg>
        Распечатать
      </button>
    </div>
  </div>
</section>

<!-- ============ ТЕКСТ ДОКУМЕНТА ============ -->
<div class="wrap doc-layout" id="doc">
  <!-- На узких экранах оглавление сворачивается: см. initDocToc в main.js -->
  <details class="doc-toc" id="docToc" open>
    <summary>Содержание<span class="chev" aria-hidden="true"></span></summary>
    <nav aria-label="Разделы договора">
{toc}
    </nav>
  </details>

  <article class="doc">
{article}
  </article>
</div>

</main>

<!-- ============ FOOTER ============ -->
<footer class="site-footer">
  <div class="wrap footer-inner">
    <div class="f-brand">
      <a class="f-logo" href="index.html" aria-label="Учебный советник — на главную">
        <img src="assets/img/logo.png" width="230" height="166" alt="Учебный советник">
      </a>
      <p>Консультационные услуги по подготовке учебных работ для студентов колледжей, бакалавриата и магистратуры.</p>
    </div>

    <nav class="f-nav" aria-label="Разделы">
      <b>Разделы</b>
      <a href="index.html#services">Услуги</a>
      <a href="index.html#process">Как работаем</a>
      <a href="index.html#pricing">Прайс-лист</a>
      <a href="index.html#calc">Калькулятор</a>
      <a href="index.html#faq">Вопросы</a>
    </nav>

    <div class="f-contacts">
      <b>Связь</b>
      <a href="index.html#order">MAX · @sovetnik</a>
      <a href="mailto:ekatpod89@gmail.com">ekatpod89@gmail.com</a>
      <a class="btn btn-ghost btn-sm" href="index.html#order">Оставить заявку</a>
    </div>

    <div class="f-legal">
      <b>Реквизиты</b>
      <p class="fl-name">ИП Подойникова Екатерина Александровна</p>
      <dl>
        <dt>ИНН</dt><dd>519055358634</dd>
        <dt>ОГРНИП</dt><dd>326510000026871</dd>
        <dt>Регион</dt><dd>Мурманская область</dd>
      </dl>
      <a class="fl-doc" href="oferta.html" aria-current="page">Договор-оферта</a>
    </div>
  </div>

  <div class="wrap footer-bottom">
    <p>© <span id="year">2026</span> ИП Подойникова Е. А. Все права защищены.</p>
    <p class="disclaimer">Оказываем консультационные услуги информационного характера. Материалы предназначены для использования в качестве образца при самостоятельной подготовке работ.</p>
  </div>
</footer>

<a class="to-top" id="toTop" href="#doc" aria-label="Наверх">
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15V5M6 9l4-4 4 4"/></svg>
</a>

<script src="assets/js/main.js?v=2"></script>
</body>
</html>
"""


def main():
    blocks = read_blocks(SRC)
    texts = [b[1] for b in blocks if b[0] == "p"]

    title, subtitle = texts[0], texts[1]
    # В документе город и дата стоят в одной строке: «г. Полярные Зори ... «14» сентября 2026 г.»
    place = next(t for t in texts if t.startswith("г. "))
    city, _, date = (p.strip() for p in place.partition("«"))
    date = "«" + date if date else ""
    region = next(t for t in texts if t == "Мурманская область")

    article, toc = render(blocks, skip={title, subtitle, place, region})
    toc_html = "\n".join(f'      <a href="#{a}">{esc(t)}</a>' for a, t in toc)

    OUT.write_text(
        PAGE.format(
            nav=NAV,
            title=esc(title),
            subtitle=esc(subtitle),
            city=esc(city),
            region=esc(region),
            date=esc(date),
            toc=toc_html,
            article="\n".join("    " + line for line in article),
        ),
        encoding="utf-8",
    )
    print(f"{OUT.relative_to(ROOT)}: разделов {len(toc)}, блоков {len(article)}")


if __name__ == "__main__":
    main()
