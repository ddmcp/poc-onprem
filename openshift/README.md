# OpenShift Deployment Guide <!-- omit in toc -->

This directory contains OpenShift manifests converted from the Docker Compose project.

## Contents <!-- omit in toc -->

- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Namespace](#namespace)
- [Docker Images Required](#docker-images-required)
- [Update Image References](#update-image-references)
- [Quick Start: Automated Deployment](#quick-start-automated-deployment)
  - [Access Your Applications](#access-your-applications)
- [Advanced: Manual Deployment](#advanced-manual-deployment)
  - [1. Create Namespace](#1-create-namespace)
  - [2. Create ServiceAccount](#2-create-serviceaccount)
  - [3. Create Secrets](#3-create-secrets)
  - [4. Create ConfigMaps](#4-create-configmaps)
  - [5. Create PersistentVolumeClaims](#5-create-persistentvolumeclaims)
  - [6. Deploy Databases](#6-deploy-databases)
  - [7. Deploy Storage and Vector DB](#7-deploy-storage-and-vector-db)
  - [8. Deploy LLM Services](#8-deploy-llm-services)
  - [9. Deploy Airflow Components](#9-deploy-airflow-components)
  - [10. Deploy Application Services](#10-deploy-application-services)
  - [11. Create Routes for External Access](#11-create-routes-for-external-access)
  - [Default Credentials](#default-credentials)
    - [Airflow](#airflow)
    - [MinIO](#minio)
    - [PostgreSQL (Airflow)](#postgresql-airflow)
    - [PostgreSQL (PDF)](#postgresql-pdf)
  - [LLM Provider Configuration](#llm-provider-configuration)
    - [Ollama (Default)](#ollama-default)
    - [OpenAI-Compatible Endpoints](#openai-compatible-endpoints)
    - [Configuration Variables](#configuration-variables)

## Directory Structure

```
openshift/
├── deploy.sh         # Automated deployment script
├── destroy.sh        # Cleanup script
├── secrets/          # Secret configurations for sensitive data
├── configmaps/       # ConfigMaps for application configuration
├── pvcs/             # PersistentVolumeClaims for persistent storage
├── deployments/      # Deployment manifests for all services
├── services/         # Service definitions for internal communication
└── routes/           # Route definitions for external access
```

## Prerequisites

1. Access to an OpenShift cluster
2. `oc` CLI tool installed and configured
3. Docker images built and pushed to a container registry accessible by OpenShift

## Namespace

All resources are deployed in the **poc-onprem** namespace. This namespace will be created as the first step of deployment.

## Docker Images Required

You need to build and push the following Docker images to your container registry:

1. **Airflow** (from root Dockerfile)
   - Build: `docker build -t <your-registry>/airflow:latest .`
   - Push: `docker push <your-registry>/airflow:latest`

2. **Ollama LLM Embedding** (from llm_services/ollama-llm-embedding)
   - Build: `docker build -t <your-registry>/ollama-llm-embedding:latest llm_services/ollama-llm-embedding/`
   - Push: `docker push <your-registry>/ollama-llm-embedding:latest`

3. **Ollama LLM Chat** (from llm_services/ollama-llm-chat)
   - Build: `docker build -t <your-registry>/ollama-llm-chat:latest llm_services/ollama-llm-chat/`
   - Push: `docker push <your-registry>/ollama-llm-chat:latest`

4. **Typing PDF Extractor Service** (from services/typing-pdf-extractor-service)
   - Build: `docker build -t <your-registry>/typing-pdf-extractor-service:latest services/typing-pdf-extractor-service/`
   - Push: `docker push <your-registry>/typing-pdf-extractor-service:latest`

5. **Embedding Service** (from services/embedding-service)
   - Build: `docker build -t <your-registry>/embedding-service:latest services/embedding-service/`
   - Push: `docker push <your-registry>/embedding-service:latest`

6. **Chat Docs Service** (from services/chat-docs-service)
   - Build: `docker build -t <your-registry>/chat-docs-service:latest services/chat-docs-service/`
   - Push: `docker push <your-registry>/chat-docs-service:latest`

7. **Chat Docs UI** (from services/chat-docs-ui)
   - Build: `docker build -t <your-registry>/chat-docs-ui:latest services/chat-docs-ui/`
   - Push: `docker push <your-registry>/chat-docs-ui:latest`

## Update Image References

Before deploying, update all deployment YAML files to reference your container registry:

Replace `<your-registry>` with your actual registry URL in the following files:
- `deployments/airflow-api-server-deployment.yaml`
- `deployments/airflow-scheduler-deployment.yaml`
- `deployments/airflow-dag-processor-deployment.yaml`
- `deployments/ollama-llm-embedding-deployment.yaml`
- `deployments/ollama-llm-chat-deployment.yaml`
- `deployments/typing-pdf-extractor-service-deployment.yaml`
- `deployments/embedding-service-deployment.yaml`
- `deployments/chat-docs-service-deployment.yaml`
- `deployments/chat-docs-ui-deployment.yaml`

## Quick Start: Automated Deployment

The fastest way to deploy is using the automated deployment script:

1. Login to your OpenShift cluster with the CLI:
   ```bash
   oc login <your-cluster-url>
   ````
2. *Optional*: set config variables in `configmaps/services-config.yaml` and `secrets/openai-secrets.yaml` e.g `LLM_PROVIDER, OPENAI_API_BASE_URL, OPENAI_MODEL, CHAT_API_URL, OPENAI_API_KEY`:
   ```bash
   vim configmaps/services-config.yaml
   vim secrets/openai-secrets.yaml
   ```
3. Run deploy script:
   ```bash
   ./deploy.sh
   ```

### Access Your Applications

After deployment completes, the script will display URLs for:
- **Airflow UI** - Workflow orchestration interface (admin/admin)
- **MinIO Console** - Object storage management (minioadmin/minioadmin)
- **Chat Docs UI** - Document chat interface

## Advanced: Manual Deployment

Deploy the resources in the following order to ensure dependencies are met:

### 1. Create Namespace
```bash
oc apply -f namespace.yaml
```

Set the namespace as default for subsequent commands:
```bash
oc project poc-onprem
```

### 2. Create ServiceAccount
```bash
oc apply -f serviceaccount.yaml
oc adm policy add-scc-to-user anyuid -n poc-onprem -z poc-onprem-sa
```

### 3. Create Secrets
```bash
oc apply -f secrets/airflow-secrets.yaml
oc apply -f secrets/postgres-airflow-secrets.yaml
oc apply -f secrets/postgres-pdf-secrets.yaml
oc apply -f secrets/minio-secrets.yaml
```

### 4. Create ConfigMaps
```bash
oc apply -f configmaps/postgres-init-script.yaml
oc apply -f configmaps/airflow-config.yaml
oc apply -f configmaps/services-config.yaml
oc apply -f configmaps/airflow-dags.yaml
```

### 5. Create PersistentVolumeClaims
```bash
oc apply -f pvcs/pg-airflow-db-pvc.yaml
oc apply -f pvcs/pg-typing-pdf-extractor-db-pvc.yaml
oc apply -f pvcs/minio-pvc.yaml
oc apply -f pvcs/qdrant-vector-db-pvc.yaml
oc apply -f pvcs/ollama-llm-embedding-pvc.yaml
oc apply -f pvcs/ollama-llm-chat-pvc.yaml
oc apply -f pvcs/airflow-logs-pvc.yaml
```

Wait for PVCs to be bound:
```bash
oc get pvc -w
```

### 6. Deploy Databases
```bash
oc apply -f deployments/pg-airflow-db-deployment.yaml
oc apply -f deployments/pg-typing-pdf-extractor-db-deployment.yaml
oc apply -f services/pg-airflow-db-service.yaml
oc apply -f services/pg-typing-pdf-extractor-db-service.yaml
```

Wait for databases to be ready:
```bash
oc wait --for=condition=available --timeout=300s deployment/pg-airflow-db
oc wait --for=condition=available --timeout=300s deployment/pg-typing-pdf-extractor-db
```

### 7. Deploy Storage and Vector DB
```bash
oc apply -f deployments/minio-deployment.yaml
oc apply -f deployments/qdrant-vector-db-deployment.yaml
oc apply -f services/minio-service.yaml
oc apply -f services/qdrant-vector-db-service.yaml
```

### 8. Deploy LLM Services
```bash
oc apply -f deployments/ollama-llm-embedding-deployment.yaml
oc apply -f deployments/ollama-llm-chat-deployment.yaml
oc apply -f services/ollama-llm-embedding-service.yaml
oc apply -f services/ollama-llm-chat-service.yaml
```

Wait for LLM services to be ready (this may take several minutes):
```bash
oc wait --for=condition=available --timeout=600s deployment/ollama-llm-embedding
oc wait --for=condition=available --timeout=600s deployment/ollama-llm-chat
```

### 9. Deploy Airflow Components
```bash
oc apply -f deployments/airflow-scheduler-deployment.yaml
oc apply -f deployments/airflow-dag-processor-deployment.yaml
oc apply -f deployments/airflow-api-server-deployment.yaml
oc apply -f services/airflow-api-server-service.yaml
```

### 10. Deploy Application Services
```bash
oc apply -f deployments/typing-pdf-extractor-service-deployment.yaml
oc apply -f deployments/embedding-service-deployment.yaml
oc apply -f deployments/chat-docs-service-deployment.yaml
oc apply -f deployments/chat-docs-ui-deployment.yaml
oc apply -f services/typing-pdf-extractor-service-service.yaml
oc apply -f services/embedding-service-service.yaml
oc apply -f services/chat-docs-service-service.yaml
oc apply -f services/chat-docs-ui-service.yaml
```

### 11. Create Routes for External Access
```bash
oc apply -f routes/airflow-api-server-route.yaml
oc apply -f routes/minio-console-route.yaml
oc apply -f routes/minio-api-route.yaml
oc apply -f routes/chat-docs-ui-route.yaml
```

### Default Credentials

#### Airflow
- Default credentials need to be created after first deployment
- Access the Airflow pod and run: `airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com`

#### MinIO
- Username: `minioadmin`
- Password: `minioadmin`
- **⚠️ Change these in production!** Update `secrets/minio-secrets.yaml`

#### PostgreSQL (Airflow)
- Username: `airflow`
- Password: `airflow`
- Database: `airflow`
- **⚠️ Change these in production!** Update `secrets/postgres-airflow-secrets.yaml`

#### PostgreSQL (PDF)
- Username: `pdfuser`
- Password: `pdfpassword`
- Database: `pdfdb`
- **⚠️ Change these in production!** Update `secrets/postgres-pdf-secrets.yaml`

### LLM Provider Configuration

The chat-docs-service supports two LLM providers:

#### Ollama (Default)
No additional configuration needed. The service will use the Ollama deployment by default.

#### OpenAI-Compatible Endpoints
To use OpenAI or any OpenAI-compatible endpoint:

1. **Update the `openai-secrets.yaml` with your API key:**
   ```bash
   # Edit the secret file
   vi openshift/secrets/openai-secrets.yaml
   # Replace REPLACE_WITH_YOUR_OPENAI_API_KEY with your actual API key
   ```

2. **Update the `services-config.yaml` ConfigMap:**
   ```yaml
   LLM_PROVIDER: "openai-compatible"
   OPENAI_API_BASE_URL: "https://api.openai.com/v1"  # Or your custom endpoint
   OPENAI_MODEL: "gpt-4"  # Or your preferred model
   OPENAI_TEMPERATURE: "0"
   ```

3. **Apply the secret and restart the chat-docs-service:**
   ```bash
   oc apply -f openshift/secrets/openai-secrets.yaml
   oc rollout restart deployment/chat-docs-service -n poc-onprem
   ```

#### Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM provider to use: `ollama` or `openai-compatible` |
| `OPENAI_API_KEY` | - | API key for OpenAI-compatible endpoint (from secret) |
| `OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | Base URL for OpenAI-compatible API |
| `OPENAI_MODEL` | `gpt-4` | Model name to use |
| `OPENAI_TEMPERATURE` | `0` | Temperature for response generation |

**Note:** The `openai-secrets` secret is optional. If not provided, the service will default to using Ollama. This allows existing Ollama-only deployments to continue working without changes.
