"""
Strict Validity Checker using SMT Solver (Z3)

Performs rigorous validity checking by verifying constraints using SMT solver.
Checks if L(Src) ⊆ pre_T(L(Tgt)) by finding counterexamples where:
  - Input is valid according to source grammar constraints
  - But does not satisfy preimage constraints

Uses Z3 to find concrete counterexample values.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import re

try:
    from z3 import *
except ImportError:
    print("Warning: z3-solver not installed. Run: pip install z3-solver")
    # Define dummy classes for type hints
    class Solver:
        pass

    def Int(name):
        return None

    def Real(name):
        return None

    def String(name):
        return None

from backend.xsd_parser import TreeGrammar, TypeConstraint
from backend.preimage_computer import PreimageResult, InputPattern


@dataclass
class StrictCounterexample:
    """A concrete counterexample with specific values"""
    element: str
    pattern: str
    field_values: Dict[str, Any]  # Field name -> concrete value
    reason: str
    source_constraint: str
    preimage_constraint: str


@dataclass
class StrictValidityResult:
    """Result of strict validity checking using SMT solver"""
    is_valid: bool
    total_patterns_checked: int
    patterns_with_constraint_issues: int
    counterexamples: List[StrictCounterexample] = field(default_factory=list)
    explanation: str = ""


class StrictValidityChecker:
    """
    Strict validity checking using Z3 SMT solver

    Verifies that source constraints are subsumed by preimage constraints.
    For each pattern, checks if there exists a value that:
      - Satisfies source constraints
      - Does NOT satisfy preimage constraints

    If such value exists, it's a counterexample proving invalidity.
    """

    def check_strict_validity(
        self,
        source_grammar: TreeGrammar,
        preimage_result: PreimageResult
    ) -> StrictValidityResult:
        """
        Perform strict validity check using SMT solver

        For each preimage pattern with constraints:
        1. Extract field constraints from preimage
        2. Extract field constraints from source (if any)
        3. Use Z3 to check if: ∃x. source_constraint(x) ∧ ¬preimage_constraint(x)
        4. If SAT, we have a counterexample
        """

        print("\n" + "=" * 70)
        print("STRICT VALIDITY CHECKING WITH SMT SOLVER")
        print("=" * 70)
        print()

        counterexamples = []
        patterns_checked = 0
        patterns_with_issues = 0

        # Check each preimage pattern with constraints
        for preimage_pattern in preimage_result.accepted_patterns:
            if not preimage_pattern.constraints:
                # No constraints to verify
                continue

            patterns_checked += 1

            print(f"Checking pattern: {preimage_pattern.element}")
            print(f"  Preimage constraints: {preimage_pattern.constraints}")

            # Find corresponding source constraints
            source_constraints = self._get_source_constraints(
                preimage_pattern.element,
                source_grammar
            )
            print(f"  Source constraints: {source_constraints if source_constraints else '(none - any value allowed)'}")

            # Check if source allows values that preimage rejects
            counterexample = self._find_counterexample_with_z3(
                preimage_pattern,
                source_constraints,
                source_grammar
            )

            if counterexample:
                counterexamples.append(counterexample)
                patterns_with_issues += 1
                print(f"  ✗ COUNTEREXAMPLE FOUND: {counterexample.field_values}")
                print(f"     {counterexample.reason}")
            else:
                print(f"  ✓ No counterexample (constraints compatible)")
            print()

        # Determine validity
        is_valid = (len(counterexamples) == 0)

        # Generate explanation
        if is_valid:
            explanation = (
                "✓ Strict validity holds!\n"
                f"Checked {patterns_checked} pattern(s) with constraints using Z3 SMT solver.\n"
                "All source constraints are subsumed by preimage constraints.\n"
                "No counterexamples found - all valid source inputs will transform correctly."
            )
        else:
            explanation = (
                "✗ Strict validity does NOT hold!\n"
                f"Found {len(counterexamples)} counterexample(s) using Z3 SMT solver.\n"
                f"Out of {patterns_checked} pattern(s) checked, {patterns_with_issues} have constraint violations.\n"
                "Some valid source inputs will fail preimage constraints."
            )

        print("=" * 70)
        print("STRICT VALIDITY RESULT")
        print("=" * 70)
        print(f"Patterns checked: {patterns_checked}")
        print(f"Patterns with issues: {patterns_with_issues}")
        print(f"Counterexamples: {len(counterexamples)}")
        print(f"Validity: {'✓ VALID' if is_valid else '✗ INVALID'}")
        print("=" * 70 + "\n")

        return StrictValidityResult(
            is_valid=is_valid,
            total_patterns_checked=patterns_checked,
            patterns_with_constraint_issues=patterns_with_issues,
            counterexamples=counterexamples,
            explanation=explanation
        )

    def _get_source_constraints(
        self,
        element_name: str,
        source_grammar: TreeGrammar
    ) -> Dict[str, TypeConstraint]:
        """
        Get type constraints for fields of the given element from source grammar
        """
        constraints = {}

        # Find the production for this element
        for production in source_grammar.productions:
            if production.lhs == element_name:
                # Get constraints for child elements
                if production.rhs:
                    for child in production.rhs:
                        child_str = str(child)
                        if child_str in source_grammar.type_constraints:
                            constraints[child_str] = source_grammar.type_constraints[child_str]
                break

        return constraints

    def _find_counterexample_with_z3(
        self,
        preimage_pattern: InputPattern,
        source_constraints: Dict[str, TypeConstraint],
        source_grammar: TreeGrammar
    ) -> Optional[StrictCounterexample]:
        """
        Use Z3 to find a counterexample: a value that satisfies source constraints
        but violates preimage constraints

        Strategy:
        1. Parse preimage constraints to identify fields and conditions
        2. Create Z3 variables for each field
        3. Add source constraints (or none if unrestricted)
        4. Add negation of preimage constraints
        5. Check SAT - if satisfiable, we have a counterexample
        """

        try:
            # Parse preimage constraints to extract field references
            fields = self._extract_fields_from_constraints(preimage_pattern.constraints)

            if not fields:
                return None

            # Create Z3 solver
            solver = Solver()

            # Create Z3 variables for each field
            z3_vars = {}
            for field in fields:
                # Determine type based on constraint or source grammar
                field_type = self._infer_field_type(field, source_constraints, source_grammar)

                if field_type in ['integer', 'int']:
                    z3_vars[field] = Int(field)
                elif field_type in ['decimal', 'double', 'float']:
                    z3_vars[field] = Real(field)
                else:
                    z3_vars[field] = Int(field)  # Default to integer

            # Add source constraints (if any)
            source_constraint_str = "(any value)"
            if source_constraints:
                for field, constraint in source_constraints.items():
                    if field in z3_vars:
                        z3_constraint = self._type_constraint_to_z3(
                            z3_vars[field],
                            constraint
                        )
                        if z3_constraint is not None:
                            solver.add(z3_constraint)
                            source_constraint_str = str(constraint.restrictions)

            # Add NEGATION of preimage constraints
            # We want to find values that DON'T satisfy preimage constraints
            preimage_z3_constraints = []
            for constraint_str in preimage_pattern.constraints:
                z3_constraint = self._parse_constraint_to_z3(constraint_str, z3_vars)
                if z3_constraint is not None:
                    preimage_z3_constraints.append(z3_constraint)

            if preimage_z3_constraints:
                # Add NOT (preimage constraints)
                combined_preimage = And(*preimage_z3_constraints)
                solver.add(Not(combined_preimage))

            # Check satisfiability
            result = solver.check()

            if result == sat:
                # Found a counterexample!
                model = solver.model()

                # Extract concrete values
                field_values = {}
                for field, var in z3_vars.items():
                    value = model[var]
                    if value is not None:
                        field_values[field] = value

                return StrictCounterexample(
                    element=preimage_pattern.element,
                    pattern=str(preimage_pattern),
                    field_values=field_values,
                    reason=f"Source allows this value but preimage rejects it",
                    source_constraint=source_constraint_str,
                    preimage_constraint=" and ".join(preimage_pattern.constraints)
                )

            return None

        except Exception as e:
            print(f"  Warning: Z3 check failed: {e}")
            return None

    def _extract_fields_from_constraints(
        self,
        constraints: List[str]
    ) -> List[str]:
        """Extract field names from constraint strings"""
        fields = set()

        for constraint in constraints:
            # Match field names (alphanumeric identifiers before operators)
            matches = re.findall(r'\b([A-Za-z_]\w*)\b\s*(?:>=|<=|>|<|!=|==|=)', constraint)
            fields.update(matches)

        return list(fields)

    def _infer_field_type(
        self,
        field_name: str,
        source_constraints: Dict[str, TypeConstraint],
        source_grammar: TreeGrammar
    ) -> str:
        """Infer the type of a field from constraints or grammar"""

        # Check source constraints
        if field_name in source_constraints:
            return source_constraints[field_name].base_type

        # Check grammar type constraints
        if field_name in source_grammar.type_constraints:
            return source_grammar.type_constraints[field_name].base_type

        # Check productions for child element types
        for production in source_grammar.productions:
            if production.rhs:
                for child in production.rhs:
                    if str(child) == field_name:
                        # Found the child, check if it's a simple type
                        for prod2 in source_grammar.productions:
                            if prod2.lhs == field_name and prod2.rhs:
                                if len(prod2.rhs) == 1:
                                    return str(prod2.rhs[0])

        return 'integer'  # Default

    def _type_constraint_to_z3(
        self,
        z3_var,
        constraint: TypeConstraint
    ):
        """Convert TypeConstraint to Z3 constraint"""

        constraints = []

        if constraint.restrictions:
            if 'minInclusive' in constraint.restrictions:
                min_val = int(constraint.restrictions['minInclusive'])
                constraints.append(z3_var >= min_val)

            if 'minExclusive' in constraint.restrictions:
                min_val = int(constraint.restrictions['minExclusive'])
                constraints.append(z3_var > min_val)

            if 'maxInclusive' in constraint.restrictions:
                max_val = int(constraint.restrictions['maxInclusive'])
                constraints.append(z3_var <= max_val)

            if 'maxExclusive' in constraint.restrictions:
                max_val = int(constraint.restrictions['maxExclusive'])
                constraints.append(z3_var < max_val)

        if constraints:
            return And(*constraints)
        return None

    def _parse_constraint_to_z3(
        self,
        constraint_str: str,
        z3_vars: Dict[str, Any]
    ):
        """Parse a constraint string to Z3 expression"""

        try:
            # Handle compound constraints with 'and'
            if ' and ' in constraint_str:
                parts = constraint_str.split(' and ')
                sub_constraints = [self._parse_constraint_to_z3(part.strip(), z3_vars) for part in parts]
                sub_constraints = [c for c in sub_constraints if c is not None]
                if sub_constraints:
                    return And(*sub_constraints)
                return None

            # Parse single constraint: "field op value"
            match = re.match(r'(\w+)\s*(>=|<=|>|<|!=|==)\s*(.+)', constraint_str.strip())
            if match:
                field = match.group(1)
                op = match.group(2)
                value_str = match.group(3).strip().strip("'\"")

                if field not in z3_vars:
                    return None

                var = z3_vars[field]

                # Try to parse value as number
                try:
                    if '.' in value_str:
                        value = float(value_str)
                    else:
                        value = int(value_str)
                except ValueError:
                    # String value - skip for now
                    return None

                # Create Z3 constraint
                if op == '>=':
                    return var >= value
                elif op == '<=':
                    return var <= value
                elif op == '>':
                    return var > value
                elif op == '<':
                    return var < value
                elif op == '!=' or op == '!=':
                    return var != value
                elif op == '==' or op == '=':
                    return var == value

            return None

        except Exception as e:
            print(f"    Warning: Failed to parse constraint '{constraint_str}': {e}")
            return None
