#!/usr/bin/env python3
"""
Server Overload Management Script
=================================

This script provides tools to manage and work around Mistral-7B server overload issues
during analysis and evaluation.

Based on observed logs:
- GPU KV cache usage: 100.0%
- Running: 4 reqs, Pending: 36 reqs
- Requests being aborted
- MCP request timeouts
"""

import requests
import time
import json
from datetime import datetime
import subprocess
import sys

class ServerOverloadManager:
    """
    Manages server overload situations and provides recovery strategies.
    """
    
    def __init__(self):
        self.chat_simulator_url = "http://localhost:8002"
        self.mcp_server_url = "http://localhost:8000"
        
    def check_system_health(self):
        """Check the health of all system components."""
        print("🔍 Checking system health...")
        
        health_status = {
            'chat_simulator': False,
            'mcp_server': False,
            'overall': False
        }
        
        # Check Chat Simulator
        try:
            response = requests.get(f"{self.chat_simulator_url}/health", timeout=10)
            if response.status_code == 200:
                health_status['chat_simulator'] = True
                print("✅ Chat Simulator: Healthy")
            else:
                print(f"⚠️  Chat Simulator: Unhealthy (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Chat Simulator: Error - {e}")
        
        # Check MCP Server
        try:
            response = requests.get(f"{self.mcp_server_url}/health", timeout=10)
            if response.status_code == 200:
                health_status['mcp_server'] = True
                print("✅ MCP Server: Healthy")
            else:
                print(f"⚠️  MCP Server: Unhealthy (status: {response.status_code})")
        except Exception as e:
            print(f"❌ MCP Server: Error - {e}")
        
        health_status['overall'] = health_status['chat_simulator'] and health_status['mcp_server']
        
        if health_status['overall']:
            print("✅ Overall system health: Good")
        else:
            print("⚠️  Overall system health: Issues detected")
        
        return health_status
    
    def test_single_request(self, timeout=60):
        """Test a single request to see if the system is responsive."""
        print(f"🧪 Testing single request (timeout: {timeout}s)...")
        
        test_message = "Hello, this is a test message."
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.chat_simulator_url}/api/send-message",
                json={
                    'message': test_message,
                    'user_id': 'health_test',
                    'username': 'HealthTest',
                    'channel_id': 'health_check'
                },
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Single request successful ({response_time:.2f}s)")
                return True, response_time, result
            else:
                print(f"⚠️  Single request failed: {response.status_code}")
                return False, response_time, None
                
        except requests.exceptions.Timeout:
            print(f"⏰ Single request timed out after {timeout}s")
            return False, timeout, None
        except Exception as e:
            print(f"❌ Single request error: {e}")
            return False, 0, None
    
    def wait_for_queue_drain(self, max_wait=600, check_interval=30):
        """Wait for the Mistral server queue to drain."""
        print(f"⏳ Waiting for server queue to drain (max {max_wait}s)...")
        
        start_time = time.time()
        last_check = 0
        
        while time.time() - start_time < max_wait:
            elapsed = time.time() - start_time
            
            # Test responsiveness every check_interval
            if elapsed - last_check >= check_interval:
                success, response_time, _ = self.test_single_request(timeout=30)
                
                if success and response_time < 10.0:  # Good response time
                    print(f"✅ Server appears to have recovered (response time: {response_time:.2f}s)")
                    return True
                elif success:
                    print(f"⚠️  Server responding but slow (response time: {response_time:.2f}s)")
                else:
                    print(f"❌ Server still overloaded or unresponsive")
                
                last_check = elapsed
            
            print(f"⏸️  Waiting... ({elapsed:.0f}s/{max_wait}s)")
            time.sleep(check_interval)
        
        print(f"❌ Server did not recover within {max_wait} seconds")
        return False
    
    def get_system_recommendations(self):
        """Provide recommendations based on current system state."""
        print("\n🔧 SYSTEM RECOMMENDATIONS")
        print("=" * 50)
        
        health = self.check_system_health()
        success, response_time, _ = self.test_single_request(timeout=30)
        
        if not health['overall']:
            print("🚨 CRITICAL: System components are down")
            print("Immediate actions:")
            print("1. Check Docker containers: docker-compose ps")
            print("2. Restart services: docker-compose restart")
            print("3. Check logs: docker-compose logs mcp-server chat-simulator")
            return
        
        if not success:
            print("🚨 HIGH: System is unresponsive")
            print("Likely cause: Mistral-7B server overload")
            print("Immediate actions:")
            print("1. Wait for queue to drain (may take 10-30 minutes)")
            print("2. Reduce analysis batch sizes")
            print("3. Increase request delays to 30+ seconds")
            return
        
        if response_time > 30:
            print("⚠️  MEDIUM: System is slow but responsive")
            print("Recommended actions:")
            print("1. Use ultra-conservative analysis settings")
            print("2. Reduce sample sizes (10-20 messages max)")
            print("3. Increase delays between requests (15+ seconds)")
        elif response_time > 10:
            print("⚠️  LOW: System is moderately slow")
            print("Recommended actions:")
            print("1. Use resource-friendly analysis settings")
            print("2. Moderate sample sizes (20-50 messages)")
            print("3. Standard delays between requests (5-10 seconds)")
        else:
            print("✅ GOOD: System is responsive")
            print("You can proceed with normal analysis")
    
    def run_safe_analysis(self, sample_size=5):
        """Run a minimal analysis that's safe for overloaded servers."""
        print(f"\n🛡️  SAFE ANALYSIS MODE")
        print("=" * 30)
        print(f"Running minimal analysis with {sample_size} messages")
        print("Ultra-conservative settings to avoid server overload")
        
        try:
            from dataset_loader import DissertationDatasetLoader
            from model_evaluation_real import ModelPerformanceEvaluator
            
            # Load minimal dataset
            loader = DissertationDatasetLoader()
            
            # Initialize evaluator with ultra-conservative settings
            evaluator = ModelPerformanceEvaluator(resource_friendly=True)
            evaluator.request_delay = 20.0  # 20 seconds between requests
            evaluator.timeout = 120.0       # 2 minute timeout
            evaluator.max_retries = 2       # Only 2 retries
            evaluator.batch_delay = 60.0    # 1 minute between batches
            
            print(f"⚙️  Ultra-conservative settings:")
            print(f"   • Request delay: {evaluator.request_delay}s")
            print(f"   • Timeout: {evaluator.timeout}s")
            print(f"   • Sample size: {sample_size}")
            
            # Run evaluation
            evaluator.collect_evaluation_data(sample_size=sample_size)
            
            # Calculate basic metrics
            metrics = evaluator.calculate_performance_metrics()
            
            if metrics:
                print(f"\n📊 Safe Analysis Results:")
                print(f"   • Accuracy: {metrics.get('accuracy', 0):.3f}")
                print(f"   • F1-Score: {metrics.get('f1_score', 0):.3f}")
                print(f"   • Success Rate: {metrics.get('dataset_info', {}).get('success_rate', 0):.1%}")
                
                # Generate minimal report
                evaluator.generate_academic_report()
                print("✅ Safe analysis completed successfully")
            else:
                print("❌ Safe analysis failed - server too overloaded")
                
        except Exception as e:
            print(f"❌ Safe analysis error: {e}")

def main():
    print("🚨 SERVER OVERLOAD MANAGEMENT")
    print("=" * 50)
    print("Managing Mistral-7B server overload during analysis")
    print("Based on observed symptoms:")
    print("• GPU KV cache usage: 100%")
    print("• High pending request queue (36 reqs)")
    print("• Request aborts and MCP timeouts")
    print("=" * 50)
    
    manager = ServerOverloadManager()
    
    # Check current system state
    manager.get_system_recommendations()
    
    # Ask user what they want to do
    print(f"\n🤔 What would you like to do?")
    print("1. Wait for server recovery (recommended)")
    print("2. Run safe minimal analysis")
    print("3. Test single request")
    print("4. Exit")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            print("\n⏳ Waiting for server recovery...")
            if manager.wait_for_queue_drain():
                print("✅ Server recovered! You can now run normal analysis.")
            else:
                print("❌ Server did not recover. Consider:")
                print("1. Scaling up Mistral-7B resources")
                print("2. Using a smaller model temporarily")
                print("3. Running analysis during off-peak hours")
        
        elif choice == "2":
            manager.run_safe_analysis(sample_size=3)
        
        elif choice == "3":
            success, response_time, result = manager.test_single_request()
            if success:
                print(f"✅ Test successful - Response time: {response_time:.2f}s")
            else:
                print("❌ Test failed - Server overloaded")
        
        elif choice == "4":
            print("👋 Exiting...")
        
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
