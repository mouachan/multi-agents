# Llama 3.3 70B INT8 Deployment

Déploiement de Llama 3.3 70B avec quantization INT8 (w8a8) sur 4x NVIDIA L4 GPU.

## Caractéristiques

- **Modèle**: [RedHatAI/Llama-3.3-70B-Instruct-quantized.w8a8](https://huggingface.co/RedHatAI/Llama-3.3-70B-Instruct-quantized.w8a8)
- **Quantization**: INT8 (w8a8) - ~70GB
- **GPU**: 4x NVIDIA L4 (23GB chacun = 92GB total)
- **Tensor Parallel**: 4 GPUs
- **Fonctionnalités**: Supporte les appels d'outils parallèles (contrairement à Llama 3.2 3B)

## Prérequis

1. Cluster OpenShift avec 4 GPU L4 disponibles
2. Secret HuggingFace token configuré (copié depuis `llama-instruct-32-3b-demo`)
3. StorageClass `gp3-csi` disponible

## Déploiement

### Étape 1: Créer le namespace et copier le secret

```bash
# Créer le namespace
oc apply -f namespace.yaml

# Copier le secret HuggingFace depuis l'ancien namespace
oc get secret huggingface-token -n llama-instruct-32-3b-demo -o yaml | \
  sed 's/namespace: llama-instruct-32-3b-demo/namespace: llama-3-3-70B/' | \
  oc apply -f -
```

### Étape 2: Créer le PVC

```bash
oc apply -f pvc.yaml
```

### Étape 3: Télécharger le modèle

```bash
# Lancer le job de download (peut prendre 30-60 min pour ~70GB)
oc apply -f download-job.yaml

# Suivre les logs
oc logs -f job/download-llama-3-3-70B-hf-cli -n llama-3-3-70B

# Vérifier le statut
oc get job -n llama-3-3-70B
```

### Étape 4: Déployer le ServingRuntime et InferenceService

```bash
# Créer le ServingRuntime vLLM
oc apply -f serving-runtime.yaml

# Créer l'InferenceService
oc apply -f inference-service.yaml

# Vérifier le déploiement
oc get inferenceservice -n llama-3-3-70B
oc get pods -n llama-3-3-70B
```

### Étape 5: Tester le modèle

```bash
# Récupérer l'URL du service
LLAMA_URL=$(oc get inferenceservice llama-3-3-70B -n llama-3-3-70B -o jsonpath='{.status.url}')

# Test simple
curl -X POST "${LLAMA_URL}/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3-3-70B",
    "prompt": "Hello, how are you?",
    "max_tokens": 50
  }'

# Test avec tool calling parallèle
curl -X POST "${LLAMA_URL}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3-3-70B",
    "messages": [
      {"role": "user", "content": "What is the weather in Paris and New York?"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get weather for a city",
          "parameters": {
            "type": "object",
            "properties": {
              "city": {"type": "string"}
            },
            "required": ["city"]
          }
        }
      }
    ]
  }'
```

## Configuration vLLM

Le modèle est configuré avec:

- `--tensor-parallel-size 4`: Distribution sur 4 GPU
- `--gpu-memory-utilization 0.9`: Utilisation 90% VRAM
- `--dtype=auto`: Détection automatique (INT8)
- `--max-model-len 32768`: Context 32k tokens
- `--enable-auto-tool-choice`: Appels d'outils parallèles activés
- `--tool-call-parser llama3_json`: Parser pour Llama 3

## Monitoring

```bash
# Logs du pod predictor
oc logs -f deployment/llama-3-3-70B-predictor -n llama-3-3-70B

# Utilisation GPU
oc exec -it deployment/llama-3-3-70B-predictor -n llama-3-3-70B -- nvidia-smi

# Métriques
oc port-forward -n llama-3-3-70B service/llama-3-3-70B-metrics 8080:8080
# Puis accéder à http://localhost:8080/metrics
```

## Mise à jour LlamaStack

Pour pointer LlamaStack vers ce nouveau modèle:

```yaml
# Dans openshift/configmaps/llamastack-config.yaml
providers:
  inference:
    - provider_id: vllm-inference-1
      provider_type: remote::vllm
      config:
        url: "http://llama-3-3-70B-predictor.llama-3-3-70B.svc.cluster.local/v1"
```

## Cleanup

```bash
# Supprimer l'InferenceService
oc delete -f inference-service.yaml

# Supprimer le ServingRuntime
oc delete -f serving-runtime.yaml

# (Optionnel) Supprimer le PVC et les données
oc delete -f pvc.yaml

# (Optionnel) Supprimer le namespace complet
oc delete namespace llama-3-3-70B
```

## Troubleshooting

### Le pod ne démarre pas (Pending)

Vérifier les GPU disponibles:
```bash
oc describe nodes | grep -A 5 "nvidia.com/gpu"
```

### Out of Memory (OOM)

Réduire `--gpu-memory-utilization` à 0.8 ou réduire `--max-model-len`

### Download job échoue

Vérifier le secret HuggingFace:
```bash
oc get secret huggingface-token -n llama-3-3-70B -o jsonpath='{.data.token}' | base64 -d
```

## Ressources

- [Llama 3.3 Model Card](https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_3/)
- [vLLM Documentation](https://docs.vllm.ai/)
- [RedHat AI Model](https://huggingface.co/RedHatAI/Llama-3.3-70B-Instruct-quantized.w8a8)
