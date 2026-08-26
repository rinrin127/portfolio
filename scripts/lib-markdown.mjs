/**
 * lib-markdown.mjs — 記事用の小さなMarkdown変換
 * 依存パッケージなし。見出し・段落・箇条書き・引用・表・コード・リンク・画像に対応。
 */

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/** 先頭の --- ブロックを設定として取り出す */
export function frontmatter(src) {
  const text = src.replace(/^﻿/, '').replace(/\r\n/g, '\n');
  const m = text.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!m) return { meta: {}, body: text };
  const meta = {};
  for (const line of m[1].split('\n')) {
    const i = line.indexOf(':');
    if (i < 0) continue;
    meta[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  }
  return { meta, body: text.slice(m[0].length) };
}

/** Markdown → HTML。u は サイト内パスを各ページからの相対パスに直す関数 */
export function markdown(src, u = (x) => x) {
  const inline = (s) => esc(s)
    .replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (_m, alt, href) =>
      `<img src="${u(href)}" alt="${alt}" loading="lazy">`)
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_m, text, href) =>
      `<a href="${/^(https?:|mailto:|#|\/)/.test(href) ? href : u(href)}"${/^https?:/.test(href) ? ' target="_blank" rel="noopener noreferrer"' : ''}>${text}</a>`)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');

  const lines = src.replace(/\r\n/g, '\n').split('\n');
  const out = [];
  let para = [];
  let list = null;      // 'ul' | 'ol'
  let listItems = [];
  let quote = [];
  let code = null;      // { lang, lines }
  let table = null;     // { head: [], rows: [][] }

  const flushPara = () => { if (para.length) { out.push(`<p>${inline(para.join('\n')).replace(/\n/g, '<br>')}</p>`); para = []; } };
  const flushList = () => { if (list) { out.push(`<${list}>${listItems.map((t) => `<li>${inline(t)}</li>`).join('')}</${list}>`); list = null; listItems = []; } };
  const flushQuote = () => { if (quote.length) { out.push(`<blockquote><p>${inline(quote.join('\n')).replace(/\n/g, '<br>')}</p></blockquote>`); quote = []; } };
  const flushTable = () => {
    if (!table) return;
    const head = table.head.length ? `<thead><tr>${table.head.map((c) => `<th>${inline(c)}</th>`).join('')}</tr></thead>` : '';
    const body = table.rows.map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join('')}</tr>`).join('');
    out.push(`<div class="post__table-wrap"><table>${head}<tbody>${body}</tbody></table></div>`);
    table = null;
  };
  const flushAll = () => { flushPara(); flushList(); flushQuote(); flushTable(); };

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, '');

    if (code) {
      if (/^```/.test(line)) { out.push(`<pre><code>${esc(code.lines.join('\n'))}</code></pre>`); code = null; }
      else code.lines.push(raw);
      continue;
    }
    if (/^```/.test(line)) { flushAll(); code = { lines: [] }; continue; }

    if (!line.trim()) { flushAll(); continue; }

    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) { flushAll(); const lv = Math.min(h[1].length + 1, 6); out.push(`<h${lv}>${inline(h[2])}</h${lv}>`); continue; }

    if (/^(\*\*\*|---|___)\s*$/.test(line)) { flushAll(); out.push('<hr>'); continue; }

    const q = line.match(/^>\s?(.*)$/);
    if (q) { flushPara(); flushList(); flushTable(); quote.push(q[1]); continue; }
    flushQuote();

    const ul = line.match(/^\s*[-*+]\s+(.*)$/);
    const ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (ul || ol) {
      flushPara(); flushTable();
      const type = ul ? 'ul' : 'ol';
      if (list && list !== type) flushList();
      list = type;
      listItems.push((ul || ol)[1]);
      continue;
    }
    flushList();

    if (/^\|.*\|$/.test(line)) {
      flushPara();
      const cells = line.slice(1, -1).split('|').map((c) => c.trim());
      if (/^[\s|:-]+$/.test(line)) continue;               // 区切り行は捨てる
      if (!table) table = { head: cells, rows: [] };
      else table.rows.push(cells);
      continue;
    }
    flushTable();

    para.push(line);
  }
  flushAll();
  if (code) out.push(`<pre><code>${esc(code.lines.join('\n'))}</code></pre>`);

  return out.join('\n');
}

/** 本文から要約を作る（excerpt が無いとき用） */
export function summarize(body, len = 90) {
  const plain = body
    .replace(/^---[\s\S]*?---\n?/, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[#>*`|-]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  return plain.length > len ? `${plain.slice(0, len)}…` : plain;
}
