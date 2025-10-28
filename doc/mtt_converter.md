# XSLT to MTT変換アルゴリズム

## 目次

1. [アルゴリズム概要](#アルゴリズム概要)
2. [理論的背景](#理論的背景)
3. [詳細設計](#詳細設計)
4. [実装](#実装)
5. [計算量解析](#計算量解析)
6. [例](#例)

## アルゴリズム概要

XSLTをMacro Tree Transducer (MTT)表現に変換するアルゴリズムです。

**入力:** XSLT文書（XML形式）
**出力:** MTT（状態、変換規則、入出力アルファベット）

### 変換の目的

XSLTをMTTに変換することで：
1. 形式的な理論検証が可能になる
2. 前像計算ができるようになる
3. 型保存性を数学的に証明できる

## 理論的背景

### Macro Tree Transducer (MTT) の定義

**形式的定義:**
```
M = (Q, Σ_in, Σ_out, q_0, R)

Q: 状態の集合
Σ_in: 入力アルファベット（要素名の集合）
Σ_out: 出力アルファベット（要素名の集合）
q_0: 初期状態
R: 変換規則の集合
```

### 変換規則の形式

```
q(σ(x₁, ..., xₙ), p₁, ..., pₖ) → t

左辺:
  q: 状態
  σ: 入力記号
  x₁, ..., xₙ: 子木変数
  p₁, ..., pₖ: パラメータ

右辺 t:
  - 出力記号
  - 状態呼び出し: q'(xᵢ, args)
  - パラメータ参照
  - リテラル値
```

### XSLTからMTTへの対応

| XSLT構成要素 | MTT要素 |
|------------|--------|
| xsl:template | 状態 q |
| match pattern | 入力パターン σ(...) |
| template body | 出力木 t |
| xsl:apply-templates | 状態呼び出し |
| xsl:with-param | パラメータ渡し |
| xsl:if | ガード付き規則 |
| リテラル要素 | 出力記号 |

## 詳細設計

### メインアルゴリズム

```
Algorithm: XSLT_TO_MTT
Input: xslt_content (XML string)
Output: MTT

1. mtt ← new MTT()
2. root ← parse_xml(xslt_content)
3.
4. // 全テンプレートの処理
5. templates ← root.findall(".//template")
6.
7. FOR EACH template IN templates:
8.     process_template(template, mtt)
9.
10. RETURN mtt
```

### テンプレート処理

```
Algorithm: PROCESS_TEMPLATE
Input: template (XML Element), mtt (MTT)
Output: Updates mtt

1. match ← template.get("match")
2. mode ← template.get("mode", default="default")
3.
4. IF match IS NULL:
5.     RETURN  // スキップ
6.
7. // 状態名の生成
8. state_name ← create_state_name(match, mode)
9. mtt.states.append(state_name)
10.
11. // マッチパターンの変換
12. lhs_pattern ← parse_match_pattern(match)
13.
14. // テンプレート本体の処理
15. rhs_output ← process_template_body(template, state_name)
16.
17. // MTT規則の生成
18. rule ← MTTRule(
19.     state = state_name,
20.     lhs_pattern = lhs_pattern,
21.     rhs_output = rhs_output,
22.     guard = "",
23.     params = []
24. )
25. mtt.rules.append(rule)
```

### 状態名生成

```
Algorithm: CREATE_STATE_NAME
Input: match (string), mode (string)
Output: state_name (string)

1. // パターンを正規化
2. state_base ← match
3. state_base ← replace(state_base, "/", "_")
4. state_base ← replace(state_base, "@", "attr_")
5. state_base ← replace(state_base, "*", "any")
6.
7. // モードを追加
8. state_name ← "q_" + state_base + "_" + mode
9.
10. RETURN state_name
```

### マッチパターン変換

```
Algorithm: PARSE_MATCH_PATTERN
Input: match (string)
Output: pattern (string)

1. IF match == "/":
2.     RETURN "root(children)"
3.
4. IF match STARTS_WITH "/":
5.     // ルート相対パス
6.     parts ← split(match.strip("/"), "/")
7.     element ← parts[last]
8.     RETURN element + "(children)"
9.
10. // 単純要素名
11. RETURN match + "(children)"
```

### テンプレート本体処理

```
Algorithm: PROCESS_TEMPLATE_BODY
Input: template (XML Element), state (string)
Output: output_tree (Dict)

1. output ← {
2.     "type": "sequence",
3.     "children": []
4. }
5.
6. // テキストコンテンツの処理
7. IF template.text EXISTS AND template.text.strip() NOT EMPTY:
8.     output["children"].append({
9.         "type": "text",
10.         "value": template.text.strip()
11.     })
12.
13. // 子要素の処理
14. FOR EACH child IN template.children:
15.     child_output ← process_instruction(child, state)
16.     IF child_output IS NOT NULL:
17.         output["children"].append(child_output)
18.
19. RETURN output
```

### 命令処理

```
Algorithm: PROCESS_INSTRUCTION
Input: elem (XML Element), current_state (string)
Output: output (Dict or NULL)

1. local_name ← get_local_name(elem.tag)
2.
3. // XSLT命令の処理
4. IF elem.tag STARTS_WITH XSLT_NS:
5.
6.     SWITCH local_name:
7.         CASE "apply-templates":
8.             RETURN process_apply_templates(elem)
9.
10.         CASE "for-each":
11.             RETURN process_for_each(elem, current_state)
12.
13.         CASE "value-of":
14.             RETURN process_value_of(elem)
15.
16.         CASE "if":
17.             RETURN process_if(elem, current_state)
18.
19.         CASE "choose":
20.             RETURN process_choose(elem, current_state)
21.
22.         CASE "text":
23.             RETURN {"type": "text", "value": elem.text OR ""}
24.
25.         CASE "element":
26.             RETURN process_element(elem, current_state)
27.
28.         CASE "attribute":
29.             RETURN process_attribute(elem)
30.
31. // リテラル結果要素
32. ELSE:
33.     RETURN process_literal_element(elem, current_state)
34.
35. RETURN NULL
```

### apply-templates処理

```
Algorithm: PROCESS_APPLY_TEMPLATES
Input: elem (XML Element)
Output: output (Dict)

1. select ← elem.get("select", default="node()")
2.
3. output ← {
4.     "type": "apply-templates",
5.     "select": select,
6.     "call": "apply_to_" + select.replace("/", "_")
7. }
8.
9. RETURN output
```

### for-each処理

```
Algorithm: PROCESS_FOR_EACH
Input: elem (XML Element), state (string)
Output: output (Dict)

1. select ← elem.get("select", default="")
2.
3. // リスト処理用の補助状態を生成
4. list_state ← state + "_foreach_" + generate_id()
5. mtt.states.append(list_state)
6.
7. // ループ本体の処理
8. body ← {
9.     "type": "sequence",
10.     "children": []
11. }
12.
13. FOR EACH child IN elem.children:
14.     child_output ← process_instruction(child, list_state)
15.     IF child_output IS NOT NULL:
16.         body["children"].append(child_output)
17.
18. output ← {
19.     "type": "for-each",
20.     "select": select,
21.     "body": body,
22.     "list_state": list_state
23. }
24.
25. RETURN output
```

### if処理

```
Algorithm: PROCESS_IF
Input: elem (XML Element), state (string)
Output: output (Dict)

1. test ← elem.get("test", default="")
2.
3. // then節の処理
4. body ← {
5.     "type": "sequence",
6.     "children": []
7. }
8.
9. FOR EACH child IN elem.children:
10.     child_output ← process_instruction(child, state)
11.     IF child_output IS NOT NULL:
12.         body["children"].append(child_output)
13.
14. output ← {
15.     "type": "if",
16.     "test": test,
17.     "then": body
18. }
19.
20. RETURN output
```

### choose処理

```
Algorithm: PROCESS_CHOOSE
Input: elem (XML Element), state (string)
Output: output (Dict)

1. branches ← []
2.
3. FOR EACH child IN elem.children:
4.     local_name ← get_local_name(child.tag)
5.
6.     IF local_name == "when":
7.         test ← child.get("test", default="")
8.         body ← process_children(child, state)
9.         branches.append({
10.             "type": "when",
11.             "test": test,
12.             "body": body
13.         })
14.
15.     ELSE IF local_name == "otherwise":
16.         body ← process_children(child, state)
17.         branches.append({
18.             "type": "otherwise",
19.             "body": body
20.         })
21.
22. output ← {
23.     "type": "choose",
24.     "branches": branches
25. }
26.
27. RETURN output
```

### リテラル要素処理

```
Algorithm: PROCESS_LITERAL_ELEMENT
Input: elem (XML Element), state (string)
Output: output (Dict)

1. children ← []
2.
3. // テキストコンテンツ
4. IF elem.text EXISTS AND elem.text.strip() NOT EMPTY:
5.     children.append({
6.         "type": "text",
7.         "value": elem.text.strip()
8.     })
9.
10. // 子要素の処理
11. FOR EACH child IN elem.children:
12.     child_output ← process_instruction(child, state)
13.     IF child_output IS NOT NULL:
14.         children.append(child_output)
15.
16.     // 末尾テキスト
17.     IF child.tail EXISTS AND child.tail.strip() NOT EMPTY:
18.         children.append({
19.             "type": "text",
20.             "value": child.tail.strip()
21.         })
22.
23. // 属性の処理
24. attributes ← []
25. FOR EACH (attr_name, attr_value) IN elem.attributes:
26.     IF attr_value CONTAINS "{" AND attr_value CONTAINS "}":
27.         // 属性値テンプレート
28.         xpath_expr ← extract_xpath_from_avt(attr_value)
29.         attributes.append({
30.             "name": attr_name,
31.             "value_expr": xpath_expr
32.         })
33.     ELSE:
34.         attributes.append({
35.             "name": attr_name,
36.             "value": attr_value
37.         })
38.
39. output ← {
40.     "type": "element",
41.     "name": get_local_name(elem.tag),
42.     "attributes": attributes,
43.     "children": children
44. }
45.
46. RETURN output
```

## 実装

### データ構造

```python
@dataclass
class MTTRule:
    """MTT変換規則"""
    state: str
    lhs_pattern: str
    rhs_output: Any
    guard: str = ""
    params: List[str] = field(default_factory=list)

@dataclass
class MTT:
    """Macro Tree Transducer"""
    states: List[str] = field(default_factory=list)
    rules: List[MTTRule] = field(default_factory=list)
    initial_state: str = "q_root"
    input_alphabet: List[str] = field(default_factory=list)
    output_alphabet: List[str] = field(default_factory=list)
```

### 主要クラス

```python
class XSLTToMTTConverter:
    def __init__(self):
        self.mtt = MTT()
        self.template_counter = 0
        self.state_map: Dict[str, str] = {}

    def convert(self, xslt_content: str) -> MTT:
        """XSLTをMTTに変換"""

    def _process_template(self, template: ET.Element):
        """テンプレートの処理"""

    def _create_state_name(self, match: str, mode: str) -> str:
        """状態名の生成"""

    def _process_template_body(self, template: ET.Element, state: str) -> Dict:
        """テンプレート本体の処理"""

    def _process_instruction(self, elem: ET.Element, state: str) -> Dict:
        """XSLT命令の処理"""

    def to_json(self) -> Dict[str, Any]:
        """JSON形式に変換"""
```

## 計算量解析

### 時間計算量

**O(m × d)**

- m: XSLT内のテンプレート数
- d: 各テンプレートの平均深さ

**詳細:**
- テンプレートの走査: O(m)
- 各テンプレート本体の処理: O(d)
- 合計: O(m × d)

通常、d は小さな定数なので、実質的には **O(m)**

### 空間計算量

**O(m × d + r)**

- m: テンプレート数
- d: 平均深さ
- r: 生成される規則数

通常、r ≈ m なので、**O(m × d)**

## 例

### 例1: 基本的な変換

**入力XSLT:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="Person">
    <Individual fullname="{Name}" years="{Age}"/>
  </xsl:template>
</xsl:stylesheet>
```

**処理ステップ:**

1. テンプレート発見: match="Person"
2. 状態名生成: q_Person_default
3. マッチパターン変換: Person(children)
4. 本体処理:
   - リテラル要素 <Individual>
   - 属性 fullname="{Name}" → value_expr: "Name"
   - 属性 years="{Age}" → value_expr: "Age"

**出力MTT:**
```python
MTT(
    states = ["q_Person_default"],
    initial_state = "q_root",
    rules = [
        MTTRule(
            state = "q_Person_default",
            lhs_pattern = "Person(children)",
            rhs_output = {
                "type": "sequence",
                "children": [{
                    "type": "element",
                    "name": "Individual",
                    "attributes": [
                        {
                            "name": "fullname",
                            "value_expr": "Name"
                        },
                        {
                            "name": "years",
                            "value_expr": "Age"
                        }
                    ],
                    "children": []
                }]
            },
            guard = "",
            params = []
        )
    ]
)
```

**形式的表記:**
```
States: Q = {q_Person_default}

Rules:
  q_Person_default(Person(Name, Age)) →
    Individual[@fullname=Name, @years=Age]
```

### 例2: 条件分岐付き

**入力XSLT:**
```xml
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="Person">
    <xsl:if test="Age >= 0">
      <Individual name="{Name}"/>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
```

**出力MTT:**
```python
MTTRule(
    state = "q_Person_default",
    lhs_pattern = "Person(children)",
    rhs_output = {
        "type": "sequence",
        "children": [{
            "type": "if",
            "test": "Age >= 0",
            "then": {
                "type": "sequence",
                "children": [{
                    "type": "element",
                    "name": "Individual",
                    "attributes": [{
                        "name": "name",
                        "value_expr": "Name"
                    }],
                    "children": []
                }]
            }
        }]
    },
    guard = "Age >= 0"  // ガード条件として抽出
)
```

**形式的表記:**
```
q_Person_default(Person(Name, Age)) [guard: Age >= 0] →
  Individual[@name=Name]

q_Person_default(Person(Name, Age)) [guard: Age < 0] →
  ε  (空木)
```

### 例3: apply-templates

**入力XSLT:**
```xml
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/People">
    <Employees>
      <xsl:apply-templates select="Person"/>
    </Employees>
  </xsl:template>

  <xsl:template match="Person">
    <Employee name="{Name}"/>
  </xsl:template>
</xsl:stylesheet>
```

**出力MTT:**
```python
MTT(
    states = ["q__People_default", "q_Person_default"],
    rules = [
        MTTRule(
            state = "q__People_default",
            lhs_pattern = "People(children)",
            rhs_output = {
                "type": "sequence",
                "children": [{
                    "type": "element",
                    "name": "Employees",
                    "children": [{
                        "type": "apply-templates",
                        "select": "Person",
                        "call": "apply_to_Person"
                    }]
                }]
            }
        ),
        MTTRule(
            state = "q_Person_default",
            lhs_pattern = "Person(children)",
            rhs_output = {
                "type": "sequence",
                "children": [{
                    "type": "element",
                    "name": "Employee",
                    "attributes": [{
                        "name": "name",
                        "value_expr": "Name"
                    }],
                    "children": []
                }]
            }
        )
    ]
)
```

**形式的表記:**
```
States: Q = {q_People, q_Person, q_Person_list}

Rules:
  q_People(People(person_list)) →
    Employees(q_Person_list(person_list))

  q_Person_list(cons(p, rest)) →
    concat(q_Person(p), q_Person_list(rest))

  q_Person_list(nil) → ε

  q_Person(Person(Name, ...)) →
    Employee[@name=Name]
```

## MTTの形式的検証

### 検証項目

1. **決定性**: 各入力パターンに対して最大1つの規則
2. **完全性**: すべての入力記号に対する規則が存在
3. **終了性**: 無限ループが存在しない

### 決定性チェック

```
Algorithm: CHECK_DETERMINISM
Input: mtt (MTT)
Output: is_deterministic (boolean)

1. pattern_map ← {}
2.
3. FOR EACH rule IN mtt.rules:
4.     key ← (rule.state, rule.lhs_pattern)
5.
6.     IF key IN pattern_map:
7.         // 同じパターンに対する複数の規則
8.         RETURN False
9.
10.     pattern_map[key] ← rule
11.
12. RETURN True
```

### 完全性チェック

```
Algorithm: CHECK_COMPLETENESS
Input: mtt (MTT), input_alphabet (Set[string])
Output: is_complete (boolean), missing (Set[string])

1. covered ← {}
2. missing ← set()
3.
4. FOR EACH rule IN mtt.rules:
5.     input_symbol ← extract_symbol(rule.lhs_pattern)
6.     covered.add(input_symbol)
7.
8. FOR EACH symbol IN input_alphabet:
9.     IF symbol NOT IN covered:
10.         missing.add(symbol)
11.
12. is_complete ← (missing.size == 0)
13. RETURN (is_complete, missing)
```

## 最適化技法

### 1. 状態の統合

同じ出力を生成する状態を統合：

```python
def merge_equivalent_states(mtt: MTT) -> MTT:
    """等価な状態を統合"""
    equivalence_classes = find_equivalent_states(mtt)

    for eq_class in equivalence_classes:
        if len(eq_class) > 1:
            representative = eq_class[0]
            for state in eq_class[1:]:
                replace_state(mtt, state, representative)

    return mtt
```

### 2. デッドコード除去

到達不可能な状態と規則を削除：

```python
def remove_unreachable_states(mtt: MTT) -> MTT:
    """到達不可能な状態を削除"""
    reachable = compute_reachable_states(mtt, mtt.initial_state)

    mtt.states = [s for s in mtt.states if s in reachable]
    mtt.rules = [r for r in mtt.rules if r.state in reachable]

    return mtt
```

## 制限事項と拡張

### 現在の制限

1. **XPath**: 簡単な式のみサポート
2. **パラメータ**: with-paramは部分的サポート
3. **mode**: 単一モードのみ実質サポート

### 今後の拡張

1. **完全なパラメータサポート**: MTTのマクロ機能を完全実装
2. **XPath評価**: より複雑なXPath式のサポート
3. **最適化**: 状態数の最小化

## 関連ドキュメント

- [システム概要](./overview.md)
- [XSDパーサー](./xsd_parser.md)
- [型保存性検証](./type_validator.md)
- [実装例](./examples.md)
