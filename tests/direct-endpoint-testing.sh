# direct testing

#!/bin/bash
echo "=== Testing MCP Server Direct ==="
curl -X POST "http://localhost:8000/moderate" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "You are the worst human being, you make me sick to my stomach.",
    "user_id": "test_user_123",
    "channel_id": "general"
  }' | jq '.'


echo "=== Testing DeepSeek LLM Direct ==="
curl -X POST "http://k8s-deepseek-deepseek-e92cca8149-b20547a64509f06f.elb.eu-west-1.amazonaws.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "messages": [
      {
        "role": "system", 
        "content": "You are a content moderation system. Analyze the following message and respond with a JSON object containing: {\"action\": \"allow|warn|block|timeout\", \"reason\": \"explanation\", \"confidence\": 0.0-1.0, \"categories\": [\"list of violation types\"]}. Be strict about toxic content."
      },
      {
        "role": "user", 
        "content": "Analyze this message: \"You are the worst human being, you make me sick to my stomach.\""
      }
    ],
    "temperature": 0.1,
    "max_tokens": 500
  }' | jq '.'

echo "=== Testing Chat Simulator API ==="
curl -X POST "http://localhost:8002/api/send-message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "You are the worst human being, you make me sick to my stomach.",
    "user_id": "test_user_123",
    "username": "TestUser",
    "channel_id": "general"
  }' | jq '.'


#  ↳ Purpose: Test normal message through WebUI API
curl -s -X POST "http://localhost:8002/api/send-message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello everyone, how are you doing today?",
    "user_id": "web_user_normal",
    "username": "NormalWebUser",
    "channel_id": "web-chat"
  }' | jq '.result.moderation_result'
 ⋮ 

#  ↳ Purpose: Test WebUI API with improved timeout configuration
curl -s -X POST "http://localhost:8002/api/send-message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "You are the worst human being, you make me sick to my stomach.",
    "user_id": "web_user_test",
    "username": "WebUser",
    "channel_id": "web-chat"
  }' | jq '.result.moderation_result'
 ⋮ 






# ======= Using DeepSeek R1 =========

curl -w "$(date +'%Y-%d-%m-%H-%M-%S') $(echo $HOSTNAME) time_namelookup: %{time_namelookup}, time_connect: %{time_connect}, time_appconnect: %{time_appconnect}, time_pretransfer: %{time_pretransfer}, time_redirect: %{time_redirect}, time_starttransfer: %{time_starttransfer}, time_total: %{time_total}\n" \
  -X POST "http://k8s-deepseek-deepseek-e92cca8149-b20547a64509f06f.elb.eu-west-1.amazonaws.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "messages": [
      {
        "role": "system", 
        "content": "You are a content moderation system. Analyze the following message and respond with a JSON object containing: {\"action\": \"allow|warn|block|timeout\", \"reason\": \"explanation\", \"confidence\": 0.0-1.0, \"categories\": [\"list of violation types\"]}. Be strict about toxic content."
      },
      {
        "role": "user", 
        "content": "Analyze this message: \"You are the worst human being, you make me sick to my stomach.\""
      }
    ],
    "temperature": 0.1,
    "max_tokens": 500
  }' 

output:
    "prompt_tokens": 93,
    "total_tokens": 536,
    "completion_tokens": 443,
2025-23-07-13-43-09  time_namelookup: 0.001761, time_connect: 0.014193, time_appconnect: 0.000000, time_pretransfer: 0.014266, time_redirect: 0.000000, time_starttransfer: 17.100094, time_total: 17.102291  

DeepSeek R1 - about 19 seconds (includes thinking)
DeepSeek V3 - 42ms
Mistral-7b: 1.849738

# ======= Using DeepSeek - V3 =========
{
  "action": "block",
  "reason": "Message contains extreme personal attacks and dehumanizing language designed to inflict emotional harm. Phrases like 'worst human being' and 'make me sick to my stomach' constitute severe harassment.",
  "confidence": 0.98,
  "categories": ["harassment", "toxicity", "personal_attack", "targeted_hate"],
  "duration_ms": 42
}

# Call the server using curl:
curl -X POST "http://k8s-deepseek-deepseek-e92cca8149-b20547a64509f06f.elb.eu-west-1.amazonaws.com/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "deepseek-ai/DeepSeek-V3",
    "messages": [
      {
        "role": "system", 
        "content": "You are a content moderation system. Analyze the following message and respond with a JSON object containing: {\"action\": \"allow|warn|block|timeout\", \"reason\": \"explanation\", \"confidence\": 0.0-1.0, \"categories\": [\"list of violation types\"]}. Be strict about toxic content."
      },
      {
        "role": "user", 
        "content": "Analyze this message: \"You are the worst human being, you make me sick to my stomach.\""
      }
    ],
    "temperature": 0.1,
    "max_tokens": 500
	}'

# ======= Using Mistral 7B =========

curl -w "time_namelookup: %{time_namelookup}, time_connect: %{time_connect}, time_appconnect: %{time_appconnect}, time_pretransfer: %{time_pretransfer}, time_redirect: %{time_redirect}, time_starttransfer: %{time_starttransfer}, time_total: %{time_total}\n" \
-s http://localhost:8080/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
    "model": "/tmp/models/mistral-7b-v0-2",
    "messages": [
      {
        "role": "user", 
        "content": "You are a content moderation system. Analyze the following message and respond with a JSON object containing: {\"action\": \"allow|warn|block|timeout\", \"reason\": \"explanation\", \"confidence\": 0.0-1.0, \"categories\": [\"list of violation types\"]}. Be strict about toxic content.\n\nAnalyze this message: \"You are the worst human being, you make me sick to my stomach.\""
      }
    ],
    "temperature": 0,
    "max_tokens": 500
}'


curl -w "time_namelookup: %{time_namelookup}, time_connect: %{time_connect}, time_appconnect: %{time_appconnect}, time_pretransfer: %{time_pretransfer}, time_redirect: %{time_redirect}, time_starttransfer: %{time_starttransfer}, time_total: %{time_total}\n" \
-s http://k8s-default-mistralp-267018ac34-e64f9f390a148c7e.elb.us-west-2.amazonaws.com/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
    "model": "/tmp/models/mistral-7b-v0-2",
    "messages": [
      {
        "role": "user", 
        "content": "You are a content moderation system. Analyze the following message and respond with a JSON object containing: {\"action\": \"allow|warn|block|timeout\", \"reason\": \"explanation\", \"confidence\": 0.0-1.0, \"categories\": [\"list of violation types\"]}. Be strict about toxic content.\n\nAnalyze this message: \"You are the worst human being, you make me sick to my stomach.\""
      }
    ],
    "temperature": 0,
    "max_tokens": 500
}'


```
{
  "id": "chatcmpl-6edcd892274d459490ccabff5d42ec9f",
  "object": "chat.completion",
  "created": 1753363894,
  "model": "/tmp/models/mistral-7b-v0-2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "reasoning_content": null,
        "content": " {\"action\": \"warn\", \"reason\": \"This message contains toxic and abusive language towards another person.\", \"confidence\": 0.9, \"categories\": [\"Insults\", \"Toxicity\"]}",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "stop",
      "stop_reason": null
    }
  ],
  "usage": {
    "prompt_tokens": 102,
    "total_tokens": 148,
    "completion_tokens": 46,
    "prompt_tokens_details": null
  },
  "prompt_logprobs": null
}
```

time_namelookup: 0.000019, time_connect: 0.000123, time_appconnect: 0.000000, time_pretransfer: 0.001324, time_redirect: 0.000000, time_starttransfer: 1.849711, time_total: 1.849738