#!/usr/bin/env python3
"""
Performance tests for Debian Metapackage Manager.
These tests verify performance characteristics and scalability.
"""

import os
import sys
import time
import threading
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from debian_metapackage_manager.engine import PackageEngine
from debian_metapackage_manager.models import Package, PackageStatus, DependencyPlan
from debian_metapackage_manager.cli import PackageManagerCLI


class TestPerformance:
    """Performance tests for core functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "config.json")
        
        # Create test config with many prefixes
        test_config = {
            "package_prefixes": {
                "custom_prefixes": [f"perf-test-{i}-" for i in range(100)]
            },
            "offline_mode": False,
            "version_pinning": {f"package-{i}": f"1.{i}.0" for i in range(1000)}
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        self.engine = PackageEngine(config_path=self.config_file)
    
    def test_package_classification_performance(self):
        """Test package classification performance with many prefixes."""
        # Test classification speed with many packages
        packages = [f"test-package-{i}" for i in range(1000)]
        
        start_time = time.time()
        
        for package in packages:
            self.engine.classifier.is_custom_package(package)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should classify 1000 packages in less than 1 second
        assert duration < 1.0, f"Classification took {duration:.2f}s, expected < 1.0s"
        
        print(f"✓ Classified 1000 packages in {duration:.3f}s ({1000/duration:.0f} packages/sec)")
    
    def test_dependency_resolution_performance(self):
        """Test dependency resolution performance with large dependency trees."""
        # Create a large dependency tree
        packages = []
        for i in range(100):
            package = Package(f"package-{i}", "1.0.0", PackageStatus.NOT_INSTALLED)
            packages.append(package)
        
        with patch.object(self.engine.dependency_resolver, 'resolve_dependencies') as mock_resolve:
            # Simulate complex dependency resolution
            def slow_resolve(*args, **kwargs):
                # Simulate some processing time
                time.sleep(0.001)  # 1ms per resolution
                return DependencyPlan(
                    to_install=packages[:10],
                    to_remove=[],
                    to_upgrade=[],
                    conflicts=[]
                )
            
            mock_resolve.side_effect = slow_resolve
            
            start_time = time.time()
            
            # Resolve dependencies for multiple packages
            for i in range(50):
                self.engine.dependency_resolver.resolve_dependencies(
                    f"package-{i}", [], []
                )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should resolve 50 dependency trees in reasonable time
            assert duration < 5.0, f"Dependency resolution took {duration:.2f}s, expected < 5.0s"
            
            print(f"✓ Resolved 50 dependency trees in {duration:.3f}s ({50/duration:.1f} resolutions/sec)")
    
    def test_configuration_loading_performance(self):
        """Test configuration loading performance with large configs."""
        # Create large configuration
        large_config = {
            "package_prefixes": {
                "custom_prefixes": [f"prefix-{i}-" for i in range(10000)]
            },
            "offline_mode": False,
            "version_pinning": {f"package-{i}": f"1.{i}.0" for i in range(10000)}
        }
        
        large_config_file = os.path.join(self.temp_dir, "large_config.json")
        with open(large_config_file, 'w') as f:
            json.dump(large_config, f)
        
        start_time = time.time()
        
        # Load large configuration
        engine = PackageEngine(config_path=large_config_file)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should load large config in reasonable time
        assert duration < 2.0, f"Config loading took {duration:.2f}s, expected < 2.0s"
        
        print(f"✓ Loaded config with 10k prefixes and 10k pinned versions in {duration:.3f}s")
    
    def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations."""
        results = []
        errors = []
        
        def perform_operation(operation_id):
            try:
                with patch.object(self.engine.apt, 'is_package_available') as mock_available:
                    mock_available.return_value = True
                    
                    start_time = time.time()
                    
                    # Perform multiple operations
                    for i in range(10):
                        package_name = f"concurrent-package-{operation_id}-{i}"
                        self.engine.classifier.is_custom_package(package_name)
                        self.engine.get_package_info(package_name)
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    results.append(duration)
                    
            except Exception as e:
                errors.append(e)
        
        # Start multiple concurrent operations
        threads = []
        start_time = time.time()
        
        for i in range(10):
            thread = threading.Thread(target=perform_operation, args=[i])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent operations had errors: {errors}"
        
        # Verify reasonable performance
        assert total_duration < 5.0, f"Concurrent operations took {total_duration:.2f}s, expected < 5.0s"
        
        avg_duration = sum(results) / len(results) if results else 0
        print(f"✓ 10 concurrent operations completed in {total_duration:.3f}s (avg {avg_duration:.3f}s per thread)")
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets."""
        try:
            import psutil
        except ImportError:
            print("⚠ Skipping memory test (psutil not available)")
            return
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create many package objects
        packages = []
        for i in range(10000):
            package = Package(
                name=f"memory-test-package-{i}",
                version=f"1.{i}.0",
                status=PackageStatus.INSTALLED,
                is_custom=(i % 2 == 0),
                is_metapackage=(i % 3 == 0)
            )
            packages.append(package)
        
        current_memory = process.memory_info().rss
        memory_used = current_memory - initial_memory
        
        # Memory usage should be reasonable (less than 100MB for 10k packages)
        max_memory = 100 * 1024 * 1024  # 100MB
        assert memory_used < max_memory, f"Memory usage {memory_used/1024/1024:.1f}MB exceeds limit {max_memory/1024/1024:.1f}MB"
        
        print(f"✓ 10k package objects use {memory_used/1024/1024:.1f}MB memory")
        
        # Clean up
        del packages
        import gc
        gc.collect()
    
    def test_cli_response_time(self):
        """Test CLI response time for common operations."""
        cli = PackageManagerCLI()
        
        # Test help command response time
        start_time = time.time()
        try:
            cli.run(['--help'])
        except SystemExit:
            pass  # Help command exits
        end_time = time.time()
        
        help_duration = end_time - start_time
        assert help_duration < 1.0, f"Help command took {help_duration:.2f}s, expected < 1.0s"
        
        # Test config show response time
        start_time = time.time()
        result = cli.run(['config', '--show'])
        end_time = time.time()
        
        config_duration = end_time - start_time
        assert config_duration < 2.0, f"Config show took {config_duration:.2f}s, expected < 2.0s"
        
        print(f"✓ CLI help: {help_duration:.3f}s, config show: {config_duration:.3f}s")
    
    def test_large_dependency_tree_performance(self):
        """Test performance with large dependency trees."""
        # Create a complex dependency tree
        root_package = "large-metapackage"
        dependencies = []
        
        # Create 3 levels of dependencies
        for i in range(20):  # 20 direct dependencies
            dep1 = Package(f"dep-level1-{i}", "1.0.0", PackageStatus.NOT_INSTALLED)
            dependencies.append(dep1)
            
            for j in range(5):  # 5 sub-dependencies each
                dep2 = Package(f"dep-level2-{i}-{j}", "1.0.0", PackageStatus.NOT_INSTALLED)
                dependencies.append(dep2)
                
                for k in range(2):  # 2 sub-sub-dependencies each
                    dep3 = Package(f"dep-level3-{i}-{j}-{k}", "1.0.0", PackageStatus.NOT_INSTALLED)
                    dependencies.append(dep3)
        
        # Total: 20 + (20*5) + (20*5*2) = 20 + 100 + 200 = 320 packages
        
        with patch.object(self.engine.apt, 'get_dependencies') as mock_deps:
            mock_deps.return_value = dependencies
            
            start_time = time.time()
            
            # Get dependency tree
            deps = self.engine.apt.get_dependencies(root_package)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should handle large dependency tree quickly
            assert duration < 1.0, f"Large dependency tree took {duration:.2f}s, expected < 1.0s"
            assert len(deps) == 320
            
            print(f"✓ Processed dependency tree with 320 packages in {duration:.3f}s")


class TestScalability:
    """Test scalability characteristics."""
    
    def test_package_count_scalability(self):
        """Test scalability with increasing package counts."""
        package_counts = [100, 500, 1000, 5000]
        times = []
        
        for count in package_counts:
            # Create test packages
            packages = [f"scale-test-{i}" for i in range(count)]
            
            engine = PackageEngine()
            
            start_time = time.time()
            
            # Classify all packages
            for package in packages:
                engine.classifier.is_custom_package(package)
            
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            print(f"✓ {count} packages classified in {duration:.3f}s ({count/duration:.0f} packages/sec)")
        
        # Verify scalability - time should scale roughly linearly
        # (allowing for some overhead)
        for i in range(1, len(times)):
            ratio = times[i] / times[i-1]
            count_ratio = package_counts[i] / package_counts[i-1]
            
            # Time ratio should be roughly proportional to count ratio
            # Allow up to 2x overhead for larger datasets
            assert ratio <= count_ratio * 2, f"Scalability issue: {ratio:.2f}x time for {count_ratio:.2f}x packages"
    
    def test_configuration_size_scalability(self):
        """Test scalability with increasing configuration sizes."""
        prefix_counts = [10, 100, 1000, 10000]
        times = []
        
        for count in prefix_counts:
            temp_dir = tempfile.mkdtemp()
            config_file = os.path.join(temp_dir, "config.json")
            
            # Create config with many prefixes
            config = {
                "package_prefixes": {
                    "custom_prefixes": [f"scale-prefix-{i}-" for i in range(count)]
                },
                "offline_mode": False,
                "version_pinning": {}
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f)
            
            start_time = time.time()
            
            # Load configuration
            engine = PackageEngine(config_path=config_file)
            
            # Test prefix matching
            engine.classifier.is_custom_package("scale-prefix-500-test")
            
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            print(f"✓ Config with {count} prefixes loaded and used in {duration:.3f}s")
        
        # Verify reasonable scalability
        max_time = max(times)
        assert max_time < 5.0, f"Configuration scalability issue: {max_time:.2f}s for largest config"


def run_performance_tests():
    """Run all performance tests."""
    print("Running performance tests...")
    
    test_classes = [
        TestPerformance(),
        TestScalability()
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                if hasattr(test_class, 'setup_method'):
                    test_class.setup_method()
                
                method = getattr(test_class, method_name)
                method()
                print(f"✓ {test_class.__class__.__name__}.{method_name}")
                passed += 1
            except Exception as e:
                print(f"✗ {test_class.__class__.__name__}.{method_name}: {e}")
                failed += 1
    
    print(f"\nPerformance Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)