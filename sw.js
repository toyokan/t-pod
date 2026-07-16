/*
 * Service Worker — Network First 戦略
 *
 * 方針:
 *  - install 時にアプリシェルをプリキャッシュ（オフライン初回表示用）
 *  - fetch 時は「ネットワーク優先」。取得できればキャッシュを更新して返す。
 *    通信失敗時はキャッシュから返す（会場の不安定な通信や完全オフラインに対応）。
 *  - 各 events/<id>.json も Network First のため、オンライン時は常に最新が表示される。
 *
 * 注意: アプリのロジック更新時は CACHE_VERSION を上げること。
 */

const CACHE_VERSION = "v39";
const CACHE_NAME = `t-pod-${CACHE_VERSION}`;

// 16進カラー（#rgb / #rgba / #rrggbb / #rrggbbaa）判定
const HEX_RE = /^#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;

// 相対パスでプリキャッシュ（GitHub Pages のサブパス配信に対応）
// イベント別アセット（icon-<id>.svg / venue-map-<id>.svg / events/<id>.json）は
// fetch ハンドラの Network First で初回閲覧時にオンデマンドキャッシュされるため列挙しない。
const APP_SHELL = [
  "./",
  "./index.html",
  "./events.json",
  "./manifest.json",
  "./assets/icon.svg",
  "https://cdn.tailwindcss.com/3.4.17",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) =>
        // CDN など一部が失敗してもインストールを止めない
        Promise.allSettled(APP_SHELL.map((url) => cache.add(url)))
      )
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            // 旧版キャッシュを削除（旧接頭辞 sansu-fes- は移行時のゴミ掃除）
            .filter((key) => (key.startsWith("t-pod-") || key.startsWith("sansu-fes-")) && key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

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

  event.respondWith(networkFirst(request));
});

// Network First: 取得成功でキャッシュ更新、失敗時はキャッシュへフォールバック
function networkFirst(request) {
  return fetch(request)
    .then((response) => {
      if (response && response.status === 200) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      }
      return response;
    })
    .catch(async () => {
      const cached = await caches.match(request);
      if (cached) return cached;
      if (request.mode === "navigate") {
        const shell = (await caches.match("./index.html")) || (await caches.match("./"));
        if (shell) return shell;
      }
      return Response.error();
    });
}

// ?id の値を取り出す（不正値・パストラバーサルは除去）
function getEventId(url) {
  const id = new URL(url).searchParams.get("id") || "";
  return /^[A-Za-z0-9_-]+$/.test(id) ? id : "";
}

// events/<id>.json の eventInfo.brandColor を取得（キャッシュ優先→無ければ取得）
async function getBrandColor(id) {
  if (!id) return null;
  const jsonUrl = new URL(`events/${id}.json`, self.location.href).href;
  try {
    let res = await caches.match(jsonUrl);
    if (!res) {
      res = await fetch(jsonUrl);
      if (res && res.status === 200) {
        const copy = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(jsonUrl, copy));
      }
    }
    if (!res || !res.ok) return null;
    const data = await res.json();
    const c = String((data && data.eventInfo && data.eventInfo.brandColor) || "").trim();
    return HEX_RE.test(c) ? c : null;
  } catch (e) {
    return null;
  }
}

// ナビゲーション処理: シェル HTML と brandColor を並行取得し、theme-color を差し替える
async function handleNavigate(request) {
  const id = getEventId(request.url);
  const responsePromise = networkFirst(request);
  const colorPromise = getBrandColor(id); // id 無し（一覧）は null
  const response = await responsePromise;
  if (!response || !response.ok) return response;
  const color = await colorPromise;
  if (!color) return response; // 一覧ページや取得失敗時は素のシェル（既定色）
  try {
    const html = await response.clone().text();
    // 静的 <meta name="theme-color" content="..."> の色をイベント色へ書き換え
    const patched = html.replace(
      /(<meta name="theme-color" content=")[^"]*(")/,
      `$1${color}$2`
    );
    if (patched === html) return response; // 対象メタが無ければそのまま
    return new Response(patched, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  } catch (e) {
    return response;
  }
}
