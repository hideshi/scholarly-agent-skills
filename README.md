# Scholarly Agent Skills (Thesis-Driven Development)

> **AI Agent skills & rules for Academic Research, Literature Search, and Paper Writing across all disciplines.**  
> ソフトウェア開発の品質規範（DDD、TDD、仕様ギャップ分析、不変条件監査、セッションハンドオーバー）を学術研究・文献調査・論文執筆へと移植した、マルチプラットフォーム（Cursor, Claude Code, OpenAI Codex, Antigravity 等）対応の共通スキル＆ルール集。

---

## 💡 概要 (Concept)

本リポジトリは、特定のエディタやツール（Cursor等）に依存しない **ツール非依存（Tool-Agnostic）の共通形式** で学術エージェントスキルを保守し、各種 AI Coding / Agent 環境で横断利用できるように設計されています。人文科学をはじめ、社会科学・自然科学・工学・医学など、全学術分野の論文執筆に対応しています。

**論文の内容・出典・投稿に関する最終責任は、常に著者（利用者）にあります。** Authors remain responsible for the manuscript, citations, and any submission. 全文は [DISCLAIMER.md](DISCLAIMER.md) および下記「免責事項 / Disclaimer」を参照してください。

- **`paper-writing-onboarding`**: 初めての論文執筆者に環境セットアップからフェーズ別ワークフローまでを段階案内する。
- **`research-plan-workshop`**: 対話で研究問い・読者/提出先・完成の定義を1ページの研究計画に固める。
- **`primary-data-integration`**: 著者自身が収集した独自調査資料（実験ログ、アンケート、インタビュー逐語録、未公開史料等）を構造化し、本文の主張にダイレクト結合。
- **`scholarly-concept-modeling`**: DDD（ドメイン駆動設計）のユビキタス言語概念を用い、多義的・専門的な基本概念の定義揺れを防止。
- **`counter-argument-tdd`**: TDD（テスト駆動開発）の手法を用い、本文執筆前に反論・反証パターン（Red）を箇条書きにし、それを克服する執筆（Green/Refactor）を行う。
- **`claim-evidence-gate`**: 不変条件監査の手法を用い、論文の主張（Claim）に対する一次史料・実験データ・引用根拠（Evidence）の整合性をゲート判定。
- **`literature-gap-analysis`**: 仕様ギャップ分析（Spec Gap Analysis）の手法を用い、先行研究の到達点（AS-IS）と自説の新規性（TO-BE）の乖離を自動抽出。
- **`literature-search`**: OpenAlex, arXiv, Crossref, Semantic Scholar から多角的にオープンアクセス論文を自動取得・マトリクス化。
- **`diachronic-claim-typing`**: 通時的論文で主張を型付けし、断面選定と伝播・連続・新規性の過大接続を監査する。
- **`source-criticism-gate`**: 情報源の信頼度（Tier 1〜3）を評価し、不確かなWebサイトやSNSからの引用を遮断する。
- **`pdf-paper-ingestion`**: PDF論文の解読、見出し構造抽出、および画像・図版の自動切り出し・Markdown埋め込み。
- **`academic-paper-translation`**: 設定ファイルの自国語に基づき、外国語論文を対照翻訳・用語対照表（Glossary）付きで構造化変換。
- **`citation-traceability-audit`**: 本文中の全主張が出典（脚注・参考文献）と1対1で対応しているか自動監査。
- **`session-research-handoff`**: セッション間や長期執筆における文脈・未解決課題・確認待ち文献の引き継ぎ。
- **`pre-reading-briefing`**: 草稿の通読・査読共有の前に、節ごとの前提・主張・想定反論を提示し校閲期の読解コストを下げる。
- **`submission-venue-advisor`**: 分野・言語・目的に応じた提出先（プレプリントサーバー等）の選定と投稿手順を案内する。

カタログの全文は [`skills/ja/README.md`](skills/ja/README.md) / [`skills/en/README.md`](skills/en/README.md) を参照してください。

---

## 🛠️ 論文執筆リポジトリへの導入マニュアル (Installation Guide)

執筆中の論文リポジトリに本スキル集を導入する方法は **2種類** あります（すべて Python 3 標準ライブラリで動作します）。

### 方法 1: Git Submodule による導入（おすすめ: 共同執筆・ポータビリティ重視）
論文リポジトリ自体を Git 管理し、他の共同研究者や別マシンでも同じスキル環境を再現したい場合に最適です。

```bash
# 1. 論文リポジトリのルートでサブモジュールとして追加
git submodule add https://github.com/<your-username>/scholarly-agent-skills.git .scholarly-agent-skills

# 2. 自動セットアップスクリプトを実行 (日本語: --lang ja | 英語: --lang en)
python3 .scholarly-agent-skills/scripts/setup_submodule.py --lang ja
```

### 方法 2: シンボリックリンクによる導入（ローカル集中管理・一元更新重視）
ローカル開発環境で1箇所（`~/repo/scholarly-agent-skills`）に本スキル集を配置し、複数の論文プロジェクトから参照させたい場合に最適です。スキルを更新すると全論文プロジェクトに即座に反映されます。

```bash
# ターゲットの論文リポジトリパスを指定して実行 (日本語: --lang ja | 英語: --lang en)
python3 /path/to/scholarly-agent-skills/scripts/link_shared_skills.py /path/to/your-paper-repository --lang ja
```

---

## 🔌 外部 API の連絡先とキー

文献検索・マクロデータ取得は公開 API を呼び出します。OpenAlex / Crossref は polite pool のため、**連絡先メールを User-Agent に含めること**を推奨しています。リポジトリに個人メールをコミットしないでください。

```bash
# 必須: 実行者本人の連絡先（ドキュメント用の example.com は拒否されます）
export SCHOLARLY_CONTACT_EMAIL="firstname.lastname@university.ac.jp"

# Semantic Scholar を頻繁に使う場合（任意）
export SEMANTIC_SCHOLAR_API_KEY="your-key"
```

設定ファイル [`config/literature_providers.json`](config/literature_providers.json) の `contact_email` でも指定できます。環境変数がある場合は環境変数が優先されます。未設定・空・`you@example.com` などのダミーのまま外部リクエストを始めると、スクリプトは **HTTP を送らず終了コード 1** で止まり、エージェント向けの設定手順を stderr に出します。

---

## 🌐 多言語対応 (i18n: 日本語 / 英語)

- **日本語版スキル (`skills/ja/`)**: 学術常体（である調）および日本語学術スタイルに対応。
- **英語版スキル (`skills/en/`)**: 英語圏学術執筆規範（Topic-Sentence-First, Active Voice, Signposting）に対応。

---

## 免責事項 / Disclaimer

全文の正本は [DISCLAIMER.md](DISCLAIMER.md) です。日本語が先、英語が後です。

本リポジトリは学術研究と論文執筆を支援する無保証のツールであり、法律・医療・投資その他の専門助言ではありません。生成文の正確性、出典の真正性、投稿規定への適合、研究倫理・個人情報の適法性は保証しません。品質ゲートを通しても誤りは残り得ます。外部APIの利用規約と User-Agent の連絡先は実行者の責任です。著作物は利用権がある場合に限り取り込んでください。ソフトウェアは MIT License のもと現状有姿で提供されます。

This repository is an as-is research-writing aid, not professional advice. Authors remain responsible for claims, citations, ethics, and submissions. Quality gates can miss errors. Venue guidance is not a guarantee. API terms and the User-Agent contact email are the executor's responsibility. Ingest copyrighted works only with a right to do so. The software is provided under the MIT License, as is, without warranty.

---

## 📜 ライセンス

MIT License。貢献手順は [CONTRIBUTING.md](CONTRIBUTING.md)、脆弱性の報告は [SECURITY.md](SECURITY.md)、免責の全文は [DISCLAIMER.md](DISCLAIMER.md) を参照してください。
