#!/usr/bin/env node
/**
 * build.mjs — content/ からサイト一式を生成する
 *
 *   npm run build
 *
 * 依存パッケージなし（Node 18+ の標準機能のみ）。
 * HTMLを直接編集しないでください。編集するのは content/ の中です。
 *
 * 生成されるページ
 *   /                トップ
 *   /service/        事業内容
 *   /works/          制作実績
 *   /business/       事業・発信
 *   /profile/        プロフィール
 *   /news/           お知らせ・ブログ一覧
 *   /news/<記事名>/   記事ページ（content/posts/*.md から）
 *   /contact/        お問い合わせ
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { frontmatter, markdown, summarize } from './lib-markdown.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

/** CSSの中身から短いハッシュを作る。
 *  <link> のURLに ?v=ハッシュ を付けることで、CSSを直したとき
 *  訪問者のブラウザが古いCSSを使い続けるのを防ぎます。 */
const assetHash = (rel) => {
  const p = join(ROOT, rel);
  if (!existsSync(p)) return '0';
  return createHash('sha1').update(readFileSync(p)).digest('hex').slice(0, 8);
};

/* ============================================================
   共通ヘルパー
   ============================================================ */

const load = (name) => {
  const p = join(ROOT, 'content', `${name}.json`);
  if (!existsSync(p)) { console.warn(`  ! content/${name}.json がありません`); return null; }
  try { return JSON.parse(readFileSync(p, 'utf8')); }
  catch (err) { throw new Error(`content/${name}.json のJSONが壊れています → ${err.message}`); }
};

const e = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const br = (s) => e(s).replace(/\n/g, '<br>');
const ext = (href) => /^https?:\/\//.test(href || '');
const linkAttrs = (href) => (ext(href) ? ' target="_blank" rel="noopener noreferrer"' : '');
const j = (arr) => arr.filter(Boolean).join('\n');
const fmtDate = (d) => String(d || '').replace(/-/g, '.');

/** ページの深さに応じてサイト内パスを相対パスに直す関数を作る */
const mkU = (depth) => (p) => {
  if (p === '' || p == null) return depth ? '../'.repeat(depth) : './';
  if (/^(https?:|mailto:|tel:|#|data:)/.test(p)) return p;
  return '../'.repeat(depth) + p;
};

/* ============================================================
   記事の読み込み
   ============================================================ */

function loadPosts() {
  const dir = join(ROOT, 'content', 'posts');
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith('.md') && f.toLowerCase() !== 'readme.md')
    .map((f) => {
      const src = readFileSync(join(dir, f), 'utf8');
      const { meta, body } = frontmatter(src);
      const slug = f.replace(/\.md$/, '');
      return {
        slug,
        title: meta.title || slug,
        date: meta.date || '',
        category: meta.category || 'お知らせ',
        excerpt: meta.excerpt || summarize(body),
        image: meta.image || '',
        body,
      };
    })
    .sort((a, b) => String(b.date).localeCompare(String(a.date)));
}

/* ============================================================
   共通パーツ
   ============================================================ */

const NAV = [
  { href: 'service/', label: '事業内容' },
  { href: 'works/', label: '制作実績' },
  { href: 'business/', label: '事業・発信' },
  { href: 'profile/', label: 'プロフィール' },
  { href: 'news/', label: 'お知らせ' },
];

function header(ctx) {
  const { u, site, current } = ctx;
  const links = NAV.map((n) =>
    `<a href="${u(n.href)}"${current === n.href ? ' aria-current="page"' : ''}>${e(n.label)}</a>`);
  return `
<header class="site-header" id="siteHeader">
  <a class="brand${enFirst(site) ? ' brand--en' : ''}" href="${u('')}">${e(mark(site))}${sub(site) ? `<span class="brand__sub">${e(sub(site))}</span>` : ''}</a>

  <nav class="nav" aria-label="メインメニュー">
    <span class="nav__links">${links.join('')}</span>
    <a class="nav__cta" href="${u('contact/')}">ご依頼・ご相談</a>
    <button class="nav__toggle" id="navToggle" type="button" aria-expanded="false" aria-controls="navDrawer" aria-label="メニューを開く">
      <span></span><span></span>
    </button>
  </nav>
</header>

<div class="drawer" id="navDrawer" hidden>
  <nav class="drawer__inner" aria-label="メニュー">
    <a href="${u('')}">トップ</a>
    ${NAV.map((n) => `<a href="${u(n.href)}">${e(n.label)}</a>`).join('\n    ')}
    <a class="drawer__cta" href="${u('contact/')}">ご依頼・ご相談</a>
  </nav>
</div>`;
}

/** ロゴの並び。site.json の wordmark で切り替える（'en-first' なら TONARIE が主） */
const enFirst = (site) => site.wordmark === 'en-first' && Boolean(site.nameEn);
const mark = (site) => (enFirst(site) ? site.nameEn : site.name);
const sub = (site) => (enFirst(site) ? site.name : site.nameEn);

/** タグラインの一部（taglineAccent）だけ色を変える。名刺の「となりに。」に合わせるため */
function taglineHtml(site) {
  const t = e(site.tagline || '');
  const a = e(site.taglineAccent || '');
  if (!a || !t.includes(a)) return t;
  return t.replace(a, `<em class="is-accent">${a}</em>`);
}

/** 名刺裏の実績3行 */
function achievements(site) {
  const items = site.achievements?.items || [];
  if (!items.length) return '';
  return `
    <ul class="proof-list u-fade" data-delay="2">
      ${items.map((t) => `<li>${e(t)}</li>`).join('\n      ')}
    </ul>`;
}

/** 見出し（日本語＋英語の2段） */
const title = (ja, en, { center = false } = {}) => `
      <hgroup class="c-title${center ? ' c-title--center' : ''}">
        <h2 class="c-title__ja u-clip"><span>${e(ja)}</span></h2>
        <p class="c-title__en u-fade" data-delay="1">${e(en)}</p>
      </hgroup>`;

/** 下層ページの見出し帯 */
function pageHero(ctx, ja, en) {
  const { u, site } = ctx;
  const img = site.hero?.slides?.[1]?.image || site.hero?.slides?.[0]?.image;
  return `
<section class="page-hero" data-hero${img ? ` style="background-image:url('${u(img)}')"` : ''}>
  <div class="page-hero__veil"></div>
  <div class="wrap page-hero__inner">
    <h1 class="page-hero__ja u-clip"><span>${e(ja)}</span></h1>
    <p class="page-hero__en u-fade" data-delay="1">${e(en)}</p>
  </div>
</section>`;
}

/** 「詳しく見る →」 */
const more = (u, href, label = '詳しく見る') =>
  `<a class="c-more u-fade" href="${u(href)}">${e(label)}<span aria-hidden="true">→</span></a>`;

function footer(ctx) {
  const { u, site } = ctx;
  const f = site.footer || {};
  const year = String(site.updated || '').slice(0, 4) || '2026';
  return `
<footer class="site-footer">
  <div class="wrap">
    <div class="site-footer__inner">
      <div>
        <div class="site-footer__brand${enFirst(site) ? ' site-footer__brand--en' : ''}">${e(mark(site))}${sub(site) ? `<span class="site-footer__brand-sub">${e(sub(site))}</span>` : ''}</div>
        <div class="site-footer__tagline">${e(site.tagline || '')}</div>
      </div>
      <nav class="site-footer__nav" aria-label="フッターメニュー">
        <a href="${u('')}">トップ</a>
        ${NAV.map((n) => `<a href="${u(n.href)}">${e(n.label)}</a>`).join('\n        ')}
        <a href="${u('contact/')}">お問い合わせ</a>
      </nav>
      <div class="site-footer__meta">
        ${f.owner ? `運営：${e(f.owner)}<br>` : ''}
        ${f.location ? `${e(f.location)}<br>` : ''}
        最終更新：${e(site.updated || '')}
      </div>
    </div>
    <div class="site-footer__bottom">
      ${f.note ? `${e(f.note)}　` : ''}© ${e(year)} ${e(site.name)}
    </div>
  </div>
</footer>`;
}

/** メールアドレス（スパム対策でJSが組み立てる。JSが無くても読める） */
function mailBlock(c, hasForm) {
  const m = c.email;
  if (!m?.user || !m?.domain) return '';
  return `
    <div class="mailto u-fade" data-delay="2">
      <span class="mailto__label">メールでも受け付けています</span>
      <a class="mailto__addr" href="#" data-user="${e(m.user)}" data-domain="${e(m.domain)}"><noscript>${e(m.user)} ＠ ${e(m.domain)}</noscript></a>
      ${hasForm && m.note ? `<span class="mailto__note">${e(m.note)}</span>` : ''}
    </div>`;
}

/** ココナラなど、サブの導線 */
function altBlock(c) {
  const a = c.alt;
  if (!a || a.show === false || !a.href) return '';
  return `
    <div class="alt-route u-fade" data-delay="3">
      <p class="alt-route__title">${e(a.title)}</p>
      ${a.text ? `<p class="alt-route__text">${e(a.text)}</p>` : ''}
      <a class="alt-route__link" href="${e(a.href)}"${linkAttrs(a.href)}>${e(a.label)}<span aria-hidden="true">↗</span></a>
    </div>`;
}

/** 問い合わせフォーム。endpoint が空のときは出さない（壊れたフォームを公開しないため） */
function formBlock(c) {
  const f = c.form || {};
  if (!f.endpoint) return '';
  const action = /^https?:/.test(f.endpoint) ? f.endpoint : `https://formspree.io/f/${f.endpoint}`;
  const topics = f.fields?.topics || [];
  return `
    <form class="form u-fade" data-delay="1" action="${e(action)}" method="POST" id="contactForm">
      <input type="hidden" name="_subject" value="${e(f.subjectPrefix || 'お問い合わせ')}">
      <p class="form__hp"><label>この欄は空のままにしてください<input type="text" name="_gotcha" tabindex="-1" autocomplete="off"></label></p>

      <div class="form__row">
        <label class="form__field">
          <span class="form__label">お名前<i>必須</i></span>
          <input type="text" name="お名前" required autocomplete="name">
        </label>
        <label class="form__field">
          <span class="form__label">会社名・屋号</span>
          <input type="text" name="会社名" autocomplete="organization">
        </label>
      </div>

      <label class="form__field">
        <span class="form__label">メールアドレス<i>必須</i></span>
        <input type="email" name="email" required autocomplete="email" placeholder="example@example.com">
      </label>

      ${topics.length ? `<label class="form__field">
        <span class="form__label">ご相談の種類</span>
        <select name="ご相談の種類">
          ${topics.map((t) => `<option>${e(t)}</option>`).join('\n          ')}
        </select>
      </label>` : ''}

      <label class="form__field">
        <span class="form__label">ご相談内容<i>必須</i></span>
        <textarea name="ご相談内容" rows="7" required placeholder="やりたいこと、お困りごと、ご予算感や希望納期など。決まっていない項目は空欄で構いません。"></textarea>
      </label>

      ${f.privacyNote ? `<p class="form__privacy">${e(f.privacyNote)}</p>` : ''}
      <button class="btn btn--primary form__submit" type="submit">送信する</button>
    </form>

    <div class="form__thanks" id="formThanks" hidden>
      <p class="form__thanks-title">お問い合わせありがとうございます。</p>
      <p class="form__thanks-text">内容を確認のうえ、${e(c.responseTime || '追ってご返信します')}。<br>数日たっても返信が届かない場合は、お手数ですがメールでご連絡ください。</p>
    </div>`;
}

/** どのページの最後にも置く相談導線 */
function contactBand(ctx) {
  const { u, site } = ctx;
  const c = site.contact || {};
  return `
<section class="section section--band">
  <div class="wrap wrap--narrow contact">
    <p class="contact__ja u-clip"><span>お仕事のご依頼・ご相談</span></p>
    ${c.lead ? `<p class="c-lead u-fade" style="text-align:center;margin:20px auto 0">${br(c.lead)}</p>` : ''}
    <div class="contact__actions u-fade" data-delay="1">
      <a class="btn btn--primary" href="${u('contact/')}">お問い合わせフォームへ</a>
    </div>
    ${c.responseTime ? `<p class="contact__note u-fade" data-delay="2">${e(c.responseTime)}</p>` : ''}
  </div>
</section>`;
}

/* ============================================================
   セクション（トップの抜粋と個別ページで共用）
   ============================================================ */

function statsBlock(site) {
  if (!site.stats?.length) return '';
  return `
    <div class="stats u-fade">
      ${site.stats.map((s) => `<div class="stat">
        <div class="stat__value">${e(s.value)}${s.unit ? `<small>${e(s.unit)}</small>` : ''}</div>
        <div class="stat__label">${e(s.label)}</div>
      </div>`).join('\n      ')}
    </div>`;
}

function pillarCards(ctx, pillars) {
  const { u } = ctx;
  return `<div class="pillar-cards">
      ${pillars.map((p) => `<a class="pillar-card u-fade" href="${u('service/')}#service-${e(p.no)}">
        <span class="pillar-card__no">${e(p.no)}</span>
        <span class="pillar-card__title">${e(p.title)}</span>
        <span class="pillar-card__sub">${e(p.subtitle || '')}</span>
      </a>`).join('\n      ')}
    </div>`;
}

function pillarsFull(ctx, pillars) {
  return pillars.map((p) => `
      <article class="pillar" id="service-${e(p.no)}">
        <div class="pillar__grid">
          <div class="u-fade">
            <div class="pillar__no">${e(p.no)}</div>
            <h3 class="pillar__title">${e(p.title)}</h3>
            ${p.subtitle ? `<p class="pillar__subtitle">${e(p.subtitle)}</p>` : ''}
            <p class="pillar__body">${br(p.body)}</p>
          </div>
          <div class="u-fade" data-delay="1">
            <ul class="pillar__items">
              ${(p.items || []).map((it) => `<li class="pillar__item">
                <div class="pillar__item-name">${e(it.name)}</div>
                ${it.note ? `<div class="pillar__item-note">${e(it.note)}</div>` : ''}
              </li>`).join('\n              ')}
            </ul>
            <div class="pillar__foot">
              ${p.price ? `<span class="pillar__price">${e(p.price)}</span>` : '<span></span>'}
              ${p.sample?.href ? `<a class="pillar__link" href="${e(p.sample.href)}"${linkAttrs(p.sample.href)}>${e(p.sample.label)} ↗</a>` : ''}
            </div>
          </div>
        </div>
      </article>`).join('');
}

function workCards(ctx, items) {
  const { u } = ctx;
  return `<div class="works">
      ${items.map((it, i) => {
    const thumb = it.image
      ? `<div class="work__thumb"><img src="${u(it.image)}" alt="${e(it.title)}" loading="lazy"></div>`
      : `<div class="work__thumb work__thumb--empty">${e(it.category || 'Work')}</div>`;
    const inner = `${thumb}
        ${it.category ? `<div class="work__cat">${e(it.category)}</div>` : ''}
        <h3 class="work__title">${e(it.title)}</h3>
        ${it.note ? `<p class="work__note">${e(it.note)}</p>` : ''}`;
    const cls = `work u-fade" data-delay="${i % 3}`;
    return it.href
      ? `<a class="${cls}" href="${e(it.href)}"${linkAttrs(it.href)}>${inner}</a>`
      : `<div class="${cls}">${inner}</div>`;
  }).join('\n      ')}
    </div>`;
}

function bizList(items) {
  return `<div>
      ${items.map((it, i) => `<div class="biz__item u-fade">
        <div class="biz__no">${String(i + 1).padStart(2, '0')}</div>
        <div>
          ${it.stage ? `<p class="biz__stage">${e(it.stage)}</p>` : ''}
          <h3 class="biz__title">${e(it.title)}</h3>
          <p class="biz__body">${br(it.body)}</p>
          ${it.numbers?.length ? `<div class="biz__numbers">${it.numbers.map((n) => `<div class="biz__num"><strong>${e(n.value)}</strong><span>${e(n.label)}</span></div>`).join('')}</div>` : ''}
        </div>
        ${it.status ? `<span class="status">${e(it.status)}</span>` : ''}
      </div>`).join('\n      ')}
    </div>`;
}

function acctList(accounts) {
  const accts = (accounts?.items || []).filter((x) => x.public !== false);
  if (!accts.length) return '';
  return `
    <div style="margin-top:clamp(56px,7vw,96px)">
      <p class="c-title__en u-fade" style="margin-bottom:8px">Accounts</p>
      ${accounts.lead ? `<p class="u-fade" style="font-size:.875rem;opacity:.72;max-width:44em;margin-bottom:28px">${br(accounts.lead)}</p>` : ''}
      <div class="accts">
        ${accts.map((a) => `<a class="acct u-fade" href="${e(a.href)}"${linkAttrs(a.href)}>
          <span>
            <span class="acct__genre">${e(a.genre)}</span>
            <span class="acct__name">${e(a.name)}</span>
            <span class="acct__handle">${e(a.platform)}　${e(a.handle)}</span>
          </span>
          <span class="acct__arrow">↗</span>
        </a>`).join('\n        ')}
      </div>
    </div>`;
}

function postList(ctx, posts) {
  const { u } = ctx;
  if (!posts.length) return '<p class="u-fade" style="color:var(--ink-faint)">まだ記事がありません。</p>';
  return `<div class="post-list">
      ${posts.map((p) => `<a class="post-card u-fade" href="${u(`news/${p.slug}/`)}">
        ${p.image ? `<div class="post-card__thumb"><img src="${u(p.image)}" alt="${e(p.title)}" loading="lazy"></div>` : ''}
        <div class="post-card__body">
          <div class="post-card__meta"><time datetime="${e(p.date)}">${e(fmtDate(p.date))}</time><span>${e(p.category)}</span></div>
          <h3 class="post-card__title">${e(p.title)}</h3>
          ${p.excerpt ? `<p class="post-card__excerpt">${e(p.excerpt)}</p>` : ''}
        </div>
      </a>`).join('\n      ')}
    </div>`;
}

function profileBlocks(ctx, p) {
  const skills = (p.skills || []).map((s) =>
    `<li><div class="skill__label">${e(s.label)}</div>${s.note ? `<div class="skill__note">${e(s.note)}</div>` : ''}</li>`).join('\n          ');
  const career = (p.career || []).map((c) =>
    `<li class="career__item"><div class="career__year">${e(c.year)}</div><div class="career__title">${e(c.title)}</div>${c.note ? `<div class="career__note">${e(c.note)}</div>` : ''}</li>`).join('\n          ');
  return `
    <div class="profile__meta">
      ${skills ? `<div class="u-fade"><div class="block-title">Skill</div><ul class="skill-list">\n          ${skills}\n        </ul></div>` : ''}
      ${career ? `<div class="u-fade" data-delay="1"><div class="block-title">Career</div><ul>\n          ${career}\n        </ul></div>` : ''}
    </div>`;
}

function profileIntro(ctx, p) {
  const { u } = ctx;
  const policy = (p.policy || []).map((t) => `<li>${e(t)}</li>`).join('\n          ');
  return `
    <div class="profile__grid">
      <div class="u-fade">
        ${p.photo ? `<div class="profile__photo"><img src="${u(p.photo)}" alt="${e(p.name || '')}" loading="lazy"></div>` : ''}
        ${p.name ? `<div class="profile__name">${e(p.name)}</div>` : ''}
        ${p.role ? `<div class="profile__role">${e(p.role)}</div>` : ''}
      </div>
      <div class="profile__intro u-fade" data-delay="1">
        ${(p.intro || []).map((t) => `<p>${br(t)}</p>`).join('\n        ')}
        ${policy ? `<ul class="policy">\n          ${policy}\n        </ul>` : ''}
        ${p.proof?.href ? `<p class="proof">
          <span class="proof__text">${e(p.proof.text)}</span>
          <a class="proof__link" href="${e(p.proof.href)}"${linkAttrs(p.proof.href)}>${e(p.proof.label)}<span aria-hidden="true">↗</span></a>
        </p>` : ''}
      </div>
    </div>`;
}

function voiceBlock(t) {
  if (!t?.items?.length) return '';
  return `
    <div class="voices">
      ${t.items.map((v, i) => `<figure class="voice u-fade" data-delay="${i % 3}" style="margin:0">
        <div class="voice__stars">★★★★★</div>
        <blockquote class="voice__body" style="margin:0">${br(v.body)}</blockquote>
        <figcaption class="voice__author">${e(v.author)}${v.service ? `　／　${e(v.service)}` : ''}</figcaption>
      </figure>`).join('\n      ')}
    </div>`;
}

/* ============================================================
   ページ
   ============================================================ */

function pageTop(ctx) {
  const { u, site, data, posts } = ctx;
  const h = site.hero || {};
  const c = site.concept || {};
  const slides = (h.slides || []).map((s, i) => `
      <div class="mv__slide${i === 0 ? ' is-active' : ''}">
        <img src="${u(s.image)}" alt="${e(s.alt || '')}" ${i === 0 ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">
      </div>`).join('');

  const worksTop = [...(data.works?.manual || []), ...(data.works?.items || [])].slice(0, 3);
  const bizTop = (data.business?.items || []).filter((x) => x.show !== false).slice(0, 3);

  return j([
    `
<section class="mv" id="top" data-hero>
  <div class="mv__slides" id="mvSlides">${slides}
  </div>
  <div class="mv__veil"></div>
  <div class="mv__logo">
    <span class="mv__logo-mark${enFirst(site) ? ' mv__logo-mark--en' : ''}">${e(mark(site))}</span>
    ${sub(site) ? `<span class="mv__logo-en${enFirst(site) ? ' mv__logo-en--ja' : ''}">${e(sub(site))}</span>` : ''}
    <span class="mv__logo-sub">${taglineHtml(site)}</span>
  </div>
  <div class="mv__scroll">${e(h.scrollLabel || 'scroll')}</div>
</section>`,

    c.catch ? `
<section class="concept">
  <div class="wrap wrap--narrow">
    <p class="concept__catch u-clip"><span>${br(c.catch)}</span></p>
    <p class="concept__text u-fade" data-delay="1">${(c.text || []).map(e).join('<br>')}</p>
    ${achievements(site)}
  </div>
</section>` : '',

    site.stats?.length ? `<section class="wrap">${statsBlock(site)}</section>` : '',

    data.services?.pillars?.length ? `
<section class="section section--white">
  <div class="wrap">
    ${title('事業内容', 'Service', { center: true })}
    ${data.services.lead ? `<p class="c-lead u-fade">${br(data.services.lead)}</p>` : ''}
    ${pillarCards(ctx, data.services.pillars)}
    <div class="c-more-wrap">${more(u, 'service/', 'サービスの詳細を見る')}</div>
  </div>
</section>` : '',

    worksTop.length ? `
<section class="section">
  <div class="wrap">
    ${title('制作実績', 'Works', { center: true })}
    ${workCards(ctx, worksTop)}
    <div class="c-more-wrap">${more(u, 'works/', '実績をすべて見る')}</div>
  </div>
</section>` : '',

    bizTop.length ? `
<section class="section section--dark">
  <div class="wrap">
    ${title('いま取り組んでいること', 'Business', { center: true })}
    ${data.business?.lead ? `<p class="c-lead u-fade" style="color:inherit;opacity:.72;text-align:center;margin-inline:auto">${br(data.business.lead)}</p>` : ''}
    ${bizList(bizTop)}
    <div class="c-more-wrap">${more(u, 'business/', '事業と発信をすべて見る')}</div>
  </div>
</section>` : '',

    data.profile ? `
<section class="section section--white">
  <div class="wrap">
    ${title('わたしについて', 'Profile', { center: true })}
    ${profileIntro(ctx, data.profile)}
    <div class="c-more-wrap">${more(u, 'profile/', '経歴・スキルを見る')}</div>
  </div>
</section>` : '',

    posts.length ? `
<section class="section">
  <div class="wrap">
    ${title('お知らせ', 'News', { center: true })}
    ${postList(ctx, posts.slice(0, 3))}
    <div class="c-more-wrap">${more(u, 'news/', 'お知らせをすべて見る')}</div>
  </div>
</section>` : '',

    contactBand(ctx),
  ]);
}

function pageService(ctx) {
  const { data } = ctx;
  return j([
    pageHero(ctx, '事業内容', 'Service'),
    `
<section class="section">
  <div class="wrap">
    ${data.services?.lead ? `<p class="c-lead c-lead--top u-fade">${br(data.services.lead)}</p>` : ''}
    ${pillarsFull(ctx, data.services?.pillars || [])}
  </div>
</section>`,
    contactBand(ctx),
  ]);
}

function pageWorks(ctx) {
  const { data } = ctx;
  const all = [...(data.works?.manual || []), ...(data.works?.items || [])];
  return j([
    pageHero(ctx, '制作実績', 'Works'),
    `
<section class="section">
  <div class="wrap">
    ${data.works?.lead ? `<p class="c-lead c-lead--top u-fade">${br(data.works.lead)}</p>` : ''}
    ${all.length ? workCards(ctx, all) : '<p class="u-fade" style="color:var(--ink-faint)">準備中です。</p>'}
  </div>
</section>`,
    contactBand(ctx),
  ]);
}

function pageBusiness(ctx) {
  const { data } = ctx;
  const items = (data.business?.items || []).filter((x) => x.show !== false);
  return j([
    pageHero(ctx, 'いま取り組んでいること', 'Business'),
    `
<section class="section section--dark">
  <div class="wrap">
    ${data.business?.lead ? `<p class="c-lead c-lead--top u-fade" style="color:inherit;opacity:.72">${br(data.business.lead)}</p>` : ''}
    ${bizList(items)}
    ${acctList(data.accounts)}
  </div>
</section>`,
    contactBand(ctx),
  ]);
}

function pageProfile(ctx) {
  const { data } = ctx;
  return j([
    pageHero(ctx, 'わたしについて', 'Profile'),
    `
<section class="section">
  <div class="wrap">
    ${profileIntro(ctx, data.profile || {})}
    ${profileBlocks(ctx, data.profile || {})}
  </div>
</section>`,
    data.testimonials?.items?.length ? `
<section class="section section--white">
  <div class="wrap">
    ${title('お客様の声', 'Voice', { center: true })}
    ${voiceBlock(data.testimonials)}
  </div>
</section>` : '',
    contactBand(ctx),
  ]);
}

function pageNews(ctx) {
  const { posts } = ctx;
  return j([
    pageHero(ctx, 'お知らせ', 'News'),
    `
<section class="section">
  <div class="wrap">
    ${postList(ctx, posts)}
  </div>
</section>`,
    contactBand(ctx),
  ]);
}

function pagePost(ctx, post) {
  const { u, posts } = ctx;
  const others = posts.filter((p) => p.slug !== post.slug).slice(0, 2);
  return j([
    `
<section class="post-hero" data-hero>
  <div class="wrap wrap--narrow">
    <div class="post-hero__meta u-fade"><time datetime="${e(post.date)}">${e(fmtDate(post.date))}</time><span>${e(post.category)}</span></div>
    <h1 class="post-hero__title u-fade" data-delay="1">${e(post.title)}</h1>
  </div>
</section>`,
    post.image ? `<div class="wrap wrap--narrow post__cover u-fade"><img src="${u(post.image)}" alt="${e(post.title)}"></div>` : '',
    `
<article class="section" style="padding-top:clamp(40px,5vw,64px)">
  <div class="wrap wrap--narrow post u-fade">
    ${markdown(post.body, u)}
  </div>
  <div class="wrap wrap--narrow" style="margin-top:clamp(48px,6vw,72px)">
    <a class="c-more" href="${u('news/')}"><span aria-hidden="true">←</span>お知らせ一覧へ</a>
  </div>
</article>`,
    others.length ? `
<section class="section section--white">
  <div class="wrap wrap--narrow">
    <p class="c-title__en u-fade" style="margin-bottom:24px">Other posts</p>
    ${postList(ctx, others)}
  </div>
</section>` : '',
    contactBand(ctx),
  ]);
}

function pageContact(ctx) {
  const { site } = ctx;
  const c = site.contact || {};
  const hasForm = Boolean(c.form?.endpoint);
  return j([
    pageHero(ctx, 'お問い合わせ', 'Contact'),
    `
<section class="section">
  <div class="wrap wrap--narrow">
    ${c.lead ? `<p class="c-lead c-lead--top u-fade" style="text-align:center;margin-inline:auto">${br(c.lead)}</p>` : ''}
    ${formBlock(c)}
    ${!hasForm ? `<p class="u-fade" style="text-align:center;color:var(--ink-soft);font-size:.9375rem">下記のメールアドレスまでお気軽にご連絡ください。</p>` : ''}
    ${mailBlock(c, hasForm)}
    ${altBlock(c)}
  </div>
</section>`,
  ]);
}

/* ============================================================
   HTMLの外枠
   ============================================================ */

function shell(ctx, body) {
  const { u, site, meta } = ctx;
  const abs = (p) => (p ? new URL(p, site.url).href : '');
  const ld = {
    '@context': 'https://schema.org',
    '@type': 'ProfessionalService',
    name: site.name,
    description: site.description,
    url: site.url,
    areaServed: 'JP',
    knowsAbout: (ctx.data.profile?.skills || []).map((s) => s.label),
  };

  return `<!doctype html>
<html lang="${e(site.lang || 'ja')}">
<head>
<meta charset="utf-8">
<script>document.documentElement.classList.add('js');</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${e(meta.title)}</title>
<meta name="description" content="${e(meta.description)}">
<link rel="canonical" href="${e(abs(meta.path))}">
<meta property="og:type" content="${meta.type || 'website'}">
<meta property="og:title" content="${e(meta.title)}">
<meta property="og:description" content="${e(meta.description)}">
<meta property="og:url" content="${e(abs(meta.path))}">
<meta property="og:image" content="${e(abs(meta.image || site.ogImage))}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Old+Mincho:wght@500;600&family=Zen+Kaku+Gothic+New:wght@400;500&family=Crimson+Pro:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="${u('assets/tokens.css')}?v=${assetHash('assets/tokens.css')}">
<link rel="stylesheet" href="${u('assets/style.css')}?v=${assetHash('assets/style.css')}">
<script type="application/ld+json">${JSON.stringify(ld)}</script>
</head>
<body>
<!--
  ⚠️ このファイルは自動生成です。直接編集しても次の「npm run build」で消えます。
  編集するのは content/ の中です。
-->
${header(ctx)}
<main>
${body}
</main>
${footer(ctx)}

<script>
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- ファーストビューのスライドショー（6秒ごとにフェード） --- */
  var slides = document.querySelectorAll('#mvSlides .mv__slide');
  if (slides.length > 1 && !reduce) {
    var i = 0;
    setInterval(function () {
      slides[i].classList.remove('is-active');
      i = (i + 1) % slides.length;
      slides[i].classList.add('is-active');
    }, 6000);
  }

  /* --- スクロールで現れる（見出しのせり上がり・フェード） --- */
  var targets = document.querySelectorAll('.u-clip, .u-fade');
  if (reduce) {
    targets.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });
    targets.forEach(function (el) { io.observe(el); });

    /* 保険：2秒たっても画面内の要素が出ていなければ強制的に表示する */
    setTimeout(function () {
      targets.forEach(function (el) {
        if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add('is-in');
      });
    }, 2000);
  }

  /* --- ヘッダー：見出し帯を抜けたら背景を出す --- */
  var header = document.getElementById('siteHeader');
  var hero = document.querySelector('[data-hero]');
  function onScroll() {
    var limit = hero ? hero.offsetHeight - 80 : 60;
    header.classList.toggle('is-solid', window.scrollY > limit);
  }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* --- スマホのメニュー --- */
  var toggle = document.getElementById('navToggle');
  var drawer = document.getElementById('navDrawer');
  if (toggle && drawer) {
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      toggle.setAttribute('aria-label', open ? 'メニューを開く' : 'メニューを閉じる');
      drawer.hidden = open;
      document.body.style.overflow = open ? '' : 'hidden';
      document.documentElement.classList.toggle('is-menu-open', !open);
    });
    drawer.addEventListener('click', function (ev) {
      if (ev.target.tagName === 'A') toggle.click();
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') toggle.click();
    });
  }

  /* --- メールアドレスを組み立てる（HTMLに直接書かないことでスパムを減らす） --- */
  document.querySelectorAll('.mailto__addr').forEach(function (a) {
    var addr = a.dataset.user + String.fromCharCode(64) + a.dataset.domain;
    a.textContent = addr;
    a.href = 'mailto:' + addr;
  });

  /* --- 送信が終わったら「ありがとうございます」を出す --- */
  var thanks = document.getElementById('formThanks');
  var form = document.getElementById('contactForm');
  if (thanks && new URLSearchParams(location.search).get('sent') === '1') {
    thanks.hidden = false;
    if (form) form.hidden = true;
    thanks.scrollIntoView({ block: 'center' });
  }
  if (form) {
    var next = form.querySelector('input[name="_next"]') || document.createElement('input');
    next.type = 'hidden'; next.name = '_next';
    next.value = location.origin + location.pathname + '?sent=1';
    form.appendChild(next);
  }

  /* --- 同じページ内のリンクをなめらかに --- */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (ev) {
      var el = document.querySelector(a.getAttribute('href'));
      if (!el) return;
      ev.preventDefault();
      window.scrollTo({ top: el.offsetTop - 70, behavior: reduce ? 'auto' : 'smooth' });
    });
  });
})();
</script>
</body>
</html>
`;
}

/* ============================================================
   実行
   ============================================================ */

const data = {
  site: load('site'),
  profile: load('profile'),
  services: load('services'),
  works: load('works'),
  business: load('business'),
  accounts: load('accounts'),
  testimonials: load('testimonials'),
};
if (!data.site) { console.error('✗ content/site.json は必須です。'); process.exit(1); }

const site = data.site;
const posts = loadPosts();

for (const s of site.hero?.slides || []) {
  if (s.image && !existsSync(join(ROOT, s.image))) {
    console.warn(`  ! ${s.image} が見つかりません`);
  }
}

const pages = [
  { slug: '', render: pageTop, title: `${site.name} | ${site.tagline}`, description: site.description },
  { slug: 'service', render: pageService, title: `事業内容 | ${site.name}`, description: data.services?.lead || site.description },
  { slug: 'works', render: pageWorks, title: `制作実績 | ${site.name}`, description: data.works?.lead || site.description },
  { slug: 'business', render: pageBusiness, title: `いま取り組んでいること | ${site.name}`, description: data.business?.lead || site.description },
  { slug: 'profile', render: pageProfile, title: `わたしについて | ${site.name}`, description: (data.profile?.intro || [])[0] || site.description },
  { slug: 'news', render: pageNews, title: `お知らせ | ${site.name}`, description: `${site.name}からのお知らせと、制作の裏側の記録です。` },
  { slug: 'contact', render: pageContact, title: `お問い合わせ | ${site.name}`, description: site.contact?.lead || site.description },
  ...posts.map((p) => ({
    slug: `news/${p.slug}`,
    render: (ctx) => pagePost(ctx, p),
    title: `${p.title} | ${site.name}`,
    description: p.excerpt,
    image: p.image,
    type: 'article',
  })),
];

const written = [];
for (const page of pages) {
  const depth = page.slug === '' ? 0 : page.slug.split('/').length;
  const u = mkU(depth);
  const path = page.slug === '' ? '' : `${page.slug}/`;
  const current = NAV.find((n) => n.href === path || (page.slug.startsWith('news/') && n.href === 'news/'))?.href;
  const ctx = {
    u, site, data, posts, current,
    meta: { title: page.title, description: page.description, path, image: page.image, type: page.type },
  };
  const html = shell(ctx, page.render(ctx));
  const out = join(ROOT, page.slug === '' ? 'index.html' : join(page.slug, 'index.html'));
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, html, 'utf8');
  written.push({ path, bytes: html.length });
}

/* sitemap.xml と robots.txt（検索に拾ってもらうため） */
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${written.map((w) => `  <url><loc>${new URL(w.path, site.url).href}</loc><lastmod>${site.updated}</lastmod></url>`).join('\n')}
</urlset>
`;
writeFileSync(join(ROOT, 'sitemap.xml'), sitemap, 'utf8');
writeFileSync(join(ROOT, 'robots.txt'), `User-agent: *\nAllow: /\nSitemap: ${new URL('sitemap.xml', site.url).href}\n`, 'utf8');

console.log(`✓ ${written.length}ページを生成しました`);
for (const w of written) console.log(`    /${w.path.padEnd(30)} ${(w.bytes / 1024).toFixed(1)} KB`);
console.log(`  記事 ${posts.length}本 / 柱 ${data.services?.pillars?.length ?? 0}本 / 実績 ${(data.works?.manual?.length ?? 0) + (data.works?.items?.length ?? 0)}件`);
if ((site.hero?.slides || []).some((s) => /\/fv-\d\.svg$/.test(s.image || ''))) {
  console.log('  ※ ファーストビューはまだ仮画像です（READMEの「ファーストビューの写真」参照）');
}
