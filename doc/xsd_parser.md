# XSDパーサーと木文法変換アルゴリズム

## 目次

1. [アルゴリズム概要](#アルゴリズム概要)
2. [理論的背景](#理論的背景)
3. [詳細設計](#詳細設計)
4. [実装](#実装)
5. [計算量解析](#計算量解析)
6. [例](#例)

## アルゴリズム概要

XSDスキーマを解析し、正規木文法（Regular Tree Grammar）に変換するアルゴリズムです。

**入力:** XSDスキーマ（XML形式）
**出力:** TreeGrammar（生成規則、型制約、属性情報）

### 主要機能

1. XSD要素の構造解析
2. 複合型と単純型の処理
3. 生成規則の生成
4. 型制約の抽出
5. カーディナリティの処理

## 理論的背景

### 正規木文法の定義

**形式的定義:**
```
G = (N, Σ, P, S)

N: 非終端記号の集合
Σ: 終端記号の集合（基本型）
P: 生成規則の集合 P ⊆ N × (N ∪ Σ)*
S: 開始記号 S ∈ N
```

### XSDから木文法への対応

| XSD構成要素 | 木文法要素 |
|------------|----------|
| xs:element | 非終端記号 N |
| xs:complexType | 生成規則 |
| xs:simpleType | 終端記号 Σ |
| xs:sequence | 順序付き生成規則 |
| xs:choice | 選択肢を持つ規則 |
| minOccurs/maxOccurs | カーディナリティ制約 |

### 生成規則の形式

```
A → σ(B₁, B₂, ..., Bₙ)

A: 非終端記号（親要素）
σ: コンストラクタ（要素名）
B₁, ..., Bₙ: 子要素（非終端記号または終端記号）
```

## 詳細設計

### アルゴリズムの構造

```
Algorithm: XSD_TO_TREE_GRAMMAR
Input: xsd_content (XML string)
Output: TreeGrammar

1. parse_xml(xsd_content) → root
2. grammar ← new TreeGrammar()
3.
4. // Phase 1: 型定義の収集
5. FOR EACH complexType IN root:
6.     collect_complex_type(complexType)
7. FOR EACH simpleType IN root:
8.     collect_simple_type(simpleType)
9.
10. // Phase 2: 要素の処理
11. FOR EACH element IN root:
12.     IF element.name EXISTS:
13.         IF grammar.root_element is empty:
14.             grammar.root_element ← element.name
15.         process_element(element, element.name)
16.
17. RETURN grammar
```

### 要素処理アルゴリズム

```
Algorithm: PROCESS_ELEMENT
Input: elem (XML Element), element_name (string)
Output: Updates grammar

1. // カーディナリティの取得
2. min_occurs ← elem.get("minOccurs", default=1)
3. max_occurs ← elem.get("maxOccurs", default=1)
4. cardinality ← (min_occurs, max_occurs)
5.
6. // 型参照のチェック
7. type_ref ← elem.get("type")
8.
9. IF type_ref EXISTS:
10.     IF type_ref STARTS_WITH "xs:":
11.         // 組み込み型
12.         base_type ← remove_prefix(type_ref, "xs:")
13.         ADD_TYPE_CONSTRAINT(element_name, base_type)
14.         ADD_PRODUCTION(element_name → base_type, cardinality)
15.     ELSE:
16.         // カスタム型参照
17.         IF type_ref IN complex_types:
18.             process_complex_type(complex_types[type_ref], element_name, cardinality)
19.         ELSE IF type_ref IN simple_types:
20.             process_simple_type(simple_types[type_ref], element_name, cardinality)
21. ELSE:
22.     // インライン型定義
23.     inline_complex ← elem.find("complexType")
24.     IF inline_complex EXISTS:
25.         process_complex_type(inline_complex, element_name, cardinality)
26.     ELSE:
27.         inline_simple ← elem.find("simpleType")
28.         IF inline_simple EXISTS:
29.             process_simple_type(inline_simple, element_name, cardinality)
```

### 複合型処理アルゴリズム

```
Algorithm: PROCESS_COMPLEX_TYPE
Input: ct (complexType element), element_name, cardinality
Output: Updates grammar

1. // 属性の処理
2. attributes ← []
3. FOR EACH attr IN ct.findall("attribute"):
4.     attr_name ← attr.get("name")
5.     attr_type ← attr.get("type", "xs:string")
6.     required ← (attr.get("use") == "required")
7.     attributes.append((attr_name, attr_type, required))
8.
9. IF attributes NOT EMPTY:
10.     grammar.attributes[element_name] ← attributes
11.
12. // コンテンツモデルの処理
13. sequence ← ct.find("sequence")
14. choice ← ct.find("choice")
15. all_elem ← ct.find("all")
16.
17. IF sequence EXISTS:
18.     process_sequence(sequence, element_name, cardinality)
19. ELSE IF choice EXISTS:
20.     process_choice(choice, element_name, cardinality)
21. ELSE IF all_elem EXISTS:
22.     process_all(all_elem, element_name, cardinality)
23. ELSE:
24.     // simpleContent
25.     simple_content ← ct.find("simpleContent")
26.     IF simple_content EXISTS:
27.         extension ← simple_content.find("extension")
28.         IF extension EXISTS:
29.             base ← extension.get("base", "xs:string")
30.             ADD_TYPE_CONSTRAINT(element_name, base)
```

### Sequence処理

```
Algorithm: PROCESS_SEQUENCE
Input: sequence (XML element), parent_name, cardinality
Output: Updates grammar

1. children ← []
2.
3. FOR EACH child IN sequence.findall("element"):
4.     child_name ← child.get("name") OR child.get("ref")
5.
6.     IF child_name EXISTS:
7.         children.append(child_name)
8.
9.         // インライン定義の場合は再帰処理
10.         IF child.get("name") EXISTS:
11.             process_element(child, child_name, parent_name)
12.
13. IF children NOT EMPTY:
14.     production ← Production(
15.         lhs = parent_name,
16.         rhs = children,
17.         type = "sequence",
18.         cardinality = cardinality
19.     )
20.     grammar.productions.append(production)
```

### 単純型処理（制約付き）

```
Algorithm: PROCESS_SIMPLE_TYPE
Input: st (simpleType element), element_name, cardinality
Output: Updates grammar

1. restriction ← st.find("restriction")
2.
3. IF restriction EXISTS:
4.     base ← restriction.get("base", "xs:string")
5.     base ← remove_prefix(base, "xs:")
6.
7.     // 制約の収集
8.     restrictions ← {}
9.     FOR EACH child IN restriction:
10.         constraint_type ← get_local_name(child.tag)
11.         value ← child.get("value")
12.
13.         IF value EXISTS:
14.             restrictions[constraint_type] ← value
15.
16.     // 型制約の追加
17.     type_constraint ← TypeConstraint(
18.         base_type = base,
19.         restrictions = restrictions
20.     )
21.     grammar.type_constraints[element_name] ← type_constraint
22.
23.     // 生成規則の追加
24.     production ← Production(
25.         lhs = element_name,
26.         rhs = [base],
27.         cardinality = cardinality
28.     )
29.     grammar.productions.append(production)
```

## 実装

### データ構造

```python
@dataclass
class TypeConstraint:
    """型制約"""
    base_type: str
    restrictions: Dict[str, Any]

@dataclass
class Production:
    """生成規則"""
    lhs: str                    # 左辺（非終端記号）
    rhs: List[str]              # 右辺（記号列）
    element_type: str           # sequence, choice, all
    cardinality: tuple          # (min, max)

@dataclass
class TreeGrammar:
    """木文法"""
    root_element: str
    productions: List[Production]
    type_constraints: Dict[str, TypeConstraint]
    attributes: Dict[str, List[tuple]]
```

### 主要な関数

```python
class XSDParser:
    def parse(self, xsd_content: str) -> TreeGrammar:
        """XSDを解析して木文法に変換"""
        root = ET.fromstring(xsd_content)
        self._collect_types(root)

        for elem in root.findall(f".//{{{XS_NS}}}element"):
            if elem.get("name"):
                element_name = elem.get("name")
                if not self.grammar.root_element:
                    self.grammar.root_element = element_name
                self._process_element(elem, element_name)

        return self.grammar
```

## 計算量解析

### 時間計算量

**最悪ケース: O(n)**

ここで、nはXSD内の要素数（element + complexType + simpleType）

**詳細:**
- XML解析: O(n)
- 型収集: O(t)（tは型定義数、t ≤ n）
- 要素処理: O(e)（eは要素数、e ≤ n）
- 各要素の処理: O(1)（子要素数は定数と仮定）

**合計: O(n) + O(t) + O(e) = O(n)**

### 空間計算量

**O(n + p)**

- n: 入力XSDのサイズ
- p: 生成される生成規則の数

通常、p ≈ n なので、**O(n)**

## 例

### 入力XSD

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Person">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Name" type="xs:string"/>
        <xs:element name="Age" type="xs:integer"/>
        <xs:element name="Email" type="xs:string" minOccurs="0"/>
      </xs:sequence>
      <xs:attribute name="id" type="xs:integer" use="required"/>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

### 処理ステップ

**Phase 1: 型収集**
- 複合型: なし（インライン定義）
- 単純型: なし

**Phase 2: 要素処理**

1. ルート要素 "Person" を発見
   - grammar.root_element = "Person"

2. Person要素の処理
   - 複合型（インライン）を検出

3. 複合型の処理
   - 属性発見: id (integer, required)
   - sequence発見

4. Sequenceの処理
   - 子要素: Name, Age, Email
   - カーディナリティ: Name(1,1), Age(1,1), Email(0,1)

### 出力TreeGrammar

```python
TreeGrammar(
    root_element = "Person",

    productions = [
        Production(
            lhs = "Person",
            rhs = ["Name", "Age", "Email"],
            element_type = "sequence",
            cardinality = (1, 1)
        ),
        Production(
            lhs = "Name",
            rhs = ["string"],
            element_type = "sequence",
            cardinality = (1, 1)
        ),
        Production(
            lhs = "Age",
            rhs = ["integer"],
            element_type = "sequence",
            cardinality = (1, 1)
        ),
        Production(
            lhs = "Email",
            rhs = ["string"],
            element_type = "sequence",
            cardinality = (0, 1)
        )
    ],

    type_constraints = {
        "Name": TypeConstraint(base_type="string", restrictions={}),
        "Age": TypeConstraint(base_type="integer", restrictions={}),
        "Email": TypeConstraint(base_type="string", restrictions={})
    },

    attributes = {
        "Person": [("id", "integer", True)]
    }
)
```

### 木文法表記

```
# 開始記号
S → Person

# 生成規則
Person → Person(Name, Age, Email?)[@id:integer]
Name → string
Age → integer
Email → string

# カーディナリティ
Name: (1, 1)
Age: (1, 1)
Email: (0, 1)
```

## エラーハンドリング

### 1. XML解析エラー

```python
try:
    root = ET.fromstring(xsd_content)
except ET.ParseError as e:
    raise ValueError(f"Invalid XSD: {str(e)}")
```

### 2. 不正な型参照

```python
if type_ref in self.complex_types:
    self._process_complex_type(...)
elif type_ref in self.simple_types:
    self._process_simple_type(...)
else:
    # 警告: 未定義の型参照
    warnings.append(f"Undefined type reference: {type_ref}")
```

### 3. 循環参照の検出

```python
def _process_element(self, elem, element_name, visited=None):
    if visited is None:
        visited = set()

    if element_name in visited:
        raise ValueError(f"Circular reference detected: {element_name}")

    visited.add(element_name)
    # 処理続行...
```

## 最適化技法

### 1. メモ化

```python
self.element_cache = {}

def _process_element(self, elem, element_name):
    if element_name in self.element_cache:
        return self.element_cache[element_name]

    result = # ... 処理 ...
    self.element_cache[element_name] = result
    return result
```

### 2. 遅延評価

型定義の解決を実際に必要になるまで遅延させる。

### 3. インクリメンタル処理

大規模なXSDの場合、ストリーミング解析を使用。

## 制限事項

1. **xs:import**: 外部スキーマのインポートは未サポート
2. **xs:include**: スキーマのインクルードは未サポート
3. **複雑なXPath**: xs:keyやxs:uniqueの制約は未処理
4. **再帰型**: 深い再帰は処理できるが、無限ループの検出が必要

## テストケース

### テスト1: 基本型

```python
def test_basic_types():
    xsd = """
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:element name="Root" type="xs:string"/>
    </xs:schema>
    """
    grammar = XSDParser().parse(xsd)
    assert grammar.root_element == "Root"
    assert len(grammar.productions) == 1
```

### テスト2: 複合型とsequence

```python
def test_complex_sequence():
    xsd = """
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:element name="Person">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="Name" type="xs:string"/>
            <xs:element name="Age" type="xs:integer"/>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
    </xs:schema>
    """
    grammar = XSDParser().parse(xsd)
    assert len(grammar.productions) == 3
```

### テスト3: 制約付き単純型

```python
def test_restricted_simple_type():
    xsd = """
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:element name="Age">
        <xs:simpleType>
          <xs:restriction base="xs:integer">
            <xs:minInclusive value="0"/>
            <xs:maxInclusive value="150"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:element>
    </xs:schema>
    """
    grammar = XSDParser().parse(xsd)
    constraint = grammar.type_constraints["Age"]
    assert constraint.restrictions["minInclusive"] == "0"
    assert constraint.restrictions["maxInclusive"] == "150"
```

## 関連ドキュメント

- [システム概要](./overview.md)
- [XSLT to MTT変換](./mtt_converter.md)
- [型保存性検証](./type_validator.md)
