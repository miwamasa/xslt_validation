#!/usr/bin/env python3
"""
Simple test script to verify the XSLT validation system
"""

import sys
sys.path.insert(0, '/home/user/xslt_validation')

from backend.xslt_checker import XSLTSubsetChecker
from backend.xsd_parser import XSDParser
from backend.mtt_converter import XSLTToMTTConverter
from backend.type_validator import TypePreservationValidator


def test_xslt_checker():
    """Test XSLT subset checker"""
    print("Testing XSLT Subset Checker...")

    xslt = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="Person">
    <xsl:if test="Age >= 0">
      <Individual fullname="{Name}" years="{Age}"/>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>"""

    checker = XSLTSubsetChecker()
    is_valid, errors, warnings = checker.check_xslt(xslt)

    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")

    if errors:
        for error in errors:
            print(f"    - {error}")

    if warnings:
        for warning in warnings:
            print(f"    ! {warning}")

    print()
    return is_valid


def test_xsd_parser():
    """Test XSD parser"""
    print("Testing XSD Parser...")

    xsd = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Person">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Name" type="xs:string"/>
        <xs:element name="Age" type="xs:integer"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""

    parser = XSDParser()
    grammar = parser.parse(xsd)

    print(f"  Root element: {grammar.root_element}")
    print(f"  Productions: {len(grammar.productions)}")
    print(f"  Type constraints: {len(grammar.type_constraints)}")

    for prod in grammar.productions:
        print(f"    {prod.lhs} → {prod.rhs}")

    print()
    return grammar


def test_mtt_converter():
    """Test XSLT to MTT converter"""
    print("Testing XSLT to MTT Converter...")

    xslt = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="Person">
    <Individual fullname="{Name}" years="{Age}"/>
  </xsl:template>
</xsl:stylesheet>"""

    converter = XSLTToMTTConverter()
    mtt = converter.convert(xslt)

    print(f"  States: {len(mtt.states)}")
    print(f"  Rules: {len(mtt.rules)}")

    for state in mtt.states:
        print(f"    State: {state}")

    print()
    return mtt


def test_full_validation():
    """Test full validation pipeline"""
    print("Testing Full Validation Pipeline...")

    source_xsd = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Person">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Name" type="xs:string"/>
        <xs:element name="Age" type="xs:integer"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""

    target_xsd = """<?xml version="1.0" encoding="UTF-8"?>
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
</xs:schema>"""

    xslt = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="Person">
    <xsl:if test="Age >= 0">
      <Individual fullname="{Name}" years="{Age}"/>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>"""

    # Parse XSDs
    source_parser = XSDParser()
    source_grammar = source_parser.parse(source_xsd)

    target_parser = XSDParser()
    target_grammar = target_parser.parse(target_xsd)

    # Convert XSLT to MTT
    converter = XSLTToMTTConverter()
    mtt = converter.convert(xslt)

    # Validate type preservation
    validator = TypePreservationValidator()
    result = validator.validate(source_grammar, target_grammar, mtt)

    print(f"  Type preservation valid: {result.is_valid}")
    print(f"  Proof steps: {len(result.proof_steps)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")

    print("\nProof Steps:")
    for step in result.proof_steps[:10]:  # Show first 10 steps
        print(f"  {step}")

    if len(result.proof_steps) > 10:
        print(f"  ... ({len(result.proof_steps) - 10} more steps)")

    print()
    return result.is_valid


def main():
    """Run all tests"""
    print("=" * 60)
    print("XSLT Validation System Test")
    print("=" * 60)
    print()

    try:
        test1 = test_xslt_checker()
        test2 = test_xsd_parser()
        test3 = test_mtt_converter()
        test4 = test_full_validation()

        print("=" * 60)
        print("Test Summary:")
        print(f"  XSLT Checker: {'PASS' if test1 else 'FAIL'}")
        print(f"  XSD Parser: {'PASS' if test2 else 'FAIL'}")
        print(f"  MTT Converter: {'PASS' if test3 else 'FAIL'}")
        print(f"  Full Validation: {'PASS' if test4 else 'FAIL'}")
        print("=" * 60)

        return all([test1, test2, test3])

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
