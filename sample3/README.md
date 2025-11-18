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

## 学習ポイント

1. **計算を含む変換**: XSLTで算術演算を使用
2. **複雑な制約**: 複数フィールドにまたがる条件
3. **ビジネスロジック**: スキーマに含まれないルールの追加
4. **型安全性**: 計算結果が出力制約を満たすことの検証
5. **SMTの威力**: 具体的な反例値の自動生成
