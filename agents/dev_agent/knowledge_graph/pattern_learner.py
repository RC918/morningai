#!/usr/bin/env python3
"""
Pattern Learner - Learn and detect code patterns
Phase 1 Week 5: Knowledge Graph System
"""
import logging
import re
from typing import List, Dict, Any, Optional
from collections import Counter
from dataclasses import dataclass
import ast

from error_handler import create_success

logger = logging.getLogger(__name__)


@dataclass
class CodePattern:
    """Detected code pattern"""
    pattern_name: str
    pattern_type: str
    template: str
    language: str
    frequency: int
    confidence: float
    examples: List[str]


class PatternLearner:
    """Learns and detects code patterns from indexed code"""

    PATTERN_TYPES = {
        'import': 'Import pattern',
        'class_definition': 'Class definition pattern',
        'function_definition': 'Function definition pattern',
        'error_handling': 'Error handling pattern',
        'logging': 'Logging pattern',
        'decorator': 'Decorator pattern',
        'singleton': 'Singleton pattern',
        'factory': 'Factory pattern',
        'dependency_injection': 'Dependency injection pattern',
    }

    def __init__(self, min_frequency: int = 3, min_confidence: float = 0.6):
        """
        Initialize Pattern Learner

        Args:
            min_frequency: Minimum frequency for pattern to be considered
            min_confidence: Minimum confidence score for pattern
        """
        self.min_frequency = min_frequency
        self.min_confidence = min_confidence
        self.learned_patterns: Dict[str, CodePattern] = {}

    def _extract_import_patterns(
            self, code: str, language: str) -> List[Dict[str, Any]]:
        """Extract import patterns from code"""
        patterns = []

        if language == 'python':
            import_lines = re.findall(
                r'^(import\s+.+|from\s+.+import\s+.+)$', code, re.MULTILINE)
            for line in import_lines:
                if 'from' in line:
                    match = re.match(r'from\s+([\w\.]+)\s+import', line)
                    if match:
                        module = match.group(1)
                        patterns.append({
                            'type': 'import',
                            'template': f'from {module} import ...',
                            'example': line.strip()
                        })
                else:
                    match = re.match(r'import\s+([\w\.]+)', line)
                    if match:
                        module = match.group(1)
                        patterns.append({
                            'type': 'import',
                            'template': f'import {module}',
                            'example': line.strip()
                        })

        elif language in ['javascript', 'typescript']:
            import_lines = re.findall(r'import\s+.+from\s+[\'"].+[\'"]', code)
            for line in import_lines:
                patterns.append({
                    'type': 'import',
                    'template': 'import ... from "..."',
                    'example': line.strip()
                })

        return patterns

    def _extract_error_handling_patterns(
            self, code: str, language: str) -> List[Dict[str, Any]]:
        """Extract error handling patterns"""
        patterns = []

        if language == 'python':
            try_blocks = re.findall(
                r'try:\s*\n(.+?)\nexcept\s+(\w+)?.*?:\s*\n(.+?)(?:\nfinally:|\n\S|\Z)',
                code,
                re.DOTALL)

            for try_body, exception, except_body in try_blocks:
                exception_type = exception if exception else 'Exception'
                patterns.append({
                    'type': 'error_handling',
                    'template': f'try/except {exception_type}',
                    'example': f'try:\n    ...\nexcept {exception_type}:\n    ...'
                })

        elif language in ['javascript', 'typescript']:
            try_blocks = re.findall(
                r'try\s*\{.+?\}\s*catch\s*\(.+?\)\s*\{.+?\}', code, re.DOTALL)
            if try_blocks:
                patterns.append({
                    'type': 'error_handling',
                    'template': 'try/catch block',
                    'example': 'try { ... } catch (error) { ... }'
                })

        return patterns

    def _extract_logging_patterns(
            self, code: str, language: str) -> List[Dict[str, Any]]:
        """Extract logging patterns"""
        patterns = []

        if language == 'python':
            logging_calls = re.findall(
                r'(logger|logging)\.(debug|info|warning|error|critical)\(',
                code
            )

            for logger_name, level in logging_calls:
                patterns.append({
                    'type': 'logging',
                    'template': f'{logger_name}.{level}()',
                    'example': f'{logger_name}.{level}("...")'
                })

        elif language in ['javascript', 'typescript']:
            logging_calls = re.findall(
                r'console\.(log|error|warn|debug|info)\(', code)
            for level in logging_calls:
                patterns.append({
                    'type': 'logging',
                    'template': f'console.{level}()',
                    'example': f'console.{level}("...")'
                })

        return patterns

    def _extract_decorator_patterns(
            self, code: str, language: str) -> List[Dict[str, Any]]:
        """Extract decorator patterns (Python)"""
        patterns = []

        if language == 'python':
            try:
                tree = ast.parse(code)

                for node in ast.walk(tree):
                    if isinstance(
                        node,
                        (ast.FunctionDef,
                         ast.AsyncFunctionDef,
                         ast.ClassDef)):
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name):
                                patterns.append({
                                    'type': 'decorator',
                                    'template': f'@{decorator.id}',
                                    'example': f'@{decorator.id}\ndef function(): ...'
                                })
                            elif isinstance(decorator, ast.Call):
                                if isinstance(decorator.func, ast.Name):
                                    patterns.append({
                                        'type': 'decorator',
                                        'template': f'@{decorator.func.id}(...)',
                                        'example': f'@{decorator.func.id}(...)\ndef function(): ...'
                                    })
            except Exception as e:
                logger.debug(f"Decorator extraction failed: {e}")

        return patterns

    def _extract_class_patterns(
            self, code: str, language: str) -> List[Dict[str, Any]]:
        """Extract class definition patterns"""
        patterns = []

        if language == 'python':
            try:
                tree = ast.parse(code)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        bases = [
                            base.id for base in node.bases if isinstance(
                                base, ast.Name)]

                        if bases:
                            patterns.append({
                                'type': 'class_definition',
                                'template': f'class ... ({", ".join(bases)}):',
                                'example': f'class {node.name}({", ".join(bases)}): ...'
                            })
                        else:
                            patterns.append({
                                'type': 'class_definition',
                                'template': 'class ...:',
                                'example': f'class {node.name}: ...'
                            })
            except Exception as e:
                logger.debug(f"Class extraction failed: {e}")

        return patterns

    def analyze_code(self, code: str, language: str) -> List[Dict[str, Any]]:
        """
        Analyze code and extract patterns

        Args:
            code: Code content to analyze
            language: Programming language

        Returns:
            List of detected patterns
        """
        patterns = []

        patterns.extend(self._extract_import_patterns(code, language))
        patterns.extend(self._extract_error_handling_patterns(code, language))
        patterns.extend(self._extract_logging_patterns(code, language))
        patterns.extend(self._extract_decorator_patterns(code, language))
        patterns.extend(self._extract_class_patterns(code, language))

        return patterns

    def learn_patterns(
            self, code_samples: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Learn patterns from multiple code samples

        Args:
            code_samples: List of dicts with 'code' and 'language' keys

        Returns:
            Dict with learned patterns
        """
        all_patterns: List[Dict[str, Any]] = []

        for sample in code_samples:
            code = sample.get('code', '')
            language = sample.get('language', 'python')
            patterns = self.analyze_code(code, language)

            for pattern in patterns:
                pattern['language'] = language
                all_patterns.append(pattern)

        pattern_counter = Counter()
        pattern_examples: Dict[str, List[str]] = {}

        for pattern in all_patterns:
            key = (pattern['type'], pattern['template'], pattern['language'])
            pattern_counter[key] += 1

            if key not in pattern_examples:
                pattern_examples[key] = []
            pattern_examples[key].append(pattern['example'])

        learned_patterns = []

        for (pattern_type, template, language), frequency in pattern_counter.items():
            if frequency >= self.min_frequency:
                confidence = min(1.0, frequency / len(code_samples))

                if confidence >= self.min_confidence:
                    pattern_name = f"{language}_{pattern_type}_{
                        hash(template) %
                        10000}"

                    learned_pattern = CodePattern(
                        pattern_name=pattern_name,
                        pattern_type=pattern_type,
                        template=template,
                        language=language,
                        frequency=frequency,
                        confidence=confidence,
                        examples=pattern_examples[(pattern_type, template, language)][:5]
                    )

                    learned_patterns.append(learned_pattern)
                    self.learned_patterns[pattern_name] = learned_pattern

        logger.info(
            f"Learned {
                len(learned_patterns)} patterns from {
                len(code_samples)} samples")

        return create_success({
            'patterns_learned': len(learned_patterns),
            'total_samples': len(code_samples),
            'patterns': [
                {
                    'name': p.pattern_name,
                    'type': p.pattern_type,
                    'template': p.template,
                    'language': p.language,
                    'frequency': p.frequency,
                    'confidence': p.confidence
                }
                for p in learned_patterns
            ]
        })

    def find_pattern_matches(self, code: str, language: str) -> Dict[str, Any]:
        """
        Find pattern matches in code

        Args:
            code: Code to search for patterns
            language: Programming language

        Returns:
            Dict with matched patterns
        """
        detected_patterns = self.analyze_code(code, language)

        matches = []

        for detected in detected_patterns:
            for pattern_name, learned_pattern in self.learned_patterns.items():
                if (detected['type'] == learned_pattern.pattern_type and
                    detected['template'] == learned_pattern.template and
                        language == learned_pattern.language):

                    matches.append({
                        'pattern_name': pattern_name,
                        'pattern_type': learned_pattern.pattern_type,
                        'template': learned_pattern.template,
                        'confidence': learned_pattern.confidence,
                        'matched_code': detected['example']
                    })

        return create_success({
            'matches_found': len(matches),
            'matches': matches
        })

    def get_pattern_suggestions(
            self, language: str, pattern_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get pattern suggestions for a language

        Args:
            language: Programming language
            pattern_type: Optional filter by pattern type

        Returns:
            Dict with pattern suggestions
        """
        suggestions = []

        for pattern in self.learned_patterns.values():
            if pattern.language == language:
                if pattern_type is None or pattern.pattern_type == pattern_type:
                    suggestions.append({
                        'name': pattern.pattern_name,
                        'type': pattern.pattern_type,
                        'template': pattern.template,
                        'confidence': pattern.confidence,
                        'examples': pattern.examples[:3]
                    })

        suggestions.sort(key=lambda x: (
            x['confidence'], -len(x['examples'])), reverse=True)

        return create_success({
            'language': language,
            'pattern_type': pattern_type,
            'suggestions': suggestions
        })


def create_pattern_learner(min_frequency: int = 3,
                           min_confidence: float = 0.6) -> PatternLearner:
    """Factory function to create Pattern Learner"""
    return PatternLearner(min_frequency, min_confidence)
