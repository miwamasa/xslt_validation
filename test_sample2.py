"""
Test script for Sample 2 (Complex Company/Organization scenario)
Tests preimage computation with multiple rules and constraints
"""

from backend.xsd_parser import XSDParser
from backend.mtt_converter import XSLTToMTTConverter
from backend.preimage_computer import PreimageComputer

def test_sample2():
    print("=" * 70)
    print("SAMPLE 2: COMPLEX COMPANY/ORGANIZATION TRANSFORMATION TEST")
    print("=" * 70)
    print()

    # Read sample files
    with open('sample2/source.xsd', 'r') as f:
        source_xsd = f.read()

    with open('sample2/target.xsd', 'r') as f:
        target_xsd = f.read()

    with open('sample2/transform.xslt', 'r') as f:
        xslt = f.read()

    # Step 1: Parse XSDs
    print("Step 1: Parsing XSDs...")
    source_parser = XSDParser()
    source_grammar = source_parser.parse(source_xsd)
    print(f"  ✓ Source grammar: {source_grammar.root_element}")
    print(f"  ✓ Production rules: {len(source_grammar.productions)}")

    target_parser = XSDParser()
    target_grammar = target_parser.parse(target_xsd)
    print(f"  ✓ Target grammar: {target_grammar.root_element}")
    print(f"  ✓ Production rules: {len(target_grammar.productions)}")
    print()

    # Step 2: Convert XSLT to MTT
    print("Step 2: Converting XSLT to MTT...")
    converter = XSLTToMTTConverter()
    mtt = converter.convert(xslt)
    print(f"  ✓ MTT states: {len(mtt.states)}")
    print(f"  ✓ MTT rules: {len(mtt.rules)}")
    print()

    # Print MTT rules for analysis
    print("MTT Rules (Detailed):")
    print("-" * 70)
    for i, rule in enumerate(mtt.rules, 1):
        print(f"{i}. State: {rule.state}")
        print(f"   LHS: {rule.lhs_pattern}")
        print(f"   Guard: {rule.guard if rule.guard else 'None'}")
        print(f"   RHS Type: {rule.rhs_output.get('type') if isinstance(rule.rhs_output, dict) else type(rule.rhs_output).__name__}")
        if isinstance(rule.rhs_output, dict) and rule.rhs_output.get('type') == 'element':
            print(f"   Output element: {rule.rhs_output.get('tag')}")
        print()

    # Step 3: Compute preimage
    print("Step 3: Computing preimage pre_M(L(G_T))...")
    print()

    preimage_computer = PreimageComputer()
    preimage_result = preimage_computer.compute_preimage(target_grammar, mtt)

    # Display results
    print("Preimage Computation Result")
    print("=" * 70)
    print()

    print("Accepted Input Patterns:")
    print("-" * 70)
    if preimage_result.accepted_patterns:
        for i, pattern in enumerate(preimage_result.accepted_patterns, 1):
            children_str = ", ".join(pattern.children) if pattern.children else "*"
            print(f"{i}. {pattern.element}({children_str})")
            if pattern.constraints:
                for constraint in pattern.constraints:
                    print(f"   条件: {constraint}")
            print()
    else:
        print("  (none)")
        print()

    print("Rejected Patterns:")
    print("-" * 70)
    if preimage_result.rejected_patterns:
        for i, (pattern, reason) in enumerate(preimage_result.rejected_patterns, 1):
            print(f"{i}. ✗ {pattern}")
            print(f"   理由: {reason}")
            print()
    else:
        print("  (none)")
        print()

    print("Statistics:")
    print("-" * 70)
    for key, value in preimage_result.statistics.items():
        label = key.replace('_', ' ').title()
        if key == 'coverage':
            print(f"  {label}: {value * 100:.1f}%")
        else:
            print(f"  {label}: {value}")
    print()

    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print()
    print("The preimage pre_M(L(G_T)) shows which source tree patterns")
    print("will transform into valid target trees.")
    print()
    print("Key observations for Sample 2:")
    print("1. Multiple source element types (Employee, Department)")
    print("2. Multiple constraints per element")
    print("3. Conditional transformations based on Role field")
    print("4. Shows which patterns are rejected and why")
    print()

if __name__ == '__main__':
    test_sample2()
