# XSLT Validation Checker

XSLTの妥当性を理論的に検証するツールです。木文法とMacro Tree Transducer (MTT)の理論に基づいて、XSLTが型保存性を満たすかどうかを検証します。

## 機能

1. **XSLTサブセットチェック**: XSLTが許可されたサブセットに準拠しているかをチェック
2. **XSD→木文法変換**: ソースとターゲットのXSDを木文法に変換
3. **XSLT→MTT変換**: XSLTをMacro Tree Transducerに変換
4. **型保存性の検証**: 変換が型を保存するかを形式的に検証
5. **前像計算**: MTTによる変換の前像 pre_M(L(G_T)) を計算
6. **妥当性検証**: L(Src) ⊆ pre_T(L(Tgt)) を検証
7. **厳密検証（SMT）**: Z3ソルバーによる制約の完全な検証と具体的反例生成
8. **Webフロントエンド**: ブラウザから簡単に利用可能

## 理論的背景

このツールは以下の理論に基づいています：

- **正規木文法 (Regular Tree Grammar)**: XSDを形式的な木文法として表現
- **トップダウン木変換器 (Top-Down Tree Transducer)**: XSLTを木変換器として表現
- **型保存性の証明**: ∀t ∈ L(G_S), M(t) ∈ L(G_T) を検証

詳細は `spec/the_theory_and_sample.md` および `spec/related_document.md` を参照してください。

## セットアップ

### 必要要件

- Python 3.8以上
- pip
- Z3ソルバー（厳密検証機能を使用する場合）

### インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt

# SMTソルバー（厳密検証機能）のインストール
pip install z3-solver
```

## 使い方

### バックエンドサーバーの起動

```bash
cd /home/user/xslt_validation
python -m backend.app
```

サーバーは `http://localhost:5000` で起動します。

### フロントエンドの起動

シンプルなHTTPサーバーを起動してフロントエンドにアクセスします：

```bash
# Python 3の場合
python -m http.server 8000

# または
python3 -m http.server 8000
```

ブラウザで `http://localhost:8000/frontend/index.html` を開きます。

### API エンドポイント

#### POST /api/validate
ソースXSD、ターゲットXSD、XSLTを受け取り、包括的な検証を実行します。

**リクエスト:**
```json
{
  "source_xsd": "<?xml version=\"1.0\"?>...",
  "target_xsd": "<?xml version=\"1.0\"?>...",
  "xslt": "<?xml version=\"1.0\"?>..."
}
```

**レスポンス:**
```json
{
  "success": true,
  "subset_check": { ... },
  "source_grammar": { ... },
  "target_grammar": { ... },
  "mtt": { ... },
  "type_validation": { ... },
  "preimage": { ... },
  "validity": { ... }
}
```

#### POST /api/validate-strict
SMTソルバー（Z3）を使用した厳密な制約検証を実行します。

**リクエスト:**
```json
{
  "source_xsd": "<?xml version=\"1.0\"?>...",
  "target_xsd": "<?xml version=\"1.0\"?>...",
  "xslt": "<?xml version=\"1.0\"?>..."
}
```

**レスポンス:**
```json
{
  "success": true,
  "strict_validity": {
    "is_valid": false,
    "counterexamples": [
      {
        "element": "Employee",
        "pattern": "Employee(*)",
        "field_values": {"Age": -1, "Salary": 0},
        "reason": "Source allows Age < 0, but preimage requires Age >= 0"
      }
    ],
    "total_patterns_checked": 5,
    "patterns_with_issues": 1,
    "explanation": "..."
  }
}
```

#### POST /api/check-subset
XSLTがサブセットに準拠しているかをチェックします。

#### POST /api/parse-xsd
XSDを木文法に変換します。

#### POST /api/convert-to-mtt
XSLTをMTTに変換します。

## プロジェクト構造

```
xslt_validation/
├── backend/
│   ├── __init__.py
│   ├── app.py                      # Flask API
│   ├── xslt_checker.py             # XSLTサブセットチェッカー
│   ├── xsd_parser.py               # XSDパーサー
│   ├── mtt_converter.py            # XSLT to MTT変換
│   ├── type_validator.py           # 型保存性検証
│   ├── preimage_computer.py        # 前像計算
│   ├── validity_checker.py         # 妥当性検証
│   └── strict_validity_checker.py  # SMTソルバーによる厳密検証
├── frontend/
│   ├── index.html                  # Webインターフェース
│   ├── style.css                   # スタイル
│   └── script.js                   # JavaScript
├── samples/
│   ├── source.xsd                  # サンプルソースXSD
│   ├── target.xsd                  # サンプルターゲットXSD
│   └── transform.xsl               # サンプルXSLT
├── sample2/
│   ├── source.xsd                  # より複雑なサンプル
│   ├── target.xsd
│   └── transform.xslt
├── doc/
│   ├── README.md                   # ドキュメント索引
│   ├── overview.md                 # システム概要
│   ├── xsd_parser.md              # XSDパーサーアルゴリズム
│   ├── mtt_converter.md           # MTT変換アルゴリズム
│   ├── type_validator.md          # 型保存性検証
│   ├── preimage_computation.md    # 前像計算アルゴリズム
│   ├── validity_checking.md       # 妥当性検証アルゴリズム
│   └── examples.md                # 実装例
├── spec/
│   ├── the_theory_and_sample.md
│   └── related_document.md
└── requirements.txt
```

## 制限事項

### 許可されているXSLT要素

- `xsl:template` (match属性)
- `xsl:apply-templates`
- `xsl:for-each`
- `xsl:value-of`
- `xsl:if`
- `xsl:choose`, `xsl:when`, `xsl:otherwise`
- `xsl:with-param`, `xsl:param`
- リテラル要素

### 禁止されている機能

- `document()` 関数
- 外部関数
- 正規表現
- 複雑な文字列操作
- 動的XPath評価

## 例

### 基本的な検証

サンプルファイル（`samples/` ディレクトリ）を使用した検証例：

1. Webインターフェースを開く
2. 「サンプル1を読み込む」ボタンをクリック
3. 「検証を実行」ボタンをクリック

結果として以下が表示されます：
- XSLTサブセットチェック結果
- ソースとターゲットの木文法
- MTT表現
- 型保存性の証明ステップ
- 前像計算結果
- 妥当性検証結果（L(Src) ⊆ pre_T(L(Tgt))）
- カバレッジマトリクス

### SMTソルバーによる厳密検証

制約の完全な検証と具体的な反例を取得：

1. 「サンプル2を読み込む」ボタンをクリック
2. 「厳密検証 (SMT)」ボタンをクリック

Z3ソルバーが以下を実行します：
- 数値制約の完全な検証
- 具体的な反例値の生成（例：Age = -1, Budget = -1）
- ソース制約と前像制約の矛盾検出

**例：Sample 2の結果**
```
反例が見つかりました：
1. Employee(*)
   具体的な値：
   - Age = 17 (ソースは制約なし、前像は Age >= 18 を要求)
   - Salary = 1

2. Department(*)
   具体的な値：
   - Budget = -1 (ソースは制約なし、前像は Budget >= 0 を要求)
```

## ライセンス

MIT License

## 参考文献

- Regular Tree Grammars
- Top-Down Tree Transducers
- XDuce型システム
