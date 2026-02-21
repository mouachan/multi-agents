# Qwen-VL 7B Multimodal Model Deployment

This directory contains OpenShift manifests to deploy **Qwen2.5-VL-7B-Instruct-FP8-Dynamic**, a multimodal vision-language model used for OCR (Optical Character Recognition) in the Claims Processing demo.

## Model Information

- **Model ID**: `RedHatAI/Qwen2.5-VL-7B-Instruct-FP8-Dynamic`
- **Model Type**: Multimodal Vision-Language Model
- **Size**: ~30GB (FP8 quantized)
- **Context Window**: 8192 tokens
- **Use Case**: Document OCR, image understanding, visual question answering
- **GPU Requirements**: 1x NVIDIA L40 (or equivalent with 24GB+ VRAM)

## Architecture

```
┌─────────────────────────────────────────────┐
│         OCR MCP Server                      │
│  (backend/mcp_servers/ocr_server)           │
└──────────────┬──────────────────────────────┘
               │
               ↓ HTTP REST API
┌──────────────────────────────────────────────┐
│    Qwen-VL 7B InferenceService               │
│    (vLLM serving with OpenAI API)            │
└──────────────┬───────────────────────────────┘
               │
               ↓ Mounted PVC
┌──────────────────────────────────────────────┐
│    PVC (50Gi)                                │
│    Model files from HuggingFace              │
└──────────────────────────────────────────────┘
```

## Deployment Steps

### Prerequisites

1. **OpenShift AI 3.0** installed with KServe
2. **GPU nodes** available (NVIDIA L40 or similar)
3. **HuggingFace token** with read access to gated models
4. **Storage class** supporting ReadWriteOnce (e.g., `gp3-csi`)

### Step 1: Update Placeholders

Edit all YAML files and replace the following placeholders:

- `namespace: multimodal-demo` → Your target namespace
- `storageClassName: gp3-csi` → Your storage class
- `topology.kubernetes.io/zone: eu-central-1a` → Your availability zone
- `value: NVIDIA-L40-PRIVATE` → Your GPU node label
- `token: "hf_XXXXXXXX..."` → Your HuggingFace token

### Step 2: Create Namespace (if needed)

```bash
oc new-project multimodal-demo
```

### Step 3: Deploy Resources in Order

**3.1 Create PVC for model storage**
```bash
oc apply -f 01-pvc.yaml
```

**3.2 Create HuggingFace secret**
```bash
# Edit the file first to add your token!
oc apply -f 02-secret-hf-token.yaml
```

**3.3 Download the model**
```bash
oc apply -f 03-model-download-job.yaml

# Monitor the download (takes ~5-10 minutes)
oc logs -f job/download-qwen-model

# Verify completion
oc get job download-qwen-model
```

**3.4 Create ServingRuntime**
```bash
oc apply -f 04-servingruntime.yaml
```

**3.5 Deploy InferenceService**
```bash
oc apply -f 05-inferenceservice.yaml

# Wait for model to load (takes ~2-3 minutes)
oc wait --for=condition=ready pod -l serving.kserve.io/inferenceservice=qwen-vl-7b --timeout=600s
```

### Step 4: Verify Deployment

**Check InferenceService status**
```bash
oc get inferenceservice qwen-vl-7b
```

Expected output:
```
NAME         URL                                                                  READY   PREV   LATEST   ...
qwen-vl-7b   https://qwen-vl-7b-multimodal-demo.apps.cluster.example.com         True
```

**Test the model**
```bash
# Get the internal service URL
QWEN_URL="http://qwen-vl-7b-predictor.multimodal-demo.svc.cluster.local:80/v1"

# Test with a simple prompt (from inside the cluster)
oc run test-qwen --rm -i --restart=Never --image=curlimages/curl -- \
  curl -X POST "${QWEN_URL}/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-vl-7b",
    "messages": [
      {
        "role": "user",
        "content": "Describe this image: https://example.com/sample.jpg"
      }
    ]
  }'
```

### Step 5: Configure OCR MCP Server

Update the OCR server environment variable to point to Qwen-VL:

```yaml
# In openshift/deployments/ocr-server-deployment.yaml
env:
- name: QWEN_VL_ENDPOINT
  value: "http://qwen-vl-7b-predictor.multimodal-demo.svc.cluster.local:80/v1"
```

## Model Capabilities

Qwen-VL 7B excels at:

1. **Document OCR**: Extracting text from scanned documents, forms, receipts
2. **Layout Understanding**: Recognizing document structure (tables, columns, sections)
3. **Handwriting Recognition**: Reading handwritten text
4. **Multi-language Support**: OCR in multiple languages
5. **Visual Question Answering**: Understanding and describing image content

## Resource Requirements

| Component | CPU | Memory | GPU | Storage |
|-----------|-----|--------|-----|---------|
| Model Download Job | 2-4 cores | 4-8Gi | None | 50Gi PVC |
| InferenceService | 2 cores | 4Gi | 1x L40 | 50Gi PVC (shared) |

## Troubleshooting

### Job fails to download model

**Error**: `HF_TOKEN environment variable is not set`

**Solution**: Verify the secret exists and contains a valid token:
```bash
oc get secret huggingface-token -o yaml
echo "<base64-token>" | base64 -d
```

### InferenceService pod CrashLoopBackOff

**Error**: `CUDA out of memory`

**Solution**: Reduce GPU memory utilization:
```yaml
args:
- --gpu-memory-utilization
- "0.75"  # Reduce from 0.85
```

### Model not responding

**Error**: Timeout or 504 errors

**Solution**: Check model loading logs:
```bash
oc logs -l serving.kserve.io/inferenceservice=qwen-vl-7b --tail=100
```

Model loading takes 2-3 minutes. Wait for "Application startup complete" message.

### OCR server cannot connect to Qwen-VL

**Error**: `Cannot connect to Qwen-VL service`

**Solution**: Verify the service endpoint:
```bash
oc get svc qwen-vl-7b-predictor
oc get route qwen-vl-7b  # Should show external URL
```

Update `QWEN_VL_ENDPOINT` in OCR server deployment to match the actual service name.

## Performance Tuning

### Increase Throughput

For higher concurrency:
```yaml
spec:
  predictor:
    minReplicas: 2  # Scale horizontally
    maxReplicas: 5
```

### Reduce Latency

For faster inference:
```yaml
args:
- --max-model-len
- "4096"  # Reduce context window
- --gpu-memory-utilization
- "0.95"  # Use more GPU memory for larger batch sizes
```

## Integration with Multi-Agent AI Platform

The OCR MCP Server (`backend/mcp_servers/ocr_server/server.py`) uses Qwen-VL for:

1. **PDF Processing**: Convert PDF pages to images, then OCR with Qwen-VL
2. **Image OCR**: Direct text extraction from JPG, PNG, TIFF images
3. **Structured Extraction**: Parse claim forms, invoices, medical records
4. **Confidence Scoring**: Qwen-VL provides high-confidence OCR results (~0.9)

Example OCR call:
```python
response = await client.post(
    f"{QWEN_VL_ENDPOINT}/chat/completions",
    json={
        "model": "qwen-vl-7b",
        "messages": [{
            "role": "user",
            "content": f"Extract all text from this insurance claim document: {image_url}"
        }]
    }
)
```

## References

- **Model Card**: https://huggingface.co/RedHatAI/Qwen2.5-VL-7B-Instruct-FP8-Dynamic
- **vLLM Documentation**: https://docs.vllm.ai/
- **KServe Documentation**: https://kserve.github.io/website/
- **OpenShift AI Documentation**: https://access.redhat.com/documentation/en-us/red_hat_openshift_ai/
