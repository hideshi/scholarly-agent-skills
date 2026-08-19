# セッショントランスクリプトのリポジトリ永続化 — アイデアメモ

| 項目 | 内容 |
| :--- | :--- |
| **関連スキル** | `session-research-handoff`, `design-science-research`（プロセスエビデンス）, `friction-driven-skill-improvement` |
| **きっかけ** | jiatama-supremacism 論文の校閲期対話（2026-08-19）— セッションログを「答え責任」の証拠装置（tracking/tracing の実演記録）として扱う発想から |
| **最終更新** | 2026-08-19 |
| **ステータス** | アイデアメモ。緊急度なし（著者判断 2026-08-19）。実装する場合は本メモを叩き台にする |

## 背景

- AI エージェントとの対話ログは、DSR 系論文におけるプロセスエビデンス（誰が何を判断し採否したかの記録）になりうる
- Cursor のトランスクリプトは `~/.cursor/projects/<project-slug>/agent-transcripts/<uuid>.jsonl` に保存されるが、リポジトリ外でありローテーション等で消失しうる
- 論文リポジトリ側には `docs/<paper-id>/design/session-transcripts/` という配置区分の規則が既にある（INDEX 区分定義）

## アイデア: git pre-push フックで push 時にコピーする

Cursor 製品側の保存設定に依存せず、git フックで実現する方式。

```bash
# .git/hooks/pre-push のイメージ
cp ~/.cursor/projects/<project-slug>/agent-transcripts/*.jsonl \
   docs/<paper-id>/design/session-transcripts/
```

### 設計分岐（2026-08-19 時点の検討案）

| 案 | 内容 | 長所 | 短所 |
| :--- | :--- | :--- | :--- |
| A. 自動コミット型 | pre-push でコピー＋専用コミット（`chore: sync session transcripts`）まで自動化 | 手間ゼロ | 意図しないコミットが積まれる。pre-push はコミット後に走るため、push 物に含めるにはフック内コミットが必須 |
| B. 警告型＋手動スクリプト | pre-push は未同期ログの警告のみ。コピー＋コミットは `scripts/` の同期スクリプトで明示実行 | コミット規律と整合。素直 | 手動ステップが残る |
| C. B＋日次同期 | cron 等で日次コピーを併用 | push 前の消失にも強い | 設定が増える |

検討時の推奨は B（必要なら C）。

### 注意点

- **push は不定期**: セッション終了直後にローテーションで消えるケースは pre-push では救えない（C の動機）
- **フックの管理**: `.git/hooks/` はバージョン管理外。`.githooks/` に置き `core.hooksPath` で参照するとフック自体も保存される
- **リポジトリ肥大**: jsonl は1行が非常に大きくなりうる。サイズ・鮮度でフィルタするか gzip を検討
- **秘匿情報**: トランスクリプトには PII・トークン等が混入しうる。コミット前のスキャン（`mask_pii_data.py` 等）か AI Ignore 対象化を検討すること — 生データのコミット禁止ルール（AGENTS.md）と整合させる
- **jsonl → 可読形式**: 証拠として読むなら jsonl のままではなく Markdown 変換する中間スクリプトがあるとよい

### 未検証事項（要調査）

- Cursor Hooks（`.cursor/hooks.json`）に SessionEnd 等のライフサイクルイベントがあるか、フックにトランスクリプトのパスが渡されるか —— 公式ドキュメントの調査が必要（2026-08-19 に調査サブエージェントを2度起動したが著者により中止。git フック方式を優先する判断のため）
- Cursor CLI のトランスクリプトエクスポート機能の有無
