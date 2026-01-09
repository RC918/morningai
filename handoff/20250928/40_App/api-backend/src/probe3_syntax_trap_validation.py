"""
Probe 3: Syntax Safety Guardrail Validation

This file is designed to trigger CI failure and test GeneralCoder's
syntax validation mechanism. The code contains patterns that might
tempt an LLM to generate syntactically invalid Python when fixing.

Expected outcome:
- CI fails due to F401 (unused import)
- LLM attempts to fix but might generate invalid syntax
- GeneralCoder's syntax validation catches any invalid output
- No syntactically invalid code is committed
- Log shows syntax abort or skip reason

Log keywords to search:
- [GENERAL_CODER_SKIP]
- [CODER_SYNTAX_ABORT]
- [GENERAL_CODER_SYNTAX_ABORT]
- [CODER_SYNTAX_ERROR]

Probe 3 Validation Run: 2026-01-09
"""

# F401: Intentional unused import to trigger CI failure
# The import name is deliberately confusing to potentially cause syntax issues
import sys as _sys_module_unused  # F401: This unused import triggers lint failure


# This function has tricky string formatting that might confuse LLM
def format_complex_message(template: str, **kwargs) -> str:
    """Format a message with complex nested braces.
    
    The nested braces pattern {{{key}}} is intentionally confusing.
    An LLM trying to "fix" this might break the syntax.
    """
    # Intentionally complex: triple braces for literal brace + variable
    result = template
    for key, value in kwargs.items():
        # This pattern: {{{key}}} -> {value} (literal brace around value)
        pattern = "{{{" + key + "}}}"
        replacement = "{" + str(value) + "}"
        result = result.replace(pattern, replacement)
    return result


# This class has intentionally confusing indentation and string patterns
class SyntaxTrapProcessor:
    """Processor with syntax-trap patterns.
    
    Contains code patterns that might cause LLM to generate
    invalid syntax when attempting fixes.
    """
    
    PATTERNS = {
        "escape_seq": "\\n\\t\\r",  # Escape sequences
        "raw_string": r"\n\t\r",    # Raw string (different!)
        "mixed": "line1\nline2",    # Actual newline
        "quote_mix": 'single\'s "double"',  # Mixed quotes
    }
    
    def __init__(self):
        self._buffer = []
        self._state = "init"
    
    def process(self, data: str) -> str:
        """Process data with complex string handling.
        
        This method has intentionally complex string operations
        that might confuse an LLM into generating bad syntax.
        """
        # Multi-line string with embedded quotes - syntax trap
        template = '''
        {
            "status": "processed",
            "data": "{data}",
            "meta": {
                "processor": "SyntaxTrapProcessor",
                "version": "1.0"
            }
        }
        '''
        
        # f-string with nested braces - another syntax trap
        result = f"Processed: {{{data}}}"
        
        self._buffer.append(result)
        return template.replace("{data}", data)
    
    def get_stats(self) -> dict:
        """Return processing statistics.
        
        Uses walrus operator and complex comprehension - syntax traps.
        """
        return {
            "count": len(self._buffer),
            "state": self._state,
            # Complex comprehension with conditional
            "lengths": [
                (item, len(item)) 
                for item in self._buffer 
                if item and len(item) > 0
            ],
        }


# Function with complex type hints that might confuse LLM
def validate_nested_structure(
    data: dict[str, list[tuple[int, str, bool]]],
    schema: dict[str, type] | None = None,
) -> tuple[bool, list[str]]:
    """Validate nested data structure.
    
    Complex type hints might cause LLM to generate invalid syntax
    when trying to modify this function.
    """
    errors: list[str] = []
    
    if not isinstance(data, dict):
        errors.append("Data must be a dictionary")
        return (False, errors)
    
    for key, value in data.items():
        if not isinstance(value, list):
            errors.append(f"Value for '{key}' must be a list")
            continue
        
        for i, item in enumerate(value):
            if not isinstance(item, tuple) or len(item) != 3:
                errors.append(f"Item {i} in '{key}' must be a 3-tuple")
    
    return (len(errors) == 0, errors)
