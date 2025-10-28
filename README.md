# XSLT Validation Checker

XSLTの妥当性を理論的に検証するツールです。木文法とMacro Tree Transducer (MTT)の理論に基づいて、XSLTが型保存性を満たすかどうかを検証します。

## 機能

1. **XSLTサブセットチェック**: XSLTが許可されたサブセットに準拠しているかをチェック
2. **XSD→木文法変換**: ソースとターゲットのXSDを木文法に変換
3. **XSLT→MTT変換**: XSLTをMacro Tree Transducerに変換
4. **型保存性の検証**: 変換が型を保存するかを形式的に検証
5. **Webフロントエンド**: ブラウザから簡単に利用可能

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

### インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt
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
  "type_validation": { ... }
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
│   ├── app.py                  # Flask API
│   ├── xslt_checker.py         # XSLTサブセットチェッカー
│   ├── xsd_parser.py           # XSDパーサー
│   ├── mtt_converter.py        # XSLT to MTT変換
│   └── type_validator.py       # 型保存性検証
├── frontend/
│   ├── index.html              # Webインターフェース
│   ├── style.css               # スタイル
│   └── script.js               # JavaScript
├── samples/
│   ├── source.xsd              # サンプルソースXSD
│   ├── target.xsd              # サンプルターゲットXSD
│   └── transform.xsl           # サンプルXSLT
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

サンプルファイル（`samples/` ディレクトリ）を使用した検証例：

1. Webインターフェースを開く
2. 「サンプルを読み込む」ボタンをクリック
3. 「検証を実行」ボタンをクリック

結果として以下が表示されます：
- XSLTサブセットチェック結果
- ソースとターゲットの木文法
- MTT表現
- 型保存性の証明ステップ
- カバレッジマトリクス

## ライセンス

MIT License

## 参考文献

- Regular Tree Grammars
- Top-Down Tree Transducers
- XDuce型システム
