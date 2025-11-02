# AI Worker Deployment Options

## Problem: Cloud Run Startup Timeout

The ai-worker service contains 3+ GB of ML libraries (TensorFlow 475MB, PyTorch 670MB, NVIDIA CUDA libraries 2.2GB, etc.) that must be loaded into memory before the container can respond to health checks.

**Cloud Run Timeout:** ~240 seconds  
**Actual Startup Time:** >300 seconds (even with optimizations)

After **five deployment attempts** with progressive optimizations:
1. ✅ Fixed LSTM async methods
2. ✅ Moved service instantiation to startup event
3. ✅ Increased CPU (2→4) and memory (2Gi→4Gi)
4. ✅ Removed all heavy imports from module level
5. ✅ Implemented background service loading with instant health check response

**Result:** Still timing out due to fundamental mismatch between Cloud Run's instant-start expectations and ML service startup requirements.

---

## Solution 1: Cloud Run with Min-Instances (Quick Fix)

Keep a warm instance running to avoid cold starts.

### Pros
- ✅ Minimal code changes
- ✅ Immediate deployment
- ✅ Works with current codebase

### Cons
- ❌ Costs $30-50/month even with zero traffic
- ❌ Doesn't scale to zero
- ❌ First request still slow if min-instance is busy

### Deploy Command
```powershell
cd ai-worker
gcloud builds submit --config=cloudbuild-min-instances.yaml --project=refined-graph-471712-n9 --timeout=30m
```

### Configuration (cloudbuild-min-instances.yaml)
```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/omni-ai-worker:latest', '.']
  
  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/omni-ai-worker:latest']
  
  # Deploy to Cloud Run with min-instances
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    args:
      - gcloud
      - run
      - deploy
      - omni-ai-worker
      - --image=gcr.io/$PROJECT_ID/omni-ai-worker:latest
      - --platform=managed
      - --region=europe-west1
      - --memory=4Gi
      - --cpu=4
      - --timeout=300
      - --min-instances=1          # Keep 1 instance always warm
      - --max-instances=10
      - --set-env-vars=CUDA_VISIBLE_DEVICES=-1,TF_FORCE_CPU=1,HF_HUB_DISABLE_TELEMETRY=1
      - --allow-unauthenticated

timeout: 1800s
```

**Estimated Cost:** ~$40/month for 1 always-on instance with 4CPU/4Gi memory.

---

## Solution 2: Split Architecture (Recommended for Production)

Separate lightweight API gateway from heavy ML workers.

### Architecture
```
Client → Cloud Run (Gateway) → Cloud Run/GKE (ML Workers)
```

### Components

**1. Lightweight Gateway (Cloud Run)**
- FastAPI with only routing, auth, and request validation
- No ML libraries, instant startup
- Proxies requests to ML workers
- ~50MB container, responds in <1s

**2. Heavy ML Workers (Cloud Run with min-instances OR GKE)**
- All current ai-worker ML services
- Runs behind gateway, not publicly exposed
- Can have longer startup times (not first-responder)
- Load-balanced across multiple instances

### Pros
- ✅ Gateway scales to zero (no idle costs)
- ✅ ML workers can be Cloud Run (min-instances) or GKE
- ✅ Better separation of concerns
- ✅ Gateway responds instantly
- ✅ Can independently scale gateway vs. workers

### Cons
- ❌ Requires code refactoring
- ❌ More complex deployment
- ❌ Extra network hop (adds ~20-50ms latency)

### Implementation Steps
1. Create `gateway/` service:
   - FastAPI with routes
   - Auth middleware
   - Metrics endpoint
   - HTTP client to forward requests to workers
   
2. Modify `ai-worker/` to accept internal requests
   - Remove public auth (gateway handles it)
   - Keep only ML endpoints
   
3. Deploy gateway to Cloud Run (no min-instances needed)
4. Deploy ai-worker to Cloud Run with min-instances=1 or GKE

**Estimated Time:** 2-3 hours  
**Estimated Cost:** $40/month (ML workers) + $0/month (gateway scales to zero)

---

## Solution 3: Migrate to GKE Autopilot (Best for Scale)

Deploy to Google Kubernetes Engine with no startup time restrictions.

### Pros
- ✅ No startup timeout limits
- ✅ Production-grade orchestration
- ✅ Better for stateful services
- ✅ Can use preemptible nodes for cost savings
- ✅ Advanced scaling, health checks, rollouts

### Cons
- ❌ More complex setup (Kubernetes manifests)
- ❌ Steeper learning curve
- ❌ Higher minimum cost (~$50-70/month)

### Deploy Command
```bash
# Create GKE Autopilot cluster (one-time)
gcloud container clusters create-auto omni-cluster \
  --region=europe-west1 \
  --project=refined-graph-471712-n9

# Apply Kubernetes manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### Required Files
- `k8s/deployment.yaml` - Pod spec with ai-worker container
- `k8s/service.yaml` - LoadBalancer service
- `k8s/ingress.yaml` - Ingress with Cloud Load Balancer

**Estimated Time:** 3-4 hours  
**Estimated Cost:** $50-70/month for Autopilot cluster

---

## Solution 4: Serverless with Longer Timeout

Use Cloud Functions 2nd gen or Cloud Run with extended startup period.

### Cloud Run 2nd Gen Execution Environment
- Supports longer startup periods
- Can set custom readiness/liveness probes
- Better for CPU-intensive workloads

### Configuration
```yaml
# Add to cloudbuild.yaml
--execution-environment=gen2
--startup-cpu-boost  # Extra CPU during startup
```

### Pros
- ✅ Stays on Cloud Run
- ✅ Minor configuration changes

### Cons
- ❌ Still has limits (may not solve 300s+ startup)
- ❌ Less predictable than min-instances

---

## Immediate Recommendation

**For today:** Deploy with **Solution 1 (min-instances)** to get service live.  
**For next week:** Plan migration to **Solution 2 (Split Architecture)** for cost optimization.

### Deploy Now (Solution 1)
```powershell
cd c:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform\omni-enterprise-ultra-max\ai-worker

# Create cloudbuild-min-instances.yaml (see above)
# Then deploy:
gcloud builds submit --config=cloudbuild-min-instances.yaml --project=refined-graph-471712-n9 --timeout=30m
```

This will keep 1 warm instance running, eliminating cold start issues. Once live, you can:
- ✅ Test all Tier 1 features (Prometheus, Auth, Sentry, Logging)
- ✅ Run tier1_tests.py
- ✅ Validate production readiness
- ⏳ Plan migration to split architecture to eliminate idle costs

---

## Cost Comparison

| Solution | Monthly Cost | Latency | Complexity | Scalability |
|----------|-------------|---------|------------|-------------|
| Min-Instances | $40 | 50-200ms | Low | Good |
| Split Architecture | $40 | 70-250ms | Medium | Excellent |
| GKE Autopilot | $60 | 50-200ms | High | Excellent |
| Current (broken) | $0 | N/A | Low | None |

**Winner:** Min-instances now → Split architecture later.
