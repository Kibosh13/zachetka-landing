/* =========================================================
   Зачётка — логика лендинга
   Прайс, калькулятор, форма, навигация, анимации
   ========================================================= */

/* ---------- Данные прайса (единый источник для таблицы и калькулятора) ---------- */
const PRICE_DATA = [
  {
    id: 'ref',
    title: 'Рефераты и доклады',
    items: [
      { name: 'Реферат (гуманитарные дисциплины)', volume: '15–20 стр.', term: '3–5 дней', price: 'от 300 ₽', calc: { min: 300, max: 900, term: '3–5 дней' } },
      { name: 'Реферат (технические дисциплины)', volume: '15–20 стр.', term: '3–5 дней', price: 'от 400 ₽', calc: null },
      { name: 'Доклад с презентацией', volume: '5–10 стр. + 10–15 слайдов', term: '2–3 дня', price: 'от 800 ₽', calc: { min: 800, max: 1800, term: '2–3 дня' } },
      { name: 'Эссе', volume: '5–10 стр.', term: '1–2 дня', price: 'от 300 ₽', calc: { min: 300, max: 800, term: '1–2 дня' } }
    ]
  },
  {
    id: 'control',
    title: 'Контрольные и практические',
    items: [
      { name: 'Контрольная работа (теоретическая)', volume: '10–15 стр.', term: '2–4 дня', price: 'от 500 ₽', calc: { min: 500, max: 1200, term: '2–4 дня' } },
      { name: 'Контрольная работа (с расчётами)', volume: '10–20 стр.', term: '3–5 дней', price: 'от 800 ₽', calc: { min: 800, max: 2000, term: '3–5 дней' } },
      { name: 'Решение задач', volume: 'за 1 задачу', term: '1–2 дня', price: 'от 150 ₽', calc: { min: 150, max: 600, term: '1–2 дня' } },
      { name: 'Лабораторная работа (отчёт)', volume: '10–15 стр.', term: '2–3 дня', price: 'от 300 ₽', calc: { min: 300, max: 900, term: '2–3 дня' } },
      { name: 'Практическая работа', volume: '5–15 стр.', term: '2–3 дня', price: 'от 600 ₽', calc: { min: 600, max: 1500, term: '2–3 дня' } }
    ]
  },
  {
    id: 'course',
    title: 'Курсовые работы',
    items: [
      { name: 'Курсовая работа (теоретическая)', volume: '25–35 стр.', term: '7–14 дней', price: '2 000 – 6 000 ₽', calc: { min: 2000, max: 6000, term: '7–14 дней' } },
      { name: 'Курсовая работа (с расчётной частью)', volume: '30–40 стр.', term: '10–14 дней', price: '3 000 – 10 000 ₽', calc: { min: 3000, max: 10000, term: '10–14 дней' } },
      { name: 'Курсовой проект (с чертежами)', volume: '30–50 стр. + чертежи', term: '14–21 день', price: '4 000 – 15 000 ₽', calc: { min: 4000, max: 15000, term: '14–21 день' } }
    ]
  },
  {
    id: 'vkr',
    title: 'Выпускные работы',
    items: [
      { name: 'ВКР бакалавра (гуманитарные)', volume: '50–70 стр.', term: '21–30 дней', price: 'от 20 000 ₽', calc: { min: 20000, max: 32000, term: '21–30 дней' } },
      { name: 'ВКР бакалавра (технические)', volume: '50–80 стр.', term: '21–30 дней', price: 'от 25 000 ₽', calc: null },
      { name: 'Магистерская диссертация', volume: '80–120 стр.', term: '30–60 дней', price: 'от 35 000 ₽', calc: { min: 35000, max: 60000, term: '30–60 дней' } }
    ]
  },
  {
    id: 'extra',
    title: 'Дополнительные услуги',
    items: [
      { name: 'Презентация (без текста)', volume: '10–15 слайдов', term: '1–2 дня', price: 'от 500 ₽', calc: { min: 500, max: 1200, term: '1–2 дня' } },
      { name: 'Речь к защите', volume: '3–5 стр.', term: '1–2 дня', price: '500 – 1 000 ₽', calc: { min: 500, max: 1000, term: '1–2 дня' } },
      { name: 'Повышение оригинальности текста', volume: 'за 1 стр.', term: '1–3 дня', price: '50 – 100 ₽', calc: null },
      { name: 'Оформление по ГОСТ / методичке', volume: 'за 1 стр.', term: '1–2 дня', price: '30 – 50 ₽', calc: null },
      { name: 'Сопровождение заданий сессии', volume: 'под ключ', term: '10–20 дней', price: 'от 10 000 ₽', calc: { min: 10000, max: 25000, term: '10–20 дней' } },
      { name: 'Доработка / правки по замечаниям', volume: '—', term: '1–5 дней', price: '30% от стоимости', calc: null },
      { name: 'Срочное выполнение', volume: 'менее 50% срока', term: '—', price: '+50–100% к стоимости', calc: null }
    ]
  }
];

const rub = (n) => Math.round(n / 50) * 50;
const fmt = (n) => rub(n).toLocaleString('ru-RU') + ' ₽';

const days = (n) => {
  const d = n % 10, dd = n % 100;
  if (d === 1 && dd !== 11) return 'день';
  if (d >= 2 && d <= 4 && (dd < 12 || dd > 14)) return 'дня';
  return 'дней';
};

// Срочный заказ сжимает стандартный срок: сохраняем диапазон, но пересчитываем границы
function shortenTerm(term, k) {
  const m = term.match(/(\d+)\s*[–-]\s*(\d+)/);
  if (!m) return term;
  const from = Math.max(1, Math.round(Number(m[1]) * k));
  const to = Math.max(from + 1, Math.round(Number(m[2]) * k));
  return `${from}–${to} ${days(to)}`;
}

/* ---------- Прайс: табы + таблицы ---------- */
function buildPricing() {
  const tabs = document.getElementById('priceTabs');
  const panels = document.getElementById('pricePanels');
  if (!tabs || !panels) return;

  PRICE_DATA.forEach((group, i) => {
    const tab = document.createElement('button');
    tab.type = 'button';
    tab.className = 'tab' + (i === 0 ? ' is-active' : '');
    tab.textContent = group.title;
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-selected', String(i === 0));
    tab.setAttribute('aria-controls', 'panel-' + group.id);
    tabs.appendChild(tab);

    const panel = document.createElement('div');
    panel.className = 'price-panel' + (i === 0 ? ' is-active' : '');
    panel.id = 'panel-' + group.id;
    panel.setAttribute('role', 'tabpanel');

    const rows = group.items.map((it) => `
      <div class="pt-row">
        <div class="pt-name">${it.name}</div>
        <div class="pt-cell"><span class="pt-label">Объём</span>${it.volume}</div>
        <div class="pt-cell"><span class="pt-label">Срок</span>${it.term}</div>
        <div class="pt-price"><span class="pt-label">Стоимость</span>${it.price}</div>
      </div>`).join('');

    panel.innerHTML = `
      <div class="price-table">
        <div class="pt-head">
          <div>Услуга</div><div>Объём</div><div>Срок</div><div style="text-align:right">Стоимость</div>
        </div>
        ${rows}
      </div>`;
    panels.appendChild(panel);
  });

  tabs.addEventListener('click', (e) => {
    const tab = e.target.closest('.tab');
    if (!tab) return;
    const idx = [...tabs.children].indexOf(tab);
    [...tabs.children].forEach((t, i) => {
      t.classList.toggle('is-active', i === idx);
      t.setAttribute('aria-selected', String(i === idx));
    });
    [...panels.children].forEach((p, i) => p.classList.toggle('is-active', i === idx));
  });
}

/* ---------- Опции «тип работы» для селектов ---------- */
function calcOptions() {
  const out = [];
  PRICE_DATA.forEach((g) => {
    g.items.forEach((it) => { if (it.calc) out.push({ label: it.name, ...it.calc }); });
  });
  return out;
}

function fillTypeSelects() {
  const options = calcOptions();
  ['calcType', 'fType'].forEach((id) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    PRICE_DATA.forEach((g) => {
      const grp = document.createElement('optgroup');
      grp.label = g.title;
      g.items.forEach((it) => {
        if (!it.calc) return;
        const o = document.createElement('option');
        o.value = String(options.findIndex((x) => x.label === it.name));
        o.textContent = it.name;
        grp.appendChild(o);
      });
      if (grp.children.length) sel.appendChild(grp);
    });
  });

  // По умолчанию — курсовая теоретическая: самый частый запрос
  const def = options.findIndex((o) => o.label.startsWith('Курсовая работа (теор'));
  const calcSel = document.getElementById('calcType');
  if (calcSel && def > -1) calcSel.value = String(def);
}

/* ---------- Калькулятор ---------- */
function initCalc() {
  const form = document.getElementById('calcForm');
  if (!form) return;

  const options = calcOptions();
  const typeSel = document.getElementById('calcType');
  const sumEl = document.getElementById('calcSum');
  const termEl = document.getElementById('calcTerm');
  const listEl = document.getElementById('calcBreakdown');
  const toOrder = document.getElementById('calcToOrder');

  const state = { discipline: 1, urgency: 1 };

  function activeChip(groupId) {
    const g = document.getElementById(groupId);
    return g ? g.querySelector('.chip.is-active') : null;
  }

  function recalc() {
    const base = options[Number(typeSel.value)] || options[0];
    const extras = [...document.querySelectorAll('#calcExtras input:checked')];
    const extraSum = extras.reduce((s, el) => s + Number(el.dataset.add), 0);

    const k = state.discipline * state.urgency;
    const min = base.min * k + extraSum;
    const max = base.max * k + extraSum;

    sumEl.textContent = min === max ? fmt(min) : `${fmt(min)} — ${fmt(max)}`;

    const urgencyLabel = activeChip('calcUrgency')?.textContent.trim() || 'Стандартный';
    if (state.urgency === 1) {
      termEl.textContent = `Срок: ${base.term}`;
    } else {
      const short = shortenTerm(base.term, state.urgency === 1.5 ? 0.6 : 0.4);
      termEl.textContent = short === base.term
        ? `Срок: ${base.term} · в срочную очередь`
        : `Срок: ${short} вместо ${base.term}`;
    }

    const rows = [
      ['Базовая стоимость', options[Number(typeSel.value)] ? (base.min === base.max ? fmt(base.min) : `${fmt(base.min)} — ${fmt(base.max)}`) : '—'],
      ['Дисциплина', activeChip('calcDiscipline')?.textContent.trim() + (state.discipline > 1 ? ` · +${Math.round((state.discipline - 1) * 100)}%` : '')],
      ['Срочность', urgencyLabel + (state.urgency > 1 ? ` · +${Math.round((state.urgency - 1) * 100)}%` : '')]
    ];
    if (extraSum) rows.push([`Доп. услуги (${extras.length})`, '+ ' + fmt(extraSum)]);

    listEl.innerHTML = rows.map(([k2, v]) => `<li><span>${k2}</span><b>${v}</b></li>`).join('');

    // Прокидываем выбор в форму заявки
    toOrder.dataset.type = base.label;
  }

  ['calcDiscipline', 'calcUrgency'].forEach((groupId) => {
    const group = document.getElementById(groupId);
    if (!group) return;
    group.addEventListener('click', (e) => {
      const chip = e.target.closest('.chip');
      if (!chip) return;
      [...group.children].forEach((c) => {
        c.classList.toggle('is-active', c === chip);
        c.setAttribute('aria-checked', String(c === chip));
      });
      state[groupId === 'calcDiscipline' ? 'discipline' : 'urgency'] = Number(chip.dataset.value);
      recalc();
    });
  });

  form.addEventListener('change', recalc);

  toOrder.addEventListener('click', () => {
    const fType = document.getElementById('fType');
    if (!fType) return;
    const opt = [...fType.options].find((o) => o.textContent === toOrder.dataset.type);
    if (opt) fType.value = opt.value;
    const topic = document.getElementById('fTopic');
    if (topic && !topic.value) {
      topic.placeholder = `Например: ${toOrder.dataset.type} — тема, дисциплина, требования`;
    }
  });

  recalc();
}

/* ---------- Форма заявки ---------- */
function initForm() {
  const form = document.getElementById('orderForm');
  if (!form) return;

  const success = document.getElementById('formSuccess');
  const showErr = (id, msg) => {
    const slot = form.querySelector(`.err[data-for="${id}"]`);
    const input = document.getElementById(id);
    if (slot) slot.textContent = msg;
    if (input) input.classList.toggle('is-invalid', Boolean(msg));
  };

  form.addEventListener('input', (e) => {
    if (e.target.id) showErr(e.target.id, '');
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    let ok = true;

    const name = document.getElementById('fName');
    const contact = document.getElementById('fContact');
    const agree = document.getElementById('fAgree');

    if (name.value.trim().length < 2) { showErr('fName', 'Укажите имя'); ok = false; }
    if (contact.value.trim().length < 3) { showErr('fContact', 'Укажите MAX или e-mail'); ok = false; }
    if (!agree.checked) { showErr('fAgree', 'Нужно согласие на обработку данных'); ok = false; }
    if (!ok) return;

    const type = document.getElementById('fType');
    const body = [
      `Имя: ${name.value.trim()}`,
      `Контакт: ${contact.value.trim()}`,
      `Тип работы: ${type.options[type.selectedIndex]?.textContent || '—'}`,
      `Срок сдачи: ${document.getElementById('fDeadline').value || 'не указан'}`,
      '',
      'Тема и требования:',
      document.getElementById('fTopic').value.trim() || '—'
    ].join('\n');

    // Без бэкенда: открываем почтовый клиент с заполненным письмом.
    // Подключение CRM/Telegram-бота — заменить этот блок на fetch().
    window.location.href =
      `mailto:hello@zachetka.ru?subject=${encodeURIComponent('Заявка с сайта — ' + name.value.trim())}&body=${encodeURIComponent(body)}`;

    form.querySelectorAll('.of-grid, .check-agree, button[type="submit"]').forEach((el) => { el.hidden = true; });
    success.hidden = false;
    success.scrollIntoView({ block: 'center', behavior: 'smooth' });
  });
}

/* ---------- Навигация: хедер, мобильное меню, активная ссылка ---------- */
function initNav() {
  const header = document.getElementById('header');
  const nav = document.getElementById('nav');
  const burger = document.getElementById('burger');
  const toTop = document.getElementById('toTop');
  const bar = document.getElementById('scrollBar');

  burger?.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    burger.setAttribute('aria-expanded', String(open));
  });

  nav?.addEventListener('click', (e) => {
    if (e.target.tagName === 'A') {
      nav.classList.remove('is-open');
      burger?.setAttribute('aria-expanded', 'false');
    }
  });

  const links = [...document.querySelectorAll('.nav a:not(.nav-cta)')];
  const sections = links
    .map((a) => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);

  let raf = null;
  const onScroll = () => {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      const y = window.scrollY;
      header.classList.toggle('is-stuck', y > 12);
      toTop?.classList.toggle('is-visible', y > 700);

      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (bar) bar.style.width = (max > 0 ? (y / max) * 100 : 0) + '%';

      const mid = y + window.innerHeight * 0.32;
      let active = -1;
      sections.forEach((s, i) => { if (s.offsetTop <= mid) active = i; });
      links.forEach((a, i) => a.classList.toggle('is-active', i === active));

      raf = null;
    });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

/* ---------- Появление блоков + счётчики ---------- */
function initReveal() {
  const items = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    items.forEach((el) => el.classList.add('is-in'));
    return;
  }

  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const siblings = [...(el.parentElement?.children || [])].filter((c) => c.classList.contains('reveal'));
      el.style.transitionDelay = Math.min(siblings.indexOf(el), 5) * 70 + 'ms';
      el.classList.add('is-in');
      io.unobserve(el);
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });

  items.forEach((el) => io.observe(el));
}

function initCounters() {
  const nums = document.querySelectorAll('[data-count]');
  const run = (el) => {
    const target = Number(el.dataset.count);
    const suffix = el.dataset.suffix || '';
    const dur = 1100;
    const t0 = performance.now();
    const tick = (t) => {
      const p = Math.min((t - t0) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  if (!('IntersectionObserver' in window)) { nums.forEach(run); return; }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { run(e.target); io.unobserve(e.target); } });
  }, { threshold: 0.6 });
  nums.forEach((el) => io.observe(el));
}

/* ---------- Инициализация ---------- */
document.addEventListener('DOMContentLoaded', () => {
  buildPricing();
  fillTypeSelects();
  initCalc();
  initForm();
  initNav();
  initReveal();
  initCounters();

  const year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  const deadline = document.getElementById('fDeadline');
  if (deadline) deadline.min = new Date().toISOString().slice(0, 10);
});
