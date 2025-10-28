# 実装例とフローチャート

## 目次

1. [完全な使用例](#完全な使用例)
2. [フローチャート](#フローチャート)
3. [コード例](#コード例)
4. [ユースケース](#ユースケース)
5. [トラブルシューティング](#トラブルシューティング)

## 完全な使用例

### 例1: 基本的な変換の検証

この例では、Person型からIndividual型への基本的な変換を検証します。

#### ステップ1: ソースXSDの定義

```xml
<?xml version="1.0" encoding="UTF-8"?>
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

#### ステップ2: ターゲットXSDの定義

```xml
<?xml version="1.0" encoding="UTF-8"?>
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

#### ステップ3: XSLT変換の定義

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

#### ステップ4: Pythonでの検証

```python
from backend.xslt_checker import XSLTSubsetChecker
from backend.xsd_parser import XSDParser
from backend.mtt_converter import XSLTToMTTConverter
from backend.type_validator import TypePreservationValidator

# ファイルからXSD/XSLTを読み込み
with open('source.xsd') as f:
    source_xsd = f.read()

with open('target.xsd') as f:
    target_xsd = f.read()

with open('transform.xsl') as f:
    xslt = f.read()

# Phase 1: XSLTサブセットチェック
print("Phase 1: XSLT Subset Check")
subset_checker = XSLTSubsetChecker()
is_valid, errors, warnings = subset_checker.check_xslt(xslt)

if not is_valid:
    print("❌ XSLT does not conform to subset")
    for error in errors:
        print(f"  ERROR: {error}")
    exit(1)

print("✓ XSLT conforms to allowed subset")

# Phase 2: XSD解析
print("\nPhase 2: XSD Parsing")
source_parser = XSDParser()
source_grammar = source_parser.parse(source_xsd)
print(f"✓ Source grammar: {source_grammar.root_element}")

target_parser = XSDParser()
target_grammar = target_parser.parse(target_xsd)
print(f"✓ Target grammar: {target_grammar.root_element}")

# Phase 3: MTT変換
print("\nPhase 3: MTT Conversion")
mtt_converter = XSLTToMTTConverter()
mtt = mtt_converter.convert(xslt)
print(f"✓ MTT generated: {len(mtt.states)} states, {len(mtt.rules)} rules")

# Phase 4: 型保存性検証
print("\nPhase 4: Type Preservation Validation")
validator = TypePreservationValidator()
result = validator.validate(source_grammar, target_grammar, mtt)

if result.is_valid:
    print("✅ Type preservation is satisfied!")
else:
    print("❌ Type preservation failed!")

# 証明ステップの表示
print("\nProof Steps:")
for step in result.proof_steps:
    print(f"  {step}")

# エラーと警告の表示
if result.errors:
    print("\nErrors:")
    for error in result.errors:
        print(f"  ❌ {error}")

if result.warnings:
    print("\nWarnings:")
    for warning in result.warnings:
        print(f"  ⚠️  {warning}")

# カバレッジマトリクスの表示
print("\nCoverage Matrix:")
for mapping in result.coverage_matrix['mappings']:
    print(f"  {mapping['source']} → {mapping['target']} [{mapping['status']}]")
```

#### 期待される出力

```
Phase 1: XSLT Subset Check
✓ XSLT conforms to allowed subset

Phase 2: XSD Parsing
✓ Source grammar: Person
✓ Target grammar: Individual

Phase 3: MTT Conversion
✓ MTT generated: 1 states, 1 rules

Phase 4: Type Preservation Validation
✅ Type preservation is satisfied!

Proof Steps:
  Type Preservation Validation
  ==================================================
  Source grammar root: Person
  Target grammar root: Individual
  MTT states: 1

  Step 1: Structural Validation
  --------------------------------------------------
  ✓ Root element mapping found: Person
  ✓ Production covered: Name → ['string']
  ✓ Production covered: Age → ['integer']
  ✓ Production covered: Person → ['Name', 'Age']

  Step 2: Type Constraint Validation
  --------------------------------------------------
  Checking type constraint for: Name
    ✓ Type compatible: string → string
  Checking type constraint for: Age
    ✓ Type compatible: integer → integer
    ! Target has restriction: minInclusive=0

  Step 3: Cardinality Validation
  --------------------------------------------------
  Cardinality check: Person (1,1) → Individual (1,1)
    ✓ Cardinality compatible

  Conclusion: Type preservation is satisfied ✓

Warnings:
  ⚠️  Target element 'years' has minInclusive=0. Ensure source values satisfy this constraint.

Coverage Matrix:
  Person → Individual [✓]
  Name → fullname [✓]
  Age → years [✓]
```

## フローチャート

### 全体フロー

```
┌─────────────────────────────────────────────────┐
│                  START                          │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  入力データ受付     │
        │  - Source XSD       │
        │  - Target XSD       │
        │  - XSLT             │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Phase 1:            │
        │ XSLTサブセット      │
        │ チェック            │
        └─────────┬───────────┘
                  │
                  ├─── No ───→ ┌──────────────┐
                  │            │ エラー返却   │ → END
                  │            └──────────────┘
                 Yes
                  │
                  ▼
        ┌─────────────────────┐
        │ Phase 2:            │
        │ XSD解析             │
        │ ・ソース文法        │
        │ ・ターゲット文法    │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Phase 3:            │
        │ XSLT → MTT変換      │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Phase 4:            │
        │ 型保存性検証        │
        │ ・構造              │
        │ ・型制約            │
        │ ・カーディナリティ  │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 結果生成            │
        │ ・証明ステップ      │
        │ ・エラー/警告       │
        │ ・カバレッジ        │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │      END            │
        └─────────────────────┘
```

### XSD解析フロー

```
┌─────────────────────────────────────────────────┐
│           XSD Parser Algorithm                  │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  XML Parse          │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Phase 1:            │
        │ 型定義の収集        │
        │ ・complexType       │
        │ ・simpleType        │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Phase 2:            │
        │ 要素の走査          │
        └─────────┬───────────┘
                  │
            ┌─────┴─────┐
            │           │
            ▼           ▼
    ┌────────────┐  ┌────────────┐
    │ 複合型     │  │ 単純型     │
    │ 処理       │  │ 処理       │
    └─────┬──────┘  └─────┬──────┘
          │               │
          ▼               ▼
    ┌────────────┐  ┌────────────┐
    │ sequence   │  │ restriction│
    │ choice     │  │ pattern    │
    │ all        │  │ enumeration│
    └─────┬──────┘  └─────┬──────┘
          │               │
          └───────┬───────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 生成規則の生成      │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ TreeGrammar返却     │
        └─────────────────────┘
```

### MTT変換フロー

```
┌─────────────────────────────────────────────────┐
│         XSLT to MTT Converter                   │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  XSLT Parse         │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ テンプレートの      │
        │ 抽出                │
        └─────────┬───────────┘
                  │
            For Each Template
                  │
                  ▼
        ┌─────────────────────┐
        │ 状態名生成          │
        │ q_pattern_mode      │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ マッチパターン変換  │
        │ Person → Person(x)  │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 本体の処理          │
        └─────────┬───────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ XSLT命令     │    │ リテラル要素 │
│ ・apply-t... │    │ ・属性       │
│ ・for-each   │    │ ・子要素     │
│ ・if/choose  │    │              │
│ ・value-of   │    │              │
└──────┬───────┘    └──────┬───────┘
       │                   │
       └─────────┬─────────┘
                 │
                 ▼
       ┌─────────────────────┐
       │ MTT規則の生成       │
       │ state(pattern) → t  │
       └─────────┬───────────┘
                 │
                 ▼
       ┌─────────────────────┐
       │ MTT返却             │
       └─────────────────────┘
```

### 型保存性検証フロー

```
┌─────────────────────────────────────────────────┐
│       Type Preservation Validator               │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Step 1:             │
        │ 構造検証            │
        └─────────┬───────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│ ルート要素      │  │ 生成規則        │
│ マッピング      │  │ カバレッジ      │
│ チェック        │  │ チェック        │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └──────────┬─────────┘
                    │
         エラー発見? ├─── Yes ──→ errors[]
                    │
                   No
                    │
                    ▼
        ┌─────────────────────┐
        │ Step 2:             │
        │ 型制約検証          │
        └─────────┬───────────┘
                  │
        For Each Type Constraint
                  │
                  ▼
        ┌─────────────────────┐
        │ ターゲット要素探索  │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 型互換性チェック    │
        │ ・基本型            │
        │ ・制約条件          │
        └─────────┬───────────┘
                  │
       互換? ─────┤
          │      No → errors[]
         Yes
          │
          ▼
        ┌─────────────────────┐
        │ Step 3:             │
        │ カーディナリティ    │
        │ 検証                │
        └─────────┬───────────┘
                  │
        For Each Production
                  │
                  ▼
        ┌─────────────────────┐
        │ カーディナリティ    │
        │ 互換性チェック      │
        │ (min, max)          │
        └─────────┬───────────┘
                  │
       互換? ─────┤
          │      No → warnings[]
         Yes
          │
          ▼
        ┌─────────────────────┐
        │ Step 4:             │
        │ カバレッジ構築      │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ ValidationResult    │
        │ 返却                │
        └─────────────────────┘
```

## コード例

### 例1: APIの使用

```python
import requests

# APIエンドポイント
API_URL = "http://localhost:5000/api/validate"

# データの準備
data = {
    "source_xsd": open("source.xsd").read(),
    "target_xsd": open("target.xsd").read(),
    "xslt": open("transform.xsl").read()
}

# 検証リクエスト
response = requests.post(API_URL, json=data)
result = response.json()

# 結果の確認
if result["success"]:
    print("✅ Validation successful!")

    # サブセットチェック
    if result["subset_check"]["valid"]:
        print("  ✓ XSLT subset: OK")

    # 型保存性
    if result["type_validation"]["valid"]:
        print("  ✓ Type preservation: OK")
    else:
        print("  ❌ Type preservation: Failed")
        for error in result["type_validation"]["errors"]:
            print(f"    ERROR: {error}")

    # 警告
    for warning in result["type_validation"]["warnings"]:
        print(f"  ⚠️  {warning}")

else:
    print(f"❌ Validation failed: {result['error']}")
```

### 例2: カスタム検証ルール

```python
from backend.xslt_checker import XSLTSubsetChecker

class CustomXSLTChecker(XSLTSubsetChecker):
    """カスタム検証ルールを追加したチェッカー"""

    def __init__(self):
        super().__init__()
        self.custom_disallowed = {"custom-element"}

    def _check_element(self, elem, path):
        super()._check_element(elem, path)

        local_name = self._get_local_name(elem.tag)

        # カスタムルール
        if local_name in self.custom_disallowed:
            self.errors.append(
                f"Custom disallowed element '{local_name}' at {path}"
            )

# 使用
checker = CustomXSLTChecker()
is_valid, errors, warnings = checker.check_xslt(xslt_content)
```

### 例3: バッチ処理

```python
import os
from pathlib import Path
from backend.xslt_checker import XSLTSubsetChecker
from backend.xsd_parser import XSDParser
from backend.mtt_converter import XSLTToMTTConverter
from backend.type_validator import TypePreservationValidator

def validate_directory(dir_path: str):
    """ディレクトリ内の全XSLTファイルを検証"""

    results = []

    # XSLTファイルを探す
    for xslt_file in Path(dir_path).glob("**/*.xsl"):
        print(f"\nValidating: {xslt_file}")

        # 対応するXSDファイルを探す
        base_name = xslt_file.stem
        source_xsd = xslt_file.parent / f"{base_name}_source.xsd"
        target_xsd = xslt_file.parent / f"{base_name}_target.xsd"

        if not source_xsd.exists() or not target_xsd.exists():
            print("  ⚠️  Missing XSD files, skipping...")
            continue

        # 検証実行
        try:
            with open(xslt_file) as f:
                xslt = f.read()
            with open(source_xsd) as f:
                src_xsd = f.read()
            with open(target_xsd) as f:
                tgt_xsd = f.read()

            # 検証処理
            subset_checker = XSLTSubsetChecker()
            is_valid, errors, warnings = subset_checker.check_xslt(xslt)

            if not is_valid:
                print(f"  ❌ Subset check failed")
                results.append((xslt_file, False, errors))
                continue

            # 型保存性検証
            source_parser = XSDParser()
            source_grammar = source_parser.parse(src_xsd)

            target_parser = XSDParser()
            target_grammar = target_parser.parse(tgt_xsd)

            mtt_converter = XSLTToMTTConverter()
            mtt = mtt_converter.convert(xslt)

            validator = TypePreservationValidator()
            result = validator.validate(source_grammar, target_grammar, mtt)

            if result.is_valid:
                print(f"  ✅ Validation passed")
                results.append((xslt_file, True, []))
            else:
                print(f"  ❌ Type preservation failed")
                results.append((xslt_file, False, result.errors))

        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            results.append((xslt_file, False, [str(e)]))

    # サマリー
    print("\n" + "=" * 60)
    print("Summary:")
    passed = sum(1 for _, valid, _ in results if valid)
    total = len(results)
    print(f"  Passed: {passed}/{total}")
    print(f"  Failed: {total - passed}/{total}")

    return results

# 使用
results = validate_directory("./transforms")
```

## ユースケース

### ユースケース1: CI/CDパイプラインへの統合

```yaml
# .github/workflows/xslt-validation.yml
name: XSLT Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run XSLT validation
      run: |
        python scripts/validate_all.py

    - name: Upload results
      if: always()
      uses: actions/upload-artifact@v2
      with:
        name: validation-results
        path: validation-results.json
```

### ユースケース2: Webサービスとしてのデプロイ

```python
# production_app.py
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# レート制限
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/validate', methods=['POST'])
@limiter.limit("10 per minute")
def validate():
    # ... 検証処理 ...
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
```

### ユースケース3: IDEプラグイン

```python
# vscode_extension/validator.py
import sys
from backend.xslt_checker import XSLTSubsetChecker

def validate_for_ide(xslt_path: str):
    """IDE向けの検証（診断情報を返す）"""

    with open(xslt_path) as f:
        xslt = f.read()

    checker = XSLTSubsetChecker()
    is_valid, errors, warnings = checker.check_xslt(xslt)

    # VS Code診断形式に変換
    diagnostics = []

    for error in errors:
        diagnostics.append({
            "severity": "error",
            "message": error,
            "source": "xslt-validator"
        })

    for warning in warnings:
        diagnostics.append({
            "severity": "warning",
            "message": warning,
            "source": "xslt-validator"
        })

    return diagnostics

if __name__ == '__main__':
    xslt_path = sys.argv[1]
    diagnostics = validate_for_ide(xslt_path)
    print(json.dumps(diagnostics))
```

## トラブルシューティング

### 問題1: XML解析エラー

**症状:**
```
XML Parse Error: mismatched tag
```

**原因:** 不正なXML形式

**解決:**
- XMLの整形性を確認
- 名前空間の宣言を確認
- タグの開始/終了が一致するか確認

```python
# デバッグ用のXMLバリデーション
import xml.etree.ElementTree as ET

try:
    ET.fromstring(xslt_content)
except ET.ParseError as e:
    print(f"Line {e.position[0]}, Column {e.position[1]}: {e.msg}")
```

### 問題2: 型制約違反が検出されない

**症状:** 明らかな型不整合があるのに検証がパスする

**原因:** MTT変換が不完全で、マッピングが正しく認識されていない

**解決:**
```python
# デバッグ: MTTの内容を確認
mtt_json = mtt_converter.to_json()
print(json.dumps(mtt_json, indent=2))

# 各規則のlhs/rhsを確認
for rule in mtt.rules:
    print(f"State: {rule.state}")
    print(f"  LHS: {rule.lhs_pattern}")
    print(f"  RHS: {rule.rhs_output}")
```

### 問題3: パフォーマンスの低下

**症状:** 大きなXSDで検証が遅い

**原因:** 生成規則の数が多い

**解決:**
```python
# プロファイリング
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 検証実行
result = validator.validate(source_grammar, target_grammar, mtt)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # トップ10を表示
```

### 問題4: メモリ使用量が多い

**症状:** 大規模なXSDでメモリエラー

**解決:**
```python
# ストリーミング解析の使用
import xml.etree.ElementTree as ET

def parse_large_xsd(xsd_path: str):
    """大規模XSDのストリーミング解析"""
    context = ET.iterparse(xsd_path, events=('start', 'end'))
    context = iter(context)
    event, root = next(context)

    for event, elem in context:
        if event == 'end':
            # 要素を処理
            process_element(elem)
            # メモリ解放
            elem.clear()
            root.clear()
```

## 関連ドキュメント

- [システム概要](./overview.md)
- [XSDパーサー](./xsd_parser.md)
- [XSLTサブセットチェッカー](./xslt_subset_checker.md)
- [MTT変換](./mtt_converter.md)
- [型保存性検証](./type_validator.md)
