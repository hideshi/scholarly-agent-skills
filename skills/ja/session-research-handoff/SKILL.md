---
name: session-research-handoff
version: 1.0.0
description: 作業セッションの終了時・長期執筆の再開時に、研究文脈・未解決課題・確認待ち文献を引き継ぎロードするスキル
---

# 長期研究・セッション引継ぎスキル (Session Research Handoff)

## 目的
ソフトウェア開発におけるセッションハンドオーバーの手法を応用し、何ヶ月も続く長編論文執筆や研究プロジェクトにおいて、AIエージェントのコンテキスト制限を超えて文脈・執筆進捗・未解決の論点をスムーズに引き継ぐ。

## 発動タイミング
- 作業セッションの終了時
- コンテキストウィンドウ制限が近づいた時
- 別の章や新しいテーマへ移行する時

## 処理手順

### Step 1: 現在状態の記録 (Handoff Report 生成)
`docs/session-handoff.md` に以下のフォーマットで作業状態を要約出力する：

```markdown
# Research Session Handoff Report

## 1. 執筆進捗 (Current Status)
- **完了した作業**: 第2章「史料Aの解読と論点整理」の初稿執筆
- **現在のファイル**: `manuscript/ch02.md`

## 2. 採用された概念モデル (Applied Domain Concepts)
- 『主体』の定義: 18世紀啓蒙思想モデルを適用（`docs/design/domain-concepts.md` 参照）

## 3. 未解決の論点・検証待ちリスト (Pending Issues)
- [ ] 史料Bの成立年代に関するSmith(2018)とJones(2021)の説の対立の決着
- [ ] 第3章への接続語の推敲

## 4. 次回セッションの再開プロトコル (Resume Protocol)
1. `docs/session-handoff.md` を読み込む。
2. 未解決リスト1番目のSmith/Jonesの対立整理から再開する。
```

### Step 2: 次回セッションでの復帰
新セッション開始時、ユーザーまたはAIは `docs/session-handoff.md` をロードすることで、過去の主要な研究文脈と未解決課題を復元する。

## 成果物
- `docs/session-handoff.md`

