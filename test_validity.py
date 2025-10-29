"""
Test script for Validity Checking
Tests L(Src) ⊆ pre_T(L(Tgt)) verification
"""

from backend.xsd_parser import XSDParser
from backend.mtt_converter import XSLTToMTTConverter
from backend.preimage_computer import PreimageComputer
from backend.validity_checker import ValidityChecker


def test_sample1_validity():
    """Test validity checking on Sample 1 (Person→Individual)"""
    print("=" * 70)
    print("SAMPLE 1: VALIDITY CHECKING TEST")
    print("=" * 70)
    print()

    # Read sample files
    with open('samples/source.xsd', 'r') as f:
        source_xsd = f.read()

    with open('samples/target.xsd', 'r') as f:
        target_xsd = f.read()

    with open('samples/transform.xsl', 'r') as f:
        xslt = f.read()

    # Parse grammars
    print("Step 1: Parsing grammars...")
    source_parser = XSDParser()
    source_grammar = source_parser.parse(source_xsd)
    print(f"  ✓ Source: {source_grammar.root_element}")
    print(f"     Productions: {len(source_grammar.productions)}")

    target_parser = XSDParser()
    target_grammar = target_parser.parse(target_xsd)
    print(f"  ✓ Target: {target_grammar.root_element}")
    print()

    # Convert to MTT
    print("Step 2: Converting XSLT to MTT...")
    converter = XSLTToMTTConverter()
    mtt = converter.convert(xslt)
    print(f"  ✓ MTT rules: {len(mtt.rules)}")
    print()

    # Compute preimage
    print("Step 3: Computing preimage...")
    preimage_computer = PreimageComputer()
    preimage_result = preimage_computer.compute_preimage(target_grammar, mtt)
    print(f"  ✓ Accepted patterns: {len(preimage_result.accepted_patterns)}")
    for pattern in preimage_result.accepted_patterns:
        print(f"     - {pattern}")
    print()

    # Check validity
    print("Step 4: Checking validity L(Src) ⊆ pre_T(L(Tgt))...")
    validity_checker = ValidityChecker()
    validity_result = validity_checker.check_validity(
        source_grammar,
        preimage_result
    )

    print()
    print("Validity Result")
    print("=" * 70)
    print(f"Is Valid: {validity_result.is_valid}")
    print(f"Total Source Patterns: {validity_result.total_source_patterns}")
    print(f"Covered Patterns: {validity_result.covered_patterns}")
    print(f"Uncovered Patterns: {validity_result.uncovered_patterns}")
    print(f"Coverage: {validity_result.coverage_percentage:.1f}%")
    print()
    print("Explanation:")
    print(validity_result.explanation)
    print()

    if validity_result.counterexamples:
        print("Counterexamples:")
        for i, ce in enumerate(validity_result.counterexamples, 1):
            print(f"  {i}. {ce.pattern}")
            print(f"     Reason: {ce.reason}")
    else:
        print("✓ No counterexamples found!")

    print()


def test_sample2_validity():
    """Test validity checking on Sample 2 (Company→Organization)"""
    print("=" * 70)
    print("SAMPLE 2: VALIDITY CHECKING TEST")
    print("=" * 70)
    print()

    # Read sample files
    with open('sample2/source.xsd', 'r') as f:
        source_xsd = f.read()

    with open('sample2/target.xsd', 'r') as f:
        target_xsd = f.read()

    with open('sample2/transform.xslt', 'r') as f:
        xslt = f.read()

    # Parse grammars
    print("Step 1: Parsing grammars...")
    source_parser = XSDParser()
    source_grammar = source_parser.parse(source_xsd)
    print(f"  ✓ Source: {source_grammar.root_element}")
    print(f"     Productions: {len(source_grammar.productions)}")

    target_parser = XSDParser()
    target_grammar = target_parser.parse(target_xsd)
    print(f"  ✓ Target: {target_grammar.root_element}")
    print()

    # Convert to MTT
    print("Step 2: Converting XSLT to MTT...")
    converter = XSLTToMTTConverter()
    mtt = converter.convert(xslt)
    print(f"  ✓ MTT rules: {len(mtt.rules)}")
    print()

    # Compute preimage
    print("Step 3: Computing preimage...")
    preimage_computer = PreimageComputer()
    preimage_result = preimage_computer.compute_preimage(target_grammar, mtt)
    print(f"  ✓ Accepted patterns: {len(preimage_result.accepted_patterns)}")
    for pattern in preimage_result.accepted_patterns:
        print(f"     - {pattern}")
    print()

    # Check validity
    print("Step 4: Checking validity L(Src) ⊆ pre_T(L(Tgt))...")
    validity_checker = ValidityChecker()
    validity_result = validity_checker.check_validity(
        source_grammar,
        preimage_result
    )

    print()
    print("Validity Result")
    print("=" * 70)
    print(f"Is Valid: {validity_result.is_valid}")
    print(f"Total Source Patterns: {validity_result.total_source_patterns}")
    print(f"Covered Patterns: {validity_result.covered_patterns}")
    print(f"Uncovered Patterns: {validity_result.uncovered_patterns}")
    print(f"Coverage: {validity_result.coverage_percentage:.1f}%")
    print()
    print("Explanation:")
    print(validity_result.explanation)
    print()

    if validity_result.counterexamples:
        print("Counterexamples:")
        for i, ce in enumerate(validity_result.counterexamples, 1):
            print(f"  {i}. {ce.pattern}")
            print(f"     Reason: {ce.reason}")
    else:
        print("✓ No counterexamples found!")

    print()


if __name__ == '__main__':
    test_sample1_validity()
    print("\n" + "=" * 70 + "\n")
    test_sample2_validity()
