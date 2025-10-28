"""
XSLT Subset Checker
Validates that XSLT uses only allowed subset of elements
Based on spec/related_document.md
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple

# XSLT namespaces
XSLT_NS = "http://www.w3.org/1999/XSL/Transform"

# Allowed XSLT elements (subset)
ALLOWED_ELEMENTS = {
    "stylesheet",
    "transform",
    "template",
    "apply-templates",
    "for-each",
    "value-of",
    "if",
    "choose",
    "when",
    "otherwise",
    "with-param",
    "param",
    "text",
    "element",
    "attribute"
}

# Disallowed features
DISALLOWED_FEATURES = {
    "document",      # External document access
    "key",           # Key function
    "import",        # Import
    "include",       # Include
    "call-template", # Named template calls (complex)
    "variable",      # Variables (can be complex)
    "sort",          # Sorting
    "number",        # Number formatting
    "copy",          # Deep copy
    "copy-of"        # Copy operations
}

class XSLTSubsetChecker:
    """Checks if XSLT conforms to the allowed subset"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def check_xslt(self, xslt_content: str) -> Tuple[bool, List[str], List[str]]:
        """
        Check if XSLT conforms to allowed subset

        Returns:
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            root = ET.fromstring(xslt_content)
        except ET.ParseError as e:
            self.errors.append(f"XML Parse Error: {str(e)}")
            return False, self.errors, self.warnings

        # Check all elements recursively
        self._check_element(root, "")

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _check_element(self, elem: ET.Element, path: str):
        """Recursively check element and its children"""

        # Get local name (without namespace)
        local_name = self._get_local_name(elem.tag)
        current_path = f"{path}/{local_name}"

        # Check if element is in XSLT namespace
        if elem.tag.startswith(f"{{{XSLT_NS}}}"):
            xslt_element = elem.tag.replace(f"{{{XSLT_NS}}}", "")

            # Check if element is disallowed
            if xslt_element in DISALLOWED_FEATURES:
                self.errors.append(
                    f"Disallowed XSLT element '{xslt_element}' at {current_path}"
                )
            # Check if element is in allowed set
            elif xslt_element not in ALLOWED_ELEMENTS:
                self.warnings.append(
                    f"Unknown XSLT element '{xslt_element}' at {current_path}"
                )

            # Check specific element constraints
            if xslt_element == "template":
                self._check_template(elem, current_path)
            elif xslt_element == "if":
                self._check_if(elem, current_path)
            elif xslt_element == "choose":
                self._check_choose(elem, current_path)
            elif xslt_element == "apply-templates":
                self._check_apply_templates(elem, current_path)
            elif xslt_element == "for-each":
                self._check_for_each(elem, current_path)
            elif xslt_element == "value-of":
                self._check_value_of(elem, current_path)

        # Recursively check children
        for child in elem:
            self._check_element(child, current_path)

    def _get_local_name(self, tag: str) -> str:
        """Extract local name from qualified tag"""
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    def _check_template(self, elem: ET.Element, path: str):
        """Check template element"""
        match = elem.get("match")
        if not match:
            self.errors.append(f"Template without 'match' attribute at {path}")
            return

        # Check for complex patterns
        if "//" in match or "ancestor::" in match or "following::" in match:
            self.warnings.append(
                f"Complex XPath pattern '{match}' at {path} - may not be fully supported"
            )

    def _check_if(self, elem: ET.Element, path: str):
        """Check if element"""
        test = elem.get("test")
        if not test:
            self.errors.append(f"'if' without 'test' attribute at {path}")
            return

        # Check for complex conditions
        if "contains(" in test or "substring(" in test or "concat(" in test:
            self.warnings.append(
                f"Complex string function in test '{test}' at {path}"
            )

    def _check_choose(self, elem: ET.Element, path: str):
        """Check choose element"""
        has_when = False
        for child in elem:
            local_name = self._get_local_name(child.tag)
            if local_name == "when":
                has_when = True

        if not has_when:
            self.errors.append(f"'choose' without 'when' at {path}")

    def _check_apply_templates(self, elem: ET.Element, path: str):
        """Check apply-templates element"""
        select = elem.get("select")
        if select:
            # Check for complex select patterns
            if "preceding::" in select or "following::" in select:
                self.warnings.append(
                    f"Complex axis in select '{select}' at {path}"
                )

    def _check_for_each(self, elem: ET.Element, path: str):
        """Check for-each element"""
        select = elem.get("select")
        if not select:
            self.errors.append(f"'for-each' without 'select' attribute at {path}")

    def _check_value_of(self, elem: ET.Element, path: str):
        """Check value-of element"""
        select = elem.get("select")
        if not select:
            self.errors.append(f"'value-of' without 'select' attribute at {path}")
