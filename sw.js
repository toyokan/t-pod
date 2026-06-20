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

const CACHE_VERSION = "v5";
const CACHE_NAME = `sansu-fes-${CACHE_VERSION}`;

// 相対パスでプリキャッシュ（GitHub Pages のサブパス配信に対応）
const APP_SHELL = [
  "./",
  "./index.html",
  "./events.json",
  "./manifest.json",
  "./assets/icon.svg",
  "./assets/favicon.svg",
  "./assets/venue-map.svg",
  "https://cdn.tailwindcss.com",
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
            .filter((key) => key.startsWith("sansu-fes-") && key !== CACHE_NAME)
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

  event.respondWith(
    fetch(request)
      .then((response) => {
        // 正常なレスポンスのみキャッシュを更新（同一オリジン or CDN）
        if (response && response.status === 200) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        }
        return response;
      })
      .catch(async () => {
        // 通信失敗 → キャッシュにフォールバック
        const cached = await caches.match(request);
        if (cached) return cached;
        // ナビゲーション要求はトップページを返す（SPA フォールバック）
        if (request.mode === "navigate") {
          const shell = await caches.match("./index.html");
          if (shell) return shell;
        }
        return Response.error();
      })
  );
});
