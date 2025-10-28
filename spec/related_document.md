いい選択です — では**XSLT の扱える簡潔なサブセットを定義**し、そのサブセットの XSLT を **Macro Tree Transducer (MTT)** に自動変換するための「雛形（ルール＋アルゴリズム＋具体例）」を提示します。
理論的に扱いやすく、実装可能な形に落とし込みます。長めですが一度で使える設計になっています。

# 概要（目的）

* 対象：XSLT の実用的だが制限されたサブセット（下に定義）。
* 出力：同等の意味を持つ MTT の規則集合（状態＋変換規則）。
* 用途：MTT に写像することで「前像計算 → 包含チェック」などの理論的解析に接続できるようにする。

---

# 1. 取り扱う XSLT サブセット（明示）

扱える構成要素を限定します（実装可能で理論検証に適したサブセット）。

* 文法要素（サブセット）

  * `xsl:template match="E"`（要素名によるマッチ、ワイルドカード `*` 可、簡単な親子パターン `A/B` 可）
  * `xsl:apply-templates select="child::E"`（子要素への再帰呼び出し、または `node()`）
  * `xsl:for-each select="child::E"`（要素列の逐次処理）
  * `xsl:value-of select="child::text()"`（子要素あるいは属性値の取り出し、簡単な文字列連結）
  * `xsl:if test="cond"` と `xsl:choose`（ただし cond は「存在チェック（child::E）、equal（child::age = '2'）などの有限判定」に限定）
  * リテラル要素生成（`<out>` を直接出力）
  * パラメータ渡し（`xsl:with-param` / `xsl:param`）は簡易サポート（マクロ的役割）
* 禁止／制限

  * `document()`、外部関数、正規表現、文字列長に関する無制限算術、動的 XPath（eval）などは不可。
  * 無制限ループやランダム値生成を含まないこと。

> 目的は：XSLT の「構造変換＋有限選択」を MTT の枠に収められること。

---

# 2. MTT（Macro Tree Transducer） の簡単な説明（形式）

MTT は**状態（マクロ）を持つ再帰的な木変換器**です。各規則は概ね次の形をとります。

```
q(f(x1,...,xn), p1,...,pk) -> t
```

* 左辺：状態 `q` が、入力記号 `f`（要素名）とその子木 `x1..xn` を受け取る（必要に応じて追加パラメータ `p1..pk`）。
* 右辺：出力木 `t` は

  * 出力記号（ターゲット要素）、
  * 子ノードに対する再帰呼び出し（例：`q'(xi, args)`）、
  * パラメータ参照、リテラル文字列 など
    で構成される。

MTT はテンプレートのパラメータ（with-param に相当）を扱えるので XSLT の多くの構成を表せます。

---

# 3. 全体の変換方針（高レベル）

1. **テンプレート → 状態（マクロ）**

   * `xsl:template match="pattern" mode="m?"` ごとに一意の状態 `q_pattern_mode` を作る。
   * 状態は「そのパターンにマッチした入力ノードを受け取り、出力木を返す関数」と考える。

2. **マッチパターンの翻訳**

   * 単純な要素名 `person` → MTT の遷移左部に `person(x1,...,xn)` を置く（`n` は子要素の最大 arity。unranked 木はリスト処理に変換）。
   * ワイルドカード `*` は任意のラベルを受け付ける遷移（MTT 側では複数ルールでカバー）。

3. **apply-templates / for-each → 再帰呼び出し**

   * `apply-templates select="child::E"` は、子ノード `E` に対応する状態呼び出し `q_E(child, params)` に置き換える。
   * `for-each` は「列処理用の補助状態（process-list）」を生成し、子列を順次処理して出力ノード列を連結する。

4. **xsl:value-of → 出力リテラル/パラメータ**

   * `value-of` は、入力ノードの子テキストを取り出す操作に対応（MTT では入力木の特定位置の文字列をパラメータとして渡すモデルにするか、出力にノード生成を許して代入）。

5. **if / choose → ガード付き規則**

   * 簡単な存在チェック（`child::age` の有無）や列挙比較（`age='0'`）は、入力パターンやガード付き規則に分解して表現する。
   * 例：`<xsl:if test="age='0'">A</xsl:if>` は、MTT では `person(..., age=0)` にマッチする専用ルールで `A` を生成する、と訳す（入力木の構造で分岐できる場合）。

6. **パラメータ**

   * `xsl:with-param` は MTT のマクロパラメータに対応。一つのテンプレート呼び出しを状態呼び出しに変換する際、パラメータを引数として渡す。

---

# 4. 具体例：XSLT（サブセット） → MTT（対応する規則）

下は先に示した toy 例（people → employees）の簡潔な XSLT（サブセット）と、それを MTT に写したもの。

## 4.1 XSLT（簡潔版）

```xml
<!-- templates.xsl : サブセットのXSLT -->
<xsl:stylesheet version="1.0" xmlns:xsl="...">
  <xsl:template match="/people">
    <employees>
      <xsl:apply-templates select="person"/>
    </employees>
  </xsl:template>

  <xsl:template match="person">
    <employee>
      <fullName>
        <xsl:value-of select="firstname"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="lastname"/>
      </fullName>
      <ageGroup>
        <xsl:choose>
          <xsl:when test="age &lt; 2">child</xsl:when>
          <xsl:otherwise>adult</xsl:otherwise>
        </xsl:choose>
      </ageGroup>
    </employee>
  </xsl:template>
</xsl:stylesheet>
```

> 注：`age < 2` はここでは有限値（0,1,2,3）を想定しており、後述する翻訳で扱います。

## 4.2 これを表す MTT（擬似構文）

MTT 側の出力アルファベットは `employees, employee, fullName, ageGroup, text(...)` とします。入力アルファベットは `people, person, firstname, lastname, age`。

MTT の状態を次のように定義します（擬似 BNF 風）：

```
States:
  q_root  (no params)      -- 対応: template match="/people"
  q_person(no params)      -- 対応: template match="person"
  q_person_list()          -- 子列処理（person のリスト）

Rules:

1) q_root( people(person_list) ) ->
     employees( q_person_list(person_list) )

  （説明：ルート people ノードの子 person_list を q_person_list で処理して employees を生成）

2) q_person_list( empty ) ->  /* 空リスト */  ε
   q_person_list( cons(p, rest) ) ->
     concat( q_person(p), q_person_list(rest) )

  （リスト構造の逐次処理。concat は出力ノード列の連結）

3) q_person( person( firstname(fn_text), lastname(ln_text), age(age_text) , ... ) ) ->
     employee(
       fullName( text(concat(fn_text, " ", ln_text)) ),
       ageGroup( q_ageGroup(age_text) )
     )

  （person の内部フィールドを取り出し fullName を作り、年齢に応じて q_ageGroup を呼ぶ）

4) q_ageGroup( age_text ) [guard: age_text = "0" or "1" ] -> text("child")
   q_ageGroup( age_text ) [guard: age_text = "2" or "3" ] -> text("adult")
```

上の q_ageGroup のように「入力の具体値に基づく分岐」を MTT のガード付きルールで表現します。
（実際の MTT 理論では値比較をどう扱うかは定義依存ですが、有限ドメインならルール列挙で表現できます。）

---

# 5. 変換アルゴリズムの雛形（擬似コード）

XSLT AST → MTT 規則を自動生成するためのアルゴリズム骨子（Python 風擬似コード）：

```
function convert_xslt_to_mtt(xslt_ast):
    mtt = MTT()
    for template in xslt_ast.templates:
        state = make_state_name(template.match, template.mode)
        mtt.add_state(state)
        rule_lhs = build_lhs_from_pattern(template.match)
        rule_rhs = translate_template_body(template.body, state)
        mtt.add_rule(state, rule_lhs, rule_rhs)
    -- 追加：list処理やfor-eachを補助状態で展開
    return mtt

function translate_template_body(body, cur_state):
    -- body は sequence of instructions
    out_seq = []
    for instr in body:
        if instr is literal_element:
            children = translate_template_body(instr.children, cur_state)
            out_seq.append( OutputNode(instr.name, children) )
        elif instr is value_of:
            out_seq.append( OutputText( extract_text_access_path(instr.select) ) )
        elif instr is apply_templates:
            sel_pattern = instr.select
            if sel_pattern is "person":
                out_seq.append( CallState(q_for_person_list, param=child_list_ref) )
            else:
                out_seq.append( CallState(lookup_state_for(sel_pattern), param=child_ref) )
        elif instr is choose/if:
            -- 条件が有限判定なら分岐ルールを作る（ガードつき規則）
            out_seq.append( translate_conditional(instr) )
    return Sequence(out_seq)
```

実装ノート：

* `build_lhs_from_pattern` は `person` → `person(x1,...,xn)` のような入力パターンを作る（unranked 木は list 表現に変換）。
* `translate_conditional` は条件が「age < 2」など有限判定なら `q_ageGroup` のように別状態へ分離し、そこで具体的な値族ごとに規則を用意する。

---

# 6. 限界と対処法（現場での注意）

* **XPath の複雑な条件**（文字列操作・正規表現・数式）は MTT の単純な形式では直接扱いにくい。対処法：

  * 条件が有限集合（列挙型）に落ちる場合は規則を列挙する。
  * それ以外は事前正規化フェーズで「スキーマ制約により可能な値集合」を使って分解するか、あるいは XSLT を先に簡約化（外部演算を別処理に置換）する。
* **無名ノード列（unranked children）**：MTT の理論ではリスト処理を補助状態で表現することで対応可能だが、実装は少し手間。
* **外部関数／document()**：これらがある場合は理論保証（前像計算）は破綻するので、変換可否の判断で拒否またはモック化する。

---

# 7. 変換後にやるべきこと（理論検証への接続）

1. 生成した MTT を使って **前像（preimage）計算**を行うアルゴリズムに渡す。

   * 研究的実装やライブラリ（学術コード）を使えば、`pre_T(A_tgt)` を構築できることが多い（ただしトランスデューサのクラスが要件を満たす必要あり）。
2. `A_src ⊆ pre_T(A_tgt)` の包含チェックを実行する（オートマトンの交差・補集合・空性検査）。
3. もし包含が成り立てば、**数学的に完全性を証明**できる（ただし XSLT がサブセット内であることが前提）。

---

# 8. 実装例（小さな骨組み：ファイル出力例）

* 出力形式はどちらでも良いが、以下のどれかが扱いやすい：

  * 自作 JSON で MTT の状態・ルールを記述（簡単に読み書き可能）。
  * 研究用の MTT 表現（既存ツールがあればそれに合わせる）。
* 例（JSON スタイル、擬似）：

```json
{
 "states": ["q_root","q_person","q_person_list","q_ageGroup"],
 "rules": [
   {"state":"q_root", "lhs":"people(person_list)", "rhs":"employees( call('q_person_list', person_list) )"},
   {"state":"q_person_list", "lhs":"cons(p,rest)", "rhs":"concat( call('q_person', p), call('q_person_list', rest) )"},
   {"state":"q_person", "lhs":"person(firstname(fn), lastname(ln), age(ag))", "rhs":"employee(fullName(text(concat(fn,' ',ln))), ageGroup(call('q_ageGroup', ag)))"},
   {"state":"q_ageGroup", "lhs":"age( '0' )", "rhs":"text('child')"},
   {"state":"q_ageGroup", "lhs":"age( '1' )", "rhs":"text('child')"},
   {"state":"q_ageGroup", "lhs":"age( '2' )", "rhs":"text('adult')"},
   {"state":"q_ageGroup", "lhs":"age( '3' )", "rhs":"text('adult')"}
 ]
}
```

---

# 9. まとめ（実務での使い方）

* この雛形に従って XSLT を正規化（サブセット化）し、AST を解析して MTT の JSON（または研究用フォーマット）を出力するコンバータが実装できます。
* コンバータ出力を使えば、次は理論ツール（前像計算・オートマトン包含）へ橋渡しが可能になります。
* 重要：XSLT がサブセット外の機能を使っている場合、その部分はモック化するか（理論解析の対象から除外）、あるいは変換の前段で別処理に置く必要があります。

---

もし望むなら、次のどれかをすぐに作ります（どれもこの会話で実行可能）：

1. この雛形に基づく **実際の変換スクリプト骨子（Python）** を書いて、簡単な XSLT ファイルを入力にして MTT（JSON）を生成するサンプル。
2. 上の MTT JSON を使って **前像計算の小さな手作りデモ**（toy の正則木オートマトンで前像を計算して包含チェック）を実行する（限定的なケースで動く）。
3. あなたの実際の XSLT（小さめのファイル）をここに貼ってもらえれば、それを自動で翻訳して MTT 規則を返す（自動化の雛形で示す）。

指定がなければ（自動的に）1 を作って、変換スクリプト骨子を示します。どれを出しましょう？
