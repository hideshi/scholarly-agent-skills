---
name: citation-traceability-audit
version: 1.3.1
description: 投稿前・各章完成時に、本文の主張や参照マーカーと参考文献リスト・脚注の1対1対応、未定義参照を監査し、references.mdを機械生成するスキル
---

# 出典・脚注トレーサビリティ監査スキル (Citation Traceability Audit)

## 目的
静的コード解析（Static Analysis）の考え方を応用し、原稿本文中のすべての記述・引用・脚注参照（`[^1]` 等）が、正本である `docs/literature/literature-matrix.md` および派生生成物である参考文献一覧（`docs/chapters/references.md`）と 1対1 で整合しているかを包括的に監査する。

## 発動タイミング
- 論文の各章執筆完了時
- 投稿・最終提出前の自動チェック

## 処理手順 (4段階メカニカル監査ワークフロー)

```text
[Step 1: 本文引用の機械抽出] ➔ [Step 2: 一次文献マトリクス照合] ➔ [Step 3: references.md 自動生成] ➔ [Step 4: 1対1整合性再監査]
```

### Step 1: 本文引用の機械抽出
同梱スクリプト `scripts/check_citation_format.py` を用い、本文（`docs/chapters/`）に存在するすべての引用マーカー（個人著者 `Son, 2010`、組織著者略称 `PSA, 2024` / `ADB, 2023`、複数単語組織 `World Bank, 2026` 等）および脚注 `[^1]` を機械的に抽出する：

```bash
python3 scripts/check_citation_format.py docs/chapters/
```

### Step 2: 正本文献マトリクス (SoT) との照合
正本である `docs/literature/literature-matrix.md` と抽出し他本文引用を照合する：

```bash
python3 scripts/check_citation_format.py --matrix docs/literature/literature-matrix.md docs/chapters/
```
- **未登録引用の検知**: 本文中で引用されているが、`literature-matrix.md` に登録のない文献が存在する場合、AIのエージェント記憶による生成を行わず、即座に一次資料調査へと差し戻す。

### Step 3: `references.md` の自動派生生成
照合完了後、`literature-matrix.md` から派生生成物として `docs/chapters/references.md` を自動生成する：

```bash
python3 scripts/check_citation_format.py --generate-references docs/chapters/references.md --matrix docs/literature/literature-matrix.md docs/chapters/
```

> ⚠️ **単一真実解（Single Source of Truth: SoT）規律**: 
> `docs/literature/literature-matrix.md` が文献情報の唯一の正本（SoT）である。`docs/chapters/references.md` は手動編集してはならず、必ずスクリプトから自動生成しなければならない（`<!-- AUTO-GENERATED -->` ヘッダを付与）。

### Step 4: 1対1整合性再監査
生成された `references.md` と本文引用の間に、未定義参照（Missing Definitions）や孤児文献（Unused References）が存在しないか最終確認する。

## 成果物
- 自動生成された `docs/chapters/references.md` (参考文献一覧)
- 監査ログ `docs/design/citation-audit.log`
