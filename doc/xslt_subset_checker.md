# XSLTサブセットチェッカーアルゴリズム

## 目次

1. [アルゴリズム概要](#アルゴリズム概要)
2. [サブセット定義](#サブセット定義)
3. [詳細設計](#詳細設計)
4. [実装](#実装)
5. [計算量解析](#計算量解析)
6. [例](#例)

## アルゴリズム概要

XSLTが許可されたサブセットに準拠しているかを検証するアルゴリズムです。

**入力:** XSLT文書（XML形式）
**出力:** (is_valid, errors, warnings)

### 検証項目

1. 許可された要素のみ使用されているか
2. 禁止された機能が使われていないか
3. 必須属性が存在するか
4. XPathの複雑度チェック

## サブセット定義

### 許可されている要素

```python
ALLOWED_ELEMENTS = {
    # スタイルシート定義
    "stylesheet",
    "transform",

    # テンプレート
    "template",

    # 制御構造
    "apply-templates",
    "for-each",
    "if",
    "choose",
    "when",
    "otherwise",

    # データ処理
    "value-of",
    "text",

    # 出力生成
    "element",
    "attribute",

    # パラメータ
    "with-param",
    "param"
}
```

### 禁止されている機能

```python
DISALLOWED_FEATURES = {
    # 外部リソースアクセス
    "document",      # 外部ドキュメント読み込み

    # 高度な機能
    "key",           # キー定義
    "import",        # スタイルシートインポート
    "include",       # スタイルシートインクルード

    # 複雑な制御フロー
    "call-template", # 名前付きテンプレート呼び出し
    "variable",      # 変数（複雑な状態管理）

    # データ操作
    "sort",          # ソート
    "number",        # 番号フォーマット

    # コピー操作
    "copy",          # 浅いコピー
    "copy-of"        # 深いコピー
}
```

### 理論的根拠

これらの制限により、XSLTをMacro Tree Transducer (MTT)に確実に変換できます：

1. **決定性**: 非決定的な要素を排除
2. **終了性**: 無限ループを防止
3. **表現力**: MTTで表現可能な変換のみ許可

## 詳細設計

### メインアルゴリズム

```
Algorithm: CHECK_XSLT_SUBSET
Input: xslt_content (XML string)
Output: (is_valid, errors[], warnings[])

1. errors ← []
2. warnings ← []
3.
4. // XML解析
5. TRY:
6.     root ← parse_xml(xslt_content)
7. CATCH ParseError as e:
8.     errors.append("XML Parse Error: " + e.message)
9.     RETURN (False, errors, warnings)
10.
11. // 再帰的に全要素をチェック
12. check_element(root, "", errors, warnings)
13.
14. // 妥当性判定
15. is_valid ← (errors.length == 0)
16.
17. RETURN (is_valid, errors, warnings)
```

### 要素チェックアルゴリズム

```
Algorithm: CHECK_ELEMENT
Input: elem (XML Element), path (string), errors[], warnings[]
Output: Updates errors and warnings

1. local_name ← get_local_name(elem.tag)
2. current_path ← path + "/" + local_name
3.
4. // XSLT名前空間のチェック
5. IF elem.tag STARTS_WITH "{http://www.w3.org/1999/XSL/Transform}":
6.     xslt_element ← remove_namespace(elem.tag)
7.
8.     // 禁止要素のチェック
9.     IF xslt_element IN DISALLOWED_FEATURES:
10.         errors.append(
11.             "Disallowed XSLT element '" + xslt_element +
12.             "' at " + current_path
13.         )
14.     // 許可要素のチェック
15.     ELSE IF xslt_element NOT IN ALLOWED_ELEMENTS:
16.         warnings.append(
17.             "Unknown XSLT element '" + xslt_element +
18.             "' at " + current_path
19.         )
20.
21.     // 要素固有のチェック
22.     SWITCH xslt_element:
23.         CASE "template":
24.             check_template(elem, current_path, errors, warnings)
25.         CASE "if":
26.             check_if(elem, current_path, errors, warnings)
27.         CASE "choose":
28.             check_choose(elem, current_path, errors, warnings)
29.         CASE "apply-templates":
30.             check_apply_templates(elem, current_path, errors, warnings)
31.         CASE "for-each":
32.             check_for_each(elem, current_path, errors, warnings)
33.         CASE "value-of":
34.             check_value_of(elem, current_path, errors, warnings)
35.
36. // 子要素の再帰的チェック
37. FOR EACH child IN elem.children:
38.     check_element(child, current_path, errors, warnings)
```

### 個別要素チェック

#### 1. Template要素

```
Algorithm: CHECK_TEMPLATE
Input: elem, path, errors[], warnings[]

1. match ← elem.get("match")
2.
3. // match属性の必須チェック
4. IF match IS NULL:
5.     errors.append("Template without 'match' attribute at " + path)
6.     RETURN
7.
8. // 複雑なXPathパターンの警告
9. IF match CONTAINS "//" OR
10.    match CONTAINS "ancestor::" OR
11.    match CONTAINS "following::":
12.     warnings.append(
13.         "Complex XPath pattern '" + match +
14.         "' at " + path + " - may not be fully supported"
15.     )
```

#### 2. If要素

```
Algorithm: CHECK_IF
Input: elem, path, errors[], warnings[]

1. test ← elem.get("test")
2.
3. // test属性の必須チェック
4. IF test IS NULL:
5.     errors.append("'if' without 'test' attribute at " + path)
6.     RETURN
7.
8. // 複雑な条件式の警告
9. IF test CONTAINS "contains(" OR
10.    test CONTAINS "substring(" OR
11.    test CONTAINS "concat(":
12.     warnings.append(
13.         "Complex string function in test '" + test +
14.         "' at " + path
15.     )
```

#### 3. Choose要素

```
Algorithm: CHECK_CHOOSE
Input: elem, path, errors[], warnings[]

1. has_when ← False
2.
3. FOR EACH child IN elem.children:
4.     local_name ← get_local_name(child.tag)
5.     IF local_name == "when":
6.         has_when ← True
7.         BREAK
8.
9. IF NOT has_when:
10.     errors.append("'choose' without 'when' at " + path)
```

#### 4. Apply-Templates要素

```
Algorithm: CHECK_APPLY_TEMPLATES
Input: elem, path, errors[], warnings[]

1. select ← elem.get("select")
2.
3. IF select EXISTS:
4.     // 複雑な軸の警告
5.     IF select CONTAINS "preceding::" OR
6.        select CONTAINS "following::":
7.         warnings.append(
8.             "Complex axis in select '" + select +
9.             "' at " + path
10.         )
```

#### 5. For-Each要素

```
Algorithm: CHECK_FOR_EACH
Input: elem, path, errors[], warnings[]

1. select ← elem.get("select")
2.
3. // select属性の必須チェック
4. IF select IS NULL:
5.     errors.append("'for-each' without 'select' attribute at " + path)
```

#### 6. Value-Of要素

```
Algorithm: CHECK_VALUE_OF
Input: elem, path, errors[], warnings[]

1. select ← elem.get("select")
2.
3. // select属性の必須チェック
4. IF select IS NULL:
5.     errors.append("'value-of' without 'select' attribute at " + path)
```

## 実装

### データ構造

```python
class XSLTSubsetChecker:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
```

### メソッド一覧

```python
class XSLTSubsetChecker:
    def check_xslt(self, xslt_content: str) -> Tuple[bool, List[str], List[str]]:
        """メインチェック関数"""

    def _check_element(self, elem: ET.Element, path: str):
        """要素の再帰的チェック"""

    def _check_template(self, elem: ET.Element, path: str):
        """template要素のチェック"""

    def _check_if(self, elem: ET.Element, path: str):
        """if要素のチェック"""

    def _check_choose(self, elem: ET.Element, path: str):
        """choose要素のチェック"""

    def _check_apply_templates(self, elem: ET.Element, path: str):
        """apply-templates要素のチェック"""

    def _check_for_each(self, elem: ET.Element, path: str):
        """for-each要素のチェック"""

    def _check_value_of(self, elem: ET.Element, path: str):
        """value-of要素のチェック"""

    def _get_local_name(self, tag: str) -> str:
        """ローカル名の取得"""
```

## 計算量解析

### 時間計算量

**O(m)**

ここで、mはXSLT文書内の要素数

**詳細:**
- XML解析: O(m)
- 要素の走査: O(m)（全要素を1回ずつ訪問）
- 各要素のチェック: O(1)（属性数は定数と仮定）

**合計: O(m)**

### 空間計算量

**O(m + e + w)**

- m: 入力XSLTのサイズ
- e: エラー数
- w: 警告数

通常、e, w << m なので、**O(m)**

## 例

### 例1: 有効なXSLT

**入力:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="Person">
    <xsl:if test="Age >= 0">
      <Individual fullname="{Name}" years="{Age}"/>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
```

**処理:**
```
1. Parse XML → success
2. Check <stylesheet> → OK (allowed)
3. Check <template match="Person"> → OK
   - match attribute exists → OK
   - Pattern "Person" is simple → OK
4. Check <if test="Age >= 0"> → OK
   - test attribute exists → OK
   - Simple comparison → OK
5. Check literal element <Individual> → OK
6. Check attribute value templates → OK
```

**出力:**
```python
is_valid = True
errors = []
warnings = []
```

### 例2: 禁止要素を含むXSLT

**入力:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <xsl:variable name="data" select="document('external.xml')"/>
    <xsl:copy-of select="$data"/>
  </xsl:template>
</xsl:stylesheet>
```

**処理:**
```
1. Parse XML → success
2. Check <stylesheet> → OK
3. Check <template> → OK
4. Check <variable> → ERROR (disallowed)
   - "variable" is in DISALLOWED_FEATURES
5. Check document() call → ERROR (disallowed)
   - "document" function detected
6. Check <copy-of> → ERROR (disallowed)
   - "copy-of" is in DISALLOWED_FEATURES
```

**出力:**
```python
is_valid = False
errors = [
    "Disallowed XSLT element 'variable' at /stylesheet/template/variable",
    "Disallowed XSLT element 'copy-of' at /stylesheet/template/copy-of"
]
warnings = []
```

### 例3: 複雑なXPath（警告）

**入力:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="//Person">
    <xsl:if test="contains(Name, 'Smith')">
      <Match/>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
```

**処理:**
```
1. Parse XML → success
2. Check <template match="//Person"> → WARNING
   - Pattern contains "//" (descendant axis)
3. Check <if test="contains(Name, 'Smith')"> → WARNING
   - Contains string function "contains()"
```

**出力:**
```python
is_valid = True
errors = []
warnings = [
    "Complex XPath pattern '//Person' at /stylesheet/template - may not be fully supported",
    "Complex string function in test 'contains(Name, 'Smith')' at /stylesheet/template/if"
]
```

## エラーメッセージ設計

### エラーの種類

1. **必須属性欠落**
   ```
   Template without 'match' attribute at /stylesheet/template
   ```

2. **禁止要素使用**
   ```
   Disallowed XSLT element 'document' at /stylesheet/template/variable
   ```

3. **構造エラー**
   ```
   'choose' without 'when' at /stylesheet/template/choose
   ```

### 警告の種類

1. **複雑なXPath**
   ```
   Complex XPath pattern '//Person' at /stylesheet/template
   ```

2. **未知の要素**
   ```
   Unknown XSLT element 'custom-element' at /stylesheet/template
   ```

3. **複雑な関数**
   ```
   Complex string function in test 'contains(...)' at /stylesheet/template/if
   ```

## 拡張可能性

### カスタムルールの追加

```python
class ExtendedXSLTChecker(XSLTSubsetChecker):
    def __init__(self):
        super().__init__()
        self.custom_rules = []

    def add_custom_rule(self, rule_func):
        """カスタム検証ルールを追加"""
        self.custom_rules.append(rule_func)

    def _check_element(self, elem, path):
        super()._check_element(elem, path)

        # カスタムルールの適用
        for rule in self.custom_rules:
            rule(elem, path, self.errors, self.warnings)
```

### 設定可能なサブセット

```python
class ConfigurableXSLTChecker(XSLTSubsetChecker):
    def __init__(self, allowed_elements=None, disallowed_features=None):
        super().__init__()
        self.allowed_elements = allowed_elements or ALLOWED_ELEMENTS
        self.disallowed_features = disallowed_features or DISALLOWED_FEATURES
```

## テストケース

### テスト1: 基本的な有効性

```python
def test_valid_basic():
    xslt = """
    <xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
      <xsl:template match="root">
        <output/>
      </xsl:template>
    </xsl:stylesheet>
    """
    checker = XSLTSubsetChecker()
    is_valid, errors, warnings = checker.check_xslt(xslt)
    assert is_valid == True
    assert len(errors) == 0
```

### テスト2: 禁止要素の検出

```python
def test_disallowed_element():
    xslt = """
    <xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
      <xsl:template match="root">
        <xsl:variable name="x" select="1"/>
      </xsl:template>
    </xsl:stylesheet>
    """
    checker = XSLTSubsetChecker()
    is_valid, errors, warnings = checker.check_xslt(xslt)
    assert is_valid == False
    assert len(errors) > 0
    assert "variable" in errors[0]
```

### テスト3: 必須属性の検証

```python
def test_missing_attribute():
    xslt = """
    <xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
      <xsl:template>
        <output/>
      </xsl:template>
    </xsl:stylesheet>
    """
    checker = XSLTSubsetChecker()
    is_valid, errors, warnings = checker.check_xslt(xslt)
    assert is_valid == False
    assert any("match" in e for e in errors)
```

### テスト4: XPath複雑度の警告

```python
def test_complex_xpath_warning():
    xslt = """
    <xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
      <xsl:template match="//person">
        <output/>
      </xsl:template>
    </xsl:stylesheet>
    """
    checker = XSLTSubsetChecker()
    is_valid, errors, warnings = checker.check_xslt(xslt)
    assert is_valid == True
    assert len(warnings) > 0
    assert "//" in warnings[0]
```

## パフォーマンス最適化

### 1. 早期リターン

重大なエラー発見時に即座に処理を中断：

```python
def check_xslt(self, xslt_content: str, fail_fast: bool = False):
    # ...
    if fail_fast and len(self.errors) > 0:
        return False, self.errors, self.warnings
```

### 2. キャッシング

要素名の正規化結果をキャッシュ：

```python
self._local_name_cache = {}

def _get_local_name(self, tag: str) -> str:
    if tag not in self._local_name_cache:
        self._local_name_cache[tag] = tag.split("}", 1)[1] if "}" in tag else tag
    return self._local_name_cache[tag]
```

## 関連ドキュメント

- [システム概要](./overview.md)
- [MTT変換アルゴリズム](./mtt_converter.md)
- [実装例](./examples.md)
