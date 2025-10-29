#!/usr/bin/env python3
"""
Detailed test to see the full proof steps
"""

import sys
sys.path.insert(0, '/home/user/xslt_validation')

from backend.xsd_parser import XSDParser
from backend.mtt_converter import XSLTToMTTConverter
from backend.type_validator import TypePreservationValidator

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

print("MTT Output:")
import json
print(json.dumps(converter.to_json(), indent=2))
print()

# Validate type preservation
validator = TypePreservationValidator()
result = validator.validate(source_grammar, target_grammar, mtt)

print("=" * 60)
print("FULL PROOF STEPS:")
print("=" * 60)
for step in result.proof_steps:
    print(step)

print("\n" + "=" * 60)
print("WARNINGS:")
print("=" * 60)
for warning in result.warnings:
    print(f"  ⚠️  {warning}")

print("\n" + "=" * 60)
print("ERRORS:")
print("=" * 60)
for error in result.errors:
    print(f"  ❌ {error}")
