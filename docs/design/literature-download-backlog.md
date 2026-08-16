# 文献 PDF 自動取得 — 今後の検討課題 (Literature Download Backlog)

| 項目 | 内容 |
| :--- | :--- |
| **関連スクリプト** | `scripts/download_literature_pdf.py`, `scripts/search_literature.py`, `scripts/convert_pdf_to_markdown.py` |
| **関連スキル** | `pdf-paper-ingestion`, `citation-traceability-audit`, `literature-search` |
| **最終更新** | 2026-08-16 |

`download_literature_pdf.py`（P1 部分実装）以降も、以下は **自動化の対象外または未実装** として扱う。エージェントは curl 等での ad hoc 取得に頼らず、各項目の正規経路を優先すること。

---

## 1. 出版社 paywall（HTTP 403 等）

**例**: Wiley (`onlinelibrary.wiley.com`), MISQ / AIS 正規ルート（Hevner 2004 等）

| 項目 | 内容 |
| :--- | :--- |
| **現状** | OpenAlex / Semantic Scholar が OA URL を返しても CDN が 403 を返すことがある |
| **正規経路** | `status: manual-stub` + **ページ番号付き書き抜き**（二次文献経由の定義引用は要出典明示） |
| **今後の検討** | Unpaywall API 連携（要メール登録）、著者ミラー URL のホワイトリスト、利用者提供 PDF の `--ingest` ハンドオフ |

---

## 2. 書籍・学位論文

**例**: Barkley (2012), Yin (2018), Singer (1998), Vygotsky (1978)

| 項目 | 内容 |
| :--- | :--- |
| **現状** | DOI/arXiv ベースの OA 解決では対象外 |
| **正規経路** | `status: manual-stub` + 所蔵・版・ページ番号付き excerpt |
| **今後の検討** | Open Library / Google Books API（プレビュー範囲のみ）、Institutional HathiTrust（利用者認証前提）、ISBN → 所蔵目録リンク生成 |

---

## 3. 機関リポジトリの非標準 URL

**例**: Bristol (`research-information.bris.ac.uk/ws/files/...`), UvA Pure (`pure.uva.nl/ws/files/...`)

| 項目 | 内容 |
| :--- | :--- |
| **現状** | OpenAlex/S2 の `pdf_url` に載らない、または landing page のみで直接 PDF パスが API に無い |
| **正規経路** | リポジトリごとの **フォールバック URL リスト**（設定ファイル）→ 失敗時は manual-stub |
| **今後の検討** | `config/literature_oa_mirrors.json`（DOI  prefix / 出版社 → 既知ミラーパターン）、CORE / Europe PMC 追加プロバイダー |

---

## 4. literature-search v2 自動ハンドオフ（P1 残）

| 項目 | 内容 |
| :--- | :--- |
| **現状** | 検索 → マトリクス反映でパイプライン断絶。DL は別コマンド |
| **目標** | `search_literature.py` 結果の `pdf_url` を `download_literature_pdf.py` → `convert_pdf_to_markdown.py` へ連鎖し `_ingestion-log.md` を自動更新 |
| **ブロッカー** | paywall 判定後の WARN 分岐、書籍タイプの除外ルール |

---

## 5. その他（レビュー指摘の継続）

- **DOI 誤マッチ**: OpenAlex 抽象のみ・別文献 abstract の混入 → ingestion 後にタイトル/DOI 照合
- **HTML 偽装 PDF**: `%PDF` 検証は実装済み。スキャン PDF 空テキストは OCR フォールバック案内
- **版 drift**: preprint vs 刊行版 DOI → frontmatter `version` フィールドの監査

---

## 参照

- 論文リポジトリ側バックログ: `docs/<paper-id>/design/literature-grounding-skill-improvement-proposal.md` §8
- fact-grounding-rule: `rules/ja/fact-grounding-rule.md` §2-B-3（manual-stub）
