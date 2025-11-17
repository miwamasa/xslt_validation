"""
Test script for Strict Validity Checking with SMT Solver
"""

from backend.xsd_parser import XSDParser
from backend.mtt_converter import XSLTToMTTConverter
from backend.preimage_computer import PreimageComputer
from backend.strict_validity_checker import StrictValidityChecker


def test_sample1_strict():
    """Test strict validation on Sample 1"""
    print("=" * 70)
    print("SAMPLE 1: STRICT VALIDITY CHECKING (SMT)")
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
    source_parser = XSDParser()
    source_grammar = source_parser.parse(source_xsd)

    target_parser = XSDParser()
    target_grammar = target_parser.parse(target_xsd)

    # Convert to MTT
    converter = XSLTToMTTConverter()
    mtt = converter.convert(xslt)

    # Compute preimage
    preimage_computer = PreimageComputer()
    preimage_result = preimage_computer.compute_preimage(target_grammar, mtt)

    # Strict validity check
    strict_checker = StrictValidityChecker()
    result = strict_checker.check_strict_validity(source_grammar, preimage_result)

    print("\n" + "=" * 70 + "\n")


def test_sample2_strict():
    """Test strict validation on Sample 2"""
    print("=" * 70)
    print("SAMPLE 2: STRICT VALIDITY CHECKING (SMT)")
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
    source_parser = XSDParser()
    source_grammar = source_parser.parse(source_xsd)

    target_parser = XSDParser()
    target_grammar = target_parser.parse(target_xsd)

    # Convert to MTT
    converter = XSLTToMTTConverter()
    mtt = converter.convert(xslt)

    # Compute preimage
    preimage_computer = PreimageComputer()
    preimage_result = preimage_computer.compute_preimage(target_grammar, mtt)

    # Strict validity check
    strict_checker = StrictValidityChecker()
    result = strict_checker.check_strict_validity(source_grammar, preimage_result)

    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    test_sample1_strict()
    test_sample2_strict()
