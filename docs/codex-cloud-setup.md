# iPhone から Codex クラウドタスクを使う

このリポジトリは、Codex のクラウド環境へ GitHub リポジトリを接続すると、iPhone の ChatGPT アプリからクラウドタスクとして編集・検証できます。

## 初回設定（PC のブラウザを推奨）

1. ChatGPT の **Codex settings → Environments** を開く。
2. GitHub アカウントを接続し、`toyokan/t-pod` へのアクセスを許可する。
3. `toyokan/t-pod` を対象にクラウド環境を作成する。
4. パッケージバージョンで Python `3.13` を選ぶ。
5. Setup script に次を設定する。

   ```bash
   bash scripts/setup_codex_cloud.sh
   ```

6. Agent internet access は **Off** のままにする。このリポジトリの編集・検証には不要。
7. Secret と環境変数は設定しない。
8. 環境を保存する。セットアップスクリプトを変更した場合は、環境画面でキャッシュをリセットする。

セットアップ時には `openpyxl` の導入、イベントデータの検証、回帰テストまで実行されます。依存関係の取得に必要なネットワーク接続はセットアップフェーズで利用できます。

## iPhone からタスクを開始する

1. iPhone の ChatGPT アプリを開き、Codex を選ぶ。
2. GitHub の `toyokan/t-pod`、作業元ブランチ、作成したクラウド環境を選ぶ。
3. 変更内容と確認条件を具体的に依頼する。
4. 完了後、差分と検証結果を確認する。コミット、push、PR 作成は内容を確認してから明示的に依頼する。

依頼例:

```text
新しいイベントを追加してください。既存イベントは削除せず、AGENTS.md の手順に従ってください。
完了前に python scripts/validate_events.py と
python -m unittest discover -s tests -v を実行し、差分と結果を報告してください。
コミット、push、PR作成はまだ行わないでください。
```

## 制約

- クラウドタスクは GitHub 上のブランチまたはコミットをチェックアウトするため、ローカルだけにある未コミットファイルは参照できない。
- イベント入力用 Excel など、タスクに必要なファイルはあらかじめ安全なブランチへ追加しておく。
- 配布資料、認証情報、未公開情報はリポジトリやプロンプトへ不用意に含めない。
- 画面の目視確認が必要な場合は、変更後にPCまたは実機のブラウザでも確認する。

## 標準の検証コマンド

```bash
python scripts/validate_events.py
python -m unittest discover -s tests -v
git diff --check
```
