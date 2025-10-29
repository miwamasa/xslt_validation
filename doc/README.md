# アルゴリズム解説ドキュメント

XSLT検証システムのアルゴリズムと実装に関する詳細なドキュメントです。

## ドキュメント一覧

### 1. [システム概要](./overview.md)
XSLT検証システム全体の概要、理論的基盤、アルゴリズムの構成、処理フローを説明します。

**内容:**
- システムアーキテクチャ
- 正規木文法（Regular Tree Grammar）
- マクロ木変換器（Macro Tree Transducer - MTT）
- 型保存性の定理
- 全体の処理フロー
- データフロー図

**対象読者:** システム全体を理解したい方、理論的背景を知りたい方

---

### 2. [XSDパーサーアルゴリズム](./xsd_parser.md)
XSDスキーマを正規木文法に変換するアルゴリズムの詳細解説です。

**内容:**
- アルゴリズムの詳細設計
- 複合型・単純型の処理
- sequence/choice/allの処理
- 型制約の抽出
- カーディナリティの処理
- 計算量解析
- 実装例

**対象読者:** XSD解析の詳細を知りたい開発者

---

### 3. [XSLTサブセットチェッカー](./xslt_subset_checker.md)
XSLTが許可されたサブセットに準拠しているかを検証するアルゴリズムです。

**内容:**
- 許可/禁止要素の定義
- 各要素の検証ロジック
- 複雑なXPathの検出
- エラーメッセージ設計
- 拡張可能性
- テストケース

**対象読者:** XSLTの制約を理解したい方、チェッカーをカスタマイズしたい開発者

---

### 4. [XSLT to MTT変換アルゴリズム](./mtt_converter.md)
XSLTをMacro Tree Transducer表現に変換するアルゴリズムの解説です。

**内容:**
- MTTの形式的定義
- テンプレート→状態の変換
- 各XSLT命令の処理
  - apply-templates
  - for-each
  - if/choose
  - リテラル要素
- 属性値テンプレートの処理
- MTTの形式的検証
- 最適化技法

**対象読者:** MTT変換の詳細を知りたい開発者、理論家

---

### 5. [型保存性検証アルゴリズム](./type_validator.md)
XSLT変換が型保存性を満たすかを検証するアルゴリズムです。

**内容:**
- 構造的帰納法による証明
- 構造検証
- 型制約検証
- カーディナリティ検証
- カバレッジマトリクス構築
- 高度な検証技法
  - パス条件解析
  - 反例生成
  - 形式的証明生成

**対象読者:** 型保存性検証の実装者、理論研究者

---

### 6. [前像計算アルゴリズム](./preimage_computation.md)
MTTによる変換の前像 pre_M(L(G_T)) を計算するアルゴリズムです。

**内容:**
- 前像の理論的背景
- 規則ごとの前像計算
- 制約の抽出
  - ガード条件からの制約
  - 型制約からの制約
  - 列挙型制約
- 出力妥当性の検証
- 入力パターンの構築
- 統計情報とカバレッジ分析
- 実用例
  - デバッグ支援
  - ドキュメント生成
  - テストケース生成

**対象読者:** 前像計算の実装者、XSLT開発者、理論研究者

---

### 7. [妥当性検証アルゴリズム](./validity_checking.md)
XSLT変換の妥当性を検証するアルゴリズムです。L(Src) ⊆ pre_T(L(Tgt)) を検証します。

**内容:**
- 理論的背景
  - 妥当性の定義
  - 前像による表現
  - 補集合との交差
- 詳細設計
  - ソースパターンの抽出
  - パターンカバレッジの確認
  - 反例の生成
- 補集合との交差チェック
- 計算量解析: O(n × m)
- 実装例
- 実用例
  - XSLT開発時の検証
  - リファクタリング時の回帰テスト
  - ドキュメント生成
  - CI/CDパイプライン統合

**対象読者:** 妥当性検証の実装者、XSLT開発者、理論研究者

---

### 8. [実装例とフローチャート](./examples.md)
実際の使用例、フローチャート、コード例、ユースケースをまとめたドキュメントです。

**内容:**
- 完全な使用例（ステップバイステップ）
- 詳細なフローチャート
  - 全体フロー
  - XSD解析フロー
  - MTT変換フロー
  - 型保存性検証フロー
- コード例
  - APIの使用
  - カスタム検証ルール
  - バッチ処理
- ユースケース
  - CI/CDパイプライン統合
  - Webサービス化
  - IDEプラグイン
- トラブルシューティング

**対象読者:** 実装する開発者、システムを利用したい方

---

## クイックナビゲーション

### 理論を学びたい
1. [システム概要](./overview.md) - 理論的基盤を理解
2. [型保存性検証](./type_validator.md) - 証明手法を学習
3. [前像計算](./preimage_computation.md) - 前像の理論を学習
4. [妥当性検証](./validity_checking.md) - 補集合との交差を学習

### 実装したい
1. [実装例](./examples.md) - まず使い方を確認
2. [XSDパーサー](./xsd_parser.md) - XSD処理の実装
3. [MTT変換](./mtt_converter.md) - XSLT変換の実装
4. [型保存性検証](./type_validator.md) - 検証ロジックの実装
5. [前像計算](./preimage_computation.md) - 前像計算の実装
6. [妥当性検証](./validity_checking.md) - 妥当性検証の実装

### 特定のアルゴリズムを理解したい
- XSD解析: [XSDパーサー](./xsd_parser.md)
- XSLT検証: [サブセットチェッカー](./xslt_subset_checker.md)
- XSLT変換: [MTT変換](./mtt_converter.md)
- 型検証: [型保存性検証](./type_validator.md)
- 前像計算: [前像計算](./preimage_computation.md)
- 妥当性検証: [妥当性検証](./validity_checking.md)

---

## 図表索引

### システムアーキテクチャ図
- [システム概要](./overview.md#システム概要) - 全体構成図
- [システム概要](./overview.md#処理フロー) - 処理フロー図

### フローチャート
- [実装例](./examples.md#全体フロー) - 全体処理フロー
- [実装例](./examples.md#xsd解析フロー) - XSD解析詳細フロー
- [実装例](./examples.md#mtt変換フロー) - MTT変換詳細フロー
- [実装例](./examples.md#型保存性検証フロー) - 検証詳細フロー

### アルゴリズム擬似コード
- [XSDパーサー](./xsd_parser.md#詳細設計) - XSD解析アルゴリズム
- [サブセットチェッカー](./xslt_subset_checker.md#詳細設計) - XSLT検証アルゴリズム
- [MTT変換](./mtt_converter.md#詳細設計) - MTT変換アルゴリズム
- [型保存性検証](./type_validator.md#詳細設計) - 型検証アルゴリズム
- [前像計算](./preimage_computation.md#詳細設計) - 前像計算アルゴリズム
- [妥当性検証](./validity_checking.md#詳細設計) - 妥当性検証アルゴリズム

---

## 記法について

### 形式的記法

**木文法:**
```
G = (N, Σ, P, S)
A → σ(B₁, ..., Bₙ)
```

**MTT:**
```
M = (Q, Σ_in, Σ_out, q_0, R)
q(σ(x₁, ..., xₙ)) → t
```

**型保存性:**
```
∀t ∈ L(G_S), M(t) ∈ L(G_T)
```

### 擬似コード記法

```
Algorithm: NAME
Input: parameters
Output: result

1. step1
2. IF condition:
3.     action
4. FOR EACH item IN collection:
5.     process(item)
6. RETURN result
```

### 記号の意味

| 記号 | 意味 |
|------|------|
| G | 木文法 |
| M | マクロ木変換器 |
| Σ | アルファベット（記号集合） |
| Q | 状態集合 |
| L(G) | 文法Gが生成する言語（木の集合） |
| → | 生成規則、変換規則 |
| ∈ | 所属 |
| ∀ | すべての |
| ∃ | 存在する |

---

## 参考文献

1. **Tree Automata**
   - Comon, H., et al. "Tree Automata Techniques and Applications" (2007)
   - [TATA Book](http://tata.gforge.inria.fr/)

2. **XDuce and XML Type Systems**
   - Hosoya, H., Pierce, B. "XDuce: A Statically Typed XML Processing Language" (2003)

3. **Tree Transducers**
   - Martens, W., Neven, F. "Typechecking Top-Down Uniform Unranked Tree Transducers" (2004)
   - Engelfriet, J. "Top-down tree transducers with regular look-ahead" (1977)

4. **XML Schema**
   - W3C XML Schema Definition Language (XSD) 1.1
   - [W3C XSD Specification](https://www.w3.org/TR/xmlschema11-1/)

5. **XSLT Specification**
   - W3C XSLT 2.0 and XPath 2.0
   - [W3C XSLT 2.0 Specification](https://www.w3.org/TR/xslt20/)

---

## 用語集

| 用語 | 説明 |
|------|------|
| 正規木文法 | 木構造を生成する文法 |
| マクロ木変換器 | パラメータ付きの木変換器 |
| 型保存性 | 変換が型情報を保存する性質 |
| 構造的帰納法 | 木の構造に基づく証明手法 |
| カーディナリティ | 要素の出現回数の制約 |
| 前像計算 | 出力集合から入力集合を逆算 |

---

## 更新履歴

- 2025-10-29: 妥当性検証追加
  - 妥当性検証アルゴリズムのドキュメント追加
  - L(Src) ⊆ pre_T(L(Tgt)) の検証
  - 補集合との交差アプローチ
  - 反例生成とカバレッジ分析

- 2025-10-29: 前像計算追加
  - 前像計算アルゴリズムのドキュメント追加
  - 理論的背景、実装、計算量解析、実用例

- 2024-01-XX: 初版作成
  - システム概要
  - XSDパーサーアルゴリズム
  - XSLTサブセットチェッカー
  - MTT変換アルゴリズム
  - 型保存性検証アルゴリズム
  - 実装例とフローチャート

---

## ライセンス

このドキュメントはMITライセンスの下で公開されています。

---

## 問い合わせ

質問や提案がある場合は、GitHubのIssueを作成してください。

[GitHub Issues](https://github.com/miwamasa/xslt_validation/issues)
