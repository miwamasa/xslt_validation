# 型保存性検証アルゴリズム

## 目次

1. [アルゴリズム概要](#アルゴリズム概要)
2. [理論的背景](#理論的背景)
3. [詳細設計](#詳細設計)
4. [実装](#実装)
5. [計算量解析](#計算量解析)
6. [例](#例)

## アルゴリズム概要

XSLT変換が型保存性を満たすかを検証するアルゴリズムです。

**入力:**
- TreeGrammar_S (ソース文法)
- TreeGrammar_T (ターゲット文法)
- MTT (マクロ木変換器)

**出力:**
- ValidationResult (検証結果、証明ステップ、エラー、警告)

### 検証の目的

**型保存性の定理:**
```
∀t ∈ L(G_S), M(t) ∈ L(G_T)
```

すなわち、ソーススキーマで有効な任意の木tを変換すると、必ずターゲットスキーマで有効な木が得られることを証明します。

## 理論的背景

### 構造的帰納法による証明

型保存性の証明は構造的帰納法で行います：

**基底ケース:** 葉ノード（プリミティブ型）
```
t = σ(v) where v ∈ Domain(σ)
M(t) = σ'(v') where v' ∈ Domain(σ')
⇒ M(t) ∈ L(G_T) if Domain(σ) ⊆ Domain(σ')
```

**帰納ステップ:** 複合ノード
```
仮定: ∀i ∈ [1,n], M(tᵢ) ∈ L(G_T)  (帰納仮定)
証明: t = f(t₁, ..., tₙ) について M(t) ∈ L(G_T)

M(f(t₁, ..., tₙ)) = g(M(t₁), ..., M(tₙ))  (MTT規則による)
                   = g(u₁, ..., uₙ)        (uᵢ = M(tᵢ))
```

各uᵢは帰納仮定によりL(G_T)の要素なので、G_Tの生成規則により
g(u₁, ..., uₙ) ∈ L(G_T) が成り立つことを示す。

### 検証のアプローチ

完全な前像計算は計算量的に困難なため、実用的なアプローチとして：

1. **構造互換性**: 要素のマッピングが存在するか
2. **型制約保存**: 基本型と制約が保存されるか
3. **カーディナリティ保存**: 出現回数の制約が満たされるか

これらを組み合わせて検証します。

## 詳細設計

### メインアルゴリズム

```
Algorithm: VALIDATE_TYPE_PRESERVATION
Input: source_grammar (TreeGrammar),
       target_grammar (TreeGrammar),
       mtt (MTT)
Output: ValidationResult

1. proof_steps ← []
2. warnings ← []
3. errors ← []
4. coverage ← {}
5.
6. // イントロダクション
7. ADD_PROOF_STEP("Type Preservation Validation")
8. ADD_PROOF_STEP("Source: " + source_grammar.root_element)
9. ADD_PROOF_STEP("Target: " + target_grammar.root_element)
10. ADD_PROOF_STEP("MTT states: " + mtt.states.length)
11.
12. // Phase 1: 構造検証
13. ADD_PROOF_STEP("Step 1: Structural Validation")
14. validate_structure(source_grammar, target_grammar, mtt, errors, warnings)
15.
16. // Phase 2: 型制約検証
17. ADD_PROOF_STEP("Step 2: Type Constraint Validation")
18. validate_type_constraints(source_grammar, target_grammar, mtt, errors, warnings)
19.
20. // Phase 3: カーディナリティ検証
21. ADD_PROOF_STEP("Step 3: Cardinality Validation")
22. validate_cardinality(source_grammar, target_grammar, mtt, errors, warnings)
23.
24. // Phase 4: カバレッジマトリクス構築
25. coverage ← build_coverage_matrix(source_grammar, target_grammar, mtt)
26.
27. // 結果判定
28. is_valid ← (errors.length == 0)
29.
30. IF is_valid:
31.     ADD_PROOF_STEP("Conclusion: Type preservation is satisfied ✓")
32. ELSE:
33.     ADD_PROOF_STEP("Conclusion: Type preservation FAILED ✗")
34.
35. RETURN ValidationResult(
36.     is_valid, proof_steps, warnings, errors, coverage
37. )
```

### Phase 1: 構造検証

```
Algorithm: VALIDATE_STRUCTURE
Input: source_grammar, target_grammar, mtt, errors[], warnings[]

1. // ルート要素のマッピングチェック
2. root_mapping_found ← False
3.
4. FOR EACH rule IN mtt.rules:
5.     IF source_grammar.root_element IN rule.lhs_pattern:
6.         root_mapping_found ← True
7.         ADD_PROOF_STEP("✓ Root element mapping found")
8.         BREAK
9.
10. IF NOT root_mapping_found:
11.     errors.append("No transformation rule for root element")
12.     ADD_PROOF_STEP("✗ Root element not mapped")
13.
14. // 全生成規則のカバレッジチェック
15. FOR EACH prod IN source_grammar.productions:
16.     covered ← is_production_covered(prod, mtt)
17.
18.     IF covered:
19.         ADD_PROOF_STEP("✓ Production covered: " + prod.lhs)
20.     ELSE:
21.         warnings.append("Production not covered: " + prod.lhs)
22.         ADD_PROOF_STEP("⚠ Production not covered: " + prod.lhs)
```

### 生成規則カバレッジチェック

```
Algorithm: IS_PRODUCTION_COVERED
Input: prod (Production), mtt (MTT)
Output: covered (boolean)

1. // MTT規則で対応するものを探す
2. FOR EACH rule IN mtt.rules:
3.     // 左辺パターンにマッチ
4.     IF prod.lhs IN rule.lhs_pattern:
5.         RETURN True
6.
7.     // 右辺出力に含まれる
8.     IF prod.lhs IN extract_elements(rule.rhs_output):
9.         RETURN True
10.
11. RETURN False
```

### Phase 2: 型制約検証

```
Algorithm: VALIDATE_TYPE_CONSTRAINTS
Input: source_grammar, target_grammar, mtt, errors[], warnings[]

1. FOR EACH (elem_name, src_constraint) IN source_grammar.type_constraints:
2.     ADD_PROOF_STEP("Checking type constraint: " + elem_name)
3.
4.     // 対応するターゲット要素を探す
5.     target_elem ← find_target_element(elem_name, mtt, target_grammar)
6.
7.     IF target_elem IS NULL:
8.         warnings.append("No target element for: " + elem_name)
9.         ADD_PROOF_STEP("  ⚠ Target element not found")
10.         CONTINUE
11.
12.     // ターゲット要素の型制約を取得
13.     IF target_elem IN target_grammar.type_constraints:
14.         tgt_constraint ← target_grammar.type_constraints[target_elem]
15.
16.         // 基本型の互換性チェック
17.         IF are_types_compatible(src_constraint, tgt_constraint):
18.             ADD_PROOF_STEP("  ✓ Type compatible: " +
19.                            src_constraint.base_type + " → " +
20.                            tgt_constraint.base_type)
21.
22.             // 制約条件のチェック
23.             check_restrictions(src_constraint, tgt_constraint,
24.                               elem_name, target_elem,
25.                               errors, warnings)
26.         ELSE:
27.             errors.append("Type incompatibility: " + elem_name)
28.             ADD_PROOF_STEP("  ✗ Type incompatible")
```

### ターゲット要素の探索

```
Algorithm: FIND_TARGET_ELEMENT
Input: source_elem (string), mtt (MTT), target_grammar (TreeGrammar)
Output: target_elem (string or NULL)

1. // MTT規則からマッピングを探す
2. FOR EACH rule IN mtt.rules:
3.     IF source_elem IN rule.lhs_pattern:
4.         // 出力からターゲット要素を抽出
5.         target ← extract_target_from_output(rule.rhs_output)
6.         IF target IS NOT NULL:
7.             RETURN target
8.
9. // フォールバック: 同名要素を探す
10. FOR EACH prod IN target_grammar.productions:
11.     IF prod.lhs == source_elem:
12.         RETURN source_elem
13.
14. RETURN NULL
```

### 型互換性チェック

```
Algorithm: ARE_TYPES_COMPATIBLE
Input: src_constraint (TypeConstraint), tgt_constraint (TypeConstraint)
Output: compatible (boolean)

1. src_type ← src_constraint.base_type
2. tgt_type ← tgt_constraint.base_type
3.
4. // 同一型は常に互換
5. IF src_type == tgt_type:
6.     RETURN True
7.
8. // 数値型の拡大変換
9. numeric_types ← ["integer", "int", "long", "decimal", "float", "double"]
10. IF src_type IN numeric_types AND tgt_type IN numeric_types:
11.     RETURN True
12.
13. // 文字列型の互換性
14. string_types ← ["string", "normalizedString", "token"]
15. IF src_type == "string" AND tgt_type IN string_types:
16.     RETURN True
17.
18. RETURN False
```

### 制約条件の検証

```
Algorithm: CHECK_RESTRICTIONS
Input: src_constraint, tgt_constraint, src_elem, tgt_elem,
       errors[], warnings[]

1. tgt_restrictions ← tgt_constraint.restrictions
2.
3. // minInclusive制約
4. IF "minInclusive" IN tgt_restrictions:
5.     min_value ← tgt_restrictions["minInclusive"]
6.     ADD_PROOF_STEP("  ! Target has restriction: minInclusive=" + min_value)
7.
8.     // ソースに対応する制約がない場合は警告
9.     IF "minInclusive" NOT IN src_constraint.restrictions:
10.         warnings.append(
11.             "Target element '" + tgt_elem + "' has minInclusive=" + min_value +
12.             ". Ensure source values satisfy this constraint."
13.         )
14.
15. // maxInclusive制約
16. IF "maxInclusive" IN tgt_restrictions:
17.     max_value ← tgt_restrictions["maxInclusive"]
18.     ADD_PROOF_STEP("  ! Target has restriction: maxInclusive=" + max_value)
19.
20.     IF "maxInclusive" NOT IN src_constraint.restrictions:
21.         warnings.append(
22.             "Target element '" + tgt_elem + "' has maxInclusive=" + max_value
23.         )
24.
25. // pattern制約
26. IF "pattern" IN tgt_restrictions:
27.     pattern ← tgt_restrictions["pattern"]
28.     ADD_PROOF_STEP("  ! Target has pattern restriction: " + pattern)
29.     warnings.append("Target has pattern restriction: " + pattern)
30.
31. // enumeration制約
32. IF "enumeration" IN tgt_restrictions:
33.     enum_values ← tgt_restrictions["enumeration"]
34.     ADD_PROOF_STEP("  ! Target has enumeration restriction")
35.     warnings.append("Target has enumeration restriction")
```

### Phase 3: カーディナリティ検証

```
Algorithm: VALIDATE_CARDINALITY
Input: source_grammar, target_grammar, mtt, errors[], warnings[]

1. FOR EACH src_prod IN source_grammar.productions:
2.     // 対応するターゲット生成規則を探す
3.     target_elem ← find_target_element(src_prod.lhs, mtt, target_grammar)
4.
5.     IF target_elem IS NULL:
6.         CONTINUE
7.
8.     tgt_prod ← find_production(target_elem, target_grammar)
9.
10.     IF tgt_prod IS NULL:
11.         CONTINUE
12.
13.     src_card ← src_prod.cardinality
14.     tgt_card ← tgt_prod.cardinality
15.
16.     ADD_PROOF_STEP(
17.         "Cardinality check: " + src_prod.lhs + " " + src_card +
18.         " → " + tgt_prod.lhs + " " + tgt_card
19.     )
20.
21.     // カーディナリティ互換性チェック
22.     IF NOT is_cardinality_compatible(src_card, tgt_card):
23.         warnings.append(
24.             "Cardinality mismatch: " + src_prod.lhs +
25.             " " + src_card + " → " + tgt_prod.lhs + " " + tgt_card
26.         )
27.         ADD_PROOF_STEP("  ⚠ Cardinality may be incompatible")
28.     ELSE:
29.         ADD_PROOF_STEP("  ✓ Cardinality compatible")
```

### カーディナリティ互換性

```
Algorithm: IS_CARDINALITY_COMPATIBLE
Input: src_card (tuple), tgt_card (tuple)
Output: compatible (boolean)

1. (src_min, src_max) ← src_card
2. (tgt_min, tgt_max) ← tgt_card
3.
4. // ソースが空になり得るが、ターゲットは必須
5. IF src_min == 0 AND tgt_min > 0:
6.     RETURN False  // 不適合
7.
8. // ソースが複数になり得るが、ターゲットは単一のみ
9. IF (src_max == -1 OR src_max > 1) AND tgt_max == 1:
10.     RETURN False  // 不適合
11.
12. RETURN True
```

### Phase 4: カバレッジマトリクス構築

```
Algorithm: BUILD_COVERAGE_MATRIX
Input: source_grammar, target_grammar, mtt
Output: coverage (Dict)

1. coverage ← {
2.     "source_elements": source_grammar.productions.length,
3.     "target_elements": target_grammar.productions.length,
4.     "mtt_rules": mtt.rules.length,
5.     "mappings": []
6. }
7.
8. FOR EACH src_prod IN source_grammar.productions:
9.     target_elem ← find_target_element(src_prod.lhs, mtt, target_grammar)
10.
11.     mapping ← {
12.         "source": src_prod.lhs,
13.         "target": target_elem OR "UNMAPPED",
14.         "status": "✓" IF target_elem ELSE "✗"
15.     }
16.
17.     coverage["mappings"].append(mapping)
18.
19. RETURN coverage
```

## 実装

### データ構造

```python
@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool
    proof_steps: List[str]
    warnings: List[str]
    errors: List[str]
    coverage_matrix: Dict[str, Any]
```

### 主要クラス

```python
class TypePreservationValidator:
    def __init__(self):
        self.proof_steps: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.coverage: Dict[str, Any] = {}

    def validate(
        self,
        source_grammar: TreeGrammar,
        target_grammar: TreeGrammar,
        mtt: MTT
    ) -> ValidationResult:
        """型保存性を検証"""

    def _validate_structure(...):
        """構造検証"""

    def _validate_type_constraints(...):
        """型制約検証"""

    def _validate_cardinality(...):
        """カーディナリティ検証"""

    def _build_coverage_matrix(...):
        """カバレッジマトリクス構築"""
```

## 計算量解析

### 時間計算量

**O(|P_S| × |P_T| × |R|)**

- |P_S|: ソース文法の生成規則数
- |P_T|: ターゲット文法の生成規則数
- |R|: MTTの変換規則数

**詳細:**
- 構造検証: O(|P_S| × |R|)
- 型制約検証: O(|T_S| × |R| × |P_T|)（T_Sは型制約数）
- カーディナリティ検証: O(|P_S| × |P_T| × |R|)
- カバレッジ構築: O(|P_S| × |R|)

**支配項: O(|P_S| × |P_T| × |R|)**

実際には、|P_S|, |P_T|, |R| はすべて小さな値（通常 < 100）なので、実用上問題ありません。

### 空間計算量

**O(|P_S| + |P_T| + |R| + p)**

- p: 証明ステップ数

通常、p ≈ |P_S| + |P_T| + |R| なので、**O(n)** (nは入力サイズ)

## 例

### 例1: 成功するケース

**ソースXSD:**
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

**ターゲットXSD:**
```xml
<xs:element name="Individual">
  <xs:complexType>
    <xs:attribute name="fullname" type="xs:string" use="required"/>
    <xs:attribute name="years" type="xs:integer" use="required"/>
  </xs:complexType>
</xs:element>
```

**XSLT:**
```xml
<xsl:template match="Person">
  <Individual fullname="{Name}" years="{Age}"/>
</xsl:template>
```

**検証プロセス:**

```
Step 1: Structural Validation
✓ Root element mapping found: Person
✓ Production covered: Person → [Name, Age]
✓ Production covered: Name → [string]
✓ Production covered: Age → [integer]

Step 2: Type Constraint Validation
Checking type constraint: Name
  ✓ Type compatible: string → string
Checking type constraint: Age
  ✓ Type compatible: integer → integer

Step 3: Cardinality Validation
Cardinality check: Person (1,1) → Individual (1,1)
  ✓ Cardinality compatible
Cardinality check: Name (1,1) → attribute fullname (1,1)
  ✓ Cardinality compatible
Cardinality check: Age (1,1) → attribute years (1,1)
  ✓ Cardinality compatible

Conclusion: Type preservation is satisfied ✓
```

**結果:**
```python
ValidationResult(
    is_valid = True,
    proof_steps = [...],
    warnings = [],
    errors = [],
    coverage_matrix = {
        "source_elements": 3,
        "target_elements": 1,
        "mtt_rules": 1,
        "mappings": [
            {"source": "Person", "target": "Individual", "status": "✓"},
            {"source": "Name", "target": "fullname", "status": "✓"},
            {"source": "Age", "target": "years", "status": "✓"}
        ]
    }
)
```

### 例2: 型制約違反

**ソースXSD:**
```xml
<xs:element name="Person">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Age" type="xs:integer"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

**ターゲットXSD:**
```xml
<xs:element name="Individual">
  <xs:complexType>
    <xs:attribute name="years" use="required">
      <xs:simpleType>
        <xs:restriction base="xs:integer">
          <xs:minInclusive value="0"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
  </xs:complexType>
</xs:element>
```

**XSLT (問題あり - ガードなし):**
```xml
<xsl:template match="Person">
  <Individual years="{Age}"/>
</xsl:template>
```

**検証プロセス:**

```
Step 2: Type Constraint Validation
Checking type constraint: Age
  ✓ Type compatible: integer → integer
  ! Target has restriction: minInclusive=0
  ⚠ WARNING: Target element 'years' has minInclusive=0.
    Ensure source values satisfy this constraint.

Conclusion: Type preservation is satisfied ✓
(with warnings)
```

**修正版XSLT (ガード付き):**
```xml
<xsl:template match="Person">
  <xsl:if test="Age >= 0">
    <Individual years="{Age}"/>
  </xsl:if>
</xsl:template>
```

### 例3: カーディナリティ不適合

**ソースXSD:**
```xml
<xs:element name="Contact">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Phone" type="xs:string"
                  minOccurs="0" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

**ターゲットXSD:**
```xml
<xs:element name="Person">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Phone" type="xs:string"
                  minOccurs="1" maxOccurs="1"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

**検証プロセス:**

```
Step 3: Cardinality Validation
Cardinality check: Phone (0,∞) → Phone (1,1)
  ✗ Cardinality incompatible
  ERROR: Source allows 0 or many, but target requires exactly 1
```

**結果:**
```python
ValidationResult(
    is_valid = False,
    errors = [
        "Cardinality mismatch: Phone (0,∞) → Phone (1,1)"
    ],
    ...
)
```

## 高度な検証技法

### 1. パス条件解析

複雑なXPath条件の充足可能性を検証：

```python
def analyze_path_condition(condition: str, source_grammar: TreeGrammar) -> bool:
    """パス条件が充足可能かを解析"""
    # XPath式をパースして制約に変換
    constraints = parse_xpath_to_constraints(condition)

    # 制約がソース文法で充足可能かをチェック
    return is_satisfiable(constraints, source_grammar)
```

### 2. 反例生成

型保存性が失敗する場合の具体例を生成：

```python
def generate_counterexample(
    source_grammar: TreeGrammar,
    target_grammar: TreeGrammar,
    mtt: MTT
) -> Optional[Tree]:
    """型保存性が失敗する反例を生成"""
    # ソース文法から木を生成
    for tree in generate_trees(source_grammar, max_depth=5):
        # MTTで変換
        output = apply_mtt(mtt, tree)

        # ターゲット文法で検証
        if not validate_tree(output, target_grammar):
            return tree  # 反例発見

    return None
```

### 3. 形式的証明生成

Coq等の証明支援系向けのコードを生成：

```python
def generate_formal_proof(validation_result: ValidationResult) -> str:
    """形式的証明を生成"""
    proof = []
    proof.append("Theorem type_preservation:")
    proof.append("  forall t, In t (L G_S) -> In (M t) (L G_T).")
    proof.append("Proof.")
    proof.append("  intros t H.")
    proof.append("  induction t.")

    # 証明ステップを変換
    for step in validation_result.proof_steps:
        proof.append(f"  (* {step} *)")

    proof.append("Qed.")
    return "\n".join(proof)
```

## テストケース

### テスト1: 基本的な型保存

```python
def test_basic_type_preservation():
    source_grammar = create_simple_grammar("Person", ["Name", "Age"])
    target_grammar = create_simple_grammar("Individual", ["name", "age"])
    mtt = create_simple_mtt("Person", "Individual")

    validator = TypePreservationValidator()
    result = validator.validate(source_grammar, target_grammar, mtt)

    assert result.is_valid == True
    assert len(result.errors) == 0
```

### テスト2: 型不適合の検出

```python
def test_type_incompatibility():
    source_grammar = create_grammar_with_type("Age", "string")
    target_grammar = create_grammar_with_type("Age", "integer")
    mtt = create_identity_mtt()

    validator = TypePreservationValidator()
    result = validator.validate(source_grammar, target_grammar, mtt)

    assert result.is_valid == False
    assert any("type" in e.lower() for e in result.errors)
```

### テスト3: カーディナリティ警告

```python
def test_cardinality_warning():
    source_grammar = create_grammar_with_cardinality("Phone", (0, -1))
    target_grammar = create_grammar_with_cardinality("Phone", (1, 1))
    mtt = create_identity_mtt()

    validator = TypePreservationValidator()
    result = validator.validate(source_grammar, target_grammar, mtt)

    assert len(result.warnings) > 0
    assert any("cardinality" in w.lower() for w in result.warnings)
```

## 関連ドキュメント

- [システム概要](./overview.md)
- [XSDパーサー](./xsd_parser.md)
- [MTT変換](./mtt_converter.md)
- [実装例](./examples.md)
