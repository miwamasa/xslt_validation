"""
Type Preservation Validator
Validates that XSLT transformation preserves type constraints
Based on spec/the_theory_and_sample.md
"""

from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from backend.xsd_parser import TreeGrammar, Production, TypeConstraint
from backend.mtt_converter import MTT


@dataclass
class ValidationResult:
    """Result of type preservation validation"""
    is_valid: bool
    proof_steps: List[str]
    warnings: List[str]
    errors: List[str]
    coverage_matrix: Dict[str, Any]


class TypePreservationValidator:
    """Validates type preservation in XSLT transformation"""

    def __init__(self):
        self.proof_steps: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.coverage: Dict[str, Any] = {}

    def validate(
        self,
        source_grammar: TreeGrammar,
        target_grammar: TreeGrammar,
        mtt: MTT
    ) -> ValidationResult:
        """
        Validate type preservation: ∀t ∈ L(G_S), M(t) ∈ L(G_T)

        This is a simplified validation that checks:
        1. Structural compatibility
        2. Type constraint preservation
        3. Cardinality constraints
        """
        self.proof_steps = []
        self.warnings = []
        self.errors = []
        self.coverage = {}

        # Step 1: Introduction
        self._add_proof_step("Type Preservation Validation")
        self._add_proof_step("=" * 50)
        self._add_proof_step(
            f"Source grammar root: {source_grammar.root_element}"
        )
        self._add_proof_step(
            f"Target grammar root: {target_grammar.root_element}"
        )
        self._add_proof_step(f"MTT states: {len(mtt.states)}")
        self._add_proof_step("")

        # Step 2: Structural validation
        self._add_proof_step("Step 1: Structural Validation")
        self._add_proof_step("-" * 50)
        self._validate_structure(source_grammar, target_grammar, mtt)
        self._add_proof_step("")

        # Step 3: Type constraint validation
        self._add_proof_step("Step 2: Type Constraint Validation")
        self._add_proof_step("-" * 50)
        self._validate_type_constraints(source_grammar, target_grammar, mtt)
        self._add_proof_step("")

        # Step 4: Cardinality validation
        self._add_proof_step("Step 3: Cardinality Validation")
        self._add_proof_step("-" * 50)
        self._validate_cardinality(source_grammar, target_grammar, mtt)
        self._add_proof_step("")

        # Step 5: Build coverage matrix
        self._build_coverage_matrix(source_grammar, target_grammar, mtt)

        # Final result
        is_valid = len(self.errors) == 0

        if is_valid:
            self._add_proof_step("Conclusion: Type preservation is satisfied ✓")
        else:
            self._add_proof_step("Conclusion: Type preservation FAILED ✗")
            self._add_proof_step(f"Errors found: {len(self.errors)}")

        return ValidationResult(
            is_valid=is_valid,
            proof_steps=self.proof_steps,
            warnings=self.warnings,
            errors=self.errors,
            coverage_matrix=self.coverage
        )

    def _add_proof_step(self, step: str):
        """Add a step to the proof"""
        self.proof_steps.append(step)

    def _validate_structure(
        self,
        source_grammar: TreeGrammar,
        target_grammar: TreeGrammar,
        mtt: MTT
    ):
        """Validate structural compatibility"""

        # Check if there's a mapping for root element
        root_mapping_found = False
        for rule in mtt.rules:
            if source_grammar.root_element in rule.lhs_pattern:
                root_mapping_found = True
                self._add_proof_step(
                    f"✓ Root element mapping found: {source_grammar.root_element}"
                )
                break

        if not root_mapping_found:
            self.errors.append(
                f"No transformation rule for root element '{source_grammar.root_element}'"
            )
            self._add_proof_step(
                f"✗ No transformation rule for root element '{source_grammar.root_element}'"
            )

        # Check coverage of all source productions
        for prod in source_grammar.productions:
            covered = self._is_production_covered(prod, mtt)
            if covered:
                self._add_proof_step(f"✓ Production covered: {prod.lhs} → {prod.rhs}")
            else:
                self.warnings.append(
                    f"Production may not be covered: {prod.lhs} → {prod.rhs}"
                )
                self._add_proof_step(f"⚠ Production not explicitly covered: {prod.lhs}")

    def _is_production_covered(self, prod: Production, mtt: MTT) -> bool:
        """Check if production is covered by MTT rules"""
        for rule in mtt.rules:
            if prod.lhs in rule.lhs_pattern or prod.lhs in str(rule.rhs_output):
                return True
        return False

    def _validate_type_constraints(
        self,
        source_grammar: TreeGrammar,
        target_grammar: TreeGrammar,
        mtt: MTT
    ):
        """Validate type constraints are preserved"""

        # For each source type constraint, check if target has compatible constraint
        for elem_name, src_constraint in source_grammar.type_constraints.items():
            self._add_proof_step(f"Checking type constraint for: {elem_name}")

            # Find corresponding target element
            target_elem = self._find_target_element(elem_name, mtt, target_grammar)

            if target_elem:
                if target_elem in target_grammar.type_constraints:
                    tgt_constraint = target_grammar.type_constraints[target_elem]

                    # Check base type compatibility
                    if self._are_types_compatible(src_constraint, tgt_constraint):
                        self._add_proof_step(
                            f"  ✓ Type compatible: {src_constraint.base_type} → {tgt_constraint.base_type}"
                        )

                        # Check restrictions
                        if tgt_constraint.restrictions:
                            self._check_restrictions(
                                src_constraint,
                                tgt_constraint,
                                elem_name,
                                target_elem
                            )
                    else:
                        self.errors.append(
                            f"Type incompatibility: {elem_name} "
                            f"({src_constraint.base_type} → {tgt_constraint.base_type})"
                        )
                        self._add_proof_step(
                            f"  ✗ Type incompatible: {src_constraint.base_type} "
                            f"→ {tgt_constraint.base_type}"
                        )
                else:
                    self._add_proof_step(f"  ⚠ No type constraint in target for {target_elem}")
            else:
                self.warnings.append(
                    f"Could not find target element for source element: {elem_name}"
                )
                self._add_proof_step(f"  ⚠ Target element not found")

    def _find_target_element(
        self,
        source_elem: str,
        mtt: MTT,
        target_grammar: TreeGrammar
    ) -> str:
        """Find corresponding target element"""
        # Look through MTT rules to find mapping
        for rule in mtt.rules:
            if source_elem in rule.lhs_pattern:
                # Try to extract target element from output
                output = rule.rhs_output
                if isinstance(output, dict):
                    target = self._extract_target_from_output(output)
                    if target:
                        return target

        # Fallback: check if same name exists in target
        for prod in target_grammar.productions:
            if prod.lhs == source_elem:
                return source_elem

        return ""

    def _extract_target_from_output(self, output: Dict) -> str:
        """Extract target element name from output tree"""
        if output.get("type") == "element":
            return output.get("name", "")
        elif output.get("type") == "sequence" and output.get("children"):
            for child in output["children"]:
                if isinstance(child, dict):
                    name = self._extract_target_from_output(child)
                    if name:
                        return name
        return ""

    def _are_types_compatible(
        self,
        src_constraint: TypeConstraint,
        tgt_constraint: TypeConstraint
    ) -> bool:
        """Check if two type constraints are compatible"""
        src_type = src_constraint.base_type
        tgt_type = tgt_constraint.base_type

        # Same type is always compatible
        if src_type == tgt_type:
            return True

        # Check numeric type widening
        numeric_types = ["integer", "int", "long", "decimal", "float", "double"]
        if src_type in numeric_types and tgt_type in numeric_types:
            return True

        # String compatibility
        if src_type == "string" and tgt_type in ["string", "normalizedString", "token"]:
            return True

        return False

    def _check_restrictions(
        self,
        src_constraint: TypeConstraint,
        tgt_constraint: TypeConstraint,
        src_elem: str,
        tgt_elem: str
    ):
        """Check if restrictions are compatible"""
        tgt_restrictions = tgt_constraint.restrictions

        # Check minInclusive
        if "minInclusive" in tgt_restrictions:
            min_value = tgt_restrictions["minInclusive"]
            self._add_proof_step(
                f"  ! Target has restriction: minInclusive={min_value}"
            )
            self.warnings.append(
                f"Target element '{tgt_elem}' has minInclusive={min_value}. "
                f"Ensure source values satisfy this constraint."
            )

        # Check maxInclusive
        if "maxInclusive" in tgt_restrictions:
            max_value = tgt_restrictions["maxInclusive"]
            self._add_proof_step(
                f"  ! Target has restriction: maxInclusive={max_value}"
            )
            self.warnings.append(
                f"Target element '{tgt_elem}' has maxInclusive={max_value}. "
                f"Ensure source values satisfy this constraint."
            )

        # Check pattern
        if "pattern" in tgt_restrictions:
            pattern = tgt_restrictions["pattern"]
            self._add_proof_step(
                f"  ! Target has pattern restriction: {pattern}"
            )
            self.warnings.append(
                f"Target element '{tgt_elem}' has pattern restriction: {pattern}"
            )

    def _validate_cardinality(
        self,
        source_grammar: TreeGrammar,
        target_grammar: TreeGrammar,
        mtt: MTT
    ):
        """Validate cardinality constraints"""

        # Build mapping from source to target productions
        for src_prod in source_grammar.productions:
            # Find corresponding target production
            target_elem = self._find_target_element(src_prod.lhs, mtt, target_grammar)

            if target_elem:
                tgt_prod = self._find_production(target_elem, target_grammar)

                if tgt_prod:
                    src_card = src_prod.cardinality
                    tgt_card = tgt_prod.cardinality

                    self._add_proof_step(
                        f"Cardinality check: {src_prod.lhs} {src_card} → "
                        f"{tgt_prod.lhs} {tgt_card}"
                    )

                    # Check if source cardinality fits in target
                    if not self._is_cardinality_compatible(src_card, tgt_card):
                        self.warnings.append(
                            f"Cardinality mismatch: {src_prod.lhs} {src_card} "
                            f"→ {tgt_prod.lhs} {tgt_card}"
                        )
                        self._add_proof_step("  ⚠ Cardinality may be incompatible")
                    else:
                        self._add_proof_step("  ✓ Cardinality compatible")

    def _find_production(self, element: str, grammar: TreeGrammar) -> Production:
        """Find production by left-hand side"""
        for prod in grammar.productions:
            if prod.lhs == element:
                return prod
        return None

    def _is_cardinality_compatible(
        self,
        src_card: Tuple[int, int],
        tgt_card: Tuple[int, int]
    ) -> bool:
        """Check if source cardinality fits in target"""
        src_min, src_max = src_card
        tgt_min, tgt_max = tgt_card

        # If source can be empty but target requires element
        if src_min == 0 and tgt_min > 0:
            return False

        # If source can have multiple but target allows only one
        if src_max == -1 or src_max > 1:
            if tgt_max == 1:
                return False

        return True

    def _build_coverage_matrix(
        self,
        source_grammar: TreeGrammar,
        target_grammar: TreeGrammar,
        mtt: MTT
    ):
        """Build test coverage matrix"""
        self.coverage = {
            "source_elements": len(source_grammar.productions),
            "target_elements": len(target_grammar.productions),
            "mtt_rules": len(mtt.rules),
            "mappings": []
        }

        for src_prod in source_grammar.productions:
            target_elem = self._find_target_element(src_prod.lhs, mtt, target_grammar)
            self.coverage["mappings"].append({
                "source": src_prod.lhs,
                "target": target_elem or "UNMAPPED",
                "status": "✓" if target_elem else "✗"
            })
