# 木変換モデルによるXSLT変換の理論的証明

具体例で理論を示します。シンプルな例から始めて、段階的に形式化していきます。

## 1. 具体例の設定

### ソースXSD（人物情報）
```xml
<!-- source.xsd -->
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
```

### ターゲットXSD（属性ベース）
```xml
<!-- target.xsd -->
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Individual">
    <xs:complexType>
      <xs:attribute name="fullname" type="xs:string" use="required"/>
      <xs:attribute name="years" use="required">
        <xs:simpleType>
          <xs:restriction base="xs:integer">
            <xs:minInclusive value="0"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

### XSLT変換
```xml
<!-- transform.xsl -->
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="Person">
    <Individual fullname="{Name}" years="{Age}"/>
  </xsl:template>
</xsl:stylesheet>
```

## 2. 木文法としての形式化

### 2.1 正規木文法（Regular Tree Grammar）での表現

**ソーススキーマ S の木文法 G_S:**
```
生成規則:
S → Person(n, a)
n → Name(text)
a → Age(integer)

型制約:
text ∈ String
integer ∈ ℤ
```

**ターゲットスキーマ T の木文法 G_T:**
```
生成規則:
T → Individual[@fullname=s, @years=i]

型制約:
s ∈ String
i ∈ ℤ⁺ (非負整数)
```

### 2.2 木変換器の形式的定義

**トップダウン木変換器（Top-Down Tree Transducer: TDTT）**

XSLT変換を TDTT として定義:
```
M = (Q, Σ_S, Σ_T, q_0, R)

Q = {q_0}  (状態集合)
Σ_S = {Person, Name, Age, text, integer}  (入力アルファベット)
Σ_T = {Individual, @fullname, @years}  (出力アルファベット)
q_0 = 初期状態

変換規則 R:
r1: q_0(Person(x_name, x_age)) 
    → Individual[@fullname=q_name(x_name), @years=q_age(x_age)]

r2: q_name(Name(s)) → s  (where s ∈ String)

r3: q_age(Age(i)) → i    (where i ∈ ℤ)
```

## 3. 型保存性の証明

### 3.1 証明すべき定理

**定理（型保存性）:**
```
∀t ∈ L(G_S), M(t) ∈ L(G_T)
```
すなわち、ソーススキーマで有効な任意の木 t を変換すると、
必ずターゲットスキーマで有効な木が得られる。

### 3.2 証明（構造的帰納法）

**ステップ1: 仮定**
```
t = Person(Name(s), Age(i)) where s ∈ String, i ∈ ℤ
```
これは G_S の生成規則により有効な木。

**ステップ2: 変換の適用**
```
M(t) = M(Person(Name(s), Age(i)))
     = Individual[@fullname=M(Name(s)), @years=M(Age(i))]  (r1 適用)
     = Individual[@fullname=s, @years=i]                    (r2, r3 適用)
```

**ステップ3: 型制約の検証**

この例では追加の型制約があります：
- ターゲットの `@years` は非負整数 (ℤ⁺) 
- ソースの `Age` は任意の整数 (ℤ)

**問題点の発見！**
```
反例: Person(Name("Alice"), Age(-5))
→ Individual[@fullname="Alice", @years=-5]  ← ターゲットXSDで無効！
```

**修正版XSLT（ガード条件追加）:**
```xml
<xsl:template match="Person">
  <xsl:if test="Age >= 0">
    <Individual fullname="{Name}" years="{Age}"/>
  </xsl:if>
</xsl:template>
```

**修正版変換規則:**
```
r1': q_0(Person(x_name, x_age)) 
     → if value(x_age) >= 0 
       then Individual[@fullname=q_name(x_name), @years=q_age(x_age)]
       else ε (空木)
```

**修正後の証明:**
```
Case 1: i >= 0
  M(t) = Individual[@fullname=s, @years=i]
  ∵ i ∈ ℤ⁺, s ∈ String
  ∴ M(t) ∈ L(G_T) ✓

Case 2: i < 0
  M(t) = ε (変換スキップ)
  ∴ 無効なターゲットXMLは生成されない ✓
```

## 4. より複雑な例：選択肢とカーディナリティ

### ソースXSD（複数の電話番号）
```xml
<xs:element name="Contact">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Name" type="xs:string"/>
      <xs:element name="Phone" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

### ターゲットXSD（最初の電話番号のみ）
```xml
<xs:element name="Person">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Name" type="xs:string"/>
      <xs:element name="PrimaryPhone" type="xs:string" minOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

### 木文法での表現

**ソース:**
```
S → Contact(n, phones)
n → Name(text)
phones → Phone(text) · phones | ε
```

**ターゲット:**
```
T → Person(n, phone?)
n → Name(text)
phone? → PrimaryPhone(text) | ε
```

### 変換規則
```
q_0(Contact(x_name, x_phones)) 
  → Person(q_name(x_name), q_first_phone(x_phones))

q_name(Name(s)) → Name(s)

q_first_phone(Phone(s) · rest) → PrimaryPhone(s)  // 最初のみ取得
q_first_phone(ε) → ε
```

### 証明のポイント

**補題1（リスト変換）:**
```
phones = Phone(s₁) · Phone(s₂) · ... · Phone(sₙ)  (n >= 0)
⇒ q_first_phone(phones) = PrimaryPhone(s₁)  if n >= 1
                         = ε                 if n = 0
```

**主定理:**
```
∀t ∈ L(G_S), M(t) ∈ L(G_T)

証明:
t = Contact(Name(s), phones) where phones は Phone の列
M(t) = Person(Name(s), q_first_phone(phones))
     = Person(Name(s), PrimaryPhone(s₁)) or Person(Name(s), ε)
これは G_T の生成規則により有効 ✓
```

## 5. 実装：型チェッカーの疑似コード

```python
# XSD → 正規木文法の変換
def xsd_to_tree_grammar(xsd_file):
    """XSDを木文法に変換"""
    grammar = {
        'productions': [],
        'type_constraints': {}
    }
    # XSDをパースして生成規則を抽出
    # 省略...
    return grammar

# XSLT → 木変換器の変換
def xslt_to_transducer(xslt_file):
    """XSLTを木変換器に変換"""
    transducer = {
        'states': set(),
        'rules': []
    }
    # XSLTをパースして変換規則を抽出
    # 省略...
    return transducer

# 型保存性の検証
def verify_type_preservation(source_grammar, target_grammar, transducer):
    """
    ∀t ∈ L(G_S), M(t) ∈ L(G_T) を検証
    """
    # 1. ソース文法から代表的な木を生成
    representative_trees = generate_representative_trees(source_grammar)
    
    # 2. 各木に変換を適用
    for tree in representative_trees:
        output_tree = apply_transducer(transducer, tree)
        
        # 3. ターゲット文法で検証
        if not validate_against_grammar(output_tree, target_grammar):
            return False, f"反例: {tree} → {output_tree}"
    
    # 4. 形式的証明の生成（構造的帰納法）
    proof = generate_induction_proof(source_grammar, target_grammar, transducer)
    
    return True, proof

# 構造的帰納法による証明生成
def generate_induction_proof(source_grammar, target_grammar, transducer):
    proof_steps = []
    
    # 基底ケース
    proof_steps.append("Base case: 葉ノード（プリミティブ型）")
    for prod in source_grammar['productions']:
        if is_terminal(prod):
            proof_steps.append(f"  {prod} の変換は型制約を保存")
    
    # 帰納ステップ
    proof_steps.append("Inductive step: 複合ノード")
    for prod in source_grammar['productions']:
        if not is_terminal(prod):
            # 対応する変換規則を見つける
            rule = find_matching_rule(transducer, prod)
            proof_steps.append(f"  {prod} → {rule.output}")
            
            # 子ノードの型チェック
            for child in rule.children:
                if not check_child_type(child, target_grammar):
                    proof_steps.append(f"    警告: {child} は型制約違反の可能性")
    
    return "\n".join(proof_steps)
```

## 6. ドキュメント化テンプレート

### 変換証明書（Transformation Certificate）

```markdown
# 変換証明書: Person → Individual

## 1. スキーマ定義
- ソース: source.xsd (Person型)
- ターゲット: target.xsd (Individual型)

## 2. 木文法
### ソース文法 G_S
- 生成規則: [上記参照]
- 型制約: Age ∈ ℤ

### ターゲット文法 G_T  
- 生成規則: [上記参照]
- 型制約: @years ∈ ℤ⁺

## 3. 変換規則
[TDTT M の定義]

## 4. 型保存性の証明
**定理**: ∀t ∈ L(G_S) s.t. Age(t) >= 0, M(t) ∈ L(G_T)

**証明**: 
[構造的帰納法による証明]

**制約条件**: 
- 入力のAge値は非負でなければならない
- 負の値の場合、変換はスキップされる

## 5. テストケース
### カバレッジマトリクス
| 構造パターン | テストケース | 期待結果 | 状態 |
|------------|-------------|---------|------|
| 基本ケース  | Age=25      | ✓       | PASS |
| 境界値     | Age=0       | ✓       | PASS |
| 無効値     | Age=-1      | スキップ | PASS |

## 6. 既知の制限
- ソースのAge < 0 の場合、情報ロスが発生
- 代替策: エラーログへの記録を推奨
```

## 7. 実用的ツールとの接続

### XDuce型チェッカー（概念実装）

```ocaml
(* XDuce風の型定義 *)
type source = Person[Name[String], Age[Int]]
type target = Individual[@fullname:String, @years:PosInt]

(* 変換関数 *)
fun transform (Person[n, a]) : target? =
  if a >= 0 then
    Some(Individual[@fullname=n, @years=a])
  else
    None

(* 型システムによる自動検証 *)
(* コンパイル時に型エラーを検出 *)
```

### Schematronによる実行時検証

```xml
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron">
  <sch:pattern>
    <sch:rule context="Person">
      <sch:assert test="Age >= 0">
        年齢は非負でなければなりません（変換前提条件）
      </sch:assert>
    </sch:rule>
  </sch:pattern>
</sch:schema>
```

## まとめ

**理論的証明の利点:**
1. ✅ **網羅性**: すべての可能な入力を数学的にカバー
2. ✅ **早期発見**: 設計段階で型不整合を検出
3. ✅ **ドキュメント**: 証明自体が厳密な仕様書

**限界:**
- 複雑なXSLT（Turing完全な機能）は解析困難
- 実用的には「証明可能な部分」と「テストで補完する部分」の組み合わせが現実的

より複雑な実例（条件分岐、複数パス、集約処理など）についても解説が必要でしょうか？