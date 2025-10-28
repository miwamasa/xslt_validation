"""
XSLT to Macro Tree Transducer (MTT) Converter
Converts XSLT subset to MTT representation
Based on spec/related_document.md
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from dataclasses import dataclass, field

XSLT_NS = "http://www.w3.org/1999/XSL/Transform"


@dataclass
class MTTRule:
    """Represents a single MTT transformation rule"""
    state: str
    lhs_pattern: str  # Input pattern
    rhs_output: Any  # Output tree/expression
    guard: str = ""  # Optional guard condition
    params: List[str] = field(default_factory=list)


@dataclass
class MTT:
    """Macro Tree Transducer representation"""
    states: List[str] = field(default_factory=list)
    rules: List[MTTRule] = field(default_factory=list)
    initial_state: str = "q_root"
    input_alphabet: List[str] = field(default_factory=list)
    output_alphabet: List[str] = field(default_factory=list)


class XSLTToMTTConverter:
    """Converts XSLT to MTT representation"""

    def __init__(self):
        self.mtt = MTT()
        self.template_counter = 0
        self.state_map: Dict[str, str] = {}  # template match -> state name

    def convert(self, xslt_content: str) -> MTT:
        """Convert XSLT to MTT"""
        try:
            root = ET.fromstring(xslt_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XSLT: {str(e)}")

        # Process all templates
        templates = root.findall(f".//{{{XSLT_NS}}}template")
        for template in templates:
            self._process_template(template)

        return self.mtt

    def _process_template(self, template: ET.Element):
        """Process a single template and create MTT state/rules"""
        match = template.get("match")
        mode = template.get("mode", "default")

        if not match:
            return

        # Create state name
        state_name = self._create_state_name(match, mode)
        self.mtt.states.append(state_name)
        self.state_map[match] = state_name

        # Parse match pattern
        lhs_pattern = self._parse_match_pattern(match)

        # Process template body
        rhs_output = self._process_template_body(template, state_name)

        # Create MTT rule
        rule = MTTRule(
            state=state_name,
            lhs_pattern=lhs_pattern,
            rhs_output=rhs_output
        )
        self.mtt.rules.append(rule)

    def _create_state_name(self, match: str, mode: str) -> str:
        """Create unique state name from template match"""
        # Sanitize match pattern for state name
        state_base = match.replace("/", "_").replace("@", "attr_").replace("*", "any")
        state_name = f"q_{state_base}_{mode}"
        return state_name

    def _parse_match_pattern(self, match: str) -> str:
        """Parse match pattern into MTT input pattern"""
        # Simplify pattern for MTT
        if match == "/":
            return "root(children)"
        elif match.startswith("/"):
            # Root-relative path
            parts = match.strip("/").split("/")
            return f"{parts[-1]}(children)"
        else:
            # Simple element name
            return f"{match}(children)"

    def _process_template_body(self, template: ET.Element, state: str) -> Dict[str, Any]:
        """Process template body and generate output expression"""
        output = {
            "type": "sequence",
            "children": []
        }

        for child in template:
            child_output = self._process_instruction(child, state)
            if child_output:
                output["children"].append(child_output)

        # Handle text content
        if template.text and template.text.strip():
            output["children"].insert(0, {
                "type": "text",
                "value": template.text.strip()
            })

        return output

    def _process_instruction(self, elem: ET.Element, current_state: str) -> Dict[str, Any]:
        """Process a single XSLT instruction"""
        local_name = self._get_local_name(elem.tag)

        # Handle XSLT instructions
        if elem.tag.startswith(f"{{{XSLT_NS}}}"):
            if local_name == "apply-templates":
                return self._process_apply_templates(elem)
            elif local_name == "for-each":
                return self._process_for_each(elem, current_state)
            elif local_name == "value-of":
                return self._process_value_of(elem)
            elif local_name == "if":
                return self._process_if(elem, current_state)
            elif local_name == "choose":
                return self._process_choose(elem, current_state)
            elif local_name == "text":
                return {"type": "text", "value": elem.text or ""}
            elif local_name == "element":
                return self._process_element(elem, current_state)
            elif local_name == "attribute":
                return self._process_attribute(elem)

        # Handle literal result elements
        else:
            return self._process_literal_element(elem, current_state)

        return None

    def _process_apply_templates(self, elem: ET.Element) -> Dict[str, Any]:
        """Process xsl:apply-templates"""
        select = elem.get("select", "node()")

        return {
            "type": "apply-templates",
            "select": select,
            "call": f"apply_to_{select.replace('/', '_')}"
        }

    def _process_for_each(self, elem: ET.Element, state: str) -> Dict[str, Any]:
        """Process xsl:for-each"""
        select = elem.get("select", "")

        # Create auxiliary state for list processing
        list_state = f"{state}_foreach_{len(self.mtt.states)}"
        self.mtt.states.append(list_state)

        body = {
            "type": "sequence",
            "children": []
        }

        for child in elem:
            child_output = self._process_instruction(child, list_state)
            if child_output:
                body["children"].append(child_output)

        return {
            "type": "for-each",
            "select": select,
            "body": body,
            "list_state": list_state
        }

    def _process_value_of(self, elem: ET.Element) -> Dict[str, Any]:
        """Process xsl:value-of"""
        select = elem.get("select", "")

        return {
            "type": "value-of",
            "select": select
        }

    def _process_if(self, elem: ET.Element, state: str) -> Dict[str, Any]:
        """Process xsl:if"""
        test = elem.get("test", "")

        body = {
            "type": "sequence",
            "children": []
        }

        for child in elem:
            child_output = self._process_instruction(child, state)
            if child_output:
                body["children"].append(child_output)

        return {
            "type": "if",
            "test": test,
            "then": body
        }

    def _process_choose(self, elem: ET.Element, state: str) -> Dict[str, Any]:
        """Process xsl:choose"""
        branches = []

        for child in elem:
            local_name = self._get_local_name(child.tag)

            if local_name == "when":
                test = child.get("test", "")
                body = {
                    "type": "sequence",
                    "children": []
                }
                for when_child in child:
                    child_output = self._process_instruction(when_child, state)
                    if child_output:
                        body["children"].append(child_output)

                branches.append({
                    "type": "when",
                    "test": test,
                    "body": body
                })

            elif local_name == "otherwise":
                body = {
                    "type": "sequence",
                    "children": []
                }
                for otherwise_child in child:
                    child_output = self._process_instruction(otherwise_child, state)
                    if child_output:
                        body["children"].append(child_output)

                branches.append({
                    "type": "otherwise",
                    "body": body
                })

        return {
            "type": "choose",
            "branches": branches
        }

    def _process_element(self, elem: ET.Element, state: str) -> Dict[str, Any]:
        """Process xsl:element"""
        name = elem.get("name", "")

        children = []
        for child in elem:
            child_output = self._process_instruction(child, state)
            if child_output:
                children.append(child_output)

        return {
            "type": "element",
            "name": name,
            "children": children
        }

    def _process_attribute(self, elem: ET.Element) -> Dict[str, Any]:
        """Process xsl:attribute"""
        name = elem.get("name", "")
        value = elem.text or ""

        return {
            "type": "attribute",
            "name": name,
            "value": value
        }

    def _process_literal_element(self, elem: ET.Element, state: str) -> Dict[str, Any]:
        """Process literal result element"""
        children = []

        # Process text content
        if elem.text and elem.text.strip():
            children.append({
                "type": "text",
                "value": elem.text.strip()
            })

        # Process child elements
        for child in elem:
            child_output = self._process_instruction(child, state)
            if child_output:
                children.append(child_output)

            # Handle tail text
            if child.tail and child.tail.strip():
                children.append({
                    "type": "text",
                    "value": child.tail.strip()
                })

        # Extract attributes
        attributes = []
        for attr_name, attr_value in elem.attrib.items():
            # Handle attribute value templates {XPath}
            if "{" in attr_value and "}" in attr_value:
                # Extract XPath expression
                start = attr_value.index("{")
                end = attr_value.index("}")
                xpath_expr = attr_value[start + 1:end]
                attributes.append({
                    "name": attr_name,
                    "value_expr": xpath_expr
                })
            else:
                attributes.append({
                    "name": attr_name,
                    "value": attr_value
                })

        return {
            "type": "element",
            "name": self._get_local_name(elem.tag),
            "attributes": attributes,
            "children": children
        }

    def _get_local_name(self, tag: str) -> str:
        """Extract local name from qualified tag"""
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    def to_json(self) -> Dict[str, Any]:
        """Convert MTT to JSON representation"""
        return {
            "states": self.mtt.states,
            "initial_state": self.mtt.initial_state,
            "input_alphabet": self.mtt.input_alphabet,
            "output_alphabet": self.mtt.output_alphabet,
            "rules": [
                {
                    "state": rule.state,
                    "lhs": rule.lhs_pattern,
                    "rhs": rule.rhs_output,
                    "guard": rule.guard,
                    "params": rule.params
                }
                for rule in self.mtt.rules
            ]
        }
