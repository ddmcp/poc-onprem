# OpenShift Deployment Guide

This directory contains OpenShift manifests converted from the Docker Compose project.

## Directory Structure

```
openshift/
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

## Deployment Order

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

**Note:** Airflow DAGs are loaded from a ConfigMap (airflow-dags), not from a PVC.

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

## Quick Deploy All

Alternatively, deploy everything at once (not recommended for first-time deployment):

```bash
# Deploy in order
oc apply -f namespace.yaml
oc project poc-onprem
oc apply -f serviceaccount.yaml
oc apply -f secrets/
oc apply -f configmaps/
oc apply -f pvcs/
# Wait for PVCs to be bound
oc get pvc -w
# Then deploy the rest
oc apply -f deployments/
oc apply -f services/
oc apply -f routes/
```

## Accessing the Applications

After deployment, get the route URLs:

```bash
# Airflow Web UI
oc get route airflow-api-server -o jsonpath='{.spec.host}'

# MinIO Console
oc get route minio-console -o jsonpath='{.spec.host}'

# Chat Docs UI
oc get route chat-docs-ui -o jsonpath='{.spec.host}'
```

## Default Credentials

### Airflow
- Default credentials need to be created after first deployment
- Access the Airflow pod and run: `airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com`

### MinIO
- Username: `minioadmin`
- Password: `minioadmin`
- **⚠️ Change these in production!** Update `secrets/minio-secrets.yaml`

### PostgreSQL (Airflow)
- Username: `airflow`
- Password: `airflow`
- Database: `airflow`
- **⚠️ Change these in production!** Update `secrets/postgres-airflow-secrets.yaml`

### PostgreSQL (PDF)
- Username: `pdfuser`
- Password: `pdfpassword`
- Database: `pdfdb`
- **⚠️ Change these in production!** Update `secrets/postgres-pdf-secrets.yaml`

## Monitoring Deployment

Check the status of all deployments:
```bash
oc get deployments
oc get pods
oc get services
oc get routes
```

View logs for a specific pod:
```bash
oc logs -f deployment/<deployment-name>
```

## Persistent Storage

All stateful services use PersistentVolumeClaims (PVCs) for data persistence:

| PVC Name                       | Size | Access Mode   | Used By                           |
| ------------------------------ | ---- | ------------- | --------------------------------- |
| pg-airflow-db-pvc              | 10Gi | ReadWriteOnce | Airflow PostgreSQL database       |
| pg-typing-pdf-extractor-db-pvc | 20Gi | ReadWriteOnce | PDF PostgreSQL database           |
| minio-pvc                      | 50Gi | ReadWriteOnce | MinIO object storage              |
| qdrant-vector-db-pvc           | 30Gi | ReadWriteOnce | Qdrant vector database            |
| ollama-llm-embedding-pvc       | 10Gi | ReadWriteOnce | Ollama embedding model data       |
| ollama-llm-chat-pvc            | 10Gi | ReadWriteOnce | Ollama chat model data            |
| airflow-logs-pvc               | 10Gi | ReadWriteMany | Airflow logs (shared across pods) |

**Note:** The PVCs use the default StorageClass in your OpenShift cluster. If you need to use a specific StorageClass, add `storageClassName: <your-storage-class>` to each PVC spec.

**Important:** Airflow logs use ReadWriteMany (RWX) access mode because they need to be shared across multiple Airflow pods (scheduler, dag-processor, and api-server). Ensure your cluster has a StorageClass that supports RWX access mode (e.g., NFS, CephFS, or GlusterFS).

## Airflow DAGs

Airflow DAG files are loaded from a ConfigMap (`airflow-dags`) rather than a PVC. This approach:
- Makes DAG updates easier (update ConfigMap and restart pods)
- Eliminates the need for RWX storage for DAGs
- Ensures all Airflow pods have the same DAG files

The ConfigMap contains all three DAG files:
- `debug_example_dag.py` - Simple test DAG
- `minio_pdf_extract_chunks_to_pg_dag.py` - PDF extraction pipeline
- `pg_chunks_to_vectors_dag.py` - Vector embedding pipeline

To update DAGs, edit the ConfigMap and restart the Airflow pods:
```bash
oc edit configmap airflow-dags
oc rollout restart deployment/airflow-scheduler
oc rollout restart deployment/airflow-dag-processor
oc rollout restart deployment/airflow-api-server
```

## Troubleshooting

### Pods not starting
```bash
oc describe pod <pod-name>
oc logs <pod-name>
```

### Database connection issues
- Verify secrets are created correctly
- Check service names match the connection strings in ConfigMaps
- Ensure databases are ready before dependent services start

### Image pull errors
- Verify image names and tags are correct
- Ensure OpenShift has access to your container registry
- Create image pull secrets if using a private registry

### Resource constraints
- Check if pods are being evicted due to resource limits
- Adjust resource requests/limits in deployment manifests
- The Ollama LLM services require significant memory (6-10GB)

## Cleanup

To remove all resources:
```bash
oc delete -f routes/
oc delete -f services/
oc delete -f deployments/
oc delete -f configmaps/
oc delete -f secrets/
```

## Security Considerations

1. **Change default passwords** in all secret files before production deployment
2. **Use proper RBAC** - create service accounts with minimal required permissions
3. **Enable network policies** to restrict pod-to-pod communication
4. **Use encrypted secrets** - consider using sealed secrets or external secret management
5. **Implement resource quotas** to prevent resource exhaustion
6. **Enable pod security policies** or pod security standards
7. **Use TLS** for all external routes (already configured)
8. **Scan container images** for vulnerabilities before deployment

## Notes

- DAGs need to be mounted or copied into Airflow pods (currently using emptyDir)
- Consider using a Git repository or ConfigMap for DAG files
- The init container in airflow-api-server runs database migrations
- Health checks are configured for critical services
- Debug port (5679) is exposed for chat-docs-service for development purposes