/*
 * ふせんネコ 24×24 マスターグリッド ── このキャラクターの**唯一の定義**。
 *
 * ここだけを編集する。SVG 資産（assets/fuseneko/fuseneko-*.svg）は
 * scripts/build_fuseneko.py がこのファイルから生成するので手で書き換えない。
 * 右下マスコットの待機アニメ（index.html）も同じ定義を読む。
 *
 * ■ 文字の意味（1 文字 = 1 ドット）
 *   K=輪郭 / B=本体 / S=折り返し（濃色）/ P=ほっぺ / E=目・鼻・口 / W=白 / .=透過
 *   **鼻はほっぺの色ではなく、目・口と同じ E**（設定資料どおり。ピンクにすると猫に見えない）。
 *   パッチでは `_` が「下の絵をそのまま残す」、`.` が「そこを透過にする」。
 *
 * ■ 崩してはいけない造形（全バリエーション共通）
 *   胴体 : col 1–17 / row 5–19 の 17×15。設定画（IMG_6983）に合わせて**ほぼ正方形・わずかに横長**。
 *          下辺は水平、左右は垂直、下の角は四角。幅を奇数にしてあるので中心は col 9 ちょうどで、
 *          顔の左右対称が整数で取れる。
 *   左耳 : col 1–4 / row 2–4。1 ドットずつの小さな階段。大きな三角にしない。
 *   頭頂部: row 5 の col 5–12 が水平な輪郭。
 *   折れ角: 右上は**耳を立てず、ふせんの角を下へ折り返す**。top edge の先から
 *          (14,6)(15,7)(16,8)(17,9) と 1 ドットずつ**階段状に切り落とし**、内側の三角を S で塗り、
 *          row 9 の横線と col 12 の縦線で折り返しを閉じる。大きな三角 1 枚にしない。
 *          ここがトレードマークなので省略しない。
 *   しっぽ: 右辺の下（row 17）から真横へ出て col 20–21 で上へ折れ、row 13 で止まる。
 *          中身 1 ドット幅・全長は胴体の 1/3 程度。U 字にも棒にもしない。
 *   顔   : 胴体の中央よりわずかに下。設定画どおりの組み立てにする。
 *          目は **1 ドット幅 × 3 ドット高の細い縦棒**（col 5 / col 13・row 11–13）。太らせない。
 *          口は **上の段に 3 点（col 7 / 9 / 11）＋下の段に 3 ドットの帯（col 8–10）** の ω。
 *          ほっぺは 2×1 のピンクで、輪郭に接触させない（col 2 / col 16 を空ける）。
 */
(function (root) {
  "use strict";

  const GRID = 24;

  // 塗り分けの CSS クラス名（index.html の <style> と生成 SVG の両方で使う）
  // FILL は「グリッドの 1 文字 → クラス」、FILL_CLASS は「役割名 → クラス」。
  const FILL = { K: "fn-outline", B: "fn-base", S: "fn-fold", P: "fn-cheek", E: "fn-face", W: "fn-white" };
  const FILL_CLASS = {
    outline: "fn-outline",
    base: "fn-base",
    fold: "fn-fold",
    cheek: "fn-cheek",
    face: "fn-face",
    white: "fn-white",
  };

  const FUSENEKO_BASE = [
    "........................",
    "........................",
    "..K.....................",
    ".KBK....................",
    ".KBBK...................",
    ".KBBBKKKKKKKK...........",
    ".KBBBBBBBBBBKSK.........",
    ".KBBBBBBBBBBKSSK........",
    ".KBBBBBBBBBBKSSSK.......",
    ".KBBBBBBBBBBKKKKKK......",
    ".KBBBBBBBBBBBBBBBK......",
    ".KBBBEBBBBBBBEBBBK......",
    ".KBBBEBBBBBBBEBBBK......",
    ".KBBBEBBBBBBBEBBBK...K..",
    ".KBBBBBEBEBEBBBBBK..KBK.",
    ".KBPPBBBEEEBBBPPBK..KBK.",
    ".KBBBBBBBBBBBBBBBKKKBBK.",
    ".KBBBBBBBBBBBBBBBKBBBK..",
    ".KBBBBBBBBBBBBBBBKKKK...",
    ".KKKKKKKKKKKKKKKKK......",
    "........................",
    "........................",
    "........................",
    "........................",
  ];

  // ---- 表情（目・口・ほっぺだけを差し替える。輪郭には触れない） ----
  // 目は col 6–7 / col 12–13 の row 12–14。口は col 7–12 の row 16–17。

  // にっこり：細い目を「^」の弧にする（左は col 4–6、右は col 12–14）
  const FN_SMILE = {
    11: "____BEB_____BEB_________",
    12: "____EBE_____EBE_________",
    13: "____BBB_____BBB_________",
  };
  // まじめ：目を 1 行縮め、口の跳ね（上の 3 点の外側）を落として一文字にする
  const FN_SERIOUS = {
    11: "_____B_______B__________",
    14: "_______B___B____________",
  };
  // まばたき：目を下 1 行だけ残す
  const FN_BLINK = {
    11: "_____B_______B__________",
    12: "_____B_______B__________",
  };
  // びっくり：目を 1 行上まで伸ばして見開き、口を下へ丸く開ける
  const FN_SURPRISE = {
    10: "_____E_______E__________",
    14: "_______B___B____________",
    16: "________EEE_____________",
  };
  // あくび：口を大きく開ける（まばたきと重ねて眠そうにする）
  const FN_YAWN = {
    14: "_______B___B____________",
    16: "_______EEEEE____________",
  };
  // よそ見（しっぽ側＝右）：両目を 1 ドット右へ寄せる
  const FN_LOOK_R = {
    11: "_____BE______BE_________",
    12: "_____BE______BE_________",
    13: "_____BE______BE_________",
  };
  // よそ見（吹き出し側＝左）
  const FN_LOOK_L = {
    11: "____EB______EB__________",
    12: "____EB______EB__________",
    13: "____EB______EB__________",
  };
  // 上を見る：目を 1 行上へずらす（来客を目で追わせる）
  const FN_LOOK_UP = {
    10: "_____E_______E__________",
    13: "_____B_______B__________",
  };
  // 耳ぴく：動くのは**左耳だけ**。右上はふせんの折れ（紙）なので動かさない
  const FN_EARS_DOWN = {
    2: "__._____________________",
    3: "_KKK____________________",
  };
  // わくわく：頭の外に光を出す。2 コマでちらつかせる
  const FN_SPARK_A = {
    0: "___________________S____",
    1: "__________________SSS___",
    2: "___________________S____",
  };
  const FN_SPARK_B = { 1: "___________________S____" };

  // 表情レジストリ。値は「重ねるパッチの配列」
  const FUSENEKO_EXPRESSIONS = {
    standard: [],
    smile: [FN_SMILE],
    serious: [FN_SERIOUS],
    blink: [FN_BLINK],
    surprise: [FN_SURPRISE],
    yawn: [FN_BLINK, FN_YAWN],
    lookR: [FN_LOOK_R],
    lookL: [FN_LOOK_L],
    lookUp: [FN_LOOK_UP],
    ears: [FN_EARS_DOWN],
    sparkleA: [FN_SMILE, FN_SPARK_A],
    sparkleB: [FN_SMILE, FN_SPARK_B],
  };

  // ---- しっぽの振り ----
  // 先端に 1 ドット足す／取るだけ。根元（row 16–18）は動かさない。
  const FUSENEKO_TAIL = {
    up: {
      12: "_____________________K__",
      13: "____________________KBK_",
    },
    down: {
      13: "_____________________.__",
      14: "____________________.K._",
    },
  };

  // ---- 重ねものについて ----
  // 教科小物（えんぴつ・本・三角定規など）と番号バッジは**載せない**。
  // 24px では小物に胴体左下の数ドット、バッジの数字に 3×3 しか取れず、
  // どちらも「何が描いてあるか判別できない色の塊」にしかならないため。
  // 増やすなら、まず表示サイズを上げるかどうかから決める。

  // ---- 合成 ----
  // ベースにパッチを順に重ねて 24 行のドット列を作る（`_` の位置は下の絵を残す）
  function applyPatches(patches) {
    return FUSENEKO_BASE.map((baseRow, y) => {
      let row = baseRow;
      (patches || []).forEach((p) => {
        const r = p && p[y];
        if (!r) return;
        let merged = "";
        for (let x = 0; x < row.length; x++) merged += r[x] === "_" ? row[x] : r[x];
        row = merged;
      });
      return row;
    });
  }

  // 表情名から「重ねるパッチの配列」を組む
  function patchesFor({ expression } = {}) {
    return (FUSENEKO_EXPRESSIONS[expression] || FUSENEKO_EXPRESSIONS.standard).slice();
  }

  // ドット列を <rect> の並びにする。横に連続する同色は 1 つにまとめて要素数を抑える
  function toRects(rows, indent = "") {
    let out = "";
    rows.forEach((row, y) => {
      let x = 0;
      while (x < row.length) {
        const ch = row[x];
        let w = 1;
        while (row[x + w] === ch) w++;
        const cls = FILL[ch];
        if (cls) out += `${indent}<rect class="${cls}" x="${x}" y="${y}" width="${w}" height="1"/>\n`;
        x += w;
      }
    });
    return out;
  }

  root.FusenekoGrid = {
    GRID,
    FILL,
    FILL_CLASS,
    BASE: FUSENEKO_BASE,
    EXPRESSIONS: FUSENEKO_EXPRESSIONS,
    TAIL: FUSENEKO_TAIL,
    applyPatches,
    patchesFor,
    toRects,
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
