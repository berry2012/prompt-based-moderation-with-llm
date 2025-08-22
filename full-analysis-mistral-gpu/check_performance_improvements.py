#!/usr/bin/env python3
"""
Performance Analysis Script - Measure Infrastructure Improvements
This script measures throughput and latency improvements from resource increases.
"""

import time
import requests
import statistics
import concurrent.futures
from datetime import datetime
import json

class PerformanceAnalyzer:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_messages = [
            "You're such an idiot, I hate you!",
            "This is a normal conversation about weather.",
            "I'm going to hurt you badly!",
            "Thanks for your help with the project.",
            "You should kill yourself, nobody likes you.",
            "Have a great day and stay safe!",
            "I'll find where you live and make you pay.",
            "The meeting is scheduled for 3 PM tomorrow.",
            "You're worthless and should disappear forever.",
            "Looking forward to our collaboration."
        ]
    
    def single_request_test(self, message):
        """Test single request latency"""
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/moderate",
                json={"text": message},
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "latency": end_time - start_time,
                    "response": response.json()
                }
            else:
                return {
                    "success": False,
                    "latency": end_time - start_time,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "latency": end_time - start_time,
                "error": str(e)
            }
    
    def concurrent_request_test(self, num_concurrent=10, num_rounds=3):
        """Test concurrent request handling"""
        print(f"\n🚀 Testing concurrent requests: {num_concurrent} concurrent, {num_rounds} rounds")
        
        all_results = []
        
        for round_num in range(num_rounds):
            print(f"  Round {round_num + 1}/{num_rounds}...")
            round_start = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                # Submit all requests
                futures = []
                for i in range(num_concurrent):
                    message = self.test_messages[i % len(self.test_messages)]
                    future = executor.submit(self.single_request_test, message)
                    futures.append(future)
                
                # Collect results
                round_results = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    round_results.append(result)
            
            round_end = time.time()
            round_duration = round_end - round_start
            
            successful_requests = [r for r in round_results if r["success"]]
            success_rate = len(successful_requests) / len(round_results) * 100
            
            if successful_requests:
                avg_latency = statistics.mean([r["latency"] for r in successful_requests])
                throughput = len(successful_requests) / round_duration
            else:
                avg_latency = 0
                throughput = 0
            
            print(f"    Success Rate: {success_rate:.1f}%")
            print(f"    Avg Latency: {avg_latency:.2f}s")
            print(f"    Throughput: {throughput:.2f} req/s")
            
            all_results.extend(round_results)
        
        return all_results
    
    def latency_distribution_test(self, num_requests=50):
        """Test latency distribution"""
        print(f"\n📊 Testing latency distribution: {num_requests} sequential requests")
        
        results = []
        for i in range(num_requests):
            if i % 10 == 0:
                print(f"  Progress: {i}/{num_requests}")
            
            message = self.test_messages[i % len(self.test_messages)]
            result = self.single_request_test(message)
            results.append(result)
            
            # Small delay to avoid overwhelming
            time.sleep(0.1)
        
        successful_results = [r for r in results if r["success"]]
        
        if successful_results:
            latencies = [r["latency"] for r in successful_results]
            
            print(f"\n📈 Latency Statistics:")
            print(f"  Successful Requests: {len(successful_results)}/{num_requests}")
            print(f"  Mean Latency: {statistics.mean(latencies):.3f}s")
            print(f"  Median Latency: {statistics.median(latencies):.3f}s")
            print(f"  Min Latency: {min(latencies):.3f}s")
            print(f"  Max Latency: {max(latencies):.3f}s")
            print(f"  Std Dev: {statistics.stdev(latencies):.3f}s")
            
            # Percentiles
            sorted_latencies = sorted(latencies)
            p50 = sorted_latencies[int(0.50 * len(sorted_latencies))]
            p90 = sorted_latencies[int(0.90 * len(sorted_latencies))]
            p95 = sorted_latencies[int(0.95 * len(sorted_latencies))]
            p99 = sorted_latencies[int(0.99 * len(sorted_latencies))]
            
            print(f"  P50: {p50:.3f}s")
            print(f"  P90: {p90:.3f}s")
            print(f"  P95: {p95:.3f}s")
            print(f"  P99: {p99:.3f}s")
        
        return results
    
    def run_comprehensive_analysis(self):
        """Run comprehensive performance analysis"""
        print("=" * 60)
        print("🔍 MISTRAL PERFORMANCE ANALYSIS")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target URL: {self.base_url}")
        
        # Test 1: Single request baseline
        print("\n1️⃣ Baseline Single Request Test")
        baseline_result = self.single_request_test(self.test_messages[0])
        if baseline_result["success"]:
            print(f"✅ Baseline latency: {baseline_result['latency']:.3f}s")
        else:
            print(f"❌ Baseline failed: {baseline_result['error']}")
            return
        
        # Test 2: Latency distribution
        self.latency_distribution_test(num_requests=30)
        
        # Test 3: Concurrent request tests
        concurrent_levels = [2, 5, 10, 15]
        for level in concurrent_levels:
            self.concurrent_request_test(num_concurrent=level, num_rounds=2)
        
        print("\n" + "=" * 60)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 60)
        print("\n💡 Key Insights:")
        print("• Model accuracy metrics won't change with more resources")
        print("• Look for improvements in:")
        print("  - Lower latency (faster response times)")
        print("  - Higher throughput (more requests/second)")
        print("  - Better success rates under load")
        print("  - More stable performance (lower std dev)")

def main():
    analyzer = PerformanceAnalyzer()
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()
