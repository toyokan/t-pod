import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const outputDir = path.resolve(".");
const workbookPath = path.join(
  outputDir,
  "2026-09-12_算数授業研究公開講座_in大阪_イベント情報.xlsx",
);
const sourceEventPath = path.resolve("../../events/2026-math-summer-fes.json");
const workbook = await SpreadsheetFile.importXlsx(
  await FileBlob.load(workbookPath),
);
const sourceEvent = JSON.parse(await fs.readFile(sourceEventPath, "utf8"));

const books = sourceEvent.books.map((book) => [
  book.title ?? null,
  book.author ?? null,
  book.publisher ?? null,
  book.cover ?? null,
  book.description ?? null,
  book.url ?? null,
  book.amazon_url ?? null,
]);
const booksSheet = workbook.worksheets.getItem("関連書籍");
booksSheet.getRange(`A4:G${books.length + 3}`).values = books;
booksSheet.getRange(`A4:G${books.length + 3}`).format.wrapText = true;
booksSheet.getRange(`A4:G${books.length + 3}`).format.autofitRows();

const linksSheet = workbook.worksheets.getItem("資料リンク");
linksSheet.getRange("A6:D6").values = [[
  "ホームページ",
  "Googleマップ",
  "八尾市立志紀小学校の所在地をGoogleマップで確認できます。",
  "https://maps.app.goo.gl/tZbbaXNo8fm7tuFm7",
]];
linksSheet.getRange("A6:D6").format.wrapText = true;
linksSheet.getRange("A6:D6").format.autofitRows();

const reviewSheet = workbook.worksheets.getItem("要確認");
reviewSheet.getRange("A5:E6").values = [
  [
    "確認済み",
    "資料リンク",
    "GoogleマップURL",
    "申込ページに掲載されている表示URLを採用し、資料リンクへ追加した。",
    "採用URL：https://maps.app.goo.gl/tZbbaXNo8fm7tuFm7",
  ],
  [
    "確認済み",
    "概要・お知らせ",
    "公開授業の詳細注記",
    "全7授業の単元・授業者が確定済みのため、旧注記「詳細は決まり次第公開」は掲載しない。",
    "今回提供された確定プログラムを最優先資料として採用。",
  ],
];
reviewSheet.getRange("A5:E6").format.wrapText = true;
reviewSheet.getRange("A5:E6").format.autofitRows();

console.log((await workbook.inspect({
  kind: "table",
  range: `関連書籍!A3:G${books.length + 3}`,
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 8,
  maxChars: 18000,
})).ndjson);
console.log((await workbook.inspect({
  kind: "table",
  range: "要確認!A3:E6",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 6,
  maxChars: 8000,
})).ndjson);
console.log((await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
})).ndjson);

await fs.mkdir(path.join(outputDir, "page-build-preview"), { recursive: true });
for (const sheetName of ["関連書籍", "資料リンク", "要確認"]) {
  const preview = await workbook.render({
    sheetName,
    autoCrop: "all",
    scale: 1.5,
    format: "png",
  });
  await fs.writeFile(
    path.join(outputDir, "page-build-preview", `${sheetName}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(workbookPath);
