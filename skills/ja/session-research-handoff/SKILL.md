---
name: session-research-handoff
version: 2.1.0
description: 作業セッションの終了時・長期執筆の再開時に、研究文脈・未解決課題・確認待ち文献・思考途中状態を引き継ぎロードするスキル。複数論文リポジトリにおける論文固有/横断の文脈書き分けに対応。
---

# 長期研究・セッション引継ぎスキル (Session Research Handoff)

## 目的
ソフトウェア開発におけるセッションハンドオーバーの手法を応用し、何ヶ月も続く長編論文執筆や研究プロジェクトにおいて、AIエージェントのコンテキスト制限を超えて文脈・執筆進捗・未解決の論点・思考途中状態をスムーズに引き継ぐ。複数論文を同一リポジトリで管理する場合の文脈書き分けにも対応する。

## 発動タイミング
- 作業セッションの終了時
- コンテキストウィンドウ制限が近づいた時
- 別の章や新しいテーマへ移行する時
- 長時間の連続作業（過集中）の中断時

## 処理手順

### Step 0: 過集中コンテキストの自動検出（S3原則）
エージェントが以下の状況を検知した場合、直ちに「現在の思考コンテキストを保存しますか？」と提案する：

- ユーザーが明示的にセッションの終了・中断を指示した場合
- 長時間の連続作業が行われている場合
- 話題が大きく転換する場合（別の論文・別の章への移行等）

### Step 1: 記録先の判定（Multi-Paper Context-Aware Routing）
複数論文を同一リポジトリで管理する場合、記録先を作業コンテキストに応じて自動判定する：

| ケース | 記録先 | 例 |
|---|---|---|
| **特定論文への没頭** | `docs/<paper-id>/session-handoff.md` | ADHD論文の第3章の仮説検証に集中していた |
| **論文間の横断作業** | `docs/session-handoff.md`（ルート） | フィリピン論文の手法をADHD論文に応用できないか検討中 |
| **複数論文の並行進行** | ルートに横断サマリ + 各 `docs/<paper-id>/session-handoff.md` に詳細 | ADHD論文の文献調査 + フィリピン論文のリビジョンを同時進行 |

- **ポインタ規則**: ルートの `docs/session-handoff.md` には、どの論文固有ファイルを参照すべきかのポインタを**必ず**残す。

### Step 2: 現在状態の記録 (Handoff Report 生成)

#### 論文固有 Handoff テンプレート (`docs/<paper-id>/session-handoff.md`)

```markdown
# Research Session Handoff Report — [論文タイトル/paper-id]

## 1. 執筆進捗 (Current Status)
- **完了した作業**: 第2章「史料Aの解読と論点整理」の初稿執筆
- **現在のファイル**: `docs/<paper-id>/chapters/chapter2.md`

## 2. 採用された概念モデル (Applied Domain Concepts)
- 『主体』の定義: 18世紀啓蒙思想モデルを適用（`docs/<paper-id>/design/domain-concepts.md` 参照）

## 3. 未解決の論点・検証待ちリスト (Pending Issues)
- [ ] 史料Bの成立年代に関するSmith(2018)とJones(2021)の説の対立の決着
- [ ] 第3章への接続語の推敲

## 4. 次回セッションの再開プロトコル (Resume Protocol)
1. 本ファイルを読み込む。
2. 未解決リスト1番目のSmith/Jonesの対立整理から再開する。

## 5. 思考の途中状態 (Active Thought Context)
- 「史料Bの年代をSmith説（1680年代）で解釈すると第4章の論旨と矛盾するが、Jones説（1710年代）なら整合する」→ まだ検証が完了していない。
- 第3章の冒頭で「経済的転換の定義」をどの範囲で使うか未決定。

## 6. 復帰時のウォームアップ質問 (Warm-Up Questions)
- 「前回は史料Bの年代についてSmith説とJones説の比較途中でした。Jones説寄りで進めますか？」
- 「第3章冒頭の『経済的転換』の定義範囲について、前回の議論を踏まえて方針を決めましょうか？」

## 7. 実行環境 (Execution Environment)
再現性・監査可能性の確保のため、セッションの実行環境を必ず記録する。
- **エージェント / モデル**: 例) Cursor (Kimi K3), Claude Code (Opus 4.8), Antigravity
- **実行日**: YYYY-MM-DD
- **主要プロンプト・指示**: 例) 「第3章の仮説検証を手伝って」
- **関連コミット**: 例) `abc1234` (対話内容と成果物の突合を可能にする監査証跡)
```

#### ルート横断 Handoff テンプレート (`docs/session-handoff.md`)

```markdown
# Research Session Handoff Report — Repository Overview

## アクティブ論文一覧 (Active Papers)
| 論文 (paper-id) | 状態 | 詳細ファイル |
|---|---|---|
| `adhd-ai` | 第3章執筆中 | → `docs/adhd-ai/session-handoff.md` |
| `philippines-poverty` | リビジョン待ち | → `docs/philippines-poverty/session-handoff.md` |

## 論文横断の未決事項 (Cross-Paper Open Items)
- [ ] フィリピン論文の「認知オフローディング」概念をADHD論文の第2章で参照する是非
- [ ] 両論文の参考文献リストに重複があるか確認

## 次回セッションの推奨開始ポイント
→ `adhd-ai` 論文の第3章から再開を推奨（締切が近いため）
```

### Step 3: 次回セッションでの復帰
新セッション開始時、エージェントは以下の順序で文脈を復元する：

1. ルートの `docs/session-handoff.md` があれば先に読み、アクティブ論文を把握する。
2. 該当する `docs/<paper-id>/session-handoff.md` を読み込む。
3. **ウォームアップ質問**（セクション6）をユーザーに投げかけ、前回の思考文脈への復帰を支援する。

## 認知スキャフォールディング
本スキルの全対話において、[認知スキャフォールディング原則](../../../rules/ja/cognitive-scaffolding-rule.md)（S1〜S4）を遵守する。特に S3（コンテキストセービング）が本スキルの中核原則であり、過集中の安全な中断と復帰コストの最小化を最優先とする。

## 成果物
- `docs/session-handoff.md`（ルート横断サマリ）
- `docs/<paper-id>/session-handoff.md`（論文固有の詳細ハンドオフ）
