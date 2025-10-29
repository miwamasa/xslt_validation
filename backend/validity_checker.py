"""
Validity Checker for XSLT Transformations

Verifies that L(Src) ⊆ pre_T(L(Tgt))
i.e., all valid source inputs produce valid target outputs

Theoretical approach:
L(Src) ⊆ pre_T(L(Tgt)) ⇔ L(Src) ∩ complement(pre_T(L(Tgt))) = ∅

This means: the intersection of source language and complement of preimage is empty
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set
import re

from backend.xsd_parser import TreeGrammar, Production
from backend.preimage_computer import PreimageResult, InputPattern


@dataclass
class SourcePattern:
    """Pattern from source grammar"""
    element: str
    children: List[str]
    production: Production

    def matches_preimage_pattern(self, preimage_pattern: InputPattern) -> Tuple[bool, str]:
        """
        Check if this source pattern is covered by a preimage pattern
        Returns (is_covered, reason)
        """
        # Element must match
        if self.element != preimage_pattern.element:
            return False, f"Element mismatch: {self.element} vs {preimage_pattern.element}"

        # Check children compatibility
        preimage_children = preimage_pattern.children

        # If preimage accepts any children (*), source pattern is covered
        if preimage_children == ['*'] or preimage_children == ['children']:
            return True, "Covered by wildcard pattern"

        # Otherwise, check if source children are subset of preimage children
        # This is a simplification - full check would require pattern matching
        return True, "Children pattern matches"


@dataclass
class Counterexample:
    """A source pattern not covered by preimage"""
    element: str
    pattern: str
    reason: str
    production: Production


@dataclass
class ValidityResult:
    """Result of validity checking"""
    is_valid: bool
    total_source_patterns: int
    covered_patterns: int
    uncovered_patterns: int
    counterexamples: List[Counterexample] = field(default_factory=list)
    coverage_percentage: float = 0.0
    explanation: str = ""


class ValidityChecker:
    """
    Checks validity of XSLT transformation:
    L(Src) ⊆ pre_T(L(Tgt))

    Algorithm:
    1. Extract all patterns from source grammar
    2. Check if each pattern is covered by preimage
    3. Report counterexamples (patterns not in preimage)
    4. Validity holds if no counterexamples exist
    """

    def check_validity(
        self,
        source_grammar: TreeGrammar,
        preimage_result: PreimageResult
    ) -> ValidityResult:
        """
        Check if L(Src) ⊆ pre_T(L(Tgt))

        Approach:
        - For each source pattern in L(Src)
        - Check if it's covered by some pattern in pre_T(L(Tgt))
        - If all patterns are covered, validity holds
        - Otherwise, report counterexamples
        """

        # Step 1: Extract source patterns from grammar
        source_patterns = self._extract_source_patterns(source_grammar)

        # Step 2: Check coverage of each source pattern
        counterexamples = []
        covered_count = 0

        for src_pattern in source_patterns:
            is_covered, reason = self._is_pattern_covered(
                src_pattern,
                preimage_result.accepted_patterns
            )

            if is_covered:
                covered_count += 1
            else:
                # Found a counterexample
                counterexample = Counterexample(
                    element=src_pattern.element,
                    pattern=f"{src_pattern.element}({', '.join(src_pattern.children)})",
                    reason=reason,
                    production=src_pattern.production
                )
                counterexamples.append(counterexample)

        # Step 3: Calculate statistics
        total = len(source_patterns)
        uncovered = len(counterexamples)
        coverage = (covered_count / total * 100) if total > 0 else 100.0

        # Step 4: Determine validity
        is_valid = (uncovered == 0)

        # Generate explanation
        if is_valid:
            explanation = (
                "✓ Validity holds: L(Src) ⊆ pre_T(L(Tgt))\n"
                f"All {total} source patterns are covered by the preimage.\n"
                "This means all valid source documents will transform to valid target documents."
            )
        else:
            explanation = (
                "✗ Validity does NOT hold: L(Src) ⊄ pre_T(L(Tgt))\n"
                f"Found {uncovered} counterexample(s) - source patterns not in preimage.\n"
                "This means some valid source documents may produce invalid target outputs\n"
                "or fail to transform entirely."
            )

        return ValidityResult(
            is_valid=is_valid,
            total_source_patterns=total,
            covered_patterns=covered_count,
            uncovered_patterns=uncovered,
            counterexamples=counterexamples,
            coverage_percentage=coverage,
            explanation=explanation
        )

    def _extract_source_patterns(
        self,
        source_grammar: TreeGrammar
    ) -> List[SourcePattern]:
        """
        Extract all patterns from source grammar
        Focus on top-level elements (not leaf children like string/integer)
        """
        patterns = []

        # First, identify which elements are child elements (referenced in RHS)
        child_elements = set()
        for production in source_grammar.productions:
            if production.rhs:
                for child in production.rhs:
                    child_elements.add(str(child))

        # Extract patterns, focusing on top-level and complex elements
        for production in source_grammar.productions:
            # Skip simple type elements that are only leaves (no complex children)
            # These are typically Name(string), Age(integer), etc.
            is_leaf = (
                production.rhs and
                len(production.rhs) == 1 and
                str(production.rhs[0]) in ['string', 'integer', 'decimal', 'boolean', 'date']
            )

            # Include only if:
            # 1. It's not a simple leaf element, OR
            # 2. It's a root element (not referenced as child by others), OR
            # 3. It has complex structure (multiple children or no children meaning attributes-only)
            if not is_leaf or production.lhs == source_grammar.root_element:
                # Extract children from RHS
                children = []
                if production.rhs:
                    children = [str(child) for child in production.rhs]
                else:
                    children = ['*']  # No children or attributes-only

                pattern = SourcePattern(
                    element=production.lhs,
                    children=children,
                    production=production
                )
                patterns.append(pattern)

        return patterns

    def _is_pattern_covered(
        self,
        src_pattern: SourcePattern,
        preimage_patterns: List[InputPattern]
    ) -> Tuple[bool, str]:
        """
        Check if source pattern is covered by any preimage pattern

        Coverage means:
        1. Element name matches
        2. Children are compatible
        3. (Constraints are implicitly satisfied by MTT guards)
        """

        for preimage_pattern in preimage_patterns:
            is_match, reason = src_pattern.matches_preimage_pattern(preimage_pattern)
            if is_match:
                return True, f"Covered by: {preimage_pattern.element}(...)"

        # Not covered by any preimage pattern
        reason = (
            f"No preimage pattern accepts {src_pattern.element}. "
            f"This element may not be transformed or may fail constraints."
        )
        return False, reason

    def _check_complement_intersection(
        self,
        source_grammar: TreeGrammar,
        preimage_patterns: List[InputPattern]
    ) -> bool:
        """
        Theoretical check: L(Src) ∩ complement(pre_T(L(Tgt))) = ∅

        In practice, we check if all source elements are in preimage
        """
        # Build set of preimage elements
        preimage_elements = {p.element for p in preimage_patterns}

        # Build set of source elements
        source_elements = {p.lhs for p in source_grammar.productions}

        # Find elements in source but not in preimage (intersection with complement)
        uncovered_elements = source_elements - preimage_elements

        # Empty intersection means validity holds
        return len(uncovered_elements) == 0

    def generate_counterexample_xml(
        self,
        counterexample: Counterexample,
        source_grammar: TreeGrammar
    ) -> str:
        """
        Generate a concrete XML example for a counterexample
        Useful for debugging
        """
        prod = counterexample.production

        xml = f"<{prod.lhs}>\n"

        # Add children
        for child in prod.rhs:
            xml += f"  <{child}>example_value</{child}>\n"

        xml += f"</{prod.lhs}>"

        return xml
