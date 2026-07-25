/*
 * ふせんネコのコンポーネント層。
 *
 *   createFuseneko({ size, color, expression, ariaLabel })  → <svg> 要素
 *   fusenekoSvg({ ... })                                   → SVG 文字列
 *   fusenekoPalette(hex)                                   → 5 色 + 白
 *
 * 小物・番号バッジは持たない（24px では判別できないため。fuseneko-grid.js の
 * 「重ねものについて」を参照）。変えられるのは色と表情だけ。
 *
 * 造形は fuseneko-grid.js（唯一の定義）に委ねる。ここは「色を作る」「SVG に組む」だけ。
 * fuseneko-grid.js を先に読み込むこと。
 */
(function (root) {
  "use strict";

  const Grid = root.FusenekoGrid;
  if (!Grid) throw new Error("fuseneko.js は fuseneko-grid.js の後に読み込んでください");

  const HEX_RE = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;
  const DEFAULT_COLOR = "#ffd900";
  const CHEEK = "#f7a8b8";

  function toRgb(hex) {
    let h = String(hex || "").trim();
    if (!HEX_RE.test(h)) h = DEFAULT_COLOR;
    h = h.slice(1);
    if (h.length === 3) h = h.split("").map((c) => c + c).join("");
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }

  const toHex = (rgb) => "#" + rgb.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");

  // テーマ色を白／黒へどれだけ混ぜるか。**この比率が唯一の基準**で、
  //   - index.html の :root --cat-* （color-mix の % は「テーマ色の残り」なので 1-ratio）
  //   - scripts/build_fuseneko.py の MIX（単体 SVG に焼く既定色）
  // が同じ値を持つ。片方だけ変えるとアプリ内と配布アイコンで色がずれる。
  const MIX = {
    base: { to: [255, 255, 255], ratio: 0.48 }, // 本体
    outline: { to: [0, 0, 0], ratio: 0.62 }, //    輪郭（黒そのものは使わず濃い同系色）
    face: { to: [0, 0, 0], ratio: 0.74 }, //       目・鼻・口（輪郭よりさらに一段濃く）
  };
  const mix = (rgb, target, ratio) => rgb.map((v, i) => v * (1 - ratio) + target[i] * ratio);
  const mixed = (rgb, k) => toHex(mix(rgb, MIX[k].to, MIX[k].ratio));

  /** テーマ色 1 色から、塗り分けに使う 5 色（＋白）を作る。 */
  function fusenekoPalette(hex) {
    const rgb = toRgb(hex);
    return {
      base: mixed(rgb, "base"),
      fold: toHex(rgb), // 折り返しはテーマ色そのまま
      outline: mixed(rgb, "outline"),
      face: mixed(rgb, "face"),
      cheek: CHEEK, // ほっぺだけは固定のピンク
      white: "#ffffff",
    };
  }

  const VAR_OF = {
    base: "--cat-base",
    fold: "--cat-fold",
    outline: "--cat-outline",
    face: "--cat-face",
    cheek: "--cat-cheek",
    white: "--cat-white",
  };

  const escapeXml = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /**
   * SVG 文字列を作る。
   * @param {object} [opts]
   * @param {number} [opts.size=24]        表示サイズ（px）。24 の整数倍にするとドットが割れない
   * @param {string} [opts.color]          テーマ色の 16 進。省略時は既定の黄
   * @param {string} [opts.expression]     FusenekoGrid.EXPRESSIONS のキー
   * @param {string} [opts.ariaLabel]      読み上げ用。省略すると装飾扱い（aria-hidden）
   */
  function fusenekoSvg(opts = {}) {
    const { size = 24, color, expression = "standard", ariaLabel } = opts;
    const pal = fusenekoPalette(color);
    const rows = Grid.applyPatches(Grid.patchesFor({ expression }));

    // 色は **この <svg> 要素に載せた CSS 変数**で渡す。
    // インライン SVG の <style> は文書全体に効くので、複数枚を同じページへ並べると
    // 最後の 1 枚のルールが全部を上書きしてしまう。変数はカスタムプロパティの継承で
    // 1 枚ずつ解決されるため、同じページに何色並べても混ざらない。
    const vars = Object.keys(VAR_OF)
      .map((k) => `${VAR_OF[k]}: ${pal[k]}`)
      .join("; ");
    // <style> 側は「変数が無いときの既定（標準の黄）」だけを持たせる。
    // 単体で <img> として読まれたときはホストページの変数が届かないので、この既定が効く。
    const fallback = fusenekoPalette(DEFAULT_COLOR);
    const style = Object.keys(VAR_OF)
      .map((k) => `    .${Grid.FILL_CLASS[k]} { fill: var(${VAR_OF[k]}, ${fallback[k]}); }`)
      .join("\n");

    const a11y = ariaLabel
      ? ` role="img" aria-label="${escapeXml(ariaLabel)}"`
      : ' role="presentation" aria-hidden="true"';
    const title = ariaLabel ? `  <title>${escapeXml(ariaLabel)}</title>\n` : "";

    return (
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${Grid.GRID} ${Grid.GRID}"` +
      ` width="${size}" height="${size}" shape-rendering="crispEdges"` +
      ` style="image-rendering: pixelated; display: block; ${vars}"${a11y}>\n` +
      title +
      "  <style>\n" +
      style +
      "\n  </style>\n" +
      Grid.toRects(rows, "  ") +
      "</svg>\n"
    );
  }

  /** 同じ引数で DOM 要素を返す。属性は SVG 文字列と同じ。 */
  function createFuseneko(opts = {}) {
    const wrap = document.createElement("div");
    wrap.innerHTML = fusenekoSvg(opts);
    return wrap.firstElementChild;
  }

  root.Fuseneko = { fusenekoSvg, createFuseneko, fusenekoPalette, CSS_VARS: VAR_OF };
})(typeof globalThis !== "undefined" ? globalThis : this);
