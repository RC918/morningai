#!/usr/bin/env python3
"""
Performance Benchmark Tests for New Features
Tests performance with large codebases (up to 100K lines)
"""
import pytest
import time
import statistics
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from refactoring import create_refactoring_engine
from testing import create_test_generator
from error_diagnosis import create_error_diagnoser
from performance import create_performance_analyzer

pytestmark = pytest.mark.benchmark


def generate_large_code(num_lines):
    """Generate code with specified number of lines"""
    lines = []
    lines.append("#!/usr/bin/env python3\n")
    lines.append('"""Large test file"""\n\n')
    
    num_functions = num_lines // 10
    for i in range(num_functions):
        lines.append(f"def function_{i}(arg):\n")
        lines.append(f'    """Function {i}"""\n')
        for j in range(7):
            lines.append(f"    x{j} = arg + {j}\n")
        lines.append(f"    return x6\n\n")
    
    return ''.join(lines)


class TestRefactoringEnginePerformance:
    """Performance benchmarks for RefactoringEngine"""
    
    @pytest.fixture
    def engine(self):
        return create_refactoring_engine()
    
    def test_small_file_performance(self, engine):
        """Test with 50-line file (target: <100ms)"""
        code = generate_large_code(50)
        
        times = []
        for _ in range(5):
            start = time.time()
            result = engine.analyze_code(code)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert result['success'] is True
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18] if len(times) > 1 else times[0]
        
        print(f"\nSmall file (50 lines):")
        print(f"  Average: {avg_time:.1f}ms")
        print(f"  P95: {p95_time:.1f}ms")
        
        assert avg_time < 100, f"Average time {avg_time:.1f}ms exceeds 100ms target"
    
    def test_medium_file_performance(self, engine):
        """Test with 500-line file (target: <500ms)"""
        code = generate_large_code(500)
        
        times = []
        for _ in range(5):
            start = time.time()
            result = engine.analyze_code(code)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert result['success'] is True
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18] if len(times) > 1 else times[0]
        
        print(f"\nMedium file (500 lines):")
        print(f"  Average: {avg_time:.1f}ms")
        print(f"  P95: {p95_time:.1f}ms")
        
        assert avg_time < 500, f"Average time {avg_time:.1f}ms exceeds 500ms target"
    
    def test_large_file_performance(self, engine):
        """Test with 1000-line file (target: <1000ms)"""
        code = generate_large_code(1000)
        
        times = []
        for _ in range(3):
            start = time.time()
            result = engine.analyze_code(code)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert result['success'] is True
        
        avg_time = statistics.mean(times)
        
        print(f"\nLarge file (1000 lines):")
        print(f"  Average: {avg_time:.1f}ms")
        
        assert avg_time < 1000, f"Average time {avg_time:.1f}ms exceeds 1000ms target"
    
    @pytest.mark.slow
    def test_very_large_file_performance(self, engine):
        """Test with 10K-line file (target: <10s)"""
        code = generate_large_code(10000)
        
        start = time.time()
        result = engine.analyze_code(code)
        elapsed = (time.time() - start) * 1000
        
        assert result['success'] is True
        
        print(f"\nVery large file (10K lines):")
        print(f"  Time: {elapsed:.1f}ms ({elapsed/1000:.2f}s)")
        
        assert elapsed < 10000, f"Time {elapsed:.1f}ms exceeds 10s target"


class TestTestGeneratorPerformance:
    """Performance benchmarks for TestGenerator"""
    
    @pytest.fixture
    def generator(self):
        return create_test_generator()
    
    def test_small_file_performance(self, generator):
        """Test with 5 functions (target: <200ms)"""
        code = generate_large_code(50)
        
        times = []
        for _ in range(5):
            start = time.time()
            result = generator.generate_tests(code)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert result['success'] is True
        
        avg_time = statistics.mean(times)
        
        print(f"\nSmall file (5 functions):")
        print(f"  Average: {avg_time:.1f}ms")
        
        assert avg_time < 200, f"Average time {avg_time:.1f}ms exceeds 200ms target"
    
    def test_medium_file_performance(self, generator):
        """Test with 50 functions (target: <1000ms)"""
        code = generate_large_code(500)
        
        times = []
        for _ in range(3):
            start = time.time()
            result = generator.generate_tests(code)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert result['success'] is True
        
        avg_time = statistics.mean(times)
        
        print(f"\nMedium file (50 functions):")
        print(f"  Average: {avg_time:.1f}ms")
        
        assert avg_time < 1000, f"Average time {avg_time:.1f}ms exceeds 1000ms target"


class TestPerformanceAnalyzerPerformance:
    """Performance benchmarks for PerformanceAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return create_performance_analyzer()
    
    def test_nested_loops_detection_performance(self, analyzer):
        """Test nested loop detection performance (target: <500ms for 1000 lines)"""
        code_lines = []
        for i in range(100):
            code_lines.append(f"def function_{i}():\n")
            code_lines.append("    for i in range(10):\n")
            code_lines.append("        for j in range(10):\n")
            code_lines.append("            for k in range(10):\n")
            code_lines.append("                pass\n")
        
        code = ''.join(code_lines)
        
        times = []
        for _ in range(3):
            start = time.time()
            result = analyzer.analyze_code(code)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert result['success'] is True
        
        avg_time = statistics.mean(times)
        
        print(f"\nNested loops (100 functions):")
        print(f"  Average: {avg_time:.1f}ms")
        
        assert avg_time < 500, f"Average time {avg_time:.1f}ms exceeds 500ms target"


class TestErrorDiagnoserPerformance:
    """Performance benchmarks for ErrorDiagnoser"""
    
    @pytest.fixture
    def diagnoser(self):
        return create_error_diagnoser()
    
    def test_single_error_diagnosis_performance(self, diagnoser):
        """Test single error diagnosis (target: <10ms)"""
        error_messages = [
            "KeyError: 'missing_key'",
            "AttributeError: 'NoneType' object has no attribute 'value'",
            "IndexError: list index out of range",
            "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        ]
        
        times = []
        for error_msg in error_messages:
            start = time.time()
            result = diagnoser.diagnose_error(error_msg)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert result['success'] is True
        
        avg_time = statistics.mean(times)
        
        print(f"\nSingle error diagnosis:")
        print(f"  Average: {avg_time:.3f}ms")
        
        assert avg_time < 10, f"Average time {avg_time:.3f}ms exceeds 10ms target"
    
    def test_batch_error_diagnosis_performance(self, diagnoser):
        """Test batch error diagnosis (target: <1s for 100 errors)"""
        error_messages = [
            "KeyError: 'key_{}'".format(i) for i in range(50)
        ] + [
            "AttributeError: 'obj_{}'".format(i) for i in range(50)
        ]
        
        start = time.time()
        results = []
        for error_msg in error_messages:
            result = diagnoser.diagnose_error(error_msg)
            results.append(result)
        elapsed = (time.time() - start) * 1000
        
        assert all(r['success'] for r in results)
        
        print(f"\nBatch error diagnosis (100 errors):")
        print(f"  Total time: {elapsed:.1f}ms")
        print(f"  Per error: {elapsed/100:.2f}ms")
        
        assert elapsed < 1000, f"Total time {elapsed:.1f}ms exceeds 1s target"


class TestIntegratedWorkflowPerformance:
    """End-to-end workflow performance tests"""
    
    def test_full_code_review_workflow_performance(self):
        """Test complete code review workflow (target: <5s for 500-line file)"""
        code = generate_large_code(500)
        
        refactoring_engine = create_refactoring_engine()
        test_generator = create_test_generator()
        performance_analyzer = create_performance_analyzer()
        
        start = time.time()
        
        refactor_result = refactoring_engine.analyze_code(code)
        assert refactor_result['success'] is True
        
        test_result = test_generator.generate_tests(code)
        assert test_result['success'] is True
        
        perf_result = performance_analyzer.analyze_code(code)
        assert perf_result['success'] is True
        
        total_elapsed = (time.time() - start) * 1000
        
        print(f"\nFull code review workflow (500 lines):")
        print(f"  Total time: {total_elapsed:.1f}ms ({total_elapsed/1000:.2f}s)")
        print(f"  Refactoring: {refactor_result.get('metrics', {}).get('analysis_time_ms', 0):.1f}ms")
        
        assert total_elapsed < 5000, f"Total time {total_elapsed:.1f}ms exceeds 5s target"
    
    @pytest.mark.slow
    def test_large_codebase_analysis_performance(self):
        """Test analysis of large codebase (target: <60s for 10K lines)"""
        code = generate_large_code(10000)
        
        refactoring_engine = create_refactoring_engine()
        
        start = time.time()
        result = refactoring_engine.analyze_code(code)
        elapsed = (time.time() - start) * 1000
        
        assert result['success'] is True
        
        print(f"\nLarge codebase analysis (10K lines):")
        print(f"  Time: {elapsed:.1f}ms ({elapsed/1000:.2f}s)")
        
        assert elapsed < 60000, f"Time {elapsed:.1f}ms exceeds 60s target"


class TestMemoryUsage:
    """Memory usage tests for large codebases"""
    
    @pytest.mark.skipif(
        lambda: pytest.importorskip("psutil") is None,
        reason="psutil not installed"
    )
    def test_refactoring_engine_memory_efficiency(self):
        """Test memory usage during large file analysis"""
        pytest.importorskip("psutil")
        
        code = generate_large_code(5000)
        
        engine = create_refactoring_engine()
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024
        
        result = engine.analyze_code(code)
        
        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before
        
        assert result['success'] is True
        
        print(f"\nMemory usage (5K lines):")
        print(f"  Before: {mem_before:.1f} MB")
        print(f"  After: {mem_after:.1f} MB")
        print(f"  Increase: {mem_increase:.1f} MB")
        
        assert mem_increase < 100, f"Memory increase {mem_increase:.1f}MB exceeds 100MB limit"


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Performance Benchmark Tests")
    print("=" * 70 + "\n")
    
    pytest.main([__file__, '-v', '--tb=short', '-s', '-m', 'not slow'])
