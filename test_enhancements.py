#!/usr/bin/env python3
"""
Comprehensive test script for Picture Finder enhancements including:
- Performance monitoring
- Hash algorithm plugins
- Security features
- Accessibility features
- Configuration management
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.image_processor import ImageProcessor, AdvancedPerformanceMonitor, ImageHasher
from core.file_manager import FileManager
from core.config import get_config, ConfigManager
from core.log_writer import get_logger


class EnhancementTester:
    """Test suite for Picture Finder enhancements."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.logger = get_logger()
        self.temp_dir = None
        self.results = {}
    
    def setup_test_environment(self):
        """Set up temporary test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix='picture_finder_test_'))
        self.logger.log_info(f"Test environment created: {self.temp_dir}")
        
        # Create test directories
        (self.temp_dir / "test_images").mkdir()
        (self.temp_dir / "output").mkdir()
        
        return self.temp_dir
    
    def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.logger.log_info("Test environment cleaned up")
    
    def create_test_image(self, path: Path, size: tuple = (100, 100), color: str = 'red'):
        """Create a test image using PIL."""
        try:
            from PIL import Image
            
            # Create a simple colored image
            img = Image.new('RGB', size, color)
            img.save(path)
            return True
            
        except ImportError:
            # Fallback: create a small dummy file
            with open(path, 'wb') as f:
                f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to create test image: {str(e)}")
            return False
    
    def test_hash_algorithm_plugins(self) -> Dict[str, Any]:
        """Test hash algorithm plugin system."""
        test_name = "Hash Algorithm Plugins"
        self.logger.log_info(f"Testing: {test_name}")
        
        results = {
            'test_name': test_name,
            'passed': False,
            'details': {},
            'errors': []
        }
        
        try:
            # Test each hash algorithm
            algorithms = ['average', 'perceptual', 'difference', 'wavelet']
            
            # Create test image
            test_image = self.temp_dir / "test_images" / "test.jpg"
            self.create_test_image(test_image)
            
            for algorithm in algorithms:
                hasher = ImageHasher(algorithm=algorithm)
                
                # Test hashing
                hash_result, file_path, metadata = hasher.hash_file(str(test_image))
                
                if hash_result:
                    results['details'][algorithm] = {
                        'hash': hash_result,
                        'processing_time': metadata.get('processing_time', 0),
                        'from_cache': metadata.get('from_cache', False)
                    }
                else:
                    results['errors'].append(f"Failed to hash with {algorithm}")
            
            # Test cache functionality
            hasher = ImageHasher(algorithm='average')
            
            # First hash (should be cache miss)
            hash1, _, meta1 = hasher.hash_file(str(test_image))
            
            # Second hash (should be cache hit)
            hash2, _, meta2 = hasher.hash_file(str(test_image))
            
            if hash1 == hash2 and meta2.get('from_cache', False):
                results['details']['cache_test'] = 'PASSED'
            else:
                results['errors'].append("Cache functionality failed")
            
            # Test cache stats
            cache_stats = hasher.get_cache_stats()
            results['details']['cache_stats'] = cache_stats
            
            results['passed'] = len(results['errors']) == 0
            
        except Exception as e:
            results['errors'].append(f"Exception: {str(e)}")
        
        return results
    
    def test_performance_monitoring(self) -> Dict[str, Any]:
        """Test performance monitoring system."""
        test_name = "Performance Monitoring"
        self.logger.log_info(f"Testing: {test_name}")
        
        results = {
            'test_name': test_name,
            'passed': False,
            'details': {},
            'errors': []
        }
        
        try:
            monitor = AdvancedPerformanceMonitor()
            
            # Test monitoring lifecycle
            monitor.start_monitoring()
            
            # Simulate processing phases
            monitor.start_phase('file_scanning')
            time.sleep(0.1)  # Simulate work
            monitor.end_phase('file_scanning')
            
            monitor.start_phase('hash_calculation')
            time.sleep(0.1)
            monitor.end_phase('hash_calculation')
            
            # Test metrics recording
            monitor.update_file_count(10)
            monitor.record_cache_hit()
            monitor.record_cache_hit()
            monitor.record_cache_miss()
            
            monitor.end_monitoring()
            
            # Get performance summary
            summary = monitor.get_performance_summary()
            
            results['details']['execution_time'] = summary['execution_time']
            results['details']['cache_hit_rate'] = summary['cache_hit_rate']
            results['details']['phase_breakdown'] = summary['phase_breakdown']
            
            # Validate results
            if summary['execution_time'] > 0 and summary['cache_hit_rate'] > 0:
                results['passed'] = True
            else:
                results['errors'].append("Invalid performance metrics")
                
        except Exception as e:
            results['errors'].append(f"Exception: {str(e)}")
        
        return results
    
    def test_security_features(self) -> Dict[str, Any]:
        """Test security enhancements."""
        test_name = "Security Features"
        self.logger.log_info(f"Testing: {test_name}")
        
        results = {
            'test_name': test_name,
            'passed': False,
            'details': {},
            'errors': []
        }
        
        try:
            file_manager = FileManager(str(self.temp_dir / "output"))
            
            # Test path sanitization
            try:
                # Test valid path
                test_image = self.temp_dir / "test_images" / "valid.jpg"
                self.create_test_image(test_image)
                sanitized = file_manager.sanitize_path(str(test_image))
                results['details']['path_sanitization'] = 'PASSED'
            except Exception as e:
                results['errors'].append(f"Path sanitization failed: {str(e)}")
            
            # Test file validation
            if test_image.exists():
                permissions_ok = file_manager.validate_file_permissions(test_image)
                type_ok = file_manager.validate_file_type(test_image)
                
                results['details']['file_validation'] = {
                    'permissions': permissions_ok,
                    'type_validation': type_ok
                }
                
                if not permissions_ok or not type_ok:
                    results['errors'].append("File validation failed")
            
            # Test ZIP password protection
            try:
                zip_path = file_manager.export_to_zip(
                    str(self.temp_dir / "test_images"),
                    password="test123"
                )
                if zip_path:
                    results['details']['zip_password_protection'] = 'PASSED'
                else:
                    results['errors'].append("ZIP password protection failed")
            except Exception as e:
                results['errors'].append(f"ZIP export failed: {str(e)}")
            
            results['passed'] = len(results['errors']) == 0
            
        except Exception as e:
            results['errors'].append(f"Exception: {str(e)}")
        
        return results
    
    def test_configuration_management(self) -> Dict[str, Any]:
        """Test configuration management system."""
        test_name = "Configuration Management"
        self.logger.log_info(f"Testing: {test_name}")
        
        results = {
            'test_name': test_name,
            'passed': False,
            'details': {},
            'errors': []
        }
        
        try:
            # Test configuration creation and loading
            config_file = self.temp_dir / "test_config.json"
            config = ConfigManager(str(config_file))
            
            # Test setting updates
            original_threshold = config.performance.similarity_threshold
            config.update_setting('performance', 'similarity_threshold', 15)
            
            if config.performance.similarity_threshold == 15:
                results['details']['setting_update'] = 'PASSED'
            else:
                results['errors'].append("Setting update failed")
            
            # Test configuration save/load
            if config.save_config():
                new_config = ConfigManager(str(config_file))
                if new_config.performance.similarity_threshold == 15:
                    results['details']['save_load'] = 'PASSED'
                else:
                    results['errors'].append("Configuration save/load failed")
            else:
                results['errors'].append("Configuration save failed")
            
            # Test validation
            validation_issues = config.validate_settings()
            results['details']['validation'] = validation_issues
            
            results['passed'] = len(results['errors']) == 0
            
        except Exception as e:
            results['errors'].append(f"Exception: {str(e)}")
        
        return results
    
    def test_enhanced_processing(self) -> Dict[str, Any]:
        """Test enhanced image processing workflow."""
        test_name = "Enhanced Processing"
        self.logger.log_info(f"Testing: {test_name}")
        
        results = {
            'test_name': test_name,
            'passed': False,
            'details': {},
            'errors': []
        }
        
        try:
            # Create test images
            test_images_dir = self.temp_dir / "test_images"
            
            # Create original and duplicate
            original = test_images_dir / "original.jpg"
            duplicate = test_images_dir / "duplicate.jpg"
            
            self.create_test_image(original, color='blue')
            shutil.copy2(original, duplicate)  # Exact duplicate
            
            # Create similar image
            similar = test_images_dir / "similar.jpg"
            self.create_test_image(similar, color='navy')  # Similar color
            
            # Test processing
            processor = ImageProcessor(
                output_dir=str(self.temp_dir / "output"),
                performance_mode='high',
                hash_algorithm='average'
            )
            
            processing_results = processor.process_folder(
                str(test_images_dir),
                mode='copy',
                recursive=False
            )
            
            if processing_results:
                results['details']['processing_results'] = processing_results
                results['passed'] = True
            else:
                results['errors'].append("Processing failed")
                
        except Exception as e:
            results['errors'].append(f"Exception: {str(e)}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all enhancement tests."""
        self.logger.log_info("=== Starting Picture Finder Enhancement Tests ===")
        
        try:
            self.setup_test_environment()
            
            # Run individual tests
            test_results = []
            
            test_results.append(self.test_hash_algorithm_plugins())
            test_results.append(self.test_performance_monitoring())
            test_results.append(self.test_security_features())
            test_results.append(self.test_configuration_management())
            test_results.append(self.test_enhanced_processing())
            
            # Compile summary
            total_tests = len(test_results)
            passed_tests = sum(1 for result in test_results if result['passed'])
            
            summary = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                'test_details': test_results
            }
            
            self.logger.log_info(f"Tests completed: {passed_tests}/{total_tests} passed")
            
            return summary
            
        finally:
            self.cleanup_test_environment()
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results."""
        print("\n" + "="*60)
        print("PICTURE FINDER ENHANCEMENT TEST RESULTS")
        print("="*60)
        
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        
        print("\nDETAILED RESULTS:")
        print("-" * 40)
        
        for test in results['test_details']:
            status = "✓ PASSED" if test['passed'] else "✗ FAILED"
            print(f"\n{test['test_name']}: {status}")
            
            if test['details']:
                print("  Details:")
                for key, value in test['details'].items():
                    print(f"    - {key}: {value}")
            
            if test['errors']:
                print("  Errors:")
                for error in test['errors']:
                    print(f"    - {error}")
        
        print("\n" + "="*60)


def main():
    """Main test execution."""
    tester = EnhancementTester()
    results = tester.run_all_tests()
    tester.print_results(results)
    
    # Return exit code based on results
    return 0 if results['failed_tests'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())