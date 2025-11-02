# IIoT-Ollama System Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           IoT Devices / Sensors                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │Vibration │  │ Pressure │  │   Temp   │  │  Custom  │               │
│  │ Sensor   │  │  Sensor  │  │  Sensor  │  │  Sensor  │   ...         │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘               │
└────────┼─────────────┼─────────────┼─────────────┼─────────────────────┘
         │             │             │             │
         └─────────────┴─────────────┴─────────────┘
                            │
                            ▼
         ╔══════════════════════════════════════════╗
         ║   Google Cloud Pub/Sub                   ║
         ║   Topic: iot-data-topic                  ║
         ║   • Ingests IoT sensor data              ║
         ║   • Message buffering                    ║
         ║   • Guaranteed delivery                  ║
         ╚══════════════════╤═══════════════════════╝
                            │
                            ▼
         ╔══════════════════════════════════════════╗
         ║   Push Subscription                      ║
         ║   Name: iot-to-ollama-trigger            ║
         ║   • Auto-triggers Cloud Run              ║
         ║   • Service account auth                 ║
         ║   • 600s ack deadline                    ║
         ╚══════════════════╤═══════════════════════╝
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Google Cloud Run Services                           │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Service: iiot-ollama-processor                                │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  FastAPI Application                                     │  │   │
│  │  │  • Receives Pub/Sub push messages                        │  │   │
│  │  │  • Decodes and validates sensor data                     │  │   │
│  │  │  • Constructs analysis prompts                           │  │   │
│  │  │  • Calls Ollama API                                      │  │   │
│  │  │  • Returns structured analysis                           │  │   │
│  │  └────────────────────┬─────────────────────────────────────┘  │   │
│  │                       │                                         │   │
│  │  Resources: 2 CPU, 4GB RAM                                     │   │
│  │  Scaling: 0-10 instances                                       │   │
│  └───────────────────────┼─────────────────────────────────────────┘   │
│                          │                                             │
│                          │ HTTP Request                                │
│                          ▼                                             │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Service: ollama-ai-inference                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  Ollama Server                                           │  │   │
│  │  │  • Pre-loaded llama3 model                               │  │   │
│  │  │  • Provides LLM inference API                            │  │   │
│  │  │  • Generates analysis from prompts                       │  │   │
│  │  │  • Returns AI-powered insights                           │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  │                                                                 │   │
│  │  Resources: 4 CPU, 8GB RAM (or GPU)                            │   │
│  │  Scaling: 0-10 instances                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ╔══════════════════════════════════════════╗
         ║   Analysis Results                       ║
         ║   • Device identification                ║
         ║   • Anomaly detection                    ║
         ║   • Health assessment                    ║
         ║   • Recommended actions                  ║
         ╚══════════════════════════════════════════╝
                            │
                            ▼
         ┌────────────────────────────────────────┐
         │  Future: Output Pub/Sub Topic           │
         │  (iot-analysis-results)                 │
         └────────────────────────────────────────┘
```

## Data Flow Sequence

```
1. IoT Device → Pub/Sub
   ┌─────────────────────────────────────────────────┐
   │ {                                               │
   │   "device_id": "sensor-001",                    │
   │   "sensor_type": "vibration",                   │
   │   "timestamp": "2024-01-15T10:30:00Z",          │
   │   "measurements": {                             │
   │     "vibration": 92.5,                          │
   │     "temperature": 78.2                         │
   │   }                                             │
   │ }                                               │
   └─────────────────────────────────────────────────┘

2. Pub/Sub → IIoT Processor (Push Subscription)
   ┌─────────────────────────────────────────────────┐
   │ POST / HTTP/1.1                                 │
   │ {                                               │
   │   "message": {                                  │
   │     "data": "eyJkZXZpY2VfaWQiOi4uLn0=",        │
   │     "messageId": "123456",                      │
   │     "publishTime": "2024-01-15T10:30:01Z"       │
   │   }                                             │
   │ }                                               │
   └─────────────────────────────────────────────────┘

3. IIoT Processor → Ollama
   ┌─────────────────────────────────────────────────┐
   │ POST /api/generate HTTP/1.1                     │
   │ {                                               │
   │   "model": "llama3",                            │
   │   "prompt": "Analyze the following IIoT...",    │
   │   "stream": false,                              │
   │   "options": {"temperature": 0.3}               │
   │ }                                               │
   └─────────────────────────────────────────────────┘

4. Ollama → IIoT Processor
   ┌─────────────────────────────────────────────────┐
   │ {                                               │
   │   "response": "Analysis:\n1. Vibration at...",  │
   │   "model": "llama3",                            │
   │   "done": true                                  │
   │ }                                               │
   └─────────────────────────────────────────────────┘

5. IIoT Processor → Pub/Sub (Response)
   ┌─────────────────────────────────────────────────┐
   │ {                                               │
   │   "status": "success",                          │
   │   "message_id": "123456",                       │
   │   "result": {                                   │
   │     "device_id": "sensor-001",                  │
   │     "analysis": "...",                          │
   │     "processed_at": "2024-01-15T10:30:05Z"      │
   │   }                                             │
   │ }                                               │
   └─────────────────────────────────────────────────┘
```

## Component Interaction Matrix

```
┌─────────────────┬──────────┬──────────┬──────────┬─────────┐
│                 │ Pub/Sub  │   IIoT   │  Ollama  │  User   │
│                 │          │Processor │          │         │
├─────────────────┼──────────┼──────────┼──────────┼─────────┤
│ Pub/Sub         │    -     │  Push    │    -     │ Publish │
│                 │          │  Msgs    │          │   Msgs  │
├─────────────────┼──────────┼──────────┼──────────┼─────────┤
│ IIoT Processor  │  Ack/    │    -     │  HTTP    │   -     │
│                 │  Nack    │          │  API     │         │
├─────────────────┼──────────┼──────────┼──────────┼─────────┤
│ Ollama          │    -     │ Response │    -     │   -     │
├─────────────────┼──────────┼──────────┼──────────┼─────────┤
│ User/IoT Device │ Publish  │  HTTP    │    -     │   -     │
│                 │          │ (test)   │          │         │
└─────────────────┴──────────┴──────────┴──────────┴─────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  IAM Service Account: ollama-runner                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Roles Granted:                                           │  │
│  │  • roles/run.invoker      → Invoke Cloud Run services     │  │
│  │  • roles/pubsub.publisher → Publish to Pub/Sub topics     │  │
│  │  • roles/pubsub.subscriber → Subscribe to Pub/Sub topics  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ╔══════════════════════════════════════════╗
         ║   Authentication Flow                    ║
         ║                                          ║
         ║   Pub/Sub → Cloud Run                    ║
         ║   • Service account token                ║
         ║   • OIDC authentication                  ║
         ║   • No public access                     ║
         ║                                          ║
         ║   IIoT Processor → Ollama                ║
         ║   • Internal Cloud Run URL               ║
         ║   • Service account token                ║
         ║   • Private networking                   ║
         ╚══════════════════════════════════════════╝
```

## Scaling Behavior

```
Load Level          Instance Count      Response Time
───────────────────────────────────────────────────────
Idle                     0                   -
Low (1-10 req/min)      1-2              ~2-3s cold
                                         ~0.5s warm
Medium (10-50 req/min)  2-5              ~0.5s
High (50-100 req/min)   5-8              ~0.5-1s
Peak (100+ req/min)     8-10             ~1-2s
```

## Cost Structure

```
Component         Resource Usage        Cost per Request
────────────────────────────────────────────────────────
Pub/Sub           1 message             $0.00004
IIoT Processor    2s @ 2CPU/4GB RAM     $0.00002
Ollama Service    10s @ 4CPU/8GB RAM    $0.00010
Networking        Negligible            $0.00000
────────────────────────────────────────────────────────
Total per Request                       ~$0.00016

Monthly (1M requests)                   ~$160
```

## File Structure

```
.
├── Dockerfile.ollama              # Ollama LLM service container
├── Dockerfile.iiot-ollama         # IIoT processor container
├── iiot_ollama_service.py         # FastAPI application
├── iot_data_generator.py          # Testing data generator
├── requirements-iiot-ollama.txt   # Python dependencies
│
├── cloudbuild.ollama.yaml         # Build config for Ollama
├── cloudbuild.iiot-ollama.yaml    # Build config for IIoT processor
│
├── setup-iiot-pubsub.sh           # Infrastructure setup
├── deploy-iiot-ollama.sh          # Complete deployment
├── test-iiot-ollama.sh            # Automated testing
│
├── IIOT_OLLAMA_INTEGRATION.md     # Main documentation (bilingual)
├── IIOT_OLLAMA_QUICKSTART.md      # Quick start guide
├── IIOT_EXAMPLE_PAYLOADS.md       # Example data and tests
├── IMPLEMENTATION_SUMMARY.md      # This summary
└── ARCHITECTURE_DIAGRAM.md        # Architecture diagrams (this file)
```

---

**Legend:**
- `═══` Strong boundary (service/infrastructure)
- `───` Weak boundary (logical grouping)
- `│ ▼` Data flow direction
- `┌─┐` Component box
