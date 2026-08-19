# 査読者可読性ルール (Reviewer-Readability Rule)

## 概要
論文本章（`docs/<paper-id>/chapters/`）は査読者向けの学術記述レイヤであり、内部記号・工程語の露出を防ぐため、**章の執筆・改訂完了時**および**原稿ビルド時**に `scripts/check_reviewer_readability.py` による機械検査を必須とするルールである。

---

## 📚 1. 語彙の3層分離

| レイヤ | 対象 | 規則 |
| :--- | :--- | :--- |
| **本文** | 章ファイルの段落・見出し・箇条書き | 日本語の学術記述のみ。内部記号（`PROP-*`, `SCAF-FAIL`, `RQ-*`, `PH-*`）、JST 時刻、バージョン番号は原則除去。節番号は連番とし、枝番（`3.2b` 等）・欠番・重複・実在しない `§` 参照を残さない |
| **表** | Markdown 表（`\|` 始まり行） | コードは残してよいが、日本語説明の併記（表注またはセル内 gloss）を必須とする |
| **付録・正本** | 付録 A–C、検証インベントリ、対話ログ | 内部記号の完全な定義と監査証跡を集約。検査対象外 |

## ✍️ 2. 負例 ID の本文表記（prose-gloss）
- 本文で負例に言及する場合は「負例として〇〇が観察された（NC-05）」の形とし、ID を文の主語にしない
- 「NC-01（図表の却下）」のような ID＋括弧 gloss の隣接形も許容する

## 🚦 3. 強制発動ポイント

1. **章完成時**: 章ファイルの執筆・改訂を完了したら、以下を実行する
   ```bash
   python3 scripts/check_reviewer_readability.py docs/<paper-id>/chapters/<file>.md
   ```
2. **原稿ビルド時**: `assemble_manuscript.py` が同チェックを自動実行し、FAIL 時はビルドを中断する（回避は `--force` のみ。回避した場合は理由を判断ログに記録する）
3. **投稿前**: `check_pre_submission.py` の第5チェックとして実行される

## ⚠️ 4. 検出時の対応
- **FAIL**: 必ず修正する。「対応不要」への分類は認めない（`reviewer-readability-check` スキル Step 2 のパターン表に従う）
- **WARN**: `reviewer-readability-check` スキルでトリアージし、「対応不要」の判断には著者承認とログ記録が必須
- **意図的な例外**: 当該行に `<!-- readability:ignore -->` を付し、根拠を `docs/<paper-id>/design/logs/reviewer-readability-log.md` に記録する

## 📖 5. コード定義の所在
- 読者向け抜粋: 論文側 付録 A.3（用語集）
- 完全な正本: 検証インベントリ §4.2（コードブック）
