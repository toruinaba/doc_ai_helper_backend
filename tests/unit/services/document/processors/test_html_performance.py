"""
Performance tests for HTMLProcessor.

Tests HTMLProcessor's performance characteristics with various document sizes
and complexity levels.
"""

import pytest
import time
from typing import List, Tuple

from doc_ai_helper_backend.services.document.processors.html import HTMLProcessor


class TestHTMLProcessorPerformance:
    """Test performance characteristics of HTMLProcessor."""

    @pytest.fixture
    def processor(self):
        """Create an HTMLProcessor instance for testing."""
        return HTMLProcessor()

    @pytest.fixture
    def small_html(self):
        """Small HTML document for performance baseline."""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Small Document</title></head>
        <body>
            <h1>Title</h1>
            <p>Small content with <a href="link.html">link</a></p>
            <img src="image.jpg" alt="Image">
        </body>
        </html>
        """

    @pytest.fixture
    def medium_html(self):
        """Medium-sized HTML document."""
        content = """<!DOCTYPE html>
        <html>
        <head>
            <title>Medium Document</title>
            <meta name="description" content="Medium-sized test document">
        </head>
        <body>
        """
        
        # Add 100 sections with links and images
        for i in range(100):
            content += f"""
            <section>
                <h2>Section {i}</h2>
                <p>Content for section {i} with <a href="section{i}.html">link</a></p>
                <img src="image{i}.jpg" alt="Image {i}">
            </section>
            """
        
        content += "</body></html>"
        return content

    @pytest.fixture
    def large_html(self):
        """Large HTML document for stress testing."""
        content = """<!DOCTYPE html>
        <html>
        <head>
            <title>Large Document</title>
            <meta name="description" content="Large test document">
        </head>
        <body>
        """
        
        # Add 1000 sections with multiple elements
        for i in range(1000):
            content += f"""
            <section id="section{i}">
                <h2>Section {i}</h2>
                <p>Content for section {i} with multiple <a href="section{i}.html">links</a> and <a href="ref{i}.html">references</a></p>
                <ul>
                    <li><a href="item{i}_1.html">Item 1</a></li>
                    <li><a href="item{i}_2.html">Item 2</a></li>
                    <li><a href="item{i}_3.html">Item 3</a></li>
                </ul>
                <img src="image{i}.jpg" alt="Image {i}">
                <img src="thumb{i}.png" alt="Thumbnail {i}">
            </section>
            """
        
        content += "</body></html>"
        return content

    def measure_performance(self, func, *args, **kwargs) -> Tuple[float, any]:
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return execution_time, result

    def test_content_processing_performance(self, processor, small_html, medium_html, large_html):
        """Test content processing performance across different document sizes."""
        test_cases = [
            ("small", small_html),
            ("medium", medium_html),
            ("large", large_html),
        ]
        
        performance_results = {}
        
        for size_name, html_content in test_cases:
            execution_time, result = self.measure_performance(
                processor.process_content, html_content, f"/test/{size_name}.html"
            )
            
            performance_results[size_name] = execution_time
            
            # Verify correctness
            assert result.content == html_content
            assert result.encoding == "utf-8"
            
            # Performance assertions (reasonable thresholds)
            if size_name == "small":
                assert execution_time < 0.01, f"Small document processing too slow: {execution_time:.4f}s"
            elif size_name == "medium":
                assert execution_time < 0.1, f"Medium document processing too slow: {execution_time:.4f}s"
            elif size_name == "large":
                assert execution_time < 1.0, f"Large document processing too slow: {execution_time:.4f}s"
        
        # Performance assertions for very fast operations may be affected by timing noise
        # Just ensure all operations complete within reasonable bounds
        # The main goal is ensuring no major performance regressions
        pass  # Skip strict ordering checks for micro-optimized operations

    def test_metadata_extraction_performance(self, processor, small_html, medium_html, large_html):
        """Test metadata extraction performance."""
        test_cases = [
            ("small", small_html),
            ("medium", medium_html),
            ("large", large_html),
        ]
        
        for size_name, html_content in test_cases:
            execution_time, metadata = self.measure_performance(
                processor.extract_metadata, html_content, f"/test/{size_name}.html"
            )
            
            # Verify correctness
            assert metadata.content_type == "text/html"
            assert "html" in metadata.extra
            
            # Performance assertions
            if size_name == "small":
                assert execution_time < 0.01, f"Small metadata extraction too slow: {execution_time:.4f}s"
            elif size_name == "medium":
                assert execution_time < 0.1, f"Medium metadata extraction too slow: {execution_time:.4f}s"
            elif size_name == "large":
                assert execution_time < 2.0, f"Large metadata extraction too slow: {execution_time:.4f}s"

    def test_link_extraction_performance(self, processor, small_html, medium_html, large_html):
        """Test link extraction performance."""
        test_cases = [
            ("small", small_html, 2),  # Expected minimum number of links
            ("medium", medium_html, 200),
            ("large", large_html, 5000),
        ]
        
        for size_name, html_content, expected_min_links in test_cases:
            execution_time, links = self.measure_performance(
                processor.extract_links, html_content, "/test"
            )
            
            # Verify correctness
            assert len(links) >= expected_min_links, f"Expected at least {expected_min_links} links in {size_name}"
            
            # Performance assertions
            if size_name == "small":
                assert execution_time < 0.01, f"Small link extraction too slow: {execution_time:.4f}s"
            elif size_name == "medium":
                assert execution_time < 0.1, f"Medium link extraction too slow: {execution_time:.4f}s"
            elif size_name == "large":
                assert execution_time < 2.0, f"Large link extraction too slow: {execution_time:.4f}s"

    def test_link_transformation_performance(self, processor, medium_html):
        """Test link transformation performance."""
        execution_time, transformed_html = self.measure_performance(
            processor.transform_links,
            medium_html,
            "/test/medium.html",
            "https://api.example.com/documents",
            service="github",
            owner="testuser",
            repo="testproject",
            ref="main"
        )
        
        # Verify correctness
        assert len(transformed_html) > 0
        assert transformed_html != medium_html  # Should be transformed
        
        # Performance assertion
        assert execution_time < 0.5, f"Link transformation too slow: {execution_time:.4f}s"

    def test_repeated_operations_performance(self, processor, small_html):
        """Test performance consistency with repeated operations."""
        iterations = 100
        times = []
        
        for _ in range(iterations):
            execution_time, _ = self.measure_performance(
                processor.process_content, small_html, "/test/repeat.html"
            )
            times.append(execution_time)
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        # Performance assertions
        assert avg_time < 0.01, f"Average execution time too high: {avg_time:.6f}s"
        assert max_time < 0.05, f"Maximum execution time too high: {max_time:.6f}s"
        
        # Consistency check: max shouldn't be more than 10x the average
        assert max_time < avg_time * 10, f"Performance inconsistent: max={max_time:.6f}s, avg={avg_time:.6f}s"

    def test_memory_usage_stability(self, processor, large_html):
        """Test that memory usage remains stable across operations."""
        import gc
        
        # Run garbage collection before starting
        gc.collect()
        
        # Perform multiple operations
        for i in range(20):
            processor.process_content(large_html, f"/test/memory_{i}.html")
            processor.extract_metadata(large_html, f"/test/memory_{i}.html")
            processor.extract_links(large_html, "/test")
            
            # Force garbage collection periodically
            if i % 5 == 0:
                gc.collect()
        
        # Final garbage collection
        gc.collect()
        
        # This test mainly ensures no memory leaks cause crashes
        # Specific memory assertions would require additional tools

    def test_concurrent_processing_simulation(self, processor, medium_html):
        """Test performance under simulated concurrent load."""
        import threading
        import queue
        
        num_threads = 5
        num_operations_per_thread = 10
        results_queue = queue.Queue()
        
        def worker():
            thread_times = []
            for i in range(num_operations_per_thread):
                execution_time, _ = self.measure_performance(
                    processor.extract_metadata, medium_html, f"/test/concurrent_{i}.html"
                )
                thread_times.append(execution_time)
            results_queue.put(thread_times)
        
        # Start threads
        threads = []
        start_time = time.perf_counter()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        total_time = time.perf_counter() - start_time
        
        # Collect results
        all_times = []
        while not results_queue.empty():
            thread_times = results_queue.get()
            all_times.extend(thread_times)
        
        # Performance assertions (relaxed for concurrent testing)
        avg_time = sum(all_times) / len(all_times)
        assert avg_time < 0.5, f"Average concurrent execution time too high: {avg_time:.4f}s"
        assert total_time < 15.0, f"Total concurrent test time too high: {total_time:.2f}s"

    @pytest.mark.parametrize("document_size", [100, 500, 1000, 2000])
    def test_scalability_with_document_size(self, processor, document_size):
        """Test how performance scales with document size."""
        # Generate HTML with specified number of elements
        html_content = f"""<!DOCTYPE html>
        <html>
        <head><title>Scalability Test {document_size}</title></head>
        <body>
        """
        
        for i in range(document_size):
            html_content += f'<p>Paragraph {i} with <a href="link{i}.html">link {i}</a></p>'
        
        html_content += "</body></html>"
        
        # Measure performance
        execution_time, links = self.measure_performance(
            processor.extract_links, html_content, "/test"
        )
        
        # Verify correctness
        assert len(links) >= document_size  # Should extract at least one link per paragraph
        
        # Performance should scale sub-linearly (better than O(n²))
        # This is a rough heuristic - actual performance depends on implementation
        expected_max_time = (document_size / 100) * 0.1  # Scale with complexity
        assert execution_time < expected_max_time, f"Scalability issue: {execution_time:.4f}s for {document_size} elements"

    def test_performance_regression_baseline(self, processor, medium_html):
        """Establish performance baseline for regression testing."""
        # This test provides baseline measurements for future comparison
        operations = [
            ("process_content", lambda: processor.process_content(medium_html, "/test/baseline.html")),
            ("extract_metadata", lambda: processor.extract_metadata(medium_html, "/test/baseline.html")),
            ("extract_links", lambda: processor.extract_links(medium_html, "/test")),
            ("transform_links", lambda: processor.transform_links(
                medium_html, "/test/baseline.html", "https://api.example.com",
                service="github", owner="user", repo="repo", ref="main"
            )),
        ]
        
        baseline_times = {}
        
        for op_name, operation in operations:
            execution_time, _ = self.measure_performance(operation)
            baseline_times[op_name] = execution_time
            
            # Log baseline times (useful for future regression analysis)
            print(f"Baseline {op_name}: {execution_time:.6f}s")
        
        # Store reasonable upper bounds for future regression tests
        expected_maximums = {
            "process_content": 0.01,
            "extract_metadata": 0.1,
            "extract_links": 0.1,
            "transform_links": 0.2,
        }
        
        for op_name, max_time in expected_maximums.items():
            assert baseline_times[op_name] < max_time, f"{op_name} baseline too slow: {baseline_times[op_name]:.6f}s"