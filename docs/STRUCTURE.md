# Repository Documentation Taxonomy Standard (標準 docs/ 成果物4分類構造)

本ドキュメントは、学術論文リポジトリにおける `docs/` 配下の公式成果物分類構造（Single Source of Truth）を定義する。

---

## 📂 4分類標準ディレクトリ構造

すべての AI エージェントスキル、ルール、スクリプトは、生成・参照する成果物を以下の4サブディレクトリに分類して配置しなければならない。

```text
docs/
├── chapters/              # 論文本文の各章原稿 (Drafts & Manuscripts)
│   ├── chapter1-introduction.md
│   ├── chapter2-macro-and-labor.md
│   └── ...
├── design/                # 論文設計・構成・防衛インベントリ・概念定義 (Thesis Design & TDD)
│   ├── paper-outline.md
│   ├── test-cases.md
│   ├── domain-concepts.md
│   ├── evidence-gate-report.md
│   └── source-criticism-report.md
├── literature/            # 文献調査・レビュー・用語集・論文ノート (Literature & Reviews)
│   ├── literature-matrix.md
│   ├── literature-gap-report.md
│   ├── bilingual-glossary.md
│   └── papers/            # 個別論文の解読・翻訳ノート
│       └── [paper_name].md
└── data/                  # 取得データ・統計集計成果物・インベントリ (Empirical Datasets)
    ├── philippines-poverty-data.md
    └── pantawid-4ps-evaluation-data.md
```

---

## 規則
- 各スキルは必ず上記4分類のサブディレクトリをターゲットとして成果物を出力しなければならない。
- `docs/` 直下に孤立した `.md` ファイルを直接作成することは原則禁止とする。
