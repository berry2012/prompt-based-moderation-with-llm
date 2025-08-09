# Using Mistral 


https://huggingface.co/aws-neuron/Mistral-7B-Instruct-v0.2-seqlen-2048-bs-1-cores-2?local-app=vllm



```bash
# Deploy with docker on Linux:
docker run --runtime nvidia --gpus all \
	--name my_vllm_container \
	-v ~/.cache/huggingface:/root/.cache/huggingface \
 	--env "HUGGING_FACE_HUB_TOKEN=<secret>" \
	-p 8000:8000 \
	--ipc=host \
	vllm/vllm-openai:latest \
	--model aws-neuron/Mistral-7B-Instruct-v0.2-seqlen-2048-bs-1-cores-2
```    


```bash
# Load and run the model:
docker exec -it my_vllm_container bash -c "vllm serve aws-neuron/Mistral-7B-Instruct-v0.2-seqlen-2048-bs-1-cores-2"
```


```bash
# Call the server using curl:
curl -X POST "http://localhost:8000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "aws-neuron/Mistral-7B-Instruct-v0.2-seqlen-2048-bs-1-cores-2",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'
```


## Optimizing deployment

- Pre-download model weights and store in Storage like Amazon FSx Lustre
- Use init container with vllm container 

```bash
curl -s http://localhost:8080/v1/completions \
-H "Content-Type: application/json" \
-d '{
    "model": "/tmp/models/mistral-7b-v0-2",
    "prompt": "San Francisco is a",
    "max_tokens": 7,
    "temperature": 0
}' | jq
```

## Alternatively for chat

```bash
curl -s http://localhost:8080/v1/chat/completions \
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
}' | jq

```

## Investigate timings

```bash
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
```