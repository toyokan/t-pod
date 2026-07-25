/*
 * ふせんネコのバリエーション表。
 *
 * **変えてよいのはここに並んでいるものだけ**（色と表情）。
 * 外周シルエット／耳／折れ角／胴体比率／しっぽ／顔の配置は fuseneko-grid.js が持つ
 * 唯一の定義で、バリエーションでは 1 ドットも変えない。
 *
 * 色は「テーマ色 1 色」だけを指定する。本体・折り返し・輪郭・目鼻口の濃淡は
 * fuseneko.js の fusenekoPalette() がそこから自動で作るので、増やすときは 16 進を 1 つ足すだけでよい。
 */
(function (root) {
  "use strict";

  // 資料 §4 のテーマカラー。用途は目安で、イベント側の brandColor をそのまま渡してもよい
  const FUSENEKO_COLORS = [
    { key: "yellow", label: "黄色（標準）", hex: "#ffd900" },
    { key: "blue", label: "青（算数）", hex: "#3b9ae1" },
    { key: "green", label: "緑（国語）", hex: "#3fb984" },
    { key: "purple", label: "紫（理科）", hex: "#9a7ae0" },
    { key: "pink", label: "ピンク（英語）", hex: "#ef7fa8" },
    { key: "orange", label: "オレンジ（社会）", hex: "#f59e0b" },
    { key: "red", label: "赤（体育）", hex: "#e05a52" },
    { key: "gray", label: "グレー（共通）", hex: "#9aa3ad" },
    { key: "brown", label: "茶（歴史）", hex: "#a9743f" },
    { key: "cyan", label: "水色（ICT）", hex: "#49bcd8" },
  ];

  // 設定資料の 6 表情（＝ SVG 資産にしてあるもの）と、待機アニメだけで使う表情
  const FUSENEKO_EXPRESSION_LIST = [
    { key: "standard", label: "標準", asset: true },
    { key: "smile", label: "にっこり", asset: true },
    { key: "serious", label: "まじめ", asset: true },
    { key: "happy", label: "うれしい", asset: true },
    { key: "idea", label: "ひらめき", asset: true },
    { key: "blink", label: "まばたき" },
    { key: "surprise", label: "びっくり" },
    { key: "yawn", label: "あくび" },
    { key: "lookR", label: "よそ見（右）" },
    { key: "lookL", label: "よそ見（左）" },
    { key: "lookUp", label: "上を見る" },
    { key: "ears", label: "耳ぴく" },
    { key: "sparkleA", label: "わくわく（1）" },
    { key: "sparkleB", label: "わくわく（2）" },
  ];

  // 教科小物（えんぴつ・本・三角定規など）と番号バッジは持たせない。
  // 24px では小物に数ドット、バッジの数字に 3×3 しか取れず、どちらも判別できないため。

  root.FusenekoVariants = {
    COLORS: FUSENEKO_COLORS,
    EXPRESSIONS: FUSENEKO_EXPRESSION_LIST,
    colorByKey: (key) => (FUSENEKO_COLORS.find((c) => c.key === key) || FUSENEKO_COLORS[0]).hex,
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
