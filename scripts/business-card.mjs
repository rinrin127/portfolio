/**
 * 名刺データ（ピンク）を content/*.json から生成する。
 *
 *   npm run card
 *
 * 出力先: print/business-card/
 *   business-card-pink.html        名刺のもと（ブラウザで開けば確認できる）
 *   business-card-pink.pdf         印刷入稿用。表・裏の2ページ、塗り足し3mm込み（97×61mm）
 *   business-card-pink-front.png   表のプレビュー画像（350dpi）
 *   business-card-pink-back.png    裏のプレビュー画像
 *
 * 載せる内容はすべて content/ から取ります。
 *   site.json     ロゴ・タグライン・実績3行・メール・URL・所在地
 *   profile.json  名前・肩書き
 *   services.json 事業の3本柱（裏面）
 *   accounts.json 本アカウントのInstagram（裏面）
 *
 * PDF/PNG を作るには Chrome か Chromium が必要です。見つからなければ HTML だけ出します。
 * 場所を指定したいときは環境変数 CHROME_PATH にブラウザ本体のパスを入れてください。
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT_DIR = path.join(ROOT, 'print', 'business-card');
const BASENAME = 'business-card-pink';

const readJson = (name) => JSON.parse(fs.readFileSync(path.join(ROOT, 'content', name), 'utf8'));
const site = readJson('site.json');
const profile = readJson('profile.json');
const services = readJson('services.json');
const accounts = readJson('accounts.json');

const e = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

/* ---------- 載せるデータ ---------- */

const enFirst = site.wordmark === 'en-first' && Boolean(site.nameEn);
const mark = enFirst ? site.nameEn : site.name;
const sub = enFirst ? site.name : site.nameEn;

const email = site.contact?.email ? `${site.contact.email.user}@${site.contact.email.domain}` : '';
const url = site.url || '';
const urlLabel = url.replace(/^https?:\/\//, '').replace(/\/$/, '');
const location = site.footer?.location || '';
const achievements = site.achievements?.items || [];
const pillars = (services.pillars || []).map((p) => ({ no: p.no, title: p.title }));
const mainAccount = (accounts.items || []).find((a) => a.public && /本アカウント/.test(a.name || ''));

/** 名前のローマ字。profile.json に nameEn があればそれを使う */
const nameEn = profile.nameEn || 'Risa Nakajima';

/** タグライン。site.json の card.tagline があればそちらを優先。taglineAccent の部分だけ色を変える */
function taglineHtml() {
  const t = e(site.card?.tagline || site.tagline || '');
  const a = e(site.card?.taglineAccent ?? site.taglineAccent ?? '');
  if (!a || !t.includes(a)) return t;
  return t.replace(a, `<em>${a}</em>`);
}

/** QRコード（print/business-card/qr-site.svg）。URLを変えたら README の手順で作り直す */
function qrSvg() {
  const p = path.join(OUT_DIR, 'qr-site.svg');
  if (!fs.existsSync(p)) return '';
  let svg = fs.readFileSync(p, 'utf8');
  const m = svg.match(/<!--\s*QR:\s*(\S+)\s*-->/);
  if (m && m[1] !== url) {
    console.warn(`⚠ qr-site.svg は ${m[1]} のQRです。site.json の url（${url}）と違うので作り直してください。`);
  }
  svg = svg.replace(/<\?xml[^>]*\?>/, '').replace(/<!--[\s\S]*?-->/g, '');
  // サイズ属性を外して CSS で大きさを決める。塗りは白（濃いピンクの上に載せる）
  return svg
    .replace(/\swidth="[^"]*"/, '')
    .replace(/\sheight="[^"]*"/, '')
    .replace('<svg', '<svg class="qr__code" fill="currentColor"');
}

/* ---------- フォント ---------- */

const FONTS = [
  ['Zen Old Mincho', 500, 'ZenOldMincho-500.ttf'],
  ['Zen Old Mincho', 600, 'ZenOldMincho-600.ttf'],
  ['Zen Old Mincho', 700, 'ZenOldMincho-700.ttf'],
  ['Zen Kaku Gothic New', 400, 'ZenKakuGothicNew-400.ttf'],
  ['Zen Kaku Gothic New', 500, 'ZenKakuGothicNew-500.ttf'],
  ['Zen Kaku Gothic New', 700, 'ZenKakuGothicNew-700.ttf'],
  ['Crimson Pro', 400, 'CrimsonPro-400.ttf'],
  ['Crimson Pro', 500, 'CrimsonPro-500.ttf'],
  ['Crimson Pro', 600, 'CrimsonPro-600.ttf'],
];
const GOOGLE_FONTS =
  'https://fonts.googleapis.com/css2?family=Zen+Old+Mincho:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Crimson+Pro:wght@400;500;600&display=block';

/**
 * フォントは Google Fonts から読む（ふつうのパソコンではこれで十分）。
 * fonts/ にTTFが置いてあれば「◯◯ (local)」という別名で先に読み、オフラインでも同じ字形で出す。
 * ローカルのファイルが無いときはブラウザが次の候補（Google Fonts）に進むので、どちらでも壊れない。
 */
function fontCss() {
  const dir = process.env.CARD_FONTS_DIR || path.join(OUT_DIR, 'fonts');
  const have = FONTS.filter(([, , file]) => fs.existsSync(path.join(dir, file)));
  const link = `<link href="${GOOGLE_FONTS}" rel="stylesheet">`;
  if (have.length !== FONTS.length) return { link, css: '' };
  const rel = path.relative(OUT_DIR, dir).split(path.sep).join('/') || '.';
  const css = have
    .map(
      ([family, weight, file]) =>
        `@font-face{font-family:"${family} (local)";font-weight:${weight};font-style:normal;src:url("${rel}/${file}") format("truetype")}`
    )
    .join('\n');
  return { link, css };
}

/* ---------- HTML ---------- */

function html() {
  const fonts = fontCss();
  return `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>名刺（ピンク）｜${e(site.name)}</title>
${fonts.link}
<style>
${fonts.css}

/* ============================================================
   名刺（ピンク）
   仕上がり 91×55mm ／ 塗り足し 3mm ／ ページ 97×61mm
   文字・線は仕上がり線から 4mm 以上内側（=ページ端から 7mm）に置く
   ============================================================ */
:root {
  --pink-bg:       #FCE9EF;  /* 表の地色 */
  --pink-soft:     #F5C9D6;  /* 罫線・淡いあしらい */
  --pink:          #E58AA5;  /* 中間のピンク */
  --pink-deep:     #C9466C;  /* 裏の地色・強調色 */
  --pink-ink:      #5A2A38;  /* 表の文字色 */
  --pink-ink-soft: #8E5F6C;  /* 表の小さな文字 */
  --on-deep:       #FFF7F9;  /* 裏の文字色 */
  --on-deep-soft:  #F7C9D6;  /* 裏の小さな文字 */

  --font-mincho: "Zen Old Mincho (local)", "Zen Old Mincho", "Hiragino Mincho ProN", "Yu Mincho", serif;
  --font-sans:   "Zen Kaku Gothic New (local)", "Zen Kaku Gothic New", "Hiragino Sans", "Yu Gothic", sans-serif;
  --font-en:     "Crimson Pro (local)", "Crimson Pro", "Zen Old Mincho (local)", "Zen Old Mincho", Georgia, serif;

  --bleed: 3mm;
  --safe:  7mm;
}

@page { size: 97mm 61mm; margin: 0; }

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: #ECE7E4;
  color: var(--pink-ink);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* 画面で見るときの並び */
.sheet { display: flex; flex-wrap: wrap; gap: 16mm; padding: 16mm; }
.card {
  position: relative;
  width: 97mm; height: 61mm;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(60,30,40,.08), 0 18px 44px rgba(60,30,40,.12);
}
/* 画面だけ：仕上がり線の目安（印刷には出ない） */
.card::after {
  content: "";
  position: absolute; inset: var(--bleed);
  border: 1px dashed rgba(201,70,108,.45);
  pointer-events: none;
}
.sheet__note { flex-basis: 100%; font-size: 12px; color: #6B5A60; line-height: 1.8; }

/* ---------- 表 ---------- */
.card--front {
  background: var(--pink-bg);
}
.card--front .band {
  position: absolute; left: 0; top: 0; bottom: 0;
  width: 5.5mm;               /* 断裁後は 2.5mm 見える */
  background: var(--pink-deep);
}
.card--front .inner {
  position: absolute;
  inset: var(--safe) var(--safe) var(--safe) calc(var(--safe) + 3.5mm);
  display: grid;
  grid-template-columns: max-content 1fr;
  grid-template-rows: auto 1fr auto;
}
.wordmark { grid-column: 1 / -1; line-height: 1; }
.wordmark__mark {
  display: block;
  font-family: var(--font-en); font-weight: 600;
  font-size: 5.6mm; letter-spacing: .2em;
  color: var(--pink-deep);
}
.wordmark__sub {
  display: block; margin-top: 1.3mm;
  font-family: var(--font-mincho); font-weight: 500;
  font-size: 2.1mm; letter-spacing: .36em;
  color: var(--pink-ink-soft);
}
.tagline {
  grid-column: 1 / -1; align-self: start;
  margin: 3.2mm 0 0;
  font-family: var(--font-mincho); font-weight: 500;
  font-size: 3.1mm; letter-spacing: .1em; line-height: 1;
  color: var(--pink-ink);
}
.tagline em { font-style: normal; color: var(--pink-deep); }

.person { align-self: end; white-space: nowrap; }
.person__role {
  margin: 0 0 1.6mm;
  font-size: 2.1mm; letter-spacing: .06em; font-weight: 500;
  color: var(--pink-ink-soft);
}
.person__name {
  margin: 0;
  font-family: var(--font-mincho); font-weight: 600;
  font-size: 6mm; letter-spacing: .14em; line-height: 1;
  color: var(--pink-ink);
}
.person__name-en {
  display: block; margin-top: 1.6mm;
  font-family: var(--font-en); font-weight: 500;
  font-size: 2.6mm; letter-spacing: .12em;
  color: var(--pink-deep);
}

.contact {
  align-self: end; justify-self: end;
  display: grid; grid-template-columns: auto auto; column-gap: 2.6mm; align-items: end;
  white-space: nowrap;
}
.contact__lines {
  margin: 0; padding: 0; list-style: none;
  text-align: right;
  font-size: 2.05mm; letter-spacing: .03em; line-height: 1.85;
  color: var(--pink-ink);
}
.contact__lines .en { font-family: var(--font-en); font-size: 2.35mm; letter-spacing: .02em; }
.contact__lines .soft { color: var(--pink-ink-soft); }

.qr {
  width: 12.5mm; height: 12.5mm; padding: 1mm;
  background: #fff; border: .25mm solid var(--pink-soft);
  color: var(--pink-ink);
}
.qr__code { display: block; width: 100%; height: 100%; }

/* ---------- 裏 ---------- */
.card--back {
  background: var(--pink-deep);
  color: var(--on-deep);
}
.card--back .inner {
  position: absolute; inset: var(--safe);
  display: flex; flex-direction: column;
}
.back__mark {
  font-family: var(--font-en); font-weight: 500;
  font-size: 2.8mm; letter-spacing: .28em;
  color: var(--on-deep-soft);
}
.proof {
  margin: auto 0; padding: 0; list-style: none;
  font-family: var(--font-mincho); font-weight: 500;
  font-size: 3.05mm; letter-spacing: .06em; line-height: 2.05;
}
.proof li { display: flex; align-items: baseline; gap: 2.2mm; }
.proof li::before {
  content: ""; flex: none;
  width: 3.2mm; height: .28mm; background: var(--on-deep-soft);
  transform: translateY(-1mm);
}
.pillars {
  margin: 0 0 2mm; padding: 0 0 2mm; list-style: none;
  display: flex; gap: 2.6mm;
  border-bottom: .25mm solid rgba(255,247,249,.35);
  font-size: 2.05mm; letter-spacing: .04em; line-height: 1;
  color: var(--on-deep);
}
.pillars__no { font-family: var(--font-en); font-weight: 600; margin-right: .9mm; color: var(--on-deep-soft); }
.back__foot {
  display: flex; justify-content: space-between; align-items: baseline;
  font-family: var(--font-en); font-size: 2.35mm; letter-spacing: .04em;
  color: var(--on-deep-soft);
}
.back__foot .handle { color: var(--on-deep); }
.back__foot .handle small { font-family: var(--font-sans); font-size: 1.9mm; margin-right: 1.2mm; color: var(--on-deep-soft); }

/* ---------- 書き出し用（?side=front / ?side=back） ---------- */
body.is-flat .sheet { display: block; padding: 0; }
body.is-flat .card { box-shadow: none; }
body.is-flat .card::after { display: none; }
body.is-flat .sheet__note { display: none; }
body.is-flat[data-side="front"] .card--back  { display: none; }
body.is-flat[data-side="back"]  .card--front { display: none; }

/* ---------- 印刷（PDF） ---------- */
@media print {
  body { background: none; }
  .sheet { display: block; padding: 0; gap: 0; }
  .card { box-shadow: none; page-break-after: always; break-after: page; }
  .card:last-of-type { page-break-after: auto; break-after: auto; }
  .card::after { display: none; }
  .sheet__note { display: none; }
}
</style>
</head>
<body>
<div class="sheet">

  <!-- 表 -->
  <section class="card card--front" aria-label="名刺 表">
    <div class="band"></div>
    <div class="inner">
      <div class="wordmark">
        <span class="wordmark__mark">${e(mark)}</span>
        <span class="wordmark__sub">${e(sub)}</span>
      </div>
      <p class="tagline">${taglineHtml()}</p>

      <div class="person">
        <p class="person__role">${e(profile.role)}</p>
        <p class="person__name">${e(profile.name)}<span class="person__name-en">${e(nameEn)}</span></p>
      </div>

      <div class="contact">
        <ul class="contact__lines">
          ${email ? `<li class="en">${e(email)}</li>` : ''}
          ${urlLabel ? `<li class="en">${e(urlLabel)}</li>` : ''}
          ${location ? `<li class="soft">${e(location)}</li>` : ''}
        </ul>
        ${url ? `<div class="qr">${qrSvg()}</div>` : ''}
      </div>
    </div>
  </section>

  <!-- 裏 -->
  <section class="card card--back" aria-label="名刺 裏">
    <div class="inner">
      <div class="back__mark">${e(site.nameEn || site.name)}</div>
      <ul class="proof">
        ${achievements.map((t) => `<li>${e(t)}</li>`).join('\n        ')}
      </ul>
      <ul class="pillars">
        ${pillars.map((p) => `<li><span class="pillars__no">${e(p.no)}</span>${e(p.title)}</li>`).join('\n        ')}
      </ul>
      <div class="back__foot">
        ${mainAccount ? `<span class="handle"><small>${e(mainAccount.platform)}</small>${e(mainAccount.handle)}</span>` : '<span></span>'}
        <span>${e(urlLabel)}</span>
      </div>
    </div>
  </section>

  <p class="sheet__note">
    仕上がり 91×55mm。点線が仕上がり線（画面だけの目安で、印刷には出ません）。外側3mmは塗り足しです。<br>
    内容を変えるときは content/ の JSON を直して <code>npm run card</code> を実行してください。
  </p>
</div>
<script>
  // ?side=front / ?side=back で片面だけ表示（PNG書き出し用）
  const side = new URLSearchParams(location.search).get('side');
  if (side === 'front' || side === 'back') {
    document.body.classList.add('is-flat');
    document.body.dataset.side = side;
  }
</script>
</body>
</html>
`;
}

/* ---------- 書き出し ---------- */

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ].filter(Boolean);
  // Playwright が入れた Chromium も探す
  const pw = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (pw && fs.existsSync(pw)) {
    for (const d of fs.readdirSync(pw)) {
      if (/^chromium-\d+$/.test(d)) candidates.push(path.join(pw, d, 'chrome-linux', 'chrome'));
    }
  }
  return candidates.find((p) => fs.existsSync(p));
}

function run(chrome, args) {
  const base = [
    '--headless=new',
    '--no-sandbox',
    '--disable-gpu',
    '--hide-scrollbars',
    '--virtual-time-budget=10000', // フォントの読み込みを待つ
  ];
  if (process.env.HTTPS_PROXY) base.push(`--proxy-server=${process.env.HTTPS_PROXY}`);
  execFileSync(chrome, [...base, ...args], { stdio: ['ignore', 'ignore', 'pipe'] });
}

function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const htmlPath = path.join(OUT_DIR, `${BASENAME}.html`);
  fs.writeFileSync(htmlPath, html());
  console.log(`✔ ${path.relative(ROOT, htmlPath)}`);

  const chrome = findChrome();
  if (!chrome) {
    console.log('  Chrome / Chromium が見つからないので PDF と PNG は作りませんでした。');
    console.log('  HTML をブラウザで開いて「印刷 → PDFに保存」でも同じものが作れます（用紙サイズは自動で 97×61mm になります）。');
    return;
  }

  const fileUrl = pathToFileURL(htmlPath).href;
  const pdfPath = path.join(OUT_DIR, `${BASENAME}.pdf`);
  run(chrome, ['--no-pdf-header-footer', `--print-to-pdf=${pdfPath}`, fileUrl]);
  console.log(`✔ ${path.relative(ROOT, pdfPath)}`);

  // PNG プレビュー。PDF の各ページをそのまま画像にする（Python の pypdfium2 があれば）
  //   pip install pypdfium2
  const py = `
import sys, pypdfium2 as pdfium
pdf = pdfium.PdfDocument(sys.argv[1])
for i, side in enumerate(['front', 'back']):
    pdf[i].render(scale=350/72).to_pil().save(sys.argv[2] % side)
`;
  try {
    execFileSync('python3', ['-c', py, pdfPath, path.join(OUT_DIR, `${BASENAME}-%s.png`)], { stdio: ['ignore', 'ignore', 'pipe'] });
    console.log(`✔ ${path.relative(ROOT, OUT_DIR)}/${BASENAME}-front.png, -back.png`);
  } catch {
    console.log('  PNG プレビューは飛ばしました（python3 と pypdfium2 があれば作られます）。PDF はできています。');
  }
}

main();
