---
name: literature-search
version: 1.0.0
description: 研究課題の設定時・文献調査フェーズにおいて、OpenAlex/arXiv/Crossref/Semantic Scholar から多角的論文検索・マトリクス作成を行うスキル
---

# 多プロバイダー対応 文献自動検索スキル (Multi-Provider Literature Search)

## 目的
設定ファイル [`config/literature_providers.json`](../../../config/literature_providers.json) に定義されたオープンアクセス論文サイト（arXiv, OpenAlex, Crossref, Semantic Scholar 等）から、研究課題に関連する論文を横断検索し、適合度評価を行って `docs/literature/literature-matrix.md` へ自動挿入する。

## 発動タイミング
- 新しい研究テーマ・論文テーマの設定時
- 新しい論点や概念に関連する文献が必要になった時
- 査読者から追加の参考文献を求められた時

## 設定によるプロバイダー拡張
`config/literature_providers.json` に新しいAPIエンドポイント（または独自の論文検索サーバー）を追加・有効化/無効化できます：

```json
{
  "default_provider": "openalex",
  "contact_email": "",
  "providers": {
    "openalex": { "name": "OpenAlex", "type": "openalex_json", "base_url": "https://api.openalex.org/works", "enabled": true },
    "arxiv": { "name": "arXiv", "type": "arxiv_atom", "base_url": "https://export.arxiv.org/api/query", "enabled": true },
    "crossref": { "name": "Crossref", "type": "crossref_json", "base_url": "https://api.crossref.org/works", "enabled": true },
    "semanticscholar": { "name": "Semantic Scholar", "type": "semanticscholar_json", "base_url": "https://api.semanticscholar.org/graph/v1/paper/search", "enabled": true }
  }
}
```

OpenAlex / Crossref の polite pool のため、実行者本人の連絡先を環境変数で渡す。git に書かない。`example.com` などのダミーは拒否される。

```bash
export SCHOLARLY_CONTACT_EMAIL="firstname.lastname@university.ac.jp"
export SEMANTIC_SCHOLAR_API_KEY="your-key"   # 任意。Semantic Scholar を頻繁に使う場合
```

未設定・空・ダミーのまま実行すると、スクリプトは HTTP を送らず終了コード 1 で止まり、stderr に設定手順を出す。エージェントはその指示に従い、ユーザーに実メールを確認してから再実行する。

## 実行手順

### Step 1: 検索スクリプトの実行
全プロバイダー横断検索、または特定プロバイダーを指定して実行：

```bash
# 全有効プロバイダーを横断検索 (サブモジュール導入時: python3 .scholarly-agent-skills/scripts/search_literature.py ...)
python3 scripts/search_literature.py --query "hermeneutics AND 'large language models'" --provider all --max-results 5

# OpenAlex（人文学・全領域カバー）を指定検索
python3 scripts/search_literature.py --query "hermeneutics" --provider openalex --max-results 5
```

> [!NOTE]
> サブモジュール導入先のリポジトリから実行する場合は、スクリプトパス頭に `.scholarly-agent-skills/` を付与してください。

### Step 2: 論文の構造化とマトリクス反映
検索結果から適合度が高い論文を `docs/literature/literature-matrix.md` に追記し、`literature-gap-analysis`（先行研究ギャップ分析）へ引き継ぐ。

## 成果物
- `docs/literature/literature-matrix.md` (検索結果・適合度評価マトリクス)

