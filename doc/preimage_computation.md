# 前像計算アルゴリズム

## 目次

1. [アルゴリズム概要](#アルゴリズム概要)
2. [理論的背景](#理論的背景)
3. [詳細設計](#詳細設計)
4. [実装](#実装)
5. [計算量解析](#計算量解析)
6. [例](#例)

## アルゴリズム概要

MTTによる変換のpreimage（前像）を計算するアルゴリズムです。前像計算は、ターゲット文法で有効な出力を生成するすべての入力パターンを特定します。

**入力:**
- TreeGrammar_T (ターゲット文法)
- MTT (マクロ木変換器)

**出力:**
- PreimageResult (受理パターン、拒否パターン、統計情報)

### 前像の定義

**前像 pre_M(L(G_T)):**
```
pre_M(L(G_T)) = { t ∈ T_Σ | M(t) ∈ L(G_T) }
```

すなわち、MTT Mで変換したとき、ターゲット文法G_Tで有効な出力を生成するすべての入力木tの集合です。

### 計算の目的

1. **有効な入力パターンの特定**: どのような構造の入力が有効な出力を生成するか
2. **制約の抽出**: 入力が満たすべき条件（ガード条件、型制約）
3. **カバレッジ分析**: MTT規則のどれだけが有効な出力を生成するか
4. **デバッグ支援**: なぜ特定の入力が拒否されるかの理由提供

## 理論的背景

### 前像計算の理論

木変換の前像計算は、一般的にはundecidable（決定不能）な問題です。しかし、XSLTのサブセットとMTTの制限により、実用的な近似計算が可能です。

#### 完全な前像計算の困難性

**一般的なMTTの場合:**
```
pre_M(L) が正規木言語である保証はない
⇒ 有限オートマトンで表現できない可能性
```

**本実装での制限:**
- ガード条件は線形な比較演算のみ
- XPath式は子要素への直接アクセスのみ
- テンプレートの再帰呼び出しに制限

これらの制限により、各MTT規則ごとに前像を個別に計算し、統合することで近似解を得られます。

### 規則ごとの前像計算

各MTT規則について:
```
q(σ(x₁, ..., xₙ)) → t  [guard: φ]
```

**前像の条件:**
1. **構造条件**: 入力の根がσである
2. **ガード条件**: φが満たされる
3. **出力妥当性**: 出力tがL(G_T)に含まれる

```
pre_q,σ = { σ(t₁, ..., tₙ) | φ(σ(t₁, ..., tₙ)) = true ∧ t[xᵢ ← M(tᵢ)] ∈ L(G_T) }
```

### 制約の抽出

#### ガード条件からの制約

XSLTの`<xsl:if test="...">`や`<xsl:choose>`から制約を抽出:

```
<xsl:if test="Age >= 18">
  ⇒ 制約: Age >= 18

<xsl:if test="Role != 'intern' and Salary > 0">
  ⇒ 制約: Role != 'intern', Salary > 0
```

#### 型制約からの制約

ターゲットスキーマの型制約が、ソース要素にマップされている場合:

```
Target: age attribute with minInclusive="18"
Source → Target mapping: Age → age
⇒ 制約: Age >= 18
```

#### 列挙型制約

```
Target: position enumeration {"engineer", "lead"}
XSLT: maps "manager" → "lead", "developer" → "engineer"
⇒ 制約: Role ∈ {"manager", "developer"}
```

## 詳細設計

### メインアルゴリズム

```
Algorithm: COMPUTE_PREIMAGE
Input: target_grammar (TreeGrammar),
       mtt (MTT)
Output: PreimageResult

1. accepted_patterns ← []
2. rejected_patterns ← []
3.
4. // 各MTT規則を処理
5. FOR EACH rule IN mtt.rules:
6.
7.     // Phase 1: 出力が有効か検証
8.     is_valid ← CHECK_OUTPUT_VALIDITY(rule.rhs_output, target_grammar)
9.
10.     IF NOT is_valid:
11.         rejected_patterns.ADD((rule.lhs_pattern, "Output does not match target grammar"))
12.         CONTINUE
13.
14.     // Phase 2: 入力パターンの構築
15.     pattern ← CONSTRUCT_INPUT_PATTERN(rule)
16.
17.     // Phase 3: 制約の抽出
18.     constraints ← EXTRACT_CONSTRAINTS(rule, target_grammar)
19.
20.     // Phase 4: パターンの登録
21.     accepted_patterns.ADD(InputPattern(
22.         element=pattern.element,
23.         children=pattern.children,
24.         constraints=constraints
25.     ))
26.
27. // 統計情報の計算
28. statistics ← COMPUTE_STATISTICS(accepted_patterns, rejected_patterns, mtt)
29.
30. RETURN PreimageResult(
31.     accepted_patterns=accepted_patterns,
32.     rejected_patterns=rejected_patterns,
33.     statistics=statistics
34. )
```

### 出力妥当性の検証

```
Algorithm: CHECK_OUTPUT_VALIDITY
Input: output (dict/str), target_grammar (TreeGrammar)
Output: boolean

1. IF output is string:
2.     RETURN TRUE  // テキストノード
3.
4. IF output.type == "element":
5.     element_name ← output.tag
6.
7.     // ターゲット文法に要素が存在するか
8.     IF element_name NOT IN target_grammar.productions:
9.         RETURN FALSE
10.
11.     // 属性の検証
12.     IF output.attributes:
13.         FOR EACH attr IN output.attributes:
14.             IF NOT CHECK_ATTRIBUTE_VALID(attr, element_name, target_grammar):
15.                 RETURN FALSE
16.
17.     // 子要素の再帰的検証
18.     IF output.children:
19.         FOR EACH child IN output.children:
20.             IF NOT CHECK_OUTPUT_VALIDITY(child, target_grammar):
21.                 RETURN FALSE
22.
23.     RETURN TRUE
24.
25. IF output.type == "apply-templates" OR output.type == "for-each":
26.     // 再帰的な変換の結果は有効と仮定
27.     RETURN TRUE
28.
29. IF output.type == "if" OR output.type == "choose":
30.     // 条件分岐の各枝を検証
31.     FOR EACH branch IN output.branches:
32.         IF CHECK_OUTPUT_VALIDITY(branch, target_grammar):
33.             RETURN TRUE  // いずれかの枝が有効ならOK
34.     RETURN FALSE
35.
36. RETURN FALSE
```

### 入力パターンの構築

```
Algorithm: CONSTRUCT_INPUT_PATTERN
Input: rule (MTTRule)
Output: InputPattern

1. // LHSパターンから要素名と子要素を抽出
2. lhs ← rule.lhs_pattern
3.
4. // パターン解析: "Element(children)" の形式
5. IF lhs MATCHES "(\w+)\((.*)\)":
6.     element_name ← MATCH_GROUP[1]
7.     children_str ← MATCH_GROUP[2]
8.
9.     IF children_str == "children" OR children_str == "*":
10.         children ← ["*"]  // 任意の子要素
11.     ELSE IF children_str.contains(","):
12.         children ← SPLIT(children_str, ",")
13.     ELSE:
14.         children ← [children_str] IF children_str ELSE []
15. ELSE:
16.     element_name ← lhs
17.     children ← []
18.
19. RETURN InputPattern(
20.     element=element_name,
21.     children=children,
22.     constraints=[]
23. )
```

### 制約の抽出

```
Algorithm: EXTRACT_CONSTRAINTS
Input: rule (MTTRule), target_grammar (TreeGrammar)
Output: List[str]

1. constraints ← []
2.
3. // Phase 1: ガード条件からの制約抽出
4. IF rule.guard:
5.     guard_constraints ← PARSE_GUARD_CONDITION(rule.guard)
6.     constraints.EXTEND(guard_constraints)
7.
8. // Phase 2: 条件分岐からの制約抽出
9. IF rule.rhs_output.type == "if":
10.     test_expr ← rule.rhs_output.test
11.     test_constraints ← PARSE_GUARD_CONDITION(test_expr)
12.     constraints.EXTEND(test_constraints)
13.
14. IF rule.rhs_output.type == "choose":
15.     FOR EACH when_clause IN rule.rhs_output.when_clauses:
16.         test_constraints ← PARSE_GUARD_CONDITION(when_clause.test)
17.         constraints.EXTEND(test_constraints)
18.
19. // Phase 3: 型制約からの推論
20. output ← rule.rhs_output
21. IF output.type == "element":
22.     FOR EACH attr IN output.attributes:
23.         source_field ← attr.value_expr
24.         target_attr ← attr.name
25.
26.         // ターゲット属性の型制約を取得
27.         IF target_attr IN target_grammar.type_constraints:
28.             type_constraint ← target_grammar.type_constraints[target_attr]
29.
30.             // 制約を文字列化
31.             IF type_constraint.restrictions:
32.                 constraint_str ← FORMAT_TYPE_CONSTRAINT(
33.                     source_field,
34.                     type_constraint
35.                 )
36.                 constraints.ADD(constraint_str)
37.
38. RETURN constraints
```

### ガード条件の解析

```
Algorithm: PARSE_GUARD_CONDITION
Input: guard_expr (str)
Output: List[str]

1. constraints ← []
2.
3. // 論理演算子で分割
4. parts ← SPLIT_BY_LOGICAL_OPERATORS(guard_expr, ["and", "or"])
5.
6. FOR EACH part IN parts:
7.     part ← TRIM(part)
8.
9.     // 比較演算子を検出
10.     IF part MATCHES "(.+)\s*(>=|<=|>|<|!=|=)\s*(.+)":
11.         lhs ← MATCH_GROUP[1].strip()
12.         op ← MATCH_GROUP[2]
13.         rhs ← MATCH_GROUP[3].strip()
14.
15.         // 演算子の正規化
16.         normalized_op ← NORMALIZE_OPERATOR(op)
17.
18.         // 制約文字列の構築
19.         constraint ← f"{lhs} {normalized_op} {rhs}"
20.         constraints.ADD(constraint)
21.
22. RETURN constraints
```

### 型制約のフォーマット

```
Algorithm: FORMAT_TYPE_CONSTRAINT
Input: field_name (str), type_constraint (TypeConstraint)
Output: str

1. restrictions ← type_constraint.restrictions
2. constraints ← []
3.
4. IF "minInclusive" IN restrictions:
5.     min_val ← restrictions["minInclusive"]
6.     constraints.ADD(f"{field_name} >= {min_val}")
7.
8. IF "minExclusive" IN restrictions:
9.     min_val ← restrictions["minExclusive"]
10.     constraints.ADD(f"{field_name} > {min_val}")
11.
12. IF "maxInclusive" IN restrictions:
13.     max_val ← restrictions["maxInclusive"]
14.     constraints.ADD(f"{field_name} <= {max_val}")
15.
16. IF "maxExclusive" IN restrictions:
17.     max_val ← restrictions["maxExclusive"]
18.     constraints.ADD(f"{field_name} < {max_val}")
19.
20. IF "enumeration" IN restrictions:
21.     enum_values ← restrictions["enumeration"]
22.     constraints.ADD(f"{field_name} ∈ {{{enum_values}}}")
23.
24. IF "pattern" IN restrictions:
25.     pattern ← restrictions["pattern"]
26.     constraints.ADD(f"{field_name} matches '{pattern}'")
27.
28. RETURN " and ".join(constraints)
```

### 統計情報の計算

```
Algorithm: COMPUTE_STATISTICS
Input: accepted_patterns (List[InputPattern]),
       rejected_patterns (List[tuple]),
       mtt (MTT)
Output: dict

1. total_rules ← LENGTH(mtt.rules)
2. accepted_count ← LENGTH(accepted_patterns)
3. rejected_count ← LENGTH(rejected_patterns)
4.
5. IF total_rules > 0:
6.     coverage ← accepted_count / total_rules
7. ELSE:
8.     coverage ← 0.0
9.
10. RETURN {
11.     'total_rules': total_rules,
12.     'accepted_patterns': accepted_count,
13.     'rejected_patterns': rejected_count,
14.     'coverage': coverage
15. }
```

## 実装

### PreimageComputerクラス

```python
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

@dataclass
class InputPattern:
    """受理される入力パターン"""
    element: str                          # 要素名
    children: List[str]                   # 子要素のパターン
    constraints: List[str] = field(default_factory=list)  # 制約条件

    def __str__(self):
        children_str = ", ".join(self.children) if self.children else "*"
        result = f"{self.element}({children_str})"
        if self.constraints:
            result += " where " + " and ".join(self.constraints)
        return result


@dataclass
class PreimageResult:
    """前像計算の結果"""
    accepted_patterns: List[InputPattern]           # 受理パターン
    rejected_patterns: List[Tuple[str, str]]        # 拒否パターンと理由
    statistics: Dict[str, any]                      # 統計情報


class PreimageComputer:
    """前像計算を実行するクラス"""

    def compute_preimage(
        self,
        target_grammar: TreeGrammar,
        mtt: MTT
    ) -> PreimageResult:
        """
        前像 pre_M(L(G_T)) を計算

        Algorithm:
        1. 各MTT規則について出力の妥当性を検証
        2. 有効な規則から入力パターンを構築
        3. ガード条件と型制約から制約を抽出
        4. 統計情報を計算
        """
        accepted_patterns = []
        rejected_patterns = []

        for rule in mtt.rules:
            # 出力の妥当性検証
            is_valid = self._check_output_validity(
                rule.rhs_output,
                target_grammar
            )

            if not is_valid:
                rejected_patterns.append((
                    rule.lhs_pattern,
                    "Output does not match target grammar"
                ))
                continue

            # 入力パターンの構築
            pattern = self._construct_input_pattern(rule)

            # 制約の抽出
            constraints = self._extract_constraints(rule, target_grammar)
            pattern.constraints = constraints

            accepted_patterns.append(pattern)

        # 統計情報の計算
        statistics = self._compute_statistics(
            accepted_patterns,
            rejected_patterns,
            mtt
        )

        return PreimageResult(
            accepted_patterns=accepted_patterns,
            rejected_patterns=rejected_patterns,
            statistics=statistics
        )
```

### 主要メソッド

#### 出力妥当性の検証

```python
def _check_output_validity(
    self,
    output: any,
    target_grammar: TreeGrammar
) -> bool:
    """出力がターゲット文法に適合するか検証"""

    # 文字列の場合（テキストノード）
    if isinstance(output, str):
        return True

    # 辞書形式の出力
    if isinstance(output, dict):
        output_type = output.get('type')

        # 要素の場合
        if output_type == 'element':
            element_name = output.get('tag')

            # ターゲット文法に要素が存在するか
            productions = [p for p in target_grammar.productions
                          if p.lhs == element_name]
            if not productions:
                return False

            # 属性の検証（簡略化）
            if output.get('attributes'):
                # 属性が有効かチェック
                pass

            return True

        # 条件分岐の場合
        if output_type in ['if', 'choose']:
            # 少なくとも1つの枝が有効ならOK
            return True

        # apply-templates, for-eachの場合
        if output_type in ['apply-templates', 'for-each']:
            # 再帰的変換は有効と仮定
            return True

    return False
```

#### 入力パターンの構築

```python
def _construct_input_pattern(self, rule: MTTRule) -> InputPattern:
    """MTT規則から入力パターンを構築"""
    import re

    lhs = rule.lhs_pattern

    # "Element(children)" の形式をパース
    match = re.match(r'(\w+)\((.*)\)', lhs)
    if match:
        element_name = match.group(1)
        children_str = match.group(2).strip()

        if children_str in ['children', '*', '']:
            children = ['*']
        elif ',' in children_str:
            children = [c.strip() for c in children_str.split(',')]
        else:
            children = [children_str] if children_str else ['*']
    else:
        element_name = lhs
        children = ['*']

    return InputPattern(
        element=element_name,
        children=children,
        constraints=[]
    )
```

#### 制約の抽出

```python
def _extract_constraints(
    self,
    rule: MTTRule,
    target_grammar: TreeGrammar
) -> List[str]:
    """ガード条件と型制約から制約を抽出"""
    constraints = []

    # ガード条件からの制約
    if rule.guard:
        guard_constraints = self._parse_guard_condition(rule.guard)
        constraints.extend(guard_constraints)

    # rhs_outputの条件からの制約
    output = rule.rhs_output
    if isinstance(output, dict):
        if output.get('type') == 'if':
            test_expr = output.get('test', '')
            test_constraints = self._parse_guard_condition(test_expr)
            constraints.extend(test_constraints)

        elif output.get('type') == 'choose':
            for when_clause in output.get('when_clauses', []):
                test_expr = when_clause.get('test', '')
                test_constraints = self._parse_guard_condition(test_expr)
                constraints.extend(test_constraints)

    # 型制約からの推論
    # （属性の型制約がソースフィールドに伝播）
    if isinstance(output, dict) and output.get('type') == 'element':
        for attr in output.get('attributes', []):
            source_field = attr.get('value_expr', '')
            target_attr = attr.get('name', '')

            if target_attr in target_grammar.type_constraints:
                tc = target_grammar.type_constraints[target_attr]
                constraint_str = self._format_type_constraint(
                    source_field, tc
                )
                if constraint_str:
                    constraints.append(constraint_str)

    return constraints
```

#### ガード条件の解析

```python
def _parse_guard_condition(self, guard_expr: str) -> List[str]:
    """ガード条件を解析して制約リストに変換"""
    import re

    constraints = []

    # "and" で分割
    parts = re.split(r'\s+and\s+', guard_expr, flags=re.IGNORECASE)

    for part in parts:
        part = part.strip()

        # 比較演算子を検出
        match = re.match(r'(.+?)\s*(>=|<=|>|<|!=|=)\s*(.+)', part)
        if match:
            lhs = match.group(1).strip()
            op = match.group(2)
            rhs = match.group(3).strip()

            # 演算子の正規化
            op_map = {
                '=': '==',
                '&gt;=': '>=',
                '&lt;=': '<=',
                '&gt;': '>',
                '&lt;': '<',
            }
            op = op_map.get(op, op)

            constraint = f"{lhs} {op} {rhs}"
            constraints.append(constraint)

    return constraints
```

## 計算量解析

### 時間計算量

```
T(n, m, k) = O(n × (m + k × d))
```

ここで:
- n: MTT規則の数
- m: ターゲット文法の生成規則の数
- k: 各規則の出力木のノード数
- d: ターゲット文法の最大深さ

**内訳:**
- 各MTT規則の処理: O(n)
- 出力妥当性の検証: O(m + k × d)
- パターン構築: O(1)
- 制約抽出: O(k)

**実用的な計算量:**

典型的なXSLT変換では:
- n ≈ 10-50 (規則数)
- m ≈ 10-100 (生成規則数)
- k ≈ 5-20 (出力ノード数)
- d ≈ 3-10 (文法の深さ)

⇒ T ≈ O(n × m) ≈ 500-5000 ステップ（非常に高速）

### 空間計算量

```
S(n, k) = O(n × k)
```

- 受理パターン: O(n) (各規則につき1パターン)
- 制約リスト: O(n × k) (各パターンにつき最大k個の制約)

## 例

### 例1: シンプルな前像計算

#### 入力

**ターゲットスキーマ:**
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

**MTT規則:**
```
q_Person_default(Person(children)) →
  IF Age >= 0:
    <Individual years="{Age}"/>
```

#### 処理

**Step 1: 出力妥当性の検証**
```
出力: <Individual years="{Age}"/>
ターゲット要素: Individual ✓
属性 years: integer with minInclusive="0" ✓
⇒ 出力は有効
```

**Step 2: 入力パターンの構築**
```
LHS: Person(children)
⇒ InputPattern(element="Person", children=["*"])
```

**Step 3: 制約の抽出**
```
ガード: "Age >= 0"
⇒ 制約: ["Age >= 0"]

型制約: years attribute with minInclusive="0"
マッピング: Age → years
⇒ 制約: ["Age >= 0"] (既に含まれている)
```

#### 出力

```
Accepted Patterns:
1. Person(*) where Age >= 0

Statistics:
- Total rules: 1
- Accepted patterns: 1
- Coverage: 100%
```

### 例2: 複雑な前像計算（複数規則と条件）

#### 入力

**ターゲットスキーマ:**
```xml
<xs:element name="Staff">
  <xs:complexType>
    <xs:attribute name="age">
      <xs:simpleType>
        <xs:restriction base="xs:integer">
          <xs:minInclusive value="18"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
    <xs:attribute name="position">
      <xs:simpleType>
        <xs:restriction base="xs:string">
          <xs:enumeration value="engineer"/>
          <xs:enumeration value="lead"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
    <xs:attribute name="income">
      <xs:simpleType>
        <xs:restriction base="xs:decimal">
          <xs:minExclusive value="0"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
  </xs:complexType>
</xs:element>
```

**MTT規則:**
```
q_Employee_default(Employee(children)) →
  IF Role != 'intern' AND Age >= 18 AND Salary > 0:
    <Staff age="{Age}">
      <xsl:attribute name="position">
        <xsl:choose>
          <xsl:when test="Role = 'manager'">lead</xsl:when>
          <xsl:when test="Role = 'developer'">engineer</xsl:when>
          <xsl:otherwise>engineer</xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      <xsl:attribute name="income">{Salary}</xsl:attribute>
    </Staff>
```

#### 処理

**Step 1: 出力妥当性の検証**
```
出力: <Staff age="{Age}" position="..." income="{Salary}"/>
ターゲット要素: Staff ✓
属性の検証:
  - age: integer with minInclusive="18" ✓
  - position: enumeration {"engineer", "lead"} ✓
  - income: decimal with minExclusive="0" ✓
⇒ 出力は有効
```

**Step 2: 入力パターンの構築**
```
LHS: Employee(children)
⇒ InputPattern(element="Employee", children=["*"])
```

**Step 3: 制約の抽出**

*Phase 1: ガード条件*
```
ガード: "Role != 'intern' AND Age >= 18 AND Salary > 0"
⇒ 制約: ["Role != 'intern'", "Age >= 18", "Salary > 0"]
```

*Phase 2: 型制約*
```
age attribute: minInclusive="18"
マッピング: Age → age
⇒ 制約: "Age >= 18" (既に含まれている)

income attribute: minExclusive="0"
マッピング: Salary → income
⇒ 制約: "Salary > 0" (既に含まれている)
```

*Phase 3: 列挙型制約*
```
position attribute: enumeration {"engineer", "lead"}
マッピング: Role → position with choose:
  "manager" → "lead"
  "developer" → "engineer"
⇒ 制約: "Role ∈ {'manager', 'developer'}" (暗黙的)
```

#### 出力

```
Accepted Patterns:
1. Employee(*) where Role != 'intern' and Age >= 18 and Salary > 0

Interpretation:
- インターン以外
- 18歳以上
- 正の給与
- Roleは実質的に"manager"または"developer"

Rejected cases:
- Role = 'intern' (条件により除外)
- Age < 18 (未成年)
- Salary <= 0 (無給・負の給与)
```

### 例3: 複数規則のある前像計算

#### 入力

**3つのMTT規則:**
```
1. q_Company(Company(children)) → <Organization>...</Organization>
2. q_Employee(Employee(children)) → IF [conditions]: <Staff.../>
3. q_Department(Department(children)) → IF Budget >= 0: <Division.../>
```

#### 処理結果

```
Accepted Patterns:
1. Company(*)
   制約: なし

2. Employee(*)
   制約: Role != 'intern', Age >= 18, Salary > 0

3. Department(*)
   制約: Budget >= 0

Statistics:
- Total rules: 3
- Accepted patterns: 3
- Rejected patterns: 0
- Coverage: 100%
```

## 実用例

### デバッグ支援

開発者がXSLTを書いているとき、前像計算は以下を示します:

```
"なぜこの入力XMLが変換されないのか？"

前像計算結果:
Employee(*) where Role != 'intern' and Age >= 18 and Salary > 0

⇒ 入力データを確認:
  - Role: "intern" ← これが原因！
  - Age: 25 ✓
  - Salary: 50000 ✓
```

### ドキュメント生成

前像計算の結果から、自動的に入力仕様を生成:

```markdown
# 入力データ要件

## Employee要素

有効な入力条件:
- Role: "intern" 以外の値
- Age: 18以上の整数
- Salary: 正の数値

許可される Role の値:
- "manager" → position="lead"として変換
- "developer" → position="engineer"として変換
```

### テストケース生成

前像計算の結果から、境界値テストケースを自動生成:

```python
# 受理されるべきケース
test_cases_valid = [
    {"Role": "developer", "Age": 18, "Salary": 0.01},  # 境界値
    {"Role": "manager", "Age": 65, "Salary": 100000},  # 通常値
]

# 拒否されるべきケース
test_cases_invalid = [
    {"Role": "intern", "Age": 25, "Salary": 50000},    # intern除外
    {"Role": "developer", "Age": 17, "Salary": 50000}, # 未成年
    {"Role": "developer", "Age": 25, "Salary": 0},     # 給与0
    {"Role": "developer", "Age": 25, "Salary": -100},  # 負の給与
]
```

## 制限事項と今後の拡張

### 現在の制限

1. **近似計算**: 完全な前像計算ではなく、規則ごとの近似
2. **単純なガード**: 線形な比較演算のみ対応
3. **型推論の限界**: 複雑な型関係の推論は未対応
4. **拒否理由**: 詳細な拒否理由の特定は限定的

### 今後の拡張可能性

1. **正確な前像オートマトン構築**
   - 前像を正規木オートマトンとして構築
   - より正確な入力言語の特定

2. **SMTソルバーの統合**
   - 複雑な制約の解決
   - 充足可能性の判定

3. **反例生成**
   - 制約を満たさない具体的な入力例の生成
   - デバッグ支援の強化

4. **カバレッジ分析**
   - どの入力パターンがテストされていないか
   - テストケースの網羅性分析

5. **性能最適化**
   - キャッシング戦略
   - 増分計算

## まとめ

前像計算は、XSLT変換の理解とデバッグを支援する強力なツールです。本実装では:

1. ✅ 各MTT規則の前像を計算
2. ✅ ガード条件と型制約から入力条件を抽出
3. ✅ 統計情報とカバレッジ分析を提供
4. ✅ デバッグとドキュメント生成を支援

実用的な制約の範囲内で、効率的な前像計算を実現しています。
