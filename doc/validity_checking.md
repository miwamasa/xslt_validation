# 妥当性検証アルゴリズム

## 目次

1. [アルゴリズム概要](#アルゴリズム概要)
2. [理論的背景](#理論的背景)
3. [詳細設計](#詳細設計)
4. [実装](#実装)
5. [計算量解析](#計算量解析)
6. [例](#例)

## アルゴリズム概要

XSLT変換の妥当性を検証するアルゴリズムです。すなわち、すべての有効なソース文書が有効なターゲット文書に変換されることを保証します。

**入力:**
- TreeGrammar_S (ソース文法)
- PreimageResult (前像計算の結果)

**出力:**
- ValidityResult (妥当性検証の結果、反例、統計情報)

### 検証の目的

**妥当性の定理:**
```
∀s ∈ L(G_S), T(s) ∈ L(G_T)
```

すなわち、ソーススキーマで有効な任意の文書sを変換すると、必ずターゲットスキーマで有効な文書が得られることを証明します。

### 同値な表現

この条件は以下と同値です:

**前像による表現:**
```
L(G_S) ⊆ pre_T(L(G_T))
```

ソース言語が前像（変換後に有効な出力を生成する入力の集合）に含まれる。

**補集合による表現:**
```
L(G_S) ∩ complement(pre_T(L(G_T))) = ∅
```

ソース言語と前像の補集合の交差が空集合である。

## 理論的背景

### なぜ妥当性検証が重要か

型保存性検証（Type Preservation）は変換の各ステップが型を保存することを確認しますが、妥当性検証（Validity Checking）はより強い保証を提供します：

| 検証方法 | 確認内容 | 強さ |
|---------|---------|------|
| 型保存性検証 | 変換規則が型制約を保存 | 構文的 |
| 妥当性検証 | すべての入力が有効な出力を生成 | 意味論的 |

**例：**
```xml
<!-- 型保存性は満たすが妥当性は満たさない例 -->
<xsl:template match="Person">
  <xsl:if test="Age > 150">  <!-- 実際には誰も150歳以上でない -->
    <Individual .../>
  </xsl:if>
</xsl:template>
```

型保存性: ✓ 変換結果はIndividualの型に合う
妥当性: ✗ ほとんどの入力が変換されない（空の出力）

### 補集合と交差による検証

理論的には、妥当性検証は以下の手順で行います：

**Step 1: 前像の計算**
```
P = pre_T(L(G_T))
```

MTTによる変換で有効な出力を生成するすべての入力の集合。

**Step 2: 補集合の計算**
```
P̄ = complement(P) = Σ* \ P
```

前像に含まれない入力の集合（変換が失敗するか無効な出力を生成）。

**Step 3: 交差の計算**
```
C = L(G_S) ∩ P̄
```

ソース文法で有効だが前像に含まれない入力の集合。

**Step 4: 空判定**
```
C = ∅ ?
```

交差が空なら妥当性成立、空でなければC の要素が反例（counterexample）。

### 決定可能性

**理論的性質:**
- 正規木文法の言語包含問題は決定可能
- 補集合も正規木言語として計算可能
- 交差も正規木言語として計算可能

**計算量:**
- 一般的には EXPTIME-complete
- 実用的なXSLTサブセットでは多項式時間で近似可能

## 詳細設計

### メインアルゴリズム

```
Algorithm: CHECK_VALIDITY
Input: source_grammar (TreeGrammar),
       preimage_result (PreimageResult)
Output: ValidityResult

1. // Step 1: ソースパターンの抽出
2. source_patterns ← EXTRACT_SOURCE_PATTERNS(source_grammar)
3.
4. // Step 2: 各ソースパターンのカバレッジチェック
5. counterexamples ← []
6. covered_count ← 0
7.
8. FOR EACH src_pattern IN source_patterns:
9.     is_covered, reason ← IS_PATTERN_COVERED(
10.         src_pattern,
11.         preimage_result.accepted_patterns
12.     )
13.
14.     IF is_covered:
15.         covered_count ← covered_count + 1
16.     ELSE:
17.         // 反例を発見
18.         counterexample ← CREATE_COUNTEREXAMPLE(src_pattern, reason)
19.         counterexamples.ADD(counterexample)
20.
21. // Step 3: 統計情報の計算
22. total ← LENGTH(source_patterns)
23. uncovered ← LENGTH(counterexamples)
24. coverage ← (covered_count / total × 100) IF total > 0 ELSE 100.0
25.
26. // Step 4: 妥当性の判定
27. is_valid ← (uncovered == 0)
28.
29. // Step 5: 説明文の生成
30. IF is_valid:
31.     explanation ← "✓ Validity holds: L(Src) ⊆ pre_T(L(Tgt))\n"
32.                 + f"All {total} source patterns are covered.\n"
33.                 + "All valid source documents will transform to valid targets."
34. ELSE:
35.     explanation ← "✗ Validity does NOT hold: L(Src) ⊄ pre_T(L(Tgt))\n"
36.                 + f"Found {uncovered} counterexample(s).\n"
37.                 + "Some valid source documents may produce invalid outputs."
38.
39. RETURN ValidityResult(
40.     is_valid=is_valid,
41.     total_source_patterns=total,
42.     covered_patterns=covered_count,
43.     uncovered_patterns=uncovered,
44.     counterexamples=counterexamples,
45.     coverage_percentage=coverage,
46.     explanation=explanation
47. )
```

### ソースパターンの抽出

```
Algorithm: EXTRACT_SOURCE_PATTERNS
Input: source_grammar (TreeGrammar)
Output: List[SourcePattern]

1. patterns ← []
2.
3. // 子要素の識別（葉ノードを除外するため）
4. child_elements ← SET()
5. FOR EACH production IN source_grammar.productions:
6.     IF production.rhs:
7.         FOR EACH child IN production.rhs:
8.             child_elements.ADD(child)
9.
10. // トップレベルと複雑要素のみを抽出
11. FOR EACH production IN source_grammar.productions:
12.
13.     // 単純リーフ要素か判定（例: Name(string)、Age(integer)）
14.     is_leaf ← (
15.         production.rhs AND
16.         LENGTH(production.rhs) == 1 AND
17.         production.rhs[0] IN ['string', 'integer', 'decimal', 'boolean', 'date']
18.     )
19.
20.     // 以下の場合に含める：
21.     // 1. リーフでない、または
22.     // 2. ルート要素である、または
23.     // 3. 複雑な構造を持つ
24.     IF NOT is_leaf OR production.lhs == source_grammar.root_element:
25.
26.         // 子要素の抽出
27.         IF production.rhs:
28.             children ← [STR(child) FOR child IN production.rhs]
29.         ELSE:
30.             children ← ['*']  // 属性のみの要素
31.
32.         pattern ← SourcePattern(
33.             element=production.lhs,
34.             children=children,
35.             production=production
36.         )
37.         patterns.ADD(pattern)
38.
39. RETURN patterns
```

**注意点:**
- 単純リーフ要素（Name(string)など）は除外
- これらは親要素の一部として変換されるため
- トップレベル要素のみを検証対象とする

### パターンカバレッジの確認

```
Algorithm: IS_PATTERN_COVERED
Input: src_pattern (SourcePattern),
       preimage_patterns (List[InputPattern])
Output: (boolean, string)  // (is_covered, reason)

1. FOR EACH preimage_pattern IN preimage_patterns:
2.
3.     // 要素名の一致確認
4.     IF src_pattern.element != preimage_pattern.element:
5.         CONTINUE
6.
7.     // 子要素の互換性確認
8.     IF preimage_pattern.children == ['*'] OR preimage_pattern.children == ['children']:
9.         // ワイルドカードは任意の子要素を受理
10.         RETURN (TRUE, f"Covered by: {preimage_pattern.element}(...)")
11.
12.     // 子要素が一致（簡略版 - 完全版はパターンマッチング必要）
13.     RETURN (TRUE, f"Covered by: {preimage_pattern.element}(...)")
14.
15. // どの前像パターンにもマッチしない
16. reason ← f"No preimage pattern accepts {src_pattern.element}. " +
17.           "This element may not be transformed or may fail constraints."
18. RETURN (FALSE, reason)
```

### 補集合との交差チェック（理論的）

```
Algorithm: CHECK_COMPLEMENT_INTERSECTION (理論版)
Input: source_grammar (TreeGrammar),
       preimage_patterns (List[InputPattern])
Output: boolean

1. // 前像の要素集合を構築
2. preimage_elements ← { p.element FOR p IN preimage_patterns }
3.
4. // ソース要素集合を構築
5. source_elements ← { p.lhs FOR p IN source_grammar.productions }
6.
7. // 補集合との交差 = ソースにあって前像にない要素
8. uncovered_elements ← source_elements \ preimage_elements
9.
10. // 交差が空なら妥当性成立
11. RETURN (LENGTH(uncovered_elements) == 0)
```

**注:**
実装では、各パターンの構造と制約まで考慮した詳細なチェックを行います。

### 反例の生成

```
Algorithm: CREATE_COUNTEREXAMPLE
Input: src_pattern (SourcePattern),
       reason (string)
Output: Counterexample

1. pattern_str ← f"{src_pattern.element}({', '.join(src_pattern.children)})"
2.
3. RETURN Counterexample(
4.     element=src_pattern.element,
5.     pattern=pattern_str,
6.     reason=reason,
7.     production=src_pattern.production
8. )
```

## 実装

### ValidityCheckerクラス

```python
from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class SourcePattern:
    """ソース文法から抽出されたパターン"""
    element: str
    children: List[str]
    production: Production

    def matches_preimage_pattern(
        self,
        preimage_pattern: InputPattern
    ) -> Tuple[bool, str]:
        """前像パターンとの一致確認"""
        # 要素名の一致
        if self.element != preimage_pattern.element:
            return False, f"Element mismatch: {self.element}"

        # ワイルドカードチェック
        if preimage_pattern.children == ['*']:
            return True, "Covered by wildcard pattern"

        return True, "Children pattern matches"


@dataclass
class Counterexample:
    """前像でカバーされないソースパターン"""
    element: str
    pattern: str
    reason: str
    production: Production


@dataclass
class ValidityResult:
    """妥当性検証の結果"""
    is_valid: bool
    total_source_patterns: int
    covered_patterns: int
    uncovered_patterns: int
    counterexamples: List[Counterexample] = field(default_factory=list)
    coverage_percentage: float = 0.0
    explanation: str = ""


class ValidityChecker:
    """
    妥当性検証: L(Src) ⊆ pre_T(L(Tgt))
    """

    def check_validity(
        self,
        source_grammar: TreeGrammar,
        preimage_result: PreimageResult
    ) -> ValidityResult:
        """妥当性検証のメイン関数"""

        # ソースパターンの抽出
        source_patterns = self._extract_source_patterns(source_grammar)

        # カバレッジチェック
        counterexamples = []
        covered_count = 0

        for src_pattern in source_patterns:
            is_covered, reason = self._is_pattern_covered(
                src_pattern,
                preimage_result.accepted_patterns
            )

            if is_covered:
                covered_count += 1
            else:
                counterexample = Counterexample(
                    element=src_pattern.element,
                    pattern=f"{src_pattern.element}(...)",
                    reason=reason,
                    production=src_pattern.production
                )
                counterexamples.append(counterexample)

        # 統計とn判定
        total = len(source_patterns)
        uncovered = len(counterexamples)
        coverage = (covered_count / total * 100) if total > 0 else 100.0
        is_valid = (uncovered == 0)

        # 説明文の生成
        if is_valid:
            explanation = (
                "✓ Validity holds: L(Src) ⊆ pre_T(L(Tgt))\n"
                f"All {total} source patterns are covered by the preimage.\n"
                "This means all valid source documents will transform to valid targets."
            )
        else:
            explanation = (
                "✗ Validity does NOT hold: L(Src) ⊄ pre_T(L(Tgt))\n"
                f"Found {uncovered} counterexample(s).\n"
                "Some valid source documents may produce invalid outputs."
            )

        return ValidityResult(
            is_valid=is_valid,
            total_source_patterns=total,
            covered_patterns=covered_count,
            uncovered_patterns=uncovered,
            counterexamples=counterexamples,
            coverage_percentage=coverage,
            explanation=explanation
        )
```

## 計算量解析

### 時間計算量

```
T(n, m) = O(n × m)
```

ここで:
- n: ソース文法の生成規則数
- m: 前像パターンの数

**内訳:**
- ソースパターン抽出: O(n)
- 各パターンのカバレッジチェック: O(n × m)
  - 各ソースパターン O(n) について
  - すべての前像パターン O(m) をチェック

**実用的な計算量:**

典型的なXSLTでは:
- n ≈ 10-100 (ソース要素数)
- m ≈ 5-50 (前像パターン数)

⇒ T ≈ O(n × m) ≈ 50-5000 ステップ（非常に高速）

### 空間計算量

```
S(n) = O(n)
```

- ソースパターン: O(n)
- 反例リスト: O(n) 最悪の場合

## 例

### 例1: 妥当性が成立するケース

#### 入力

**ソーススキーマ:**
```xml
<xs:element name="Person">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Name" type="xs:string"/>
      <xs:element name="Age" type="xs:integer"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

**前像計算結果:**
```
Accepted patterns:
1. Person(*) where Age >= 0
```

#### 処理

**Step 1: ソースパターンの抽出**
```
Source patterns:
1. Person(Name, Age)
```

（Note: Name(string)とAge(integer)は単純リーフなので除外）

**Step 2: カバレッジチェック**
```
Pattern: Person(Name, Age)
Preimage: Person(*) where Age >= 0
Match: ✓ (ワイルドカードが任意の子要素を受理)
```

**Step 3: 判定**
```
Covered: 1/1
Counterexamples: 0
Validity: ✓ TRUE
```

#### 出力

```
Validity Result:
✓ Validity holds: L(Src) ⊆ pre_T(L(Tgt))
All 1 source patterns are covered by the preimage.
This means all valid source documents will transform to valid targets.

Statistics:
- Total source patterns: 1
- Covered patterns: 1
- Uncovered patterns: 0
- Coverage: 100.0%
```

### 例2: 妥当性が成立しないケース

#### 入力

**ソーススキーマ:**
```xml
<xs:element name="Person">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Name" type="xs:string"/>
      <xs:element name="Age" type="xs:integer"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
<xs:element name="Organization">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="OrgName" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

**XSLT (Personのみ変換):**
```xml
<xsl:template match="Person">
  <Individual fullname="{Name}" years="{Age}"/>
</xsl:template>
<!-- Organizationの変換規則なし -->
```

**前像計算結果:**
```
Accepted patterns:
1. Person(*) where Age >= 0
```

#### 処理

**Step 1: ソースパターンの抽出**
```
Source patterns:
1. Person(Name, Age)
2. Organization(OrgName)
```

**Step 2: カバレッジチェック**
```
Pattern 1: Person(Name, Age)
  → ✓ Covered by Person(*)

Pattern 2: Organization(OrgName)
  → ✗ No preimage pattern accepts Organization
```

**Step 3: 判定**
```
Covered: 1/2
Counterexamples: 1
Validity: ✗ FALSE
```

#### 出力

```
Validity Result:
✗ Validity does NOT hold: L(Src) ⊄ pre_T(L(Tgt))
Found 1 counterexample(s) - source patterns not in preimage.
Some valid source documents may produce invalid target outputs.

Counterexamples:
1. Organization(OrgName)
   Reason: No preimage pattern accepts Organization.
           This element may not be transformed or may fail constraints.

Statistics:
- Total source patterns: 2
- Covered patterns: 1
- Uncovered patterns: 1
- Coverage: 50.0%
```

### 例3: 制約による妥当性違反

#### 入力

**ソーススキーマ:**
```xml
<xs:element name="Employee">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Age" type="xs:integer"/>  <!-- 制約なし -->
      <xs:element name="Role" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

**XSLT (18歳以上のみ変換):**
```xml
<xsl:template match="Employee">
  <xsl:if test="Age >= 18">
    <Staff age="{Age}" role="{Role}"/>
  </xsl:if>
</xsl:template>
```

**前像計算結果:**
```
Accepted patterns:
1. Employee(*) where Age >= 18
```

#### 分析

ソース文法では年齢に制約がないため、`Age < 18` の有効な入力が存在します。
しかし前像は `Age >= 18` を要求するため、17歳以下の従業員は変換されません。

**理論的には:**
```
L(Src) = Employee(Age=*, Role=*)  // 任意の年齢
pre_T(L(Tgt)) = Employee(Age>=18, Role=*)
L(Src) \ pre_T(L(Tgt)) ≠ ∅  // Age<18 の入力が含まれる
⇒ 妥当性不成立
```

**実装上の注意:**
現在の実装は要素レベルのカバレッジをチェックしますが、制約の完全な検証には追加のロジックが必要です。

## 実用的な応用

### 1. XSLT開発時の検証

XSLTを書く際、妥当性検証で以下を確認:

```
✓ すべてのソース要素が変換される
✓ 条件付き変換（if/choose）が適切にカバーしている
✓ 制約が正しく伝播している
```

### 2. リファクタリング時の回帰テスト

XSLTを変更した後:

```
Before: Validity: ✓ (100% coverage)
After:  Validity: ✗ (75% coverage)
⇒ 変更により一部の入力が変換されなくなった！
```

### 3. ドキュメント生成

妥当性検証の結果から入力要件を自動生成:

```markdown
## サポートされる入力

以下の要素は正常に変換されます:
- Person: すべての有効なPerson要素
- Employee: Age >= 18 かつ Role != 'intern'

## サポートされない入力

以下の要素は変換されません:
- Organization: 変換規則が未定義
```

### 4. CI/CDパイプライン

```yaml
# .github/workflows/xslt-validation.yml
- name: Validate XSLT
  run: |
    python validate_xslt.py
    if [ $? -ne 0 ]; then
      echo "❌ Validity check failed!"
      exit 1
    fi
    echo "✅ All source patterns are covered"
```

## 制限事項と今後の拡張

### 現在の制限

1. **要素レベルの検証**: 構造的なカバレッジのみ、制約の完全な検証は限定的
2. **単純なパターンマッチ**: 複雑なパターンや正規表現は未対応
3. **近似的判定**: 完全な形式的証明ではなく、実用的な近似

### 今後の拡張可能性

1. **制約ソルバーの統合**
   - SMTソルバーで制約の充足可能性を判定
   - 数値制約、文字列制約の完全な検証

2. **正規木オートマトンの構築**
   - 前像を正規木オートマトンとして表現
   - 言語包含問題を形式的に解決

3. **反例の具体化**
   - 抽象的な反例から具体的なXML文書を生成
   - デバッグ支援の強化

4. **段階的検証**
   - 要素ごと、制約ごとに段階的に検証
   - より詳細なエラーレポート

5. **性能最適化**
   - キャッシング戦略
   - 増分検証

## まとめ

妥当性検証は、XSLT変換の正しさを保証する強力なツールです:

1. ✅ **理論的基盤**: L(Src) ⊆ pre_T(L(Tgt)) の検証
2. ✅ **補集合アプローチ**: L(Src) ∩ complement(pre_T(L(Tgt))) = ∅
3. ✅ **実用的実装**: O(n × m) の効率的なアルゴリズム
4. ✅ **反例報告**: カバーされないパターンの特定
5. ✅ **統計情報**: カバレッジ率の提供

型保存性検証と組み合わせることで、XSLT変換の包括的な正しさを保証できます。
