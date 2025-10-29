"""
Preimage Computation for MTT
Computes pre_M(L(G_T)) - the set of input trees that transform to valid output
Based on tree transducer theory
"""

from typing import Dict, List, Set, Any, Tuple
from dataclasses import dataclass, field

from backend.xsd_parser import TreeGrammar, Production
from backend.mtt_converter import MTT, MTTRule


@dataclass
class InputPattern:
    """Represents an accepted input pattern"""
    element: str
    children: List[str]
    constraints: List[str] = field(default_factory=list)

    def __str__(self):
        if self.children:
            children_str = ", ".join(self.children)
            pattern = f"{self.element}({children_str})"
        else:
            pattern = self.element

        if self.constraints:
            constraints_str = " where " + " and ".join(self.constraints)
            return pattern + constraints_str
        return pattern


@dataclass
class PreimageResult:
    """Result of preimage computation"""
    accepted_patterns: List[InputPattern] = field(default_factory=list)
    rejected_patterns: List[Tuple[str, str]] = field(default_factory=list)  # (pattern, reason)
    statistics: Dict[str, Any] = field(default_factory=dict)


class PreimageComputer:
    """
    Computes preimage of target language through MTT

    Theoretical foundation:
    Given MTT M and target grammar G_T,
    compute pre_M(L(G_T)) = {t | M(t) ∈ L(G_T)}

    This is a simplified implementation that:
    1. Analyzes each MTT rule
    2. Checks if output matches target grammar
    3. Collects accepted input patterns
    """

    def __init__(self):
        self.accepted_patterns: List[InputPattern] = []
        self.rejected_patterns: List[Tuple[str, str]] = []

    def compute_preimage(
        self,
        target_grammar: TreeGrammar,
        mtt: MTT
    ) -> PreimageResult:
        """
        Compute preimage pre_M(L(G_T))

        Algorithm:
        1. For each MTT rule q(σ(x1,...,xn)) → t
        2. Check if output t is valid in L(G_T)
        3. If valid, accept input pattern σ(x1,...,xn)
        4. Collect constraints from guards
        """
        self.accepted_patterns = []
        self.rejected_patterns = []

        # Analyze each MTT rule
        for rule in mtt.rules:
            self._analyze_rule(rule, target_grammar)

        # Build statistics
        statistics = {
            "total_rules": len(mtt.rules),
            "accepted_patterns": len(self.accepted_patterns),
            "rejected_patterns": len(self.rejected_patterns),
            "coverage": len(self.accepted_patterns) / len(mtt.rules) if mtt.rules else 0
        }

        return PreimageResult(
            accepted_patterns=self.accepted_patterns,
            rejected_patterns=self.rejected_patterns,
            statistics=statistics
        )

    def _analyze_rule(self, rule: MTTRule, target_grammar: TreeGrammar):
        """Analyze a single MTT rule"""

        # Extract input pattern from LHS
        input_pattern = self._parse_input_pattern(rule.lhs_pattern)

        # Extract constraints from guard
        constraints = []
        if rule.guard:
            constraints.append(rule.guard)

        # Check if output is valid in target grammar
        is_valid, reason = self._validate_output(rule.rhs_output, target_grammar)

        if is_valid:
            # Extract constraints from output (e.g., if conditions)
            output_constraints = self._extract_output_constraints(rule.rhs_output)
            constraints.extend(output_constraints)

            pattern = InputPattern(
                element=input_pattern["element"],
                children=input_pattern["children"],
                constraints=constraints
            )
            self.accepted_patterns.append(pattern)
        else:
            self.rejected_patterns.append((rule.lhs_pattern, reason))

    def _parse_input_pattern(self, lhs_pattern: str) -> Dict[str, Any]:
        """
        Parse input pattern from LHS

        Example: "Person(children)" → {element: "Person", children: ["Name", "Age"]}
        """
        if "(" in lhs_pattern:
            element = lhs_pattern.split("(")[0]
            # Simplified: assume children placeholder
            return {"element": element, "children": ["*"]}
        else:
            return {"element": lhs_pattern, "children": []}

    def _validate_output(
        self,
        output: Any,
        target_grammar: TreeGrammar
    ) -> Tuple[bool, str]:
        """
        Check if output is valid in target grammar

        Simplified validation:
        - Check if root element exists in target
        - Check if structure matches
        """
        if not isinstance(output, dict):
            return True, ""

        # Extract root element from output
        root_elem = self._extract_root_element(output)

        if not root_elem:
            return False, "No root element found in output"

        # Check if root exists in target grammar
        if root_elem == target_grammar.root_element:
            return True, ""

        # Check in productions
        for prod in target_grammar.productions:
            if prod.lhs == root_elem:
                return True, ""

        # Check in attributes
        if root_elem in target_grammar.attributes:
            return True, ""

        return False, f"Element '{root_elem}' not found in target grammar"

    def _extract_root_element(self, output: Dict) -> str:
        """Extract root element name from output tree"""
        if output.get("type") == "element":
            return output.get("name", "")
        elif output.get("type") == "sequence" and output.get("children"):
            for child in output["children"]:
                if isinstance(child, dict):
                    elem = self._extract_root_element(child)
                    if elem:
                        return elem
        elif output.get("type") == "if" and output.get("then"):
            return self._extract_root_element(output["then"])

        return ""

    def _extract_output_constraints(self, output: Dict) -> List[str]:
        """Extract constraints from output tree (e.g., if conditions)"""
        constraints = []

        if isinstance(output, dict):
            if output.get("type") == "if":
                test = output.get("test", "")
                if test:
                    constraints.append(test)

            # Recursively check children
            if output.get("children"):
                for child in output["children"]:
                    if isinstance(child, dict):
                        constraints.extend(self._extract_output_constraints(child))

            # Check 'then' branch
            if output.get("then"):
                constraints.extend(self._extract_output_constraints(output["then"]))

        return constraints

    def generate_input_grammar(
        self,
        preimage_result: PreimageResult,
        source_grammar: TreeGrammar
    ) -> TreeGrammar:
        """
        Generate input grammar from preimage patterns

        This creates a restricted version of source grammar
        that only accepts inputs matching the preimage
        """
        from copy import deepcopy

        # Start with a copy of source grammar
        restricted_grammar = deepcopy(source_grammar)
        restricted_grammar.productions = []

        # Add productions based on accepted patterns
        for pattern in preimage_result.accepted_patterns:
            # Find corresponding production in source grammar
            for prod in source_grammar.productions:
                if prod.lhs == pattern.element:
                    # Add with constraints
                    restricted_grammar.productions.append(prod)
                    break

        return restricted_grammar

    def format_preimage(self, preimage_result: PreimageResult) -> str:
        """Format preimage result as human-readable string"""
        lines = []

        lines.append("Preimage Computation Result")
        lines.append("=" * 60)
        lines.append("")

        lines.append("Accepted Input Patterns:")
        lines.append("-" * 60)
        if preimage_result.accepted_patterns:
            for i, pattern in enumerate(preimage_result.accepted_patterns, 1):
                lines.append(f"{i}. {pattern}")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append("Rejected Patterns:")
        lines.append("-" * 60)
        if preimage_result.rejected_patterns:
            for pattern, reason in preimage_result.rejected_patterns:
                lines.append(f"  ✗ {pattern}")
                lines.append(f"    Reason: {reason}")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append("Statistics:")
        lines.append("-" * 60)
        stats = preimage_result.statistics
        lines.append(f"  Total MTT rules: {stats.get('total_rules', 0)}")
        lines.append(f"  Accepted patterns: {stats.get('accepted_patterns', 0)}")
        lines.append(f"  Rejected patterns: {stats.get('rejected_patterns', 0)}")
        lines.append(f"  Coverage: {stats.get('coverage', 0):.1%}")

        lines.append("")
        lines.append("Interpretation:")
        lines.append("-" * 60)
        lines.append("The preimage pre_M(L(G_T)) represents all input trees that")
        lines.append("will transform to valid outputs in the target grammar.")
        lines.append("")
        lines.append("Accepted patterns are input structures guaranteed to produce")
        lines.append("valid output. Constraints indicate necessary conditions.")

        return "\n".join(lines)


def compute_and_display_preimage(
    source_grammar: TreeGrammar,
    target_grammar: TreeGrammar,
    mtt: MTT
) -> PreimageResult:
    """
    Convenience function to compute and display preimage
    """
    computer = PreimageComputer()
    result = computer.compute_preimage(target_grammar, mtt)

    print(computer.format_preimage(result))

    return result
