---
name: pdf-paper-ingestion
version: 1.1.0
description: PDF論文をダウンロードした時やテキスト分析時に、見出し構造抽出・埋め込み画像 (JPEG/PNG) の切り出し保存・Markdown埋め込みを行うスキル (※スキャンPDFは非対応・OCR推奨)
---

# PDF論文 Markdown変換・画像自動抽出スキル (PDF Paper Ingestion)

## 目的
ダウンロードしたデジタルPDF形式の論文（arXiv, 学術誌論文等）を読み込み、**外部ライブラリ不要（Python標準ライブラリのみ）** でテキストストリームの解読、見出し構造の整理、およびPDFに埋め込まれた画像・図版（JPEG/PPM）の切り出し・保存を行い、`assets/` ディレクトリ配下に保存して画像リンク付きの Markdown ファイルへ自動変換する。

## 発動タイミング
- デジタルライブラリ・arXiv・学術誌サイト等からPDF論文をダウンロードした時
- PDF論文をテキスト分析や他スキルのインプットとして構造化する時

> [!WARNING]
> **スクリプトの制限事項 (Known Limitations)**:
> 1. **スキャンPDF (画像のみ)**: 埋め込みテキストを含まないスキャンPDFは空テキスト（注記のみ）が出力されます。OCR処理が必要です。
> 2. **CJK (日本語・中国語・韓国語) CIDFont PDF**: 固有エンコーディングによりテキストが空または文字化けする場合があります。
> 3. **暗号化・パスワード保護PDF**: 読み込み不可のためエラー終了します。

## 処理手順

### Step 1: PDF変換スクリプトの実行
リポジトリ同梱の [`scripts/convert_pdf_to_markdown.py`](../../../scripts/convert_pdf_to_markdown.py) を実行する：

```bash
# 基本的な使い方 (同じディレクトリに .md と assets/ を出力) (サブモジュール導入時: python3 .scholarly-agent-skills/scripts/convert_pdf_to_markdown.py ...)
python3 scripts/convert_pdf_to_markdown.py path/to/paper.pdf

# 出力先ディレクトリを指定する場合
python3 scripts/convert_pdf_to_markdown.py path/to/paper.pdf --output-dir docs/literature/papers/
```

> [!NOTE]
> サブモジュール導入先のリポジトリから実行する場合は、スクリプトパス頭に `.scholarly-agent-skills/` を付与してください。

### Step 2: 抽出結果の確認とフォールバック処理

- **通常成功時**:
  - `[paper_name].md`: 抽出された見出し構造・本文・画像リンク。
  - `assets/` ディレクトリ: 抽出された図版ファイル群。
- **PPM → PNG 自動変換（v1.1.0）**:
  - PDF 内の FlateDecode 画像は一度 `.ppm` として抽出される。
  - **Pillow** または **ImageMagick** (`convert` / `magick`) が利用可能な場合、変換直後に `.png` へ正規化し、Markdown 内の参照も `.png` になる。
  - 既存の `.ppm` のみ変換する場合:
    ```bash
    python3 scripts/convert_pdf_to_markdown.py \
      --normalize-ppm-dir docs/literature/papers/assets \
      --update-md docs/literature/papers/risko-gilbert-2016.md
    ```
- **フォールバック（スキャンPDF・CJK文字化け・暗号化時）**:
  標準スクリプトでテキストが正しく抽出できない場合は、以下のサードパーティ製ツールや外部ライブラリを案内・使用してください：
  - **pymupdf (`fitz`) / pdfplumber**: 高精度なテキスト・CJKエンコーディング抽出
  - **tesseract OCR / ocrmypdf**: スキャンPDFからのテキスト自動抽出

### Step 3: 先行研究分析への組み込み
変換された Markdown ファイルを `literature-gap-analysis`（先行研究ギャップ分析）や `claim-evidence-gate`（エビデンス検証ゲート）へ読み込ませ、テキスト分析を行う。

## 成果物
- `docs/literature/papers/[paper_name].md`
- `docs/literature/papers/assets/extracted_image_*.jpg`
- `docs/literature/papers/assets/extracted_image_*.png`（PPM 正規化成功時）

