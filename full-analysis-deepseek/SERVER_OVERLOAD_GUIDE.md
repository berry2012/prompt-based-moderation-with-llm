# Server Overload Management Guide

## 🚨 Problem Identification

### Symptoms Observed:
```
Mistral-7B Logs:
- GPU KV cache usage: 100.0%
- Running: 4 reqs, Pending: 36 reqs
- Aborted requests: chatcmpl-xxx
- Low generation throughput: 6.3 tokens/s

Chat Simulator Logs:
- MCP request timeout errors
- HTTP requests failing
```

### Root Cause:
The Mistral-7B LLM server on Kubernetes is overwhelmed with requests, causing a cascade of failures throughout the moderation system.

## 🛠️ Immediate Solutions

### 1. **Check System Status**
```bash
# Quick health check
python manage_server_overload.py

# Manual health checks
curl http://localhost:8002/health
curl http://localhost:8000/health
```

### 2. **Wait for Recovery (Recommended)**
```bash
# Use the management script to wait for recovery
python manage_server_overload.py
# Choose option 1: Wait for server recovery
```

**Expected Recovery Time:** 10-30 minutes depending on queue size

### 3. **Run Ultra-Conservative Analysis**
```bash
# Test with minimal load
python test_overloaded_server.py

# Run safe analysis with tiny sample
python manage_server_overload.py
# Choose option 2: Run safe minimal analysis
```

## ⚙️ Updated Analysis Settings

### Ultra-Conservative Settings (For Overloaded Server):
```python
# Model Evaluation
request_delay = 15.0 seconds    # vs 2.0s normal
timeout = 120.0 seconds         # vs 45s normal  
max_retries = 2                 # vs 5 normal
batch_delay = 60.0 seconds      # vs 5s normal
sample_size = 3-5 messages      # vs 50+ normal

# Experimental Design  
request_delay = 15.0 seconds
timeout = 120.0 seconds
max_retries = 2
batch_delay = 60.0 seconds
max_batch_size = 3              # vs 10+ normal
```

### Analysis Scripts Updated:
- ✅ `model_evaluation_real.py` - Ultra-conservative settings
- ✅ `experimental_design_real.py` - Ultra-conservative settings  
- ✅ `test_overloaded_server.py` - Specialized overload testing
- ✅ `manage_server_overload.py` - Comprehensive management

## 🔧 Long-term Solutions

### 1. **Scale Mistral-7B Resources**
```bash
# Increase GPU memory allocation
kubectl edit deployment mistral-7b-deployment

# Add more replicas
kubectl scale deployment mistral-7b-deployment --replicas=3
```

### 2. **Implement Request Queuing**
- Add request rate limiting in Chat Simulator
- Implement backpressure mechanisms
- Add circuit breaker patterns

### 3. **Optimize Model Configuration**
```yaml
# Reduce concurrent requests
max_concurrent_requests: 2  # vs 4+ current

# Increase timeout settings
request_timeout: 180s

# Enable request batching
enable_batching: true
max_batch_size: 4
```

### 4. **Consider Alternative Models**
- Use smaller model temporarily (e.g., Mistral-7B-Instruct-v0.1)
- Implement model switching based on load
- Use quantized models to reduce memory usage

## 📊 Monitoring Commands

### Check Kubernetes Resources:
```bash
# Check pod status
kubectl get pods -l app=mistral-7b

# Check resource usage
kubectl top pods -l app=mistral-7b

# Check logs
kubectl logs -l app=mistral-7b --tail=50
```

### Check Docker Services:
```bash
# Check container status
docker-compose ps

# Check resource usage
docker stats

# Check logs
docker-compose logs mcp-server
docker-compose logs chat-simulator
```

## 🎯 Analysis Strategy During Overload

### Phase 1: Assessment (5 minutes)
```bash
python manage_server_overload.py
# Check system health and get recommendations
```

### Phase 2: Recovery Wait (10-30 minutes)
```bash
# Wait for natural recovery
python manage_server_overload.py
# Choose option 1: Wait for server recovery
```

### Phase 3: Minimal Testing (5-10 minutes)
```bash
# Test with 3-5 messages only
python test_overloaded_server.py
```

### Phase 4: Gradual Scale-up
```bash
# If minimal test succeeds, try larger samples
python model_evaluation_real.py  # Will use ultra-conservative settings
```

## ⚠️ What NOT to Do During Overload

❌ **Don't run multiple analysis scripts simultaneously**
❌ **Don't use large sample sizes (>10 messages)**
❌ **Don't reduce timeouts or delays**
❌ **Don't increase retry attempts**
❌ **Don't restart services repeatedly**

## ✅ Best Practices

✅ **Wait for natural recovery first**
✅ **Use ultra-conservative settings**
✅ **Test with single requests before batches**
✅ **Monitor system health continuously**
✅ **Scale analysis based on server capacity**

## 🆘 Emergency Actions

If system is completely unresponsive:

```bash
# 1. Stop all analysis scripts
pkill -f python

# 2. Restart Docker services
docker-compose restart

# 3. Wait 5 minutes for stabilization
sleep 300

# 4. Check health
curl http://localhost:8002/health

# 5. If still failing, full restart
docker-compose down
docker-compose up -d
```

## 📞 Support Information

**System Architecture:**
- Chat Simulator (Port 8002) → MCP Server (Port 8000) → Mistral-7B (EKS)

**Key Endpoints:**
- Chat Simulator API: `http://localhost:8002/api/send-message`
- Health Checks: `http://localhost:8002/health`, `http://localhost:8000/health`

**Log Locations:**
- Docker: `docker-compose logs [service]`
- Kubernetes: `kubectl logs -l app=mistral-7b`
- Analysis: `./logs/` directory

---
*This guide addresses the specific server overload issues observed during dissertation analysis.*
