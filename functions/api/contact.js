/**
 * /api/contact — お問い合わせフォームの受け口（Cloudflare Pages Functions）
 *
 * フォームから送られた内容を、Resend経由でメールとして届けます。
 * 外部の問い合わせフォームサービスは使いません（無料・自前・月3,000通まで）。
 *
 * 必要な環境変数（Cloudflare Pages の Settings → Variables and Secrets）
 *   RESEND_API_KEY … Resendの管理画面 → API Keys で作成（Secret として登録）
 *   CONTACT_TO     … 受信するメールアドレス（省略時は info@risalink1.com）
 *   CONTACT_FROM   … 送信元（省略時は トナリエ お問い合わせ <info@news.risalink1.com>）
 *                    ※Resendで認証済みのドメインでないと送れません
 */

/** 戻り先として許可するサイト（勝手なURLへ飛ばされないようにするため） */
const ALLOWED_ORIGINS = [
  'https://risalink1.com',
  'https://www.risalink1.com',
  'https://tonarie.pages.dev',
  'https://rinrin127.github.io',
];

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const isEmail = (s) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(s || '').trim());

/** 戻り先URLを検証する。許可したサイト以外は無視する */
function safeNext(raw) {
  if (!raw) return null;
  try {
    const u = new URL(raw);
    if (!ALLOWED_ORIGINS.includes(u.origin)) return null;
    return u.toString();
  } catch { return null; }
}

export async function onRequestPost(context) {
  const { request, env } = context;

  let data;
  const ct = request.headers.get('content-type') || '';
  try {
    if (ct.includes('application/json')) {
      data = await request.json();
    } else {
      const fd = await request.formData();
      data = Object.fromEntries(fd.entries());
    }
  } catch {
    return json({ ok: false, error: '送信内容を読み取れませんでした' }, 400);
  }

  /* 迷惑メール対策：人には見えない欄に入力があったら黙って受け付けたことにする */
  if (String(data._gotcha || '').trim()) {
    return finish(data, request, { ok: true });
  }

  const name = String(data['お名前'] || data.name || '').trim();
  const company = String(data['会社名'] || '').trim();
  const email = String(data.email || '').trim();
  const topic = String(data['ご相談の種類'] || '').trim();
  const body = String(data['ご相談内容'] || data.message || '').trim();

  const errors = [];
  if (!name) errors.push('お名前が空です');
  if (!isEmail(email)) errors.push('メールアドレスの形式が正しくありません');
  if (!body) errors.push('ご相談内容が空です');
  if (name.length > 100 || company.length > 200 || body.length > 8000) errors.push('入力が長すぎます');
  if (errors.length) return json({ ok: false, error: errors.join(' / ') }, 400);

  if (!env.RESEND_API_KEY) {
    console.error('RESEND_API_KEY が未設定です');
    return json({ ok: false, error: '送信の設定が未完了です。お手数ですがメールでご連絡ください。' }, 500);
  }

  const to = env.CONTACT_TO || 'info@risalink1.com';
  const from = env.CONTACT_FROM || 'トナリエ お問い合わせ <info@news.risalink1.com>';

  const rows = [
    ['お名前', name],
    ['会社名・屋号', company || '（未記入）'],
    ['メールアドレス', email],
    ['ご相談の種類', topic || '（未選択）'],
  ];

  const html = `<div style="font-family:sans-serif;line-height:1.9;color:#4A382F">
  <p style="margin:0 0 16px">サイトのお問い合わせフォームから届きました。</p>
  <table style="border-collapse:collapse;font-size:14px">
    ${rows.map(([k, v]) => `<tr>
      <th style="text-align:left;padding:6px 16px 6px 0;color:#7A6558;white-space:nowrap;vertical-align:top">${esc(k)}</th>
      <td style="padding:6px 0">${esc(v)}</td></tr>`).join('')}
  </table>
  <p style="margin:20px 0 6px;color:#7A6558;font-size:13px">ご相談内容</p>
  <div style="white-space:pre-wrap;border-left:3px solid #B4505D;padding:4px 0 4px 14px">${esc(body)}</div>
  <p style="margin-top:24px;font-size:12px;color:#A8968A">このメールにそのまま返信すると、送信者に届きます。</p>
</div>`;

  const text = [
    'サイトのお問い合わせフォームから届きました。',
    '',
    ...rows.map(([k, v]) => `${k}: ${v}`),
    '',
    '【ご相談内容】',
    body,
  ].join('\n');

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from,
      to: [to],
      reply_to: email,          // 返信するとお客様に直接届く
      subject: `【トナリエ】お問い合わせ／${name} 様${topic ? `（${topic}）` : ''}`,
      html,
      text,
    }),
  });

  if (!res.ok) {
    console.error('Resend error', res.status, await res.text().catch(() => ''));
    return json({ ok: false, error: '送信に失敗しました。お手数ですがメールでご連絡ください。' }, 502);
  }

  return finish(data, request, { ok: true });
}

/** フォーム送信なら元のページへ戻し、fetch送信ならJSONを返す */
function finish(data, request, payload) {
  const next = safeNext(data._next);
  const wantsJson = (request.headers.get('accept') || '').includes('application/json');
  if (next && !wantsJson) {
    return new Response(null, { status: 303, headers: { Location: next } });
  }
  return json(payload, 200);
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

/** GETで開かれたときの案内（直接アクセス対策） */
export async function onRequestGet() {
  return json({ ok: false, error: 'このURLはフォームの送信先です。サイトのお問い合わせページからご利用ください。' }, 405);
}
