# AGENTS.md — Scholarly Agent Skills & Rules Engine

> **全 AI エージェント（Claude Code, OpenAI Codex, Cursor, Antigravity 等）共通統合エントリーポイント**

本ドキュメントは、本リポジトリを利用するすべての AI エージェントに対する共通指示書です。

## 免責事項 / Disclaimer

詳細は [`DISCLAIMER.md`](DISCLAIMER.md)（日本語が先、英語が後）。エージェントは次を守ること。

- 本スキル集は無保証の支援ツールである。生成文・出典・投稿の正確性は保証しない。
- 品質ゲートを通しても誤りは残り得る。確定情報として述べない。
- 提出先案内は現行規定の確認を利用者に求める。投稿可否を断定しない。
- 研究倫理・PII・IRB・著作権・外部API規約は利用者の責任である。エージェントは適法性を保証しない。
- 法律・医療・投資その他の専門助言をしない。
- 免責を省略したり、「問題ないので投稿してよい」と保証したりしない。

- This repository is an as-is aid. Do not claim that generated text, citations, or venue advice are guaranteed correct.
- Quality gates can miss errors. Ask the user to verify primary sources.
- Research ethics, PII, copyright, and API terms remain the user's responsibility.
- Do not give legal, medical, or financial advice, and do not omit this disclaimer.

---

## 🛠️ ディレクトリ構造

本リポジトリのスキル・ルールは、特定エディタに非依存の共通形式で配置されています：

- **正本スキル群 (日本語)**: [`skills/ja/`](skills/ja) (カタログ: [`skills/ja/README.md`](skills/ja/README.md))
- **正本スキル群 (英語)**: [`skills/en/`](skills/en) (カタログ: [`skills/en/README.md`](skills/en/README.md))
- **正本ルール群**: [`rules/ja/`](rules/ja) および [`rules/en/`](rules/en)
  - **重要ルール**: [`rules/ja/fact-grounding-rule.md`](rules/ja/fact-grounding-rule.md) (ハルシネーション完全防止・インターネット一次情報リアルタイム取得＆リポジトリ実体化ルール)
- **スクリプト群**: [`scripts/`](scripts) (多プロバイダー論文検索、PDF変換・画像抽出、AI Ignore設定、PIIマスキング、出典自動チェック、テスト実行)

---

## 📋 論文執筆リポジトリへの導入コマンド

### 方法 1: Git サブモジュール
```bash
# <your-username> をご自身または組織の GitHub ユーザー名・リポジトリパスに置き換えて実行してください
git submodule add https://github.com/<your-username>/scholarly-agent-skills.git .scholarly-agent-skills
python3 .scholarly-agent-skills/scripts/setup_submodule.py --lang ja
```

### 方法 2: シンボリックリンク
```bash
python3 /path/to/scholarly-agent-skills/scripts/link_shared_skills.py /path/to/target-repo --lang ja
```

---

## 📂 成果物（Artifacts）の Git 運用指針と標準 `docs/` ディレクトリ構造

論文リポジトリにおける成果物は、可読性と整理整頓のため以下の5分類構成で管理することを推奨します（複数論文を同一リポジトリで管理する場合は `docs/<paper-id>/` 配下に本構造を配置）：

- `docs/manuscript/` (または `docs/<paper-id>/manuscript/`): 完成論文原稿・ビルド成果物 (`[paper_title].md`, `[paper_title].html`, `[paper_title].pdf`)
- `docs/chapters/`: 論文本文の各章原稿 (`chapter1-introduction.md`, `chapter2-macro-and-labor.md` 等)
- `docs/design/`: 論文設計・構成・防衛インベントリ (`paper-outline.md`, `test-cases.md`, `domain-concepts.md`, `evidence-gate-report.md`)
- `docs/literature/`: 文献調査・用語集・論文ノート (`literature-matrix.md`, `literature-gap-report.md`, `bilingual-glossary.md`, `papers/*.md`)
- `docs/data/`: 取得データ・統計集計成果物 (`philippines-poverty-data.md` 等)

- **コミット推奨**: スキルによって生成される上記 `docs/` 配下の報告書・インベントリ・本文草稿・完成原稿 (manuscript) は、論文のトレーサビリティ確保と共同研究者との文脈共有のため、**Git リポジトリへコミットしてバージョン管理することを推奨**します。
- **コミット厳禁（要除外）**: 生の調査データ（`raw_data/`）および PII マッピング用ファイル（`mapping.json` 等）は、プライバシー・セキュリティ保護のため `.gitignore` および `python3 scripts/setup_ai_ignore.py` による AI Ignore 対象に設定し、コミットしないでください。

