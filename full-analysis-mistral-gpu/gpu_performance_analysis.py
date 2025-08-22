#!/usr/bin/env python3
"""
GPU Performance Analysis Script
Specialized performance testing for GPU-based Mistral deployment.
"""

import time
import requests
import statistics
import concurrent.futures
from datetime import datetime
import json

class GPUPerformanceAnalyzer:
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
            "Looking forward to our collaboration.",
            "This toxic message contains multiple threats and harassment.",
            "A completely benign message about daily activities.",
            "Extremely offensive content with explicit threats of violence.",
            "Professional communication regarding business matters.",
            "Cyberbullying content targeting personal characteristics."
        ]
    
    def gpu_specific_tests(self):
        """Run GPU-specific performance tests"""
        print("🎮 GPU-SPECIFIC PERFORMANCE TESTS")
        print("=" * 50)
        
        # Test 1: Cold start performance
        print("\n❄️ Cold Start Test (first request after deployment)")
        cold_start = self.single_request_test(self.test_messages[0])
        if cold_start["success"]:
            print(f"  Cold start latency: {cold_start['latency']:.3f}s")
        else:
            print(f"  Cold start failed: {cold_start['error']}")
        
        # Test 2: Warm-up requests
        print("\n🔥 Warm-up Phase (5 sequential requests)")
        warmup_latencies = []
        for i in range(5):
            result = self.single_request_test(self.test_messages[i % len(self.test_messages)])
            if result["success"]:
                warmup_latencies.append(result["latency"])
                print(f"  Request {i+1}: {result['latency']:.3f}s")
            time.sleep(0.5)
        
        if warmup_latencies:
            avg_warmup = statistics.mean(warmup_latencies)
            print(f"  Average warm-up latency: {avg_warmup:.3f}s")
        
        # Test 3: Sustained performance
        print("\n⚡ Sustained Performance Test")
        return self.sustained_performance_test()
    
    def sustained_performance_test(self, duration_seconds=60):
        """Test sustained performance over time"""
        print(f"Running sustained test for {duration_seconds} seconds...")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        results = []
        request_count = 0
        
        while time.time() < end_time:
            message = self.test_messages[request_count % len(self.test_messages)]
            result = self.single_request_test(message)
            results.append(result)
            request_count += 1
            
            # Small delay to avoid overwhelming
            time.sleep(0.2)
            
            if request_count % 10 == 0:
                elapsed = time.time() - start_time
                print(f"  Progress: {request_count} requests in {elapsed:.1f}s")
        
        # Analyze results
        successful_results = [r for r in results if r["success"]]
        success_rate = len(successful_results) / len(results) * 100
        
        if successful_results:
            latencies = [r["latency"] for r in successful_results]
            total_time = time.time() - start_time
            throughput = len(successful_results) / total_time
            
            print(f"\n📊 Sustained Performance Results:")
            print(f"  Total requests: {len(results)}")
            print(f"  Successful requests: {len(successful_results)}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Average latency: {statistics.mean(latencies):.3f}s")
            print(f"  Median latency: {statistics.median(latencies):.3f}s")
            print(f"  Min latency: {min(latencies):.3f}s")
            print(f"  Max latency: {max(latencies):.3f}s")
            print(f"  Throughput: {throughput:.2f} req/s")
            
            return {
                "success_rate": success_rate,
                "avg_latency": statistics.mean(latencies),
                "throughput": throughput,
                "latencies": latencies
            }
        
        return None
    
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
    
    def concurrent_load_test(self, concurrent_levels=[2, 4, 8, 16, 32]):
        """Test performance under different concurrent loads"""
        print("\n🚀 CONCURRENT LOAD TESTING")
        print("=" * 40)
        
        results = {}
        
        for level in concurrent_levels:
            print(f"\n📈 Testing {level} concurrent requests...")
            
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=level) as executor:
                # Submit concurrent requests
                futures = []
                for i in range(level):
                    message = self.test_messages[i % len(self.test_messages)]
                    future = executor.submit(self.single_request_test, message)
                    futures.append(future)
                
                # Collect results
                batch_results = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    batch_results.append(result)
            
            end_time = time.time()
            batch_duration = end_time - start_time
            
            successful_requests = [r for r in batch_results if r["success"]]
            success_rate = len(successful_requests) / len(batch_results) * 100
            
            if successful_requests:
                avg_latency = statistics.mean([r["latency"] for r in successful_requests])
                throughput = len(successful_requests) / batch_duration
            else:
                avg_latency = 0
                throughput = 0
            
            results[level] = {
                "success_rate": success_rate,
                "avg_latency": avg_latency,
                "throughput": throughput,
                "batch_duration": batch_duration
            }
            
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Avg Latency: {avg_latency:.3f}s")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Batch Duration: {batch_duration:.2f}s")
        
        return results
    
    def memory_stress_test(self):
        """Test with longer messages to stress GPU memory"""
        print("\n💾 GPU MEMORY STRESS TEST")
        print("=" * 35)
        
        # Create progressively longer messages
        base_message = "This is a toxic message that contains harassment and threats. "
        stress_messages = []
        
        for multiplier in [1, 5, 10, 20, 50]:
            long_message = base_message * multiplier
            stress_messages.append({
                "length": len(long_message),
                "message": long_message
            })
        
        results = []
        for msg_data in stress_messages:
            print(f"\n  Testing message length: {msg_data['length']} characters")
            result = self.single_request_test(msg_data['message'])
            
            if result["success"]:
                print(f"    Latency: {result['latency']:.3f}s")
                results.append({
                    "length": msg_data['length'],
                    "latency": result['latency'],
                    "success": True
                })
            else:
                print(f"    Failed: {result['error']}")
                results.append({
                    "length": msg_data['length'],
                    "latency": result['latency'],
                    "success": False
                })
        
        return results
    
    def run_comprehensive_gpu_analysis(self):
        """Run comprehensive GPU performance analysis"""
        print("=" * 60)
        print("🎮 MISTRAL GPU PERFORMANCE ANALYSIS")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target URL: {self.base_url}")
        
        # Run all tests
        gpu_results = self.gpu_specific_tests()
        concurrent_results = self.concurrent_load_test()
        memory_results = self.memory_stress_test()
        
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        if gpu_results:
            print(f"🎯 Sustained Performance:")
            print(f"  Average Latency: {gpu_results['avg_latency']:.3f}s")
            print(f"  Throughput: {gpu_results['throughput']:.2f} req/s")
            print(f"  Success Rate: {gpu_results['success_rate']:.1f}%")
        
        print(f"\n🚀 Concurrent Performance:")
        for level, result in concurrent_results.items():
            print(f"  {level} concurrent: {result['throughput']:.2f} req/s, {result['avg_latency']:.3f}s avg latency")
        
        print(f"\n💾 Memory Handling:")
        successful_memory_tests = [r for r in memory_results if r['success']]
        if successful_memory_tests:
            max_length = max([r['length'] for r in successful_memory_tests])
            print(f"  Max message length handled: {max_length} characters")
        
        print("\n💡 GPU OPTIMIZATION INSIGHTS:")
        insights = [
            "• GPU should show lower latency than Neuron for inference",
            "• Higher concurrent throughput expected with GPU acceleration",
            "• Memory usage should be more efficient with VRAM",
            "• Watch for GPU memory limits with very long messages"
        ]
        
        for insight in insights:
            print(f"  {insight}")

def main():
    analyzer = GPUPerformanceAnalyzer()
    analyzer.run_comprehensive_gpu_analysis()

if __name__ == "__main__":
    main()
