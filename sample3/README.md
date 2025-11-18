# Sample 3: CO2排出量計算

このサンプルは、XSLTで**計算を含む変換**を示します。

## 概要

電力使用データからCO2排出レポートを生成する変換です。

### 計算式

```
CO2排出量 (kgCO2e) = 電力量 (kWh) × 排出原単位 (kgCO2e/kWh)
```

## ファイル

### source.xsd - 電力使用データ

```xml
PowerUsageData
  └─ Facility (複数)
       ├─ FacilityName: string
       ├─ PowerConsumption: decimal (>= 0)
       ├─ EmissionFactor: decimal (> 0)
       └─ Year: integer
```

**制約:**
- `PowerConsumption` (電力量): 非負の小数（kWh）
- `EmissionFactor` (排出原単位): 正の小数（kgCO2e/kWh）、0より大きい
- `Year`: 整数

### target.xsd - CO2排出レポート

```xml
EmissionReport
  └─ FacilityEmission (複数)
       属性:
       ├─ facility: string
       ├─ totalEmission: decimal (>= 0)
       ├─ year: integer
       └─ verified: boolean
```

**制約:**
- `totalEmission` (総排出量): 非負の小数（kgCO2e）

### transform.xslt - 変換ロジック

**主な処理:**

1. **フィルタリング**: 以下の条件を満たす施設のみ変換
   - `PowerConsumption >= 0`
   - `EmissionFactor > 0`
   - `Year >= 2020` （2020年以降のデータのみ）

2. **計算**:
   ```xpath
   totalEmission = PowerConsumption * EmissionFactor
   ```

3. **検証フラグ**:
   ```xpath
   verified = (EmissionFactor >= 0.3) ? true : false
   ```
   排出原単位が0.3以上なら公式データとみなす

## 検証のポイント

### 型保存性

- **入力**: `PowerConsumption >= 0` かつ `EmissionFactor > 0`
- **計算**: `totalEmission = PowerConsumption * EmissionFactor`
- **出力制約**: `totalEmission >= 0`

∵ 非負 × 正 = 正（>= 0）なので型制約は保存される ✓

### 妥当性検証（基本）

- ソースパターン: `Facility(FacilityName, PowerConsumption, EmissionFactor, Year)`
- 前像パターン: `Facility(*) where PowerConsumption >= 0 and EmissionFactor > 0 and Year >= 2020`

**検証ポイント:**
- `Year < 2020` のデータは変換されない → 反例となる可能性

### SMT厳密検証

Z3ソルバーで以下をチェック:

```python
# ソース制約
PowerConsumption >= 0
EmissionFactor > 0

# 前像制約
PowerConsumption >= 0 AND EmissionFactor > 0 AND Year >= 2020

# 反例を探す: ソースは満たすが前像は満たさない
∃ PowerConsumption, EmissionFactor, Year.
    (PowerConsumption >= 0 AND EmissionFactor > 0) AND
    NOT (PowerConsumption >= 0 AND EmissionFactor > 0 AND Year >= 2020)
```

**期待される反例:**
```
Year = 2019 (または任意の 2020未満の値)
```

ソーススキーマでは`Year`に制約がないため、2019年のデータは有効な入力だが、XSLTでは変換されない。

## 実行例

### 入力例

```xml
<PowerUsageData>
  <Facility>
    <FacilityName>Tokyo Office</FacilityName>
    <PowerConsumption>10000</PowerConsumption>
    <EmissionFactor>0.5</EmissionFactor>
    <Year>2023</Year>
  </Facility>
  <Facility>
    <FacilityName>Osaka Factory</FacilityName>
    <PowerConsumption>50000</PowerConsumption>
    <EmissionFactor>0.4</EmissionFactor>
    <Year>2019</Year>  <!-- 2020未満なので変換されない -->
  </Facility>
</PowerUsageData>
```

### 期待される出力

```xml
<EmissionReport>
  <FacilityEmission
    facility="Tokyo Office"
    totalEmission="5000"
    year="2023"
    verified="true"/>
  <!-- Osaka Factory は Year < 2020 なので出力されない -->
</EmissionReport>
```

### 計算の詳細

**Tokyo Office:**
- 電力量: 10,000 kWh
- 排出原単位: 0.5 kgCO2e/kWh
- **CO2排出量 = 10,000 × 0.5 = 5,000 kgCO2e** ✓
- 検証済み: EmissionFactor (0.5) >= 0.3 → `true`

**Osaka Factory:**
- Year = 2019 < 2020 → フィルタリングされて出力なし

## このサンプルが示すもの

### 1. 算術計算

XSLT内で乗算を使用:
```xpath
<xsl:value-of select="PowerConsumption * EmissionFactor"/>
```

### 2. 複数条件のフィルタリング

```xpath
<xsl:if test="PowerConsumption &gt;= 0 and EmissionFactor &gt; 0 and Year &gt;= 2020">
```

### 3. 条件分岐（choose）

```xpath
<xsl:choose>
  <xsl:when test="EmissionFactor &gt;= 0.3">true</xsl:when>
  <xsl:otherwise>false</xsl:otherwise>
</xsl:choose>
```

### 4. 型制約の伝播

入力の数値制約が計算を通じて出力の制約を満たすことの検証

### 5. ビジネスルールの反映

- 2020年以降のデータのみ処理（ビジネスルール）
- ソーススキーマにはない制約がXSLTで追加される
- SMT検証でこの矛盾を検出

## SMT検証の期待結果

### ケース1: Year制約の検出

**デフォルトのtarget.xsd:**
```
✗ 妥当性不成立
検証したパターン: 1
制約違反: 1

反例:
1. Facility(*)
   具体的な値:
   - Year = 2019 (または任意の 2020未満の値)
   - PowerConsumption = 0 (任意の非負値)
   - EmissionFactor = 0.1 (任意の正の値)

   理由: ソーススキーマでは Year に制約がないが、
         XSLTは Year >= 2020 を要求する
```

### ケース2: 計算結果の制約検証

**target.xsdに `<xs:maxInclusive value="500"/>` を追加した場合:**

```xml
<xs:simpleType name="NonNegativeDecimal">
  <xs:restriction base="xs:decimal">
    <xs:minInclusive value="0"/>
    <xs:maxInclusive value="500"/>  <!-- 追加 -->
  </xs:restriction>
</xs:simpleType>
```

**制約の意味:**
- `totalEmission <= 500` が必要
- しかし `totalEmission = PowerConsumption × EmissionFactor`
- ソースには `PowerConsumption` の上限がない！

**期待される検出（SMT厳密検証）:**
```
✗ 妥当性不成立
検証したパターン: 1
制約違反: 1

反例:
1. Facility(*)
   具体的な値:
   - PowerConsumption = 1001 (または >= 501 の任意の値)
   - EmissionFactor = 1.0
   - Year = 2020

   計算結果: totalEmission = 1001 × 1.0 = 1001 > 500

   理由: 計算結果が出力制約 (totalEmission <= 500) を違反
```

**重要な注意:**
現在の基本的な型保存性検証は、直接コピーされるフィールドの制約は検証しますが、
**計算式を含む属性の制約検証**は限定的です。

このような計算を含む制約違反は、**SMT厳密検証**を使用することで検出できます：
1. Z3ソルバーが計算式を解析
2. 出力制約 `totalEmission <= 500` を入力制約に逆算
3. `PowerConsumption × EmissionFactor > 500` となる具体的な値を発見

## 現在の実装の制限事項

### 計算式を含む制約の検証

現在のバージョンでは、以下の制限があります：

**検出できるもの:**
- ✅ `xsl:if`/`xsl:choose`による条件フィルタリング（Year >= 2020など）
- ✅ 直接コピーされるフィールドの型制約
- ✅ 単純なフィールドマッピングの制約

**検出が限定的なもの:**
- ⚠️ **計算式を含む属性の制約**（totalEmission = PowerConsumption × EmissionFactorなど）
- ⚠️ 出力スキーマの制約から入力制約への逆算
- ⚠️ 複数フィールドの演算結果に対する制約

### 回避策

出力に上限制約を加えたい場合（例：totalEmission <= 500）、以下の方法があります：

#### 方法1: ソーススキーマに制約を追加

```xml
<!-- source.xsdに追加 -->
<xs:simpleType name="LimitedPowerConsumption">
  <xs:restriction base="xs:decimal">
    <xs:minInclusive value="0"/>
    <xs:maxInclusive value="500"/>  <!-- 上限を追加 -->
  </xs:restriction>
</xs:simpleType>
```

これにより、入力時点で制約が強制されます。

#### 方法2: XSLTに明示的なフィルタリングを追加

```xslt
<xsl:template match="Facility">
  <!-- 計算結果が500以下の場合のみ出力 -->
  <xsl:if test="PowerConsumption * EmissionFactor &lt;= 500 and
                PowerConsumption &gt;= 0 and
                EmissionFactor &gt; 0 and
                Year &gt;= 2020">
    <FacilityEmission .../>
  </xsl:if>
</xsl:template>
```

この制約は前像計算とSMT検証で検出されます。

### 将来の改善

以下の機能拡張が計画されています：

1. **出力スキーマ制約の前像計算への統合**
   - ターゲットスキーマの制約を読み取り
   - 属性の制約を抽出
   - 入力制約に逆算

2. **計算式の解析と制約伝播**
   - XPath式のパース
   - 演算子（+, -, *, /）の処理
   - SMTソルバーへの変換

3. **高度なSMT検証**
   - 計算式を含む制約の完全な検証
   - 出力制約違反の自動検出

## 学習ポイント

1. **計算を含む変換**: XSLTで算術演算を使用
2. **複雑な制約**: 複数フィールドにまたがる条件
3. **ビジネスロジック**: スキーマに含まれないルールの追加
4. **型安全性**: 計算結果が出力制約を満たすことの検証
5. **SMTの威力**: 具体的な反例値の自動生成
6. **実装の限界**: 計算式を含む制約検証の課題と回避策
