#!/usr/bin/env python3
"""
Test preimage computation
"""

import sys
sys.path.insert(0, '/home/user/xslt_validation')

from backend.xsd_parser import XSDParser
from backend.mtt_converter import XSLTToMTTConverter
from backend.preimage_computer import PreimageComputer

# Load sample files
with open('samples/source.xsd') as f:
    source_xsd = f.read()

with open('samples/target.xsd') as f:
    target_xsd = f.read()

with open('samples/transform.xsl') as f:
    xslt = f.read()

print("=" * 70)
print("PREIMAGE COMPUTATION TEST")
print("=" * 70)
print()

# Parse XSDs
print("Step 1: Parsing XSDs...")
source_parser = XSDParser()
source_grammar = source_parser.parse(source_xsd)
print(f"  ✓ Source grammar: {source_grammar.root_element}")

target_parser = XSDParser()
target_grammar = target_parser.parse(target_xsd)
print(f"  ✓ Target grammar: {target_grammar.root_element}")

# Convert XSLT to MTT
print("\nStep 2: Converting XSLT to MTT...")
converter = XSLTToMTTConverter()
mtt = converter.convert(xslt)
print(f"  ✓ MTT states: {len(mtt.states)}")
print(f"  ✓ MTT rules: {len(mtt.rules)}")

# Compute preimage
print("\nStep 3: Computing preimage pre_M(L(G_T))...")
print()

computer = PreimageComputer()
preimage_result = computer.compute_preimage(target_grammar, mtt)

# Display results
print(computer.format_preimage(preimage_result))

print()
print("=" * 70)
print("DETAILED ANALYSIS")
print("=" * 70)
print()

# Show MTT rules
print("MTT Rules:")
print("-" * 70)
for i, rule in enumerate(mtt.rules, 1):
    print(f"{i}. State: {rule.state}")
    print(f"   LHS: {rule.lhs_pattern}")
    print(f"   RHS: (output tree)")
    if rule.guard:
        print(f"   Guard: {rule.guard}")
    print()

# Show accepted patterns in detail
print("Accepted Input Patterns (Detailed):")
print("-" * 70)
for pattern in preimage_result.accepted_patterns:
    print(f"Pattern: {pattern.element}")
    if pattern.children:
        print(f"  Children: {', '.join(pattern.children)}")
    if pattern.constraints:
        print(f"  Constraints:")
        for constraint in pattern.constraints:
            print(f"    - {constraint}")
    print()

print("=" * 70)
print("INTERPRETATION")
print("=" * 70)
print()
print("pre_M(L(G_T)) = the set of all source trees that transform to valid target trees")
print()
print("In this example:")
print(f"  Input language: Trees matching {source_grammar.root_element}")
print(f"  Output language: L(G_T) where root is {target_grammar.root_element}")
print(f"  Transformation: MTT with {len(mtt.rules)} rule(s)")
print()
print("The preimage tells us which source trees are GUARANTEED to produce")
print("valid output when transformed through the XSLT.")
print()
