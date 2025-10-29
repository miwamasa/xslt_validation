"""
Flask API for XSLT Validation System
Provides endpoints for validating XSLT transformations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import traceback

from backend.xslt_checker import XSLTSubsetChecker
from backend.xsd_parser import XSDParser
from backend.mtt_converter import XSLTToMTTConverter
from backend.type_validator import TypePreservationValidator
from backend.preimage_computer import PreimageComputer

app = Flask(__name__)
CORS(app)


@app.route('/api/validate', methods=['POST'])
def validate():
    """
    Main validation endpoint
    Accepts source XSD, target XSD, and XSLT
    Returns validation results
    """
    try:
        data = request.json

        source_xsd = data.get('source_xsd', '')
        target_xsd = data.get('target_xsd', '')
        xslt = data.get('xslt', '')

        if not all([source_xsd, target_xsd, xslt]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: source_xsd, target_xsd, xslt'
            }), 400

        result = {
            'success': True,
            'subset_check': {},
            'source_grammar': {},
            'target_grammar': {},
            'mtt': {},
            'type_validation': {},
            'preimage': {}
        }

        # Step 1: Check XSLT subset compliance
        subset_checker = XSLTSubsetChecker()
        is_valid, errors, warnings = subset_checker.check_xslt(xslt)

        result['subset_check'] = {
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings
        }

        # If XSLT doesn't conform to subset, return early
        if not is_valid:
            return jsonify(result), 200

        # Step 2: Parse source XSD to tree grammar
        try:
            source_parser = XSDParser()
            source_grammar = source_parser.parse(source_xsd)

            result['source_grammar'] = {
                'root_element': source_grammar.root_element,
                'productions': [
                    {
                        'lhs': p.lhs,
                        'rhs': p.rhs,
                        'type': p.element_type,
                        'cardinality': p.cardinality
                    }
                    for p in source_grammar.productions
                ],
                'type_constraints': {
                    name: {
                        'base_type': tc.base_type,
                        'restrictions': tc.restrictions
                    }
                    for name, tc in source_grammar.type_constraints.items()
                },
                'attributes': source_grammar.attributes
            }
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error parsing source XSD: {str(e)}'
            }), 400

        # Step 3: Parse target XSD to tree grammar
        try:
            target_parser = XSDParser()
            target_grammar = target_parser.parse(target_xsd)

            result['target_grammar'] = {
                'root_element': target_grammar.root_element,
                'productions': [
                    {
                        'lhs': p.lhs,
                        'rhs': p.rhs,
                        'type': p.element_type,
                        'cardinality': p.cardinality
                    }
                    for p in target_grammar.productions
                ],
                'type_constraints': {
                    name: {
                        'base_type': tc.base_type,
                        'restrictions': tc.restrictions
                    }
                    for name, tc in target_grammar.type_constraints.items()
                },
                'attributes': target_grammar.attributes
            }
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error parsing target XSD: {str(e)}'
            }), 400

        # Step 4: Convert XSLT to MTT
        try:
            mtt_converter = XSLTToMTTConverter()
            mtt = mtt_converter.convert(xslt)

            result['mtt'] = mtt_converter.to_json()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error converting XSLT to MTT: {str(e)}'
            }), 400

        # Step 5: Validate type preservation
        try:
            validator = TypePreservationValidator()
            validation_result = validator.validate(
                source_grammar,
                target_grammar,
                mtt
            )

            result['type_validation'] = {
                'valid': validation_result.is_valid,
                'proof_steps': validation_result.proof_steps,
                'warnings': validation_result.warnings,
                'errors': validation_result.errors,
                'coverage_matrix': validation_result.coverage_matrix
            }
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error validating type preservation: {str(e)}'
            }), 400

        # Step 6: Compute preimage
        try:
            preimage_computer = PreimageComputer()
            preimage_result = preimage_computer.compute_preimage(
                target_grammar,
                mtt
            )

            result['preimage'] = {
                'accepted_patterns': [
                    {
                        'element': p.element,
                        'children': p.children,
                        'constraints': p.constraints,
                        'pattern_string': str(p)
                    }
                    for p in preimage_result.accepted_patterns
                ],
                'rejected_patterns': [
                    {
                        'pattern': pattern,
                        'reason': reason
                    }
                    for pattern, reason in preimage_result.rejected_patterns
                ],
                'statistics': preimage_result.statistics
            }
        except Exception as e:
            # Preimage computation is optional, don't fail the whole request
            result['preimage'] = {
                'error': f'Error computing preimage: {str(e)}',
                'accepted_patterns': [],
                'rejected_patterns': [],
                'statistics': {}
            }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/check-subset', methods=['POST'])
def check_subset():
    """
    Check if XSLT conforms to allowed subset
    """
    try:
        data = request.json
        xslt = data.get('xslt', '')

        if not xslt:
            return jsonify({
                'success': False,
                'error': 'Missing required field: xslt'
            }), 400

        checker = XSLTSubsetChecker()
        is_valid, errors, warnings = checker.check_xslt(xslt)

        return jsonify({
            'success': True,
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/parse-xsd', methods=['POST'])
def parse_xsd():
    """
    Parse XSD and return tree grammar
    """
    try:
        data = request.json
        xsd = data.get('xsd', '')

        if not xsd:
            return jsonify({
                'success': False,
                'error': 'Missing required field: xsd'
            }), 400

        parser = XSDParser()
        grammar = parser.parse(xsd)

        return jsonify({
            'success': True,
            'grammar': {
                'root_element': grammar.root_element,
                'productions': [
                    {
                        'lhs': p.lhs,
                        'rhs': p.rhs,
                        'type': p.element_type,
                        'cardinality': p.cardinality
                    }
                    for p in grammar.productions
                ],
                'type_constraints': {
                    name: {
                        'base_type': tc.base_type,
                        'restrictions': tc.restrictions
                    }
                    for name, tc in grammar.type_constraints.items()
                },
                'attributes': grammar.attributes
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/convert-to-mtt', methods=['POST'])
def convert_to_mtt():
    """
    Convert XSLT to MTT representation
    """
    try:
        data = request.json
        xslt = data.get('xslt', '')

        if not xslt:
            return jsonify({
                'success': False,
                'error': 'Missing required field: xslt'
            }), 400

        converter = XSLTToMTTConverter()
        mtt = converter.convert(xslt)

        return jsonify({
            'success': True,
            'mtt': converter.to_json()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'XSLT Validation API'
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
