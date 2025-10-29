// API endpoint
const API_URL = 'http://localhost:5000/api';

// DOM elements
const sourceXsdInput = document.getElementById('source-xsd');
const targetXsdInput = document.getElementById('target-xsd');
const xsltInput = document.getElementById('xslt');
const validateBtn = document.getElementById('validate-btn');
const loadSampleBtn = document.getElementById('load-sample-btn');
const loadSample2Btn = document.getElementById('load-sample2-btn');
const clearBtn = document.getElementById('clear-btn');
const resultsSection = document.getElementById('results-section');
const loadingDiv = document.getElementById('loading');
const errorMessageDiv = document.getElementById('error-message');

// Event listeners
validateBtn.addEventListener('click', validateXSLT);
loadSampleBtn.addEventListener('click', loadSample);
loadSample2Btn.addEventListener('click', loadSample2);
clearBtn.addEventListener('click', clearInputs);

async function validateXSLT() {
    const sourceXsd = sourceXsdInput.value.trim();
    const targetXsd = targetXsdInput.value.trim();
    const xslt = xsltInput.value.trim();

    if (!sourceXsd || !targetXsd || !xslt) {
        showError('すべてのフィールドを入力してください。');
        return;
    }

    // Show loading
    loadingDiv.style.display = 'block';
    resultsSection.style.display = 'none';
    errorMessageDiv.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_xsd: sourceXsd,
                target_xsd: targetXsd,
                xslt: xslt
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'サーバーエラーが発生しました。');
        }

        if (!data.success) {
            throw new Error(data.error || '検証に失敗しました。');
        }

        displayResults(data);

    } catch (error) {
        showError(error.message);
    } finally {
        loadingDiv.style.display = 'none';
    }
}

function displayResults(data) {
    resultsSection.style.display = 'block';

    // 1. Subset Check
    displaySubsetCheck(data.subset_check);

    // 2. Grammar Info
    displayGrammarInfo(data.source_grammar, data.target_grammar);

    // 3. MTT
    displayMTT(data.mtt);

    // 4. Type Validation
    displayTypeValidation(data.type_validation);

    // 5. Coverage Matrix
    displayCoverageMatrix(data.type_validation?.coverage_matrix);

    // 6. Preimage Computation
    displayPreimage(data.preimage);
}

function displaySubsetCheck(subsetCheck) {
    const content = document.getElementById('subset-content');

    const status = subsetCheck.valid ? 'valid' : 'invalid';
    const statusText = subsetCheck.valid ? '✓ 有効' : '✗ 無効';

    let html = `<span class="status-badge status-${status}">${statusText}</span>`;

    if (subsetCheck.errors && subsetCheck.errors.length > 0) {
        html += '<h4>エラー:</h4><ul class="error-list">';
        subsetCheck.errors.forEach(error => {
            html += `<li>${escapeHtml(error)}</li>`;
        });
        html += '</ul>';
    }

    if (subsetCheck.warnings && subsetCheck.warnings.length > 0) {
        html += '<h4>警告:</h4><ul class="warning-list">';
        subsetCheck.warnings.forEach(warning => {
            html += `<li>${escapeHtml(warning)}</li>`;
        });
        html += '</ul>';
    }

    if (subsetCheck.valid && subsetCheck.warnings.length === 0) {
        html += '<p>XSLTは許可されたサブセットに準拠しています。</p>';
    }

    content.innerHTML = html;
}

function displayGrammarInfo(sourceGrammar, targetGrammar) {
    const sourceContent = document.getElementById('source-grammar-content');
    const targetContent = document.getElementById('target-grammar-content');

    sourceContent.innerHTML = formatGrammar(sourceGrammar);
    targetContent.innerHTML = formatGrammar(targetGrammar);
}

function formatGrammar(grammar) {
    if (!grammar) return '<p>文法情報がありません。</p>';

    let html = `<p><strong>ルート要素:</strong> ${grammar.root_element}</p>`;

    if (grammar.productions && grammar.productions.length > 0) {
        html += '<h5>生成規則:</h5>';
        grammar.productions.forEach(prod => {
            const cardStr = formatCardinality(prod.cardinality);
            html += `<div class="production-rule">`;
            html += `<strong>${prod.lhs}</strong> → `;
            html += `${prod.rhs.join(', ')} `;
            html += `<em>(${prod.type}, ${cardStr})</em>`;
            html += `</div>`;
        });
    }

    if (grammar.type_constraints && Object.keys(grammar.type_constraints).length > 0) {
        html += '<h5>型制約:</h5>';
        Object.entries(grammar.type_constraints).forEach(([name, constraint]) => {
            html += `<div class="code-block">`;
            html += `${name}: ${constraint.base_type}`;
            if (constraint.restrictions && Object.keys(constraint.restrictions).length > 0) {
                html += ' [' + Object.entries(constraint.restrictions)
                    .map(([k, v]) => `${k}=${v}`)
                    .join(', ') + ']';
            }
            html += `</div>`;
        });
    }

    if (grammar.attributes && Object.keys(grammar.attributes).length > 0) {
        html += '<h5>属性:</h5>';
        Object.entries(grammar.attributes).forEach(([elem, attrs]) => {
            html += `<div class="code-block"><strong>${elem}:</strong><br>`;
            attrs.forEach(([name, type, required]) => {
                html += `  @${name}: ${type} ${required ? '(required)' : '(optional)'}<br>`;
            });
            html += `</div>`;
        });
    }

    return html;
}

function formatCardinality(card) {
    if (!card) return '(1,1)';
    const [min, max] = card;
    return `(${min},${max === -1 ? '∞' : max})`;
}

function displayMTT(mtt) {
    const content = document.getElementById('mtt-content');

    if (!mtt || !mtt.states) {
        content.innerHTML = '<p>MTT情報がありません。</p>';
        return;
    }

    let html = '<h4>状態:</h4>';
    html += '<div class="code-block">' + mtt.states.join(', ') + '</div>';

    if (mtt.rules && mtt.rules.length > 0) {
        html += '<h4>変換規則:</h4>';
        mtt.rules.forEach((rule, index) => {
            html += `<div class="mtt-rule">`;
            html += `<strong>Rule ${index + 1}:</strong><br>`;
            html += `State: ${rule.state}<br>`;
            html += `LHS: ${rule.lhs}<br>`;
            html += `RHS: ${formatMTTOutput(rule.rhs)}`;
            if (rule.guard) {
                html += `<br>Guard: ${rule.guard}`;
            }
            html += `</div>`;
        });
    }

    content.innerHTML = html;
}

function formatMTTOutput(output) {
    if (typeof output === 'string') {
        return output;
    }
    return JSON.stringify(output, null, 2);
}

function displayTypeValidation(validation) {
    const content = document.getElementById('type-validation-content');

    if (!validation) {
        content.innerHTML = '<p>型検証情報がありません。</p>';
        return;
    }

    const status = validation.valid ? 'valid' : 'invalid';
    const statusText = validation.valid ? '✓ 型保存性が確認されました' : '✗ 型保存性に問題があります';

    let html = `<span class="status-badge status-${status}">${statusText}</span>`;

    if (validation.errors && validation.errors.length > 0) {
        html += '<h4>エラー:</h4><ul class="error-list">';
        validation.errors.forEach(error => {
            html += `<li>${escapeHtml(error)}</li>`;
        });
        html += '</ul>';
    }

    if (validation.warnings && validation.warnings.length > 0) {
        html += '<h4>警告:</h4><ul class="warning-list">';
        validation.warnings.forEach(warning => {
            html += `<li>${escapeHtml(warning)}</li>`;
        });
        html += '</ul>';
    }

    if (validation.proof_steps && validation.proof_steps.length > 0) {
        html += '<h4>証明ステップ:</h4>';
        html += '<div class="proof-steps">' +
            validation.proof_steps.map(escapeHtml).join('\n') +
            '</div>';
    }

    content.innerHTML = html;
}

function displayCoverageMatrix(coverage) {
    const content = document.getElementById('coverage-content');

    if (!coverage || !coverage.mappings) {
        content.innerHTML = '<p>カバレッジ情報がありません。</p>';
        return;
    }

    let html = '<table class="coverage-table">';
    html += '<thead><tr>';
    html += '<th>ソース要素</th>';
    html += '<th>ターゲット要素</th>';
    html += '<th>状態</th>';
    html += '</tr></thead><tbody>';

    coverage.mappings.forEach(mapping => {
        html += '<tr>';
        html += `<td>${escapeHtml(mapping.source)}</td>`;
        html += `<td>${escapeHtml(mapping.target)}</td>`;
        html += `<td>${mapping.status}</td>`;
        html += '</tr>';
    });

    html += '</tbody></table>';

    html += `<p style="margin-top: 15px;">`;
    html += `<strong>統計:</strong> `;
    html += `ソース要素: ${coverage.source_elements}, `;
    html += `ターゲット要素: ${coverage.target_elements}, `;
    html += `MTT規則: ${coverage.mtt_rules}`;
    html += `</p>`;

    content.innerHTML = html;
}

function displayPreimage(preimage) {
    const content = document.getElementById('preimage-content');

    if (!preimage) {
        content.innerHTML = '<p>前像計算情報がありません。</p>';
        return;
    }

    if (preimage.error) {
        content.innerHTML = `<p class="error-message">${escapeHtml(preimage.error)}</p>`;
        return;
    }

    let html = '<div class="preimage-section">';

    // Explanation
    html += '<p class="preimage-explanation">';
    html += '前像 pre<sub>M</sub>(L(G<sub>T</sub>)) は、MTT M による変換後に';
    html += 'ターゲット文法 G<sub>T</sub> の言語に含まれる入力木の集合を表します。';
    html += '</p>';

    // Accepted Patterns
    html += '<h4>受理される入力パターン:</h4>';
    if (preimage.accepted_patterns && preimage.accepted_patterns.length > 0) {
        html += '<ul class="accepted-patterns">';
        preimage.accepted_patterns.forEach(pattern => {
            let patternStr = escapeHtml(pattern.element);
            if (pattern.children && pattern.children.length > 0) {
                patternStr += '(' + pattern.children.map(escapeHtml).join(', ') + ')';
            }

            html += `<li><strong>${patternStr}</strong>`;

            if (pattern.constraints && pattern.constraints.length > 0) {
                html += '<br><span class="constraint">条件: ';
                html += pattern.constraints.map(c => escapeHtml(c)).join(' かつ ');
                html += '</span>';
            }

            html += '</li>';
        });
        html += '</ul>';
    } else {
        html += '<p class="no-data">受理されるパターンがありません。</p>';
    }

    // Rejected Patterns
    if (preimage.rejected_patterns && preimage.rejected_patterns.length > 0) {
        html += '<h4>拒否されたパターン:</h4>';
        html += '<ul class="rejected-patterns">';
        preimage.rejected_patterns.forEach(([pattern, reason]) => {
            html += `<li>`;
            html += `<span class="rejected-pattern">✗ ${escapeHtml(pattern)}</span><br>`;
            html += `<span class="rejection-reason">理由: ${escapeHtml(reason)}</span>`;
            html += `</li>`;
        });
        html += '</ul>';
    }

    // Statistics
    if (preimage.statistics) {
        html += '<h4>統計情報:</h4>';
        html += '<div class="preimage-stats">';
        html += `<p><strong>MTT規則総数:</strong> ${preimage.statistics.total_rules}</p>`;
        html += `<p><strong>受理パターン数:</strong> ${preimage.statistics.accepted_patterns}</p>`;
        html += `<p><strong>拒否パターン数:</strong> ${preimage.statistics.rejected_patterns}</p>`;

        const coverage = (preimage.statistics.coverage * 100).toFixed(1);
        html += `<p><strong>カバレッジ:</strong> ${coverage}%</p>`;
        html += '</div>';
    }

    html += '</div>';

    content.innerHTML = html;
}

async function loadSample() {
    try {
        // Load sample files
        const [sourceXsd, targetXsd, xslt] = await Promise.all([
            fetch('/samples/source.xsd').then(r => r.text()),
            fetch('/samples/target.xsd').then(r => r.text()),
            fetch('/samples/transform.xsl').then(r => r.text())
        ]);

        sourceXsdInput.value = sourceXsd;
        targetXsdInput.value = targetXsd;
        xsltInput.value = xslt;

    } catch (error) {
        // If samples don't exist, load hardcoded examples
        loadHardcodedSamples();
    }
}

async function loadSample2() {
    try {
        // Load sample2 files (complex scenario)
        const [sourceXsd, targetXsd, xslt] = await Promise.all([
            fetch('/sample2/source.xsd').then(r => r.text()),
            fetch('/sample2/target.xsd').then(r => r.text()),
            fetch('/sample2/transform.xslt').then(r => r.text())
        ]);

        sourceXsdInput.value = sourceXsd;
        targetXsdInput.value = targetXsd;
        xsltInput.value = xslt;

    } catch (error) {
        showError('サンプル2の読み込みに失敗しました: ' + error.message);
    }
}

function loadHardcodedSamples() {
    // Sample from spec/the_theory_and_sample.md
    sourceXsdInput.value = `<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Person">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Name" type="xs:string"/>
        <xs:element name="Age" type="xs:integer"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>`;

    targetXsdInput.value = `<?xml version="1.0" encoding="UTF-8"?>
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
</xs:schema>`;

    xsltInput.value = `<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="Person">
    <xsl:if test="Age >= 0">
      <Individual fullname="{Name}" years="{Age}"/>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>`;
}

function clearInputs() {
    sourceXsdInput.value = '';
    targetXsdInput.value = '';
    xsltInput.value = '';
    resultsSection.style.display = 'none';
    errorMessageDiv.style.display = 'none';
}

function showError(message) {
    errorMessageDiv.textContent = 'エラー: ' + message;
    errorMessageDiv.style.display = 'block';
    resultsSection.style.display = 'none';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
