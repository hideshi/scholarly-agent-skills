---
description: 史料批判・文献解読における解釈飛躍・Quote Miningガード
globs: ["**/*.md", "**/*.tex"]
---

# 史料批判・解釈飛躍ガード (Source Criticism Rule)

## 目的
AI Agentが史料や文献テキストを要約・引用・解析する際、テキストの前後の文脈を無視した勝手な切り取り（Quote Mining）や過剰解釈（Overinterpretation）を防ぐ。

## 必須監査チェックリスト
エージェントがテキストの解釈や引用を生成・提案する際、以下の3項目を自発的にチェックすること：

1. **Context Safeguard（文脈の保護）**:
   - 引用した一文が、原典の章・節の主旨と逆の意味になっていないか確認する。
2. **Philological Validity（文献学的妥当性）**:
   - 訳語・用語の現代的意味を過去のテキストに無批判に当てはめていないか（時代錯誤・Anachronismのチェック）。
3. **Evidence Strength（根拠の強さ）**:
   - 1つの断片的記述から「〇〇時代全体で〇〇であった」といった過度な一般化（Overgeneralization）を行っていないか。
