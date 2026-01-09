"""
Probe 3 Advanced: Syntax Safety Guardrail - Extreme Test

This file contains EXTREMELY tricky Python syntax patterns designed to
cause LLM to generate syntactically INVALID Python when attempting fixes.

The goal is to trigger [CODER_SYNTAX_ABORT] by having the LLM fail
to preserve valid syntax while fixing the lint error.

Patterns included:
1. Nested f-strings with escaped braces
2. Regex with complex escape sequences
3. Walrus operator in nested comprehensions
4. Match-case with guard clauses
5. Lambda with lambda default arguments
6. Async comprehensions
7. Metaclass with __slots__

Expected outcome:
- CI fails due to F401 (unused import)
- LLM attempts fix but generates invalid syntax
- GeneralCoder's syntax validation catches the error
- [CODER_SYNTAX_ABORT] or [GENERAL_CODER_SKIP] logged
- No bad code committed

Log keywords:
- [GENERAL_CODER_SKIP]
- [CODER_SYNTAX_ABORT]
- [GENERAL_CODER_SYNTAX_ABORT]

Probe 3 Advanced Validation Run: 2026-01-09
"""

# F401: Intentional unused import - THIS TRIGGERS CI FAILURE
# The import is embedded in complex code to make fixing harder
import re as _regex_module_for_pattern_validation_unused  # F401 error here


from typing import TypeVar, Generic, Callable, Awaitable
from dataclasses import dataclass
from abc import ABC, abstractmethod


T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


# Pattern 1: Nested f-strings with escaped braces - SYNTAX TRAP
def format_nested_template(outer: str, inner: str, value: int) -> str:
    """Format with nested f-string - LLM often breaks this.

    The triple/quadruple braces are intentional and valid Python.
    """
    # This is valid: f"{{" produces literal "{"
    # f"{f'{{x}}'}" is a nested f-string with escaped braces
    result = f"outer={{{outer}}} inner={{{f'{{{inner}}}'}}} val={{{{{value}}}}}"

    # Even more complex: f-string inside format string
    template = "prefix_{key}_{{literal}}_suffix"
    formatted = template.format(key=f"{outer}:{inner}")

    return f"{result} | {formatted}"


# Pattern 2: Regex with escape sequences - SYNTAX TRAP
COMPLEX_PATTERNS = {
    # Raw strings with backslashes - LLM often messes these up
    "escape_test": r"\\n\\t\\r\n\t\r",
    "regex_group": r"(?P<name>\w+)(?::\s*(?P<value>[^,]+))?",
    "nested_groups": r"((\d+)\.(\d+)\.(\d+))",
    "lookahead": r"(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}",
    "raw_vs_normal": (r"\n\t", "\n\t"),  # Tuple of raw and normal
    "backslash_hell": r"C:\\Users\\name\\path\\to\\file\.txt",
}


# Pattern 3: Walrus operator in nested comprehension - SYNTAX TRAP
def process_with_walrus(items: list[dict[str, int]]) -> list[tuple[str, int, int]]:
    """Use walrus operator in complex comprehension.

    This pattern often confuses LLMs into generating invalid syntax.
    """
    # Walrus in nested comprehension with multiple conditions
    return [
        (key, val, squared)
        for item in items
        if (keys := list(item.keys()))
        for key in keys
        if (val := item.get(key, 0)) > 0
        if (squared := val * val) < 1000
    ]


# Pattern 4: Match-case with guards - SYNTAX TRAP (Python 3.10+)
def parse_command(cmd: str | dict | list | None) -> str:
    """Parse command using match-case with guards.

    Match-case is newer syntax that LLMs sometimes break.
    """
    match cmd:
        case str(s) if s.startswith("!"):
            return f"command:{s[1:]}"
        case str(s) if len(s) > 100:
            return f"long:{s[:50]}..."
        case {"action": action, "target": target} if action in ("get", "set"):
            return f"{action}:{target}"
        case {"action": action, **rest} if rest:
            return f"{action}:{rest}"
        case [first, *middle, last] if len(middle) > 2:
            return f"list:{first}...{last}"
        case [single]:
            return f"single:{single}"
        case None:
            return "none"
        case _:
            return "unknown"


# Pattern 5: Lambda with lambda default - SYNTAX TRAP
# This is valid but extremely confusing syntax
identity = lambda x: x
nested_lambda = lambda f=lambda x: x: lambda y: f(y)
curried = lambda a: lambda b: lambda c: a + b + c
compose = lambda f: lambda g: lambda x: f(g(x))

# Even more confusing: lambda returning lambda with default lambda
factory = lambda default=lambda: None: lambda value=None: value if value is not None else default()


# Pattern 6: Async comprehension - SYNTAX TRAP
async def async_processor(items: list[Awaitable[int]]) -> list[int]:
    """Process items asynchronously with comprehension.

    Async comprehensions are tricky for LLMs.
    """
    # Async list comprehension
    results = [await item async for item in async_gen(items) if await should_include(item)]

    # Async generator expression
    async_sum = sum([x async for x in async_gen(items)])

    return results


async def async_gen(items):
    """Async generator helper."""
    for item in items:
        yield await item


async def should_include(item) -> bool:
    """Check if item should be included."""
    return True


# Pattern 7: Metaclass with __slots__ - SYNTAX TRAP
class SlottedMeta(type):
    """Metaclass that enforces __slots__."""

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        if '__slots__' not in namespace:
            namespace['__slots__'] = ()
        return super().__new__(mcs, name, bases, namespace)


class BaseSlotted(metaclass=SlottedMeta):
    """Base class with slots."""
    __slots__ = ('_id', '_name')

    def __init__(self, id_: int, name: str):
        self._id = id_
        self._name = name


class DerivedSlotted(BaseSlotted):
    """Derived class extending slots."""
    __slots__ = ('_value', '_metadata')

    def __init__(self, id_: int, name: str, value: float):
        super().__init__(id_, name)
        self._value = value
        self._metadata: dict[str, str | int | None] = {}


# Pattern 8: Complex type hints - SYNTAX TRAP
@dataclass
class Container(Generic[T, K, V]):
    """Generic container with complex type hints."""

    items: dict[K, list[tuple[T, V | None, bool]]]
    transform: Callable[[T], Awaitable[V]] | None = None
    fallback: T | Callable[[], T] | None = None

    def get_nested(
        self,
        key: K,
        index: int,
        default: tuple[T, V | None, bool] | None = None
    ) -> tuple[T, V | None, bool] | None:
        """Get nested item with complex return type."""
        if key in self.items and index < len(self.items[key]):
            return self.items[key][index]
        return default


# Pattern 9: String with all quote types - SYNTAX TRAP
QUOTE_HELL = {
    "single": 'value with "double" quotes',
    "double": "value with 'single' quotes",
    "triple_single": '''multi
    line with "double" and 'single' quotes''',
    "triple_double": """another
    multi-line with 'single' and "double" quotes""",
    "escaped": "escaped \"double\" and \'single\' quotes",
    "raw_escaped": r"raw with \"escaped\" quotes",
    "f_with_quotes": f"f-string with {'nested \"quotes\"'}",
}


# Pattern 10: Decorator chain with arguments - SYNTAX TRAP
def decorator_with_args(arg1: str, arg2: int = 0):
    """Decorator factory."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            return func(*args, **kwargs)
        return wrapper
    return decorator


def another_decorator(func: Callable[..., T]) -> Callable[..., T]:
    """Simple decorator."""
    return func


@decorator_with_args("test", arg2=42)
@another_decorator
@decorator_with_args(
    arg1="multi-line",
    arg2=100,
)
def heavily_decorated_function(
    x: int,
    y: str = "default",
    *args: tuple[int, ...],
    **kwargs: dict[str, str | int | None],
) -> dict[str, list[tuple[int, str, bool]]]:
    """Function with many decorators and complex signature."""
    return {"result": [(x, y, True)]}


# Pattern 11: Class with complex __init_subclass__ - SYNTAX TRAP
class PluginBase(ABC):
    """Base class with __init_subclass__ hook."""

    _registry: dict[str, type["PluginBase"]] = {}

    def __init_subclass__(cls, *, plugin_name: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        name = plugin_name or cls.__name__.lower()
        cls._registry[name] = cls

    @abstractmethod
    def execute(self, data: dict[str, str | int | list[str]]) -> bool:
        """Execute the plugin."""
        ...


class ConcretePlugin(PluginBase, plugin_name="concrete"):
    """Concrete plugin implementation."""

    def execute(self, data: dict[str, str | int | list[str]]) -> bool:
        return bool(data)


# Final validation function
def validate_all_patterns() -> dict[str, bool]:
    """Validate all syntax patterns work correctly."""
    results = {}

    # Test nested f-string
    results["nested_fstring"] = bool(format_nested_template("a", "b", 1))

    # Test regex patterns
    results["regex"] = all(isinstance(v, (str, tuple)) for v in COMPLEX_PATTERNS.values())

    # Test walrus
    results["walrus"] = bool(process_with_walrus([{"a": 5, "b": 10}]))

    # Test match-case
    results["match_case"] = parse_command("!test") == "command:test"

    # Test lambdas
    results["lambda"] = nested_lambda()(42) == 42

    # Test metaclass
    results["metaclass"] = hasattr(DerivedSlotted, '__slots__')

    # Test container
    results["container"] = Container[int, str, float](items={}).get_nested("x", 0) is None

    # Test quotes
    results["quotes"] = len(QUOTE_HELL) == 7

    # Test decorated
    results["decorated"] = callable(heavily_decorated_function)

    # Test plugin
    results["plugin"] = "concrete" in PluginBase._registry

    return results


if __name__ == "__main__":
    results = validate_all_patterns()
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
