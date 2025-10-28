# XSLT検証システム - アルゴリズム解説

## 目次

1. [システム概要](#システム概要)
2. [理論的基盤](#理論的基盤)
3. [アルゴリズムの構成](#アルゴリズムの構成)
4. [処理フロー](#処理フロー)

## システム概要

本システムは、XSLTの妥当性を理論的に検証するためのツールです。以下の4つの主要なアルゴリズムで構成されています：

```
┌─────────────────────────────────────────────────────────┐
│                  XSLT検証システム                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐      ┌─────────────────┐          │
│  │  Source XSD    │      │   Target XSD    │          │
│  └────────┬───────┘      └────────┬────────┘          │
│           │                       │                    │
│           ▼                       ▼                    │
│  ┌────────────────┐      ┌─────────────────┐          │
│  │  XSDParser     │      │   XSDParser     │          │
│  │  (Algorithm 1) │      │  (Algorithm 1)  │          │
│  └────────┬───────┘      └────────┬────────┘          │
│           │                       │                    │
│           ▼                       ▼                    │
│  ┌────────────────┐      ┌─────────────────┐          │
│  │ TreeGrammar_S  │      │ TreeGrammar_T   │          │
│  └────────┬───────┘      └────────┬────────┘          │
│           │                       │                    │
│           └───────────┬───────────┘                    │
│                       │                                │
│  ┌────────────────┐   │   ┌─────────────────┐         │
│  │     XSLT       │   │   │                 │         │
│  └────────┬───────┘   │   │                 │         │
│           │           │   │                 │         │
│           ▼           │   │                 │         │
│  ┌────────────────┐   │   │                 │         │
│  │ SubsetChecker  │   │   │                 │         │
│  │ (Algorithm 2)  │   │   │                 │         │
│  └────────┬───────┘   │   │                 │         │
│           │           │   │                 │         │
│           ▼           │   │                 │         │
│  ┌────────────────┐   │   │                 │         │
│  │ MTTConverter   │   │   │                 │         │
│  │ (Algorithm 3)  │   │   │                 │         │
│  └────────┬───────┘   │   │                 │         │
│           │           │   │                 │         │
│           ▼           ▼   ▼                 │         │
│  ┌─────────────────────────────────┐        │         │
│  │   TypePreservationValidator     │        │         │
│  │        (Algorithm 4)             │        │         │
│  └──────────────┬──────────────────┘        │         │
│                 │                           │         │
│                 ▼                           │         │
│  ┌─────────────────────────────────┐        │         │
│  │     検証結果 + 証明             │        │         │
│  └─────────────────────────────────┘        │         │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## 理論的基盤

### 1. 正規木文法 (Regular Tree Grammar)

XSDスキーマを形式的に表現するために使用します。

**定義:**
```
G = (N, Σ, P, S)

N: 非終端記号の集合（要素名）
Σ: 終端記号の集合（基本型）
P: 生成規則の集合
S: 開始記号
```

**例:**
```
Person → Person(Name, Age)
Name → string
Age → integer
```

### 2. マクロ木変換器 (Macro Tree Transducer - MTT)

XSLTの変換を形式的に表現します。

**定義:**
```
M = (Q, Σ_input, Σ_output, q_0, R)

Q: 状態の集合
Σ_input: 入力アルファベット
Σ_output: 出力アルファベット
q_0: 初期状態
R: 変換規則の集合
```

**変換規則の形式:**
```
q(σ(x₁, ..., xₙ)) → t

q: 状態
σ: 入力記号
x₁, ..., xₙ: 変数
t: 出力木（再帰呼び出しを含む）
```

### 3. 型保存性の定理

**定理:**
```
∀t ∈ L(G_S), M(t) ∈ L(G_T)
```

すなわち、ソーススキーマで有効な任意の木tを変換すると、必ずターゲットスキーマで有効な木が得られる。

**証明手法:** 構造的帰納法
1. 基底ケース: 葉ノード（プリミティブ型）の変換
2. 帰納ステップ: 複合ノードの変換

## アルゴリズムの構成

### Algorithm 1: XSD → TreeGrammar変換

**入力:** XSDスキーマ（XML文書）
**出力:** 正規木文法

**時間計算量:** O(n)（nはXSD内の要素数）

詳細: [xsd_parser.md](./xsd_parser.md)

### Algorithm 2: XSLTサブセットチェック

**入力:** XSLT文書
**出力:** 妥当性フラグ、エラーリスト、警告リスト

**時間計算量:** O(m)（mはXSLT内の要素数）

詳細: [xslt_subset_checker.md](./xslt_subset_checker.md)

### Algorithm 3: XSLT → MTT変換

**入力:** XSLT文書
**出力:** マクロ木変換器

**時間計算量:** O(m)（mはテンプレート数）

詳細: [mtt_converter.md](./mtt_converter.md)

### Algorithm 4: 型保存性検証

**入力:** TreeGrammar_S, TreeGrammar_T, MTT
**出力:** 検証結果、証明ステップ

**時間計算量:** O(|P_S| × |P_T| × |R|)
- |P_S|: ソース文法の生成規則数
- |P_T|: ターゲット文法の生成規則数
- |R|: MTTの変換規則数

詳細: [type_validator.md](./type_validator.md)

## 処理フロー

### 全体フロー

```
START
  │
  ├─→ [入力受付]
  │     - Source XSD
  │     - Target XSD
  │     - XSLT
  │
  ├─→ [Phase 1: XSLTサブセットチェック]
  │     │
  │     ├─→ parse_xslt()
  │     ├─→ check_allowed_elements()
  │     ├─→ check_disallowed_features()
  │     │
  │     └─→ valid? ─no→ [エラー返却] → END
  │            │
  │           yes
  │            │
  ├─→ [Phase 2: XSD解析]
  │     │
  │     ├─→ parse_source_xsd()
  │     │     └─→ TreeGrammar_S
  │     │
  │     └─→ parse_target_xsd()
  │           └─→ TreeGrammar_T
  │
  ├─→ [Phase 3: MTT生成]
  │     │
  │     └─→ convert_xslt_to_mtt()
  │           └─→ MTT
  │
  ├─→ [Phase 4: 型保存性検証]
  │     │
  │     ├─→ validate_structure()
  │     ├─→ validate_type_constraints()
  │     ├─→ validate_cardinality()
  │     └─→ generate_proof()
  │
  └─→ [結果出力]
        - 検証結果
        - 証明ステップ
        - カバレッジマトリクス
        │
       END
```

### データフロー

```
XSD (XML) ──┐
            │
            ├──→ [Parser] ──→ AST ──→ [Grammar Generator] ──→ TreeGrammar
            │
            └──→ [Type Extractor] ──→ Type Constraints


XSLT (XML) ─┐
            │
            ├──→ [Subset Checker] ──→ Validation Result
            │
            └──→ [MTT Converter] ──→ States + Rules ──→ MTT


TreeGrammar_S ─┐
               │
TreeGrammar_T ─┼──→ [Type Validator] ──→ Proof + Coverage
               │
MTT ───────────┘
```

## 実装における最適化

### 1. メモ化

- XSD要素の解析結果をキャッシュ
- 型制約の検証結果をメモ化

### 2. 早期終了

- XSLTサブセットチェックで失敗時、即座に処理を中断
- 型制約違反発見時、詳細検証をスキップ可能

### 3. 並列処理の可能性

- ソースXSDとターゲットXSDの解析を並列実行可能
- 複数の生成規則の検証を並列化可能

## 制限事項と今後の拡張

### 現在の制限

1. **XSLTサブセット**: 限定的な要素のみサポート
2. **XPath**: 複雑なXPath式は警告のみ
3. **型チェック**: 基本型の互換性チェックのみ

### 今後の拡張案

1. **完全な前像計算**: MTTの前像を厳密に計算
2. **オートマトン包含チェック**: 正規木オートマトンの包含関係を検証
3. **反例生成**: 型保存性が満たされない場合の具体例を生成

## 参考文献

1. Comon, H., et al. "Tree Automata Techniques and Applications" (2007)
2. Hosoya, H., Pierce, B. "XDuce: A Statically Typed XML Processing Language" (2003)
3. Martens, W., Neven, F. "Typechecking Top-Down Uniform Unranked Tree Transducers" (2004)

## 関連ドキュメント

- [XSDパーサーアルゴリズム](./xsd_parser.md)
- [XSLTサブセットチェッカー](./xslt_subset_checker.md)
- [MTT変換アルゴリズム](./mtt_converter.md)
- [型保存性検証アルゴリズム](./type_validator.md)
- [実装例とフローチャート](./examples.md)
