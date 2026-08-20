# スキル案: 論文リポジトリ提出・アーカイブ (Repository Submission Archive)

| 項目 | 内容 |
| :--- | :--- |
| **提案 ID** | RSS-2026-08-16-v0.1 |
| **提案者** | Cursor / Composer 2.5（cognitive-scaffolding ケースより一般化） |
| **レビュー依頼** | Kimi K3（外部レビュー） |
| **関連スキル** | `submission-venue-advisor`, `citation-traceability-audit`, `session-research-handoff`, `claim-evidence-gate`, `primary-data-integration` |
| **想定配置** | `skills/ja/repository-submission-archive/SKILL.md` + `scripts/export_submission_archive.py` |

---

## 1. 背景・問題設定

DSR / 単一ケーススタディ論文が **Git 監査証跡**（コミットハッシュ、タイムスタンプ、`Agent:`/`Model:` 行）を方法論として引用する場合、読者・査読者は次を期待しうる：

- コミット ID が**検証可能**であること
- 対話ログ・設計文書が**利用可能**であること
- 一方で著者は **執筆中リポジトリを常時 public にしたくない** 場合がある

**よくある誤解**: 「本文に `85e1bcc` と書いた＝GitHub を今すぐ public にせよ」  
**本スキルの立場**: コミット ID は**内部監査索引**。公開は **受理後スナップショット（Zenodo 等）** または **git bundle** で履歴ごと提供する。

**既知の落とし穴（cognitive-scaffolding ケースより）**:

| 落とし穴 | 結果 |
| :--- | :--- |
| Markdown だけ zip | **コミットログが失われる** → ハッシュが検証不能 |
| 全リポジトリ public | 他論文・未完成稿・PII が混入 |
| プロンプトのみ export | Gemini 帯は可；Cursor 帯は Git 正本が必要 |
| dialogue-log に GitHub ユーザー名 | 匿名査読と矛盾 |

---

## 2. スキル目的

論文 **受理後（または査読者要求時）** に、再現性・監査証跡を満たす**提出用アーカイブ**を機械的に組み立て、Data Availability 声明文案まで生成する。

---

## 3. 発動タイミング

- 論文 **accept 後**、補足資料・データ可用性を整備するとき
- 査読者から「commit hash を検証したい」と **reproducibility request** が来たとき
- 本文に Git コミット ID / 対話ログ参照を含む **第4章ケーススタudy** 完成前の自己監査
- `submission-venue-advisor` で Zenodo / OSF を選んだ後の**具体パッケージング**

---

## 4. ワークフロー（7 Step）

### Step 0: スコープ確定

入力（ユーザーまたは `config/submission_archive.json`）:

```json
{
  "paper_id": "cognitive-scaffolding",
  "source_repo": "/path/to/academic-papers",
  "include_paths": ["docs/cognitive-scaffolding/"],
  "exclude_globs": ["**/raw_data/**", "**/.env*"],
  "git_ref": "main",
  "git_since_commit": null,
  "other_papers_in_repo": ["medieval-japan-information-flow", "philippines-poverty"]
}
```

**原則**: 1論文 = 1アーカイブ。マルチ論文リポジトリは **サブツリー + git 履歴フィルタ** または **orphan branch**。

### Step 1: 除外監査（PII・秘密・著作権）

| チェック | 手段 |
| :--- | :--- |
| PII | `mask_pii_data.py` 対象パス確認 |
| 秘密 | `.env`, API key, `mapping.json` grep |
| 他論文 | `include_paths` 外が bundle に含まれないこと |
| 文献 PDF | `_downloads/` の OA・公式 PDF は原本として同梱。再配布不可 PDF は取得せず **stub のみ** |
| 匿名化 | `dialogue-prompts-log.md` 内 GitHub URL・著者メールの redaction |

### Step 2: Git 監査証跡のエクスポート（必須）

**方式 A（推奨）: `git bundle`**

```bash
# サブツリー履歴付き bundle（スクリプト化）
git log --format=fuller -- docs/cognitive-scaffolding/ > archive/git-log-fuller.txt
git bundle create archive/cognitive-scaffolding.bundle <ref-list>
```

**方式 B: GitHub Release + Zenodo 連携**（live repo を一時 public にできる場合）

**方式 C（補助）: テキストのみ**

```bash
git log -p -- docs/cognitive-scaffolding/ > archive/git-log-with-patches.txt
```

> **ゲート**: 本文で引用した各短 hash（例 `85e1bcc`, `e19a6b4`）が `git-log-fuller.txt` または bundle 内で **`git cat-file -t` 可能**であることをスクリプト検証。

### Step 3: 対話ログ・handoff の同梱

| ソース | ファイル |
| :--- | :--- |
| Gemini / 全プロンプト | `design/dialogue-prompts-log.md` |
| Phase 索引 | `design/session-transcripts/*.md` |
| コミットしない作業 | `test-cases.md` §5（該当行） |

### Step 4: 再現性マニフェスト生成

`archive/MANIFEST.md`（自動生成）:

- 論文 ID、生成日時、git ref、bundle SHA256
- 本文引用コミット一覧 ↔ `git log` 突合結果 PASS/FAIL
- 含まれるファイルツリー
- ライセンス（CC-BY 4.0 推奨）
- **限界声明**（一括エクスポートタイミング、システムプロンプト未収録等）

### Step 5: Data Availability 声明文案

テンプレ（論文 §5.4 / Cover letter 用）:

> Case study materials, including Git audit trail (`cognitive-scaffolding.bundle`), dialogue log, and design inventories, are archived on Zenodo (DOI: TBD). Commit hashes in §4.1 refer to objects in snapshot `<tag>`. The live development repository remains private; the archived bundle is the authoritative reproducibility source.

Modality: **TBD を受理後 DOI で置換**。「完全再現」を主張しない。

### Step 6: Zenodo / OSF アップロード

- `submission-venue-advisor` の Zenodo 手順に委譲
- アップロード物: `archive/` ディレクトリを zip（**bundle + MANIFEST + 同梱 md**）
- メタデータ: 論文タイトル、著者、関連 publication DOI、ライセンス

### Step 7: 論文側の整合更新

- §5.4 Data Availability に DOI 追記
- コミット hash の脚注「See Zenodo snapshot `<tag>`」
- `evidence-gate-report` に RR-2 / RR-4 達成を記録

---

## 5. 提案スクリプト `export_submission_archive.py`

```bash
python3 scripts/export_submission_archive.py \
  --paper-id cognitive-scaffolding \
  --repo /path/to/academic-papers \
  --include docs/cognitive-scaffolding \
  --git-ref main \
  --verify-commits 85e1bcc,e19a6b4,2766fa0,8e41cc9 \
  --output ./submission-archive-out/
```

**出力**:

```
submission-archive-out/
├── MANIFEST.md
├── git-log-fuller.txt
├── cognitive-scaffolding.bundle
├── docs/                    # 同梱用コピー（または bundle のみ）
├── data-availability.md     # 声明文案
└── zenodo-upload.zip
```

**非目標（v0.1）**: Zenodo API 自動投稿（手動アップロードで十分）

---

## 6. スキル SKILL.md  frontmatter（草案）

```yaml
---
name: repository-submission-archive
version: 0.1.0
description: 論文受理後・査読対応時に、Git監査証跡付きリポジトリスナップショット（git bundle/Zenodo）を組み立て、Data Availability声明を生成するスキル
---
```

---

## 7. 既存スキルとの境界

| スキル | 境界 |
| :--- | :--- |
| `submission-venue-advisor` | **どこに**出すか（Zenodo vs arXiv） |
| **本スキル** | **何を**どう梱包するか（bundle・除外・manifest） |
| `citation-traceability-audit` | 本文引用 ↔ literature/ 整合（アーカイブ**前**） |
| `primary-data-integration` | raw_data / PII 除外ルール |
| `session-research-handoff` | 執筆中引継ぎ（アーカイブ**前**） |

---

## 8. テストケース（スキル品質）

| ID | 入力 | 期待 |
| :--- | :--- | :--- |
| T1 | `--verify-commits 85e1bcc` | MANIFEST に PASS |
| T2 | `include_paths` 外の論文ディレクトリ | bundle に含まれない |
| T3 | `_downloads/*.pdf`（OA・公式） | 同梱。再配布不可は stub のみ |
| T4 | 存在しない hash | FAIL + stderr |
| T5 | `dialogue-prompts-log` に github.com/ユーザー名 | redaction 警告 |

---

## 9. 未決事項（Kimi レビュー用）

1. **orphan branch vs git subtree filter** — どちらを default にするか
2. **査読中** anonymous Zenodo（embargo）の扱い
3. **scholarly-agent-skills** を同一 DOI に含めるか別 DOI か
4. 日本語論文向け JAIRO / 機関リポジトリ分岐
5. スキル名: `repository-submission-archive` vs `reproducibility-archive` vs `case-study-data-deposit`

---

## 10. Kimi K3 レビュー依頼チェックリスト

- [x] DSR / Yin 単一ケースの方法論と矛盾しない Modality か → **要修正**（"reproducibility source" → "audit-trail source"）
- [x] git bundle 推奨は過剰か → **デフォルト維持**（全履歴・フィルタなし Mode A）
- [x] 7 Step はエージェント実行可能な粒度か → **2モード設計追加後に可**
- [x] submission-venue-advisor との重複 → **別スキル維持、双方向リンク**
- [x] bundle に .git/config credential → **誤解**（bundle は含まない；真のリスクは author 情報・履歴内秘密）
- [x] MANIFEST に復元手順必須 → **賛成**

---

## 11. Kimi K3 外部レビュー結果（2026-08-16）

**Verdict: APPROVE WITH REVISIONS**

### 採用する修正（v0.2 提案へ反映予定）

1. **2モード設計**
   - **Mode A（デフォルト）**: フィルタなし `git bundle` → 本文ハッシュ完全検証可能（他論文履歴混入は MANIFEST で開示）
   - **Mode B**: `git filter-repo` + author 匿名化 + `commit-map` 同梱（ダブルブラインド査読用；ハッシュは写し）

2. **Critical: サブツリーフィルタとハッシュ検証は両立不可** — filter-repo はハッシュを書き換える

3. **ハッシュ検証**: bundle から clone したコピー内で `git cat-file`；本文 Markdown から自動抽出（手動リストは漏れる）

4. **セキュリティ追加**: コミット author/email、履歴内秘密（gitleaks）、`file:///home/...` パス redaction

5. **命名**: `repository-submission-archive` 維持（`reproducibility-archive` は Modality 過剰）

6. **scholarly-agent-skills**: **別 DOI** + related identifier で相互リンク

7. **Data Availability 文案**: "authoritative **audit-trail** source"（reproducibility ではない）

### v0.1 スクリプト MVP（Kimi 優先順）

1. 本文からコミット hash 自動抽出 + `git cat-file -e`
2. `git bundle create` → verify → clone 内で全 hash 検証
3. `git log --format=fuller` テキスト export
4. 秘密パターン grep（現行ワークツリー）
5. MANIFEST.md + data-availability.md 生成
6. zenodo-upload.zip（手動アップロード）

### MANIFEST 必須フィールド（Kimi 案）

paper_id、生成日時・スクリプト版、Mode A/B、git ref/tag、bundle SHA256、`list-heads`、引用 hash 突合表、ファイルツリー、redaction サマリ、二層ライセンス、**復元手順**、限界声明、関連 DOI

---

## 12. 次アクション

- [ ] 本提案を v0.2 に更新（2モード・MANIFEST 必須項目）
- [ ] `skills/ja/repository-submission-archive/SKILL.md` 起草
- [ ] `scripts/export_submission_archive.py` v0.1 実装
- [ ] `submission-venue-advisor` に「コミット hash 引用時は本スキル予約」1行追加
