/*
 * Service Worker — 経路ごとに戦略を分ける
 *
 * 会場の回線は「切れている」より「つながっているが極端に遅い」ことのほうが多い。
 * 素の Network First はこの状態がいちばん苦手で、手元にキャッシュがあっても
 * ネットワークを待ち続けてしまう。そこで対象ごとに戦略を変える:
 *
 *  | 経路        | 対象                                   | 戦略                                    |
 *  | ----------- | -------------------------------------- | --------------------------------------- |
 *  | immutable   | 版が URL に入っている外部資産          | キャッシュ優先・再検証なし              |
 *  | passthrough | その他のクロスオリジン（書影など）     | 素通し（ブラウザの HTTP キャッシュ任せ）|
 *  | eventJson   | events/<id>.json                       | ネットワーク優先・失敗時のみキャッシュ  |
 *  | shell       | 同一オリジンのその他＋ナビゲーション   | ネットワーク＋時間切れでキャッシュ      |
 *
 * キャッシュは 2 本に分ける。版ごとに捨てるシェルと、版をまたいで残すランタイム。
 * 1 本だと CACHE_VERSION を上げるたびに書影とイベント JSON まで捨ててしまい、
 * シェルを更新した直後だけ会場でまた遅くなる。
 *
 * 注意: アプリのロジック更新時は CACHE_VERSION を上げること。
 */

const CACHE_VERSION = "v106";
// シェル（HTML/JS/アセット）。版ごとに作り直す
const SHELL_CACHE = `t-pod-${CACHE_VERSION}`;
// 版に依存しない長寿命キャッシュ。events/<id>.json・書影・フォント実体・Tailwind を入れる。
// index.html も同じ名前で読み書きするので、変えるときは index.html の RUNTIME_CACHE も揃えること。
const RUNTIME_CACHE = "t-pod-runtime-1";

// 16進カラー（#rgb / #rgba / #rrggbb / #rrggbbaa）判定
const HEX_RE = /^#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;

// 版が URL に含まれる＝内容が変わらない外部資産。キャッシュ優先で返してよい。
// Google Fonts は CSS も実体（fonts.gstatic.com）も URL にハッシュを持つ。
const IMMUTABLE_HOSTS = new Set([
  "cdn.tailwindcss.com",
  "fonts.googleapis.com",
  "fonts.gstatic.com",
]);

// シェルを待つ上限。超えたらキャッシュで先に描かせ、ネットワークは裏で走らせ続ける
const NET_TIMEOUT_MS = 2500;

// ランタイムキャッシュの上限。書影だけが青天井に増えるので蓋をする
const RUNTIME_MAX = 120;

// 相対パスでプリキャッシュ（GitHub Pages のサブパス配信に対応）
// イベント別アセット（icon-<id>.svg / venue-map-<id>.svg / events/<id>.json）は
// fetch ハンドラで初回閲覧時にオンデマンドキャッシュされるため列挙しない。
const APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./assets/icon.svg",
  // マスコットの造形定義。これが無いと右下のふせんネコが組めないのでシェル扱いにする
  "./assets/fuseneko/fuseneko-grid.js",
];

// 版固定なのでランタイム側へ入れる（CACHE_VERSION を上げても取り直さない）
const RUNTIME_PRECACHE = ["https://cdn.tailwindcss.com/3.4.17"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    Promise.all([
      // CDN など一部が失敗してもインストールを止めない
      caches.open(SHELL_CACHE).then((cache) =>
        Promise.allSettled(APP_SHELL.map((url) => cache.add(url)))
      ),
      caches.open(RUNTIME_CACHE).then((cache) =>
        Promise.allSettled(
          RUNTIME_PRECACHE.map(async (url) => {
            // すでにあれば取り直さない（版固定 URL なので中身は変わらない）
            if (await cache.match(url)) return;
            return cache.add(url);
          })
        )
      ),
    ]).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            // 旧版シェルを削除（旧接頭辞 sansu-fes- は移行時のゴミ掃除）。
            // ランタイムは版をまたいで残すので消さない。
            .filter(
              (key) =>
                (key.startsWith("t-pod-") || key.startsWith("sansu-fes-")) &&
                key !== SHELL_CACHE &&
                key !== RUNTIME_CACHE
            )
            .map((key) => caches.delete(key))
        )
      )
      .then(() => trimRuntime(true))
      .then(() => self.clients.claim())
  );
});

// ランタイムキャッシュを上限まで削る。Cache API の keys() は挿入順なので
// 先頭（＝古いもの）から捨てれば FIFO になり、追加のメタデータを持たずに済む。
// put のたびに全件舐めると重いので、ふだんは間引いて走らせる。
let putCount = 0;
async function trimRuntime(force) {
  if (!force && ++putCount % 20 !== 0) return;
  try {
    const cache = await caches.open(RUNTIME_CACHE);
    const keys = await cache.keys();
    if (keys.length <= RUNTIME_MAX) return;
    await Promise.all(keys.slice(0, keys.length - RUNTIME_MAX).map((k) => cache.delete(k)));
  } catch (e) {}
}

// 保存してよい応答か（opaque は no-cors のクロスオリジンで status 0 になる）
const isCacheable = (res) => !!res && (res.status === 200 || res.type === "opaque");

// 応答を複製してキャッシュへ書く。呼び出し元は待たない（表示を遅らせないため）
function putLater(request, response, cacheName) {
  if (!isCacheable(response)) return;
  const copy = response.clone();
  caches
    .open(cacheName)
    .then((cache) => cache.put(request, copy))
    .then(() => trimRuntime(false))
    .catch(() => {});
}

function routeOf(request) {
  const url = new URL(request.url);
  if (IMMUTABLE_HOSTS.has(url.hostname)) return "immutable";
  if (url.origin !== self.location.origin) return "passthrough";
  if (/\/events\/[A-Za-z0-9_-]+\.json$/.test(url.pathname)) return "eventJson";
  return "shell";
}

// キャッシュ優先。無いときだけ取りに行く（版固定 URL なので再検証しない）
async function cacheFirst(request, cacheName) {
  const hit = await caches.match(request);
  if (hit) return hit;
  try {
    const res = await fetch(request);
    putLater(request, res, cacheName);
    return res;
  } catch (e) {
    return Response.error();
  }
}

// ネットワーク優先。ただし ms を過ぎたらキャッシュで先に返す。
// **中断はしない**——AbortSignal で切るとバックグラウンドのキャッシュ更新まで
// 殺してしまい、次回も遅いままになる。race で表示だけ先行させ、
// ネットワークは走らせ続けてキャッシュを温める。
function networkWithTimeout(request, cacheName, ms) {
  const net = fetch(request).then((res) => {
    putLater(request, res, cacheName);
    return res;
  });
  // race で捨てられた側の拒否が unhandledrejection にならないようにする
  net.catch(() => {});
  return caches.match(request).then((cached) => {
    if (!cached) return net.catch(() => fallbackShell(request));
    const timer = new Promise((resolve) => setTimeout(() => resolve(cached), ms));
    return Promise.race([net.catch(() => cached), timer]);
  });
}

// events/<id>.json は index.html 側がキャッシュ優先＋再検証を持っている。
// **ここでタイムアウトによるキャッシュ返却をしてはいけない**——すでに表示に使った
// バイト列がそのまま返り、ページ側の差分比較が常に「変化なし」になって
// いつまでも更新されなくなる。鮮度の責任は 1 層だけが持つ。
// ハード失敗のときだけキャッシュへ落とす（このとき表示はもう出ているので実害がない）。
function networkThenCacheOnError(request, cacheName) {
  return fetch(request)
    .then((res) => {
      putLater(request, res, cacheName);
      return res;
    })
    .catch(async () => (await caches.match(request)) || Response.error());
}

// ナビゲーションがネットワークもキャッシュも取れないときの最後の砦
async function fallbackShell(request) {
  if (request.mode === "navigate") {
    const shell = (await caches.match("./index.html")) || (await caches.match("./"));
    if (shell) return shell;
  }
  return Response.error();
}

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // GET 以外（フォーム送信等）はそのまま通す
  if (request.method !== "GET") return;

  // イベントページのナビゲーション（?id あり）は、シェル HTML の theme-color を
  // イベント色に書き換えてから返す。→ iOS Safari 等が「パース時点」で正しい色を採用でき、
  // リロード時にノッチ/ステータスバーが既定色（黄）へ戻る問題を解消する。
  if (request.mode === "navigate") {
    event.respondWith(handleNavigate(request));
    return;
  }

  const kind = routeOf(request);
  // 書影などクロスオリジンの画像は SW を通さない。ブラウザの HTTP キャッシュに任せたほうが
  // 速く、SW のキャッシュを画像で埋めずに済む
  if (kind === "passthrough") return;
  if (kind === "immutable") {
    event.respondWith(cacheFirst(request, RUNTIME_CACHE));
    return;
  }
  if (kind === "eventJson") {
    event.respondWith(networkThenCacheOnError(request, RUNTIME_CACHE));
    return;
  }
  event.respondWith(networkWithTimeout(request, SHELL_CACHE, NET_TIMEOUT_MS));
});

// ?id の値を取り出す（不正値・パストラバーサルは除去）
function getEventId(url) {
  const id = new URL(url).searchParams.get("id") || "";
  return /^[A-Za-z0-9_-]+$/.test(id) ? id : "";
}

// events/<id>.json の eventInfo.brandColor を**キャッシュにある分だけ**見る。
// 取りに行かないのが要点——以前はここで 34KB の JSON を fetch しており、
// 初回ナビゲーションがノッチの色のために 2 本目のリクエスト待ちで止まっていた。
// 未キャッシュのときは素のシェルを返し、色は JS の applyBrandColor() が当てる
// （次回以降は <head> の inline script が localStorage から即時復元する）。
async function getBrandColorCached(id) {
  if (!id) return null;
  try {
    const res = await caches.match(new URL(`events/${id}.json`, self.location.href).href);
    if (!res || !res.ok) return null;
    const data = await res.json();
    const c = String((data && data.eventInfo && data.eventInfo.brandColor) || "").trim();
    return HEX_RE.test(c) ? c : null;
  } catch (e) {
    return null;
  }
}

// ナビゲーション処理: 先にキャッシュから色を引き（Cache API なのでサブ ms）、
// 色があるときだけ HTML を読み直して theme-color を差し替える。
// 色が無ければ 171KB のバッファと書き換えを丸ごと飛ばせる＝ストリーミングが生きる。
async function handleNavigate(request) {
  const color = await getBrandColorCached(getEventId(request.url));
  const response = await networkWithTimeout(request, SHELL_CACHE, NET_TIMEOUT_MS);
  if (!color || !response || !response.ok) return response;
  try {
    const html = await response.clone().text();
    // 静的 <meta name="theme-color" content="..."> の色をイベント色へ書き換え
    const patched = html.replace(
      /(<meta name="theme-color" content=")[^"]*(")/,
      `$1${color}$2`
    );
    if (patched === html) return response; // 対象メタが無ければそのまま
    // 本文長が変わるため content-length を除去（不整合だと本文が途切れる環境がある）
    const headers = new Headers(response.headers);
    headers.delete("content-length");
    return new Response(patched, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  } catch (e) {
    return response;
  }
}
