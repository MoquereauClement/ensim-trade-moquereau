'use strict';

const series = [
  { id: 'clement', name: 'Clément', color: '#006a54', width: 3 },
  { id: 'random_trader', name: 'Trader aléatoire', color: '#285bae', width: 1.7 },
  { id: 'random_buyer', name: 'Acheteur aléatoire', color: '#7846a1', width: 1.7 },
  { id: 'random_seller', name: 'Vendeur aléatoire', color: '#a64e20', width: 1.7 },
];
const number = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });
const price = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
const percent = new Intl.NumberFormat('fr-FR', { style: 'percent', maximumFractionDigits: 2 });
const date = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Europe/Paris' });
const $ = (id) => document.getElementById(id);
const format = (formatter, value) => Number.isFinite(value) ? formatter.format(value) : '—';
const formatDate = (value) => date.format(new Date(value));
let data = { performance: [], decisions: [] };
let logLimit = 20;
let points = [];
let plotBounds;

function element(tag, content, className) {
  const node = document.createElement(tag);
  if (content !== undefined) node.textContent = content;
  if (className) node.className = className;
  return node;
}

function orderBadge(signal) {
  const units = number.format(Math.abs(signal * 100));
  if (signal > 0) return element('span', `Acheter ${units}`, 'badge buy');
  if (signal < 0) return element('span', `Vendre ${units}`, 'badge sell');
  return element('span', 'Attendre', 'badge');
}

function withDrawdown(rows) {
  const peaks = {};
  return rows.map((row) => {
    const risk = {};
    for (const { id } of series) {
      const value = row.values[id];
      if (!Number.isFinite(value)) continue;
      peaks[id] = Math.max(peaks[id] ?? value, value);
      risk[id] = peaks[id] > 0 ? (value / peaks[id]) - 1 : 0;
    }
    return { ...row, risk };
  });
}

function renderPerformance() {
  const rows = withDrawdown(data.performance);
  const own = rows.filter((row) => Number.isFinite(row.values.clement));
  const last = own.at(-1);
  if (last) {
    const first = own[0];
    $('value').textContent = number.format(last.values.clement);
    $('return').textContent = first.values.clement > 0 ? percent.format(last.values.clement / first.values.clement - 1) : '—';
    $('return-note').textContent = `Depuis le tour ${first.turn}`;
    $('drawdown').textContent = percent.format(-Math.min(0, ...own.map((row) => row.risk.clement)));
  }
  const lastRound = rows.at(-1);
  if (lastRound) $('market-round').textContent = `Tour ${lastRound.turn}`;
  $('legend').replaceChildren(...series.map(({ name, color }) => {
    const item = element('li');
    const swatch = element('span', undefined, 'swatch');
    swatch.style.background = color;
    swatch.setAttribute('aria-hidden', 'true');
    item.append(swatch, document.createTextNode(name));
    return item;
  }));
  const limit = Number($('chart-range').value);
  points = limit ? rows.slice(-limit) : rows;
  $('chart-empty').hidden = points.length > 0;
  $('chart').parentElement.hidden = points.length === 0;
  $('cursor').disabled = points.length < 2;
  $('cursor').max = Math.max(0, points.length - 1);
  $('cursor').value = $('cursor').max;
  drawChart();
}

function drawChart() {
  const measure = $('chart-mode').value === 'risk' ? 'risk' : 'values';
  const formatter = measure === 'risk' ? percent : number;
  $('chart-note').textContent = measure === 'risk' ? 'Écart par rapport au meilleur niveau observé jusque-là' : 'Valeurs du classement officiel';
  if (!points.length) return;
  const canvas = $('chart');
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (!width || !height) return;
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = width * pixelRatio;
  canvas.height = height * pixelRatio;
  const ctx = canvas.getContext('2d');
  ctx.scale(pixelRatio, pixelRatio);
  const padding = { left: 65, right: 18, top: 15, bottom: 30 };
  const spanX = width - padding.left - padding.right;
  const spanY = height - padding.top - padding.bottom;
  const firstTurn = points[0].turn;
  const lastTurn = points.at(-1).turn;
  const x = (turn) => padding.left + (lastTurn === firstTurn ? spanX / 2 : (turn - firstTurn) * spanX / (lastTurn - firstTurn));
  plotBounds = { x };
  const values = points.flatMap((row) => Object.values(row[measure])).filter(Number.isFinite);
  if (!values.length) {
    $('chart-point').textContent = 'Valeurs indisponibles pour cette mesure.';
    return;
  }
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (measure === 'risk') max = 0;
  const buffer = (max - min) * .05 || (measure === 'risk' ? .01 : 1);
  min -= buffer;
  if (measure !== 'risk') max += buffer;
  const y = (value) => padding.top + spanY * (max - value) / (max - min);

  ctx.font = '12px system-ui';
  ctx.fillStyle = '#48635f';
  ctx.strokeStyle = '#dde9e4';
  ctx.lineWidth = 1;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  for (let j = 0; j <= 4; j++) {
    const tick = max - (max - min) * j / 4;
    const ordinate = y(tick);
    ctx.beginPath();
    ctx.moveTo(padding.left, ordinate);
    ctx.lineTo(width - padding.right, ordinate);
    ctx.stroke();
    ctx.fillText(formatter.format(tick), padding.left - 8, ordinate);
  }
  const tickCount = Math.min(points.length, width < 480 ? 3 : 6);
  ctx.textAlign = 'center';
  for (let j = 0; j < tickCount; j++) {
    const index = tickCount === 1 ? 0 : Math.round(j * (points.length - 1) / (tickCount - 1));
    ctx.fillText(points[index].turn, x(points[index].turn), height - 14);
  }

  for (const { id, color, width: strokeWidth } of [...series].reverse()) {
    ctx.strokeStyle = color;
    ctx.lineWidth = strokeWidth;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    let active = false;
    for (const row of points) {
      const value = row[measure][id];
      if (!Number.isFinite(value)) { active = false; continue; }
      if (active) ctx.lineTo(x(row.turn), y(value));
      else ctx.moveTo(x(row.turn), y(value));
      active = true;
    }
    ctx.stroke();
  }

  const row = points[Number($('cursor').value)] ?? points.at(-1);
  ctx.strokeStyle = '#728f89';
  ctx.lineWidth = 1;
  ctx.setLineDash([3, 4]);
  ctx.beginPath();
  ctx.moveTo(x(row.turn), padding.top);
  ctx.lineTo(x(row.turn), height - padding.bottom);
  ctx.stroke();
  ctx.setLineDash([]);
  for (const { id, color } of series) {
    if (!Number.isFinite(row[measure][id])) continue;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x(row.turn), y(row[measure][id]), 4, 0, 2 * Math.PI);
    ctx.fill();
  }
  const selected = series.map(({ id, name }) => `${name} ${format(formatter, row[measure][id])}`);
  $('cursor').setAttribute('aria-valuetext', `Tour ${row.turn}`);
  $('chart-point').textContent = [`Tour ${row.turn}`, ...selected].join(' · ');
}

function renderSignals() {
  const last = data.decisions.at(-1);
  if (!last) return;
  $('signals-note').textContent = `Tour ${last.turn} · calcul du ${formatDate(last.at)}`;
  $('signals').replaceChildren(...Object.entries(last.products).map(([product, entry]) => {
    const card = element('article', undefined, 'card');
    const heading = element('div', undefined, 'signal-header');
    heading.append(element('h2', `Produit ${product}`), orderBadge(entry.signal));
    const values = element('dl', undefined, 'signal-values');
    for (const [name, value] of [['Prix', entry.price], ['Achat ≤', entry.buy_limit], ['Vente ≥', entry.sell_limit]]) {
      const pair = element('div');
      pair.append(element('dt', name), element('dd', format(price, value)));
      values.append(pair);
    }
    card.append(heading, values, element('p', entry.reason, 'signal-reason'));
    return card;
  }));
}

function renderJournal() {
  const productFilter = $('product-filter').value;
  const entries = [...data.decisions].reverse().flatMap((decision) =>
    Object.entries(decision.products)
      .filter(([product]) => !productFilter || product === productFilter)
      .map(([product, values]) => ({ ...values, product, turn: decision.turn, at: decision.at })));
  $('journal').replaceChildren(...entries.slice(0, logLimit).map((entry) => {
    const row = element('tr');
    const order = element('td');
    order.append(orderBadge(entry.signal));
    row.append(element('td', entry.turn), element('td', formatDate(entry.at)), element('td', entry.product), order, element('td', entry.reason));
    return row;
  }));
  $('journal-empty').hidden = entries.length > 0;
  $('show-more').hidden = entries.length <= logLimit;
}

async function refresh() {
  $('refresh').disabled = true;
  $('status').classList.remove('error');
  $('status').textContent = 'Chargement des données…';
  try {
    const response = await fetch('./data/observations.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const snapshot = await response.json();
    if (!Array.isArray(snapshot.performance) || !Array.isArray(snapshot.decisions)) throw new Error('Format inattendu');
    data = snapshot;
    renderPerformance();
    renderSignals();
    renderJournal();
    const last = data.performance.at(-1);
    $('status').textContent = last ? `Relevé marché du ${formatDate(last.at)} (Paris)` : 'En attente du premier relevé.';
  } catch (error) {
    $('status').classList.add('error');
    $('status').textContent = 'Impossible de charger les données. Réessaie avec Actualiser.';
    console.error(error);
  } finally {
    $('refresh').disabled = false;
  }
}

$('refresh').addEventListener('click', refresh);
$('chart-mode').addEventListener('change', drawChart);
$('chart-range').addEventListener('change', renderPerformance);
$('cursor').addEventListener('input', drawChart);
$('chart').addEventListener('pointermove', (event) => {
  if (!plotBounds || !points.length) return;
  const pointerX = event.clientX - $('chart').getBoundingClientRect().left;
  const nearest = points.reduce((best, row, i) =>
    Math.abs(plotBounds.x(row.turn) - pointerX) < Math.abs(plotBounds.x(points[best].turn) - pointerX) ? i : best, 0);
  if (nearest !== Number($('cursor').value)) {
    $('cursor').value = nearest;
    drawChart();
  }
});
$('product-filter').addEventListener('change', () => { logLimit = 20; renderJournal(); });
$('show-more').addEventListener('click', () => { logLimit += 20; renderJournal(); });
new ResizeObserver(drawChart).observe($('chart').parentElement);
refresh();
