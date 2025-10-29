"""
XSD Parser and Tree Grammar Converter
Converts XSD schemas to tree grammar representation
Based on spec/the_theory_and_sample.md
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Set, Any
from dataclasses import dataclass, field

# XSD namespaces
XS_NS = "http://www.w3.org/2001/XMLSchema"


@dataclass
class TypeConstraint:
    """Represents a type constraint"""
    base_type: str
    restrictions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Production:
    """Represents a production rule in tree grammar"""
    lhs: str  # Left-hand side (non-terminal)
    rhs: List[str]  # Right-hand side (terminals/non-terminals)
    element_type: str = "sequence"  # sequence, choice, all
    cardinality: tuple = (1, 1)  # (min, max) - max=-1 means unbounded


@dataclass
class TreeGrammar:
    """Tree grammar representation of XSD"""
    root_element: str
    productions: List[Production] = field(default_factory=list)
    type_constraints: Dict[str, TypeConstraint] = field(default_factory=dict)
    attributes: Dict[str, List[tuple]] = field(default_factory=dict)  # element -> [(attr_name, type, required)]


class XSDParser:
    """Parses XSD and converts to tree grammar"""

    def __init__(self):
        self.grammar = TreeGrammar(root_element="")
        self.complex_types: Dict[str, ET.Element] = {}
        self.simple_types: Dict[str, ET.Element] = {}

    def parse(self, xsd_content: str) -> TreeGrammar:
        """Parse XSD and return tree grammar"""
        try:
            root = ET.fromstring(xsd_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XSD: {str(e)}")

        # First pass: collect type definitions
        self._collect_types(root)

        # Second pass: process elements
        for elem in root.findall(f".//{{{XS_NS}}}element"):
            if elem.get("name"):  # Top-level element
                element_name = elem.get("name")
                if not self.grammar.root_element:
                    self.grammar.root_element = element_name

                self._process_element(elem, element_name)

        return self.grammar

    def _collect_types(self, root: ET.Element):
        """Collect all type definitions"""
        # Collect complex types
        for ct in root.findall(f".//{{{XS_NS}}}complexType"):
            name = ct.get("name")
            if name:
                self.complex_types[name] = ct

        # Collect simple types
        for st in root.findall(f".//{{{XS_NS}}}simpleType"):
            name = st.get("name")
            if name:
                self.simple_types[name] = st

    def _process_element(self, elem: ET.Element, element_name: str, parent_path: str = ""):
        """Process an element and generate productions"""

        # Get cardinality
        min_occurs = int(elem.get("minOccurs", "1"))
        max_occurs_str = elem.get("maxOccurs", "1")
        max_occurs = -1 if max_occurs_str == "unbounded" else int(max_occurs_str)

        # Check for type reference
        type_ref = elem.get("type")
        if type_ref:
            # Handle built-in types
            if type_ref.startswith("xs:"):
                base_type = type_ref.replace("xs:", "")
                self.grammar.type_constraints[element_name] = TypeConstraint(
                    base_type=base_type
                )
                # Leaf production
                prod = Production(
                    lhs=element_name,
                    rhs=[base_type],
                    cardinality=(min_occurs, max_occurs)
                )
                self.grammar.productions.append(prod)
            else:
                # Custom type reference
                if type_ref in self.complex_types:
                    self._process_complex_type(
                        self.complex_types[type_ref],
                        element_name,
                        (min_occurs, max_occurs)
                    )
                elif type_ref in self.simple_types:
                    self._process_simple_type(
                        self.simple_types[type_ref],
                        element_name,
                        (min_occurs, max_occurs)
                    )
        else:
            # Inline type definition
            complex_type = elem.find(f"./{{{XS_NS}}}complexType")
            if complex_type is not None:
                self._process_complex_type(complex_type, element_name, (min_occurs, max_occurs))
            else:
                simple_type = elem.find(f"./{{{XS_NS}}}simpleType")
                if simple_type is not None:
                    self._process_simple_type(simple_type, element_name, (min_occurs, max_occurs))

    def _process_complex_type(self, ct: ET.Element, element_name: str, cardinality: tuple):
        """Process complex type definition"""

        # Process attributes
        attributes = []
        for attr in ct.findall(f".//{{{XS_NS}}}attribute"):
            attr_name = attr.get("name")
            attr_type_ref = attr.get("type")
            required = attr.get("use") == "required"

            # Check for inline simpleType with restrictions
            inline_simple = attr.find(f"./{{{XS_NS}}}simpleType")
            if inline_simple is not None:
                restriction = inline_simple.find(f"./{{{XS_NS}}}restriction")
                if restriction is not None:
                    base = restriction.get("base", "xs:string").replace("xs:", "")

                    # Collect restrictions
                    restrictions = {}
                    for child in restriction:
                        local_name = child.tag.replace(f"{{{XS_NS}}}", "")
                        value = child.get("value")
                        if value:
                            restrictions[local_name] = value

                    # Add type constraint for this attribute
                    self.grammar.type_constraints[attr_name] = TypeConstraint(
                        base_type=base,
                        restrictions=restrictions
                    )
                    attributes.append((attr_name, base, required))
                else:
                    # No restriction, use base type
                    attr_type = "string"
                    attributes.append((attr_name, attr_type, required))
            elif attr_type_ref:
                attr_type = attr_type_ref.replace("xs:", "")
                # Add type constraint for basic types
                self.grammar.type_constraints[attr_name] = TypeConstraint(
                    base_type=attr_type,
                    restrictions={}
                )
                attributes.append((attr_name, attr_type, required))
            else:
                # Default to string
                attr_type = "string"
                self.grammar.type_constraints[attr_name] = TypeConstraint(
                    base_type=attr_type,
                    restrictions={}
                )
                attributes.append((attr_name, attr_type, required))

        if attributes:
            self.grammar.attributes[element_name] = attributes

        # Process content model
        sequence = ct.find(f"./{{{XS_NS}}}sequence")
        choice = ct.find(f"./{{{XS_NS}}}choice")
        all_elem = ct.find(f"./{{{XS_NS}}}all")

        if sequence is not None:
            self._process_sequence(sequence, element_name, cardinality)
        elif choice is not None:
            self._process_choice(choice, element_name, cardinality)
        elif all_elem is not None:
            self._process_all(all_elem, element_name, cardinality)
        else:
            # Simple content or empty
            simple_content = ct.find(f"./{{{XS_NS}}}simpleContent")
            if simple_content is not None:
                extension = simple_content.find(f"./{{{XS_NS}}}extension")
                if extension is not None:
                    base = extension.get("base", "xs:string").replace("xs:", "")
                    self.grammar.type_constraints[element_name] = TypeConstraint(
                        base_type=base
                    )

    def _process_sequence(self, sequence: ET.Element, parent_name: str, cardinality: tuple):
        """Process xs:sequence"""
        children = []
        for child in sequence.findall(f"./{{{XS_NS}}}element"):
            child_name = child.get("name") or child.get("ref")
            if child_name:
                children.append(child_name)
                # Recursively process child
                if child.get("name"):  # Inline definition
                    self._process_element(child, child_name, parent_name)

        if children:
            prod = Production(
                lhs=parent_name,
                rhs=children,
                element_type="sequence",
                cardinality=cardinality
            )
            self.grammar.productions.append(prod)

    def _process_choice(self, choice: ET.Element, parent_name: str, cardinality: tuple):
        """Process xs:choice"""
        children = []
        for child in choice.findall(f"./{{{XS_NS}}}element"):
            child_name = child.get("name") or child.get("ref")
            if child_name:
                children.append(child_name)
                if child.get("name"):
                    self._process_element(child, child_name, parent_name)

        if children:
            prod = Production(
                lhs=parent_name,
                rhs=children,
                element_type="choice",
                cardinality=cardinality
            )
            self.grammar.productions.append(prod)

    def _process_all(self, all_elem: ET.Element, parent_name: str, cardinality: tuple):
        """Process xs:all"""
        children = []
        for child in all_elem.findall(f"./{{{XS_NS}}}element"):
            child_name = child.get("name") or child.get("ref")
            if child_name:
                children.append(child_name)
                if child.get("name"):
                    self._process_element(child, child_name, parent_name)

        if children:
            prod = Production(
                lhs=parent_name,
                rhs=children,
                element_type="all",
                cardinality=cardinality
            )
            self.grammar.productions.append(prod)

    def _process_simple_type(self, st: ET.Element, element_name: str, cardinality: tuple):
        """Process simple type definition"""
        restriction = st.find(f"./{{{XS_NS}}}restriction")
        if restriction is not None:
            base = restriction.get("base", "xs:string").replace("xs:", "")

            # Collect restrictions
            restrictions = {}
            for child in restriction:
                local_name = child.tag.replace(f"{{{XS_NS}}}", "")
                value = child.get("value")
                if value:
                    restrictions[local_name] = value

            self.grammar.type_constraints[element_name] = TypeConstraint(
                base_type=base,
                restrictions=restrictions
            )

            # Create production
            prod = Production(
                lhs=element_name,
                rhs=[base],
                cardinality=cardinality
            )
            self.grammar.productions.append(prod)
