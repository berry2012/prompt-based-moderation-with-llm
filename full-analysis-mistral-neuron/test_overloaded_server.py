#!/usr/bin/env python3
"""
Overloaded Server Test Script
============================

This script is specifically designed to test the moderation system when the 
Mistral-7B LLM server is overloaded with high GPU memory usage and request queues.

It implements ultra-conservative request patterns to avoid overwhelming the server further.
"""

import requests
import json
import time
from datetime import datetime
from dataset_loader import DissertationDatasetLoader

class OverloadedServerTester:
    """
    Ultra-conservative tester for overloaded Mistral servers.
    """
    
    def __init__(self):
        self.request_delay = 15.0      # 15 seconds between requests
        self.timeout = 180.0           # 3 minute timeout
        self.max_retries = 2           # Only 2 retries to avoid pile-up
        self.batch_delay = 60.0        # 1 minute between batches
        self.health_check_interval = 5 # Check health every 5 requests
        
        print("🚨 Overloaded Server Tester Initialized")
        print(f"   • Ultra-conservative settings for overloaded Mistral-7B")
        print(f"   • Request delay: {self.request_delay}s")
        print(f"   • Timeout: {self.timeout}s")
        print(f"   • Max retries: {self.max_retries}")
    
    def check_server_health(self):
        """Check if the Chat Simulator is responsive."""
        try:
            response = requests.get('http://localhost:8002/health', timeout=10.0)
            if response.status_code == 200:
                print("✅ Chat Simulator health check passed")
                return True
            else:
                print(f"⚠️  Chat Simulator health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Chat Simulator health check error: {e}")
            return False
    
    def wait_for_server_recovery(self, max_wait=300):
        """Wait for server to recover from overload."""
        print("⏳ Waiting for server recovery...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if self.check_server_health():
                recovery_time = time.time() - start_time
                print(f"✅ Server recovered after {recovery_time:.1f} seconds")
                return True
            
            print("⏸️  Server still overloaded, waiting 30s...")
            time.sleep(30.0)
        
        print(f"❌ Server did not recover within {max_wait} seconds")
        return False
    
    def send_single_message(self, message, user_id, attempt=1):
        """Send a single message with ultra-conservative approach."""
        print(f"📤 Sending message (attempt {attempt}): {message[:50]}...")
        
        try:
            response = requests.post(
                'http://localhost:8002/api/send-message',
                json={
                    'message': message,
                    'user_id': user_id,
                    'username': f'TestUser{user_id}',
                    'channel_id': 'overload_test'
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Message processed successfully")
                return result
            else:
                print(f"⚠️  Request failed with status: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏰ Request timed out after {self.timeout}s - server likely overloaded")
            return None
        except requests.exceptions.RequestException as e:
            print(f"🔌 Connection error: {e}")
            return None
    
    def test_with_recovery(self, messages, max_messages=5):
        """Test messages with automatic recovery handling."""
        print(f"🧪 Testing {min(len(messages), max_messages)} messages with recovery handling")
        
        results = []
        successful = 0
        failed = 0
        
        # Limit to small number for overloaded server
        test_messages = messages[:max_messages]
        
        for i, (message, true_label) in enumerate(test_messages):
            print(f"\n--- Message {i+1}/{len(test_messages)} ---")
            
            # Health check every few requests
            if i % self.health_check_interval == 0 and i > 0:
                if not self.check_server_health():
                    print("🚨 Server appears overloaded, waiting for recovery...")
                    if not self.wait_for_server_recovery():
                        print("❌ Stopping test due to server overload")
                        break
            
            # Attempt to send message
            result = None
            for attempt in range(1, self.max_retries + 1):
                result = self.send_single_message(message, f"test_{i}", attempt)
                
                if result is not None:
                    successful += 1
                    results.append({
                        'message': message,
                        'true_label': true_label,
                        'result': result,
                        'attempt': attempt
                    })
                    break
                else:
                    if attempt < self.max_retries:
                        backoff_delay = self.request_delay * (2 ** attempt)
                        print(f"⏸️  Backing off {backoff_delay:.1f}s before retry...")
                        time.sleep(backoff_delay)
            
            if result is None:
                failed += 1
                print(f"❌ Message failed after {self.max_retries} attempts")
            
            # Long delay between messages to avoid overloading
            if i < len(test_messages) - 1:
                print(f"⏸️  Waiting {self.request_delay}s before next message...")
                time.sleep(self.request_delay)
            
            # Extra long delay every few messages
            if (i + 1) % 3 == 0 and i < len(test_messages) - 1:
                print(f"⏸️  Extended batch delay ({self.batch_delay}s) for server recovery...")
                time.sleep(self.batch_delay)
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   • Total messages: {len(test_messages)}")
        print(f"   • Successful: {successful}")
        print(f"   • Failed: {failed}")
        print(f"   • Success rate: {successful/len(test_messages):.1%}")
        
        return results

def main():
    print("🚨 OVERLOADED SERVER TEST")
    print("=" * 50)
    print("This script is designed for testing when Mistral-7B is overloaded:")
    print("• GPU KV cache usage: 100%")
    print("• High pending request queue")
    print("• Frequent request aborts")
    print("=" * 50)
    
    try:
        # Initialize tester
        tester = OverloadedServerTester()
        
        # Load a very small dataset sample
        loader = DissertationDatasetLoader()
        messages = loader.get_balanced_sample(n_samples=6, random_state=42)  # Very small sample
        
        print(f"\n📋 Loaded {len(messages)} test messages")
        
        # Initial health check
        if not tester.check_server_health():
            print("⚠️  Server appears to be having issues, but proceeding with ultra-conservative test...")
        
        # Run test with recovery
        results = tester.test_with_recovery(messages, max_messages=3)  # Only test 3 messages
        
        if results:
            print(f"\n✅ Test completed with {len(results)} successful results")
            
            # Show sample results
            for i, result in enumerate(results[:2]):  # Show first 2 results
                moderation_result = result['result'].get('result', {}).get('moderation_result', {})
                action = moderation_result.get('action', 'unknown')
                print(f"   {i+1}. [{result['true_label']}] → [{action}] (attempt {result['attempt']})")
        else:
            print("❌ No successful results - server is severely overloaded")
            print("\n🔧 Recommendations:")
            print("1. Scale up Mistral-7B resources (more GPU memory)")
            print("2. Reduce concurrent request limits")
            print("3. Implement request queuing with backpressure")
            print("4. Consider using a smaller model temporarily")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if Chat Simulator is running: curl http://localhost:8002/health")
        print("2. Check Mistral-7B logs for overload indicators")
        print("3. Monitor GPU memory usage on Kubernetes cluster")

if __name__ == "__main__":
    main()
