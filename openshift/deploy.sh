#!/bin/bash
set -e

echo "🚀 Starting OpenShift Deployment for poc-onprem..."
echo "=================================================="

# 1. Create Namespace
echo "📁 Creating namespace..."
oc apply -f namespace.yaml
oc project poc-onprem

# 2. Create ServiceAccount with SCC
echo "👤 Creating ServiceAccount and applying SCC..."
oc apply -f serviceaccount.yaml
oc adm policy add-scc-to-user anyuid -n poc-onprem -z poc-onprem-sa

# 3. Create Secrets
echo "🔐 Creating secrets..."
oc apply -f secrets/airflow-secrets.yaml
oc apply -f secrets/postgres-airflow-secrets.yaml
oc apply -f secrets/postgres-pdf-secrets.yaml
oc apply -f secrets/minio-secrets.yaml
oc apply -f secrets/openai-secrets.yaml

# 4. Create ConfigMaps
echo "⚙️  Creating ConfigMaps..."
oc apply -f configmaps/postgres-init-script.yaml
oc apply -f configmaps/airflow-config.yaml
oc apply -f configmaps/services-config.yaml
oc apply -f configmaps/airflow-dags.yaml

# 5. Create PVCs
echo "💾 Creating PersistentVolumeClaims..."
oc apply -f pvcs/pg-airflow-db-pvc.yaml
oc apply -f pvcs/pg-typing-pdf-extractor-db-pvc.yaml
oc apply -f pvcs/minio-pvc.yaml
oc apply -f pvcs/qdrant-vector-db-pvc.yaml
oc apply -f pvcs/ollama-llm-embedding-pvc.yaml
oc apply -f pvcs/ollama-llm-chat-pvc.yaml
oc apply -f pvcs/airflow-logs-pvc.yaml
oc apply -f pvcs/airflow-dags-pvc.yaml

echo "⏳ Waiting for PVCs to be bound (timeout: 5 minutes)..."
oc wait --for=jsonpath='{.status.phase}'=Bound pvc --all --timeout=300s || echo "⚠️  Some PVCs may still be pending"

# 6. Deploy Databases
echo "🗄️  Deploying databases..."
oc apply -f deployments/pg-airflow-db-deployment.yaml
oc apply -f deployments/pg-typing-pdf-extractor-db-deployment.yaml
oc apply -f services/pg-airflow-db-service.yaml
oc apply -f services/pg-typing-pdf-extractor-db-service.yaml

echo "⏳ Waiting for databases to be ready (timeout: 5 minutes)..."
oc wait --for=condition=available --timeout=300s deployment/pg-airflow-db || echo "⚠️  pg-airflow-db may need more time"
oc wait --for=condition=available --timeout=300s deployment/pg-typing-pdf-extractor-db || echo "⚠️  pg-typing-pdf-extractor-db may need more time"

# 7. Deploy Storage and Vector DB
echo "📦 Deploying MinIO and Qdrant..."
oc apply -f deployments/minio-deployment.yaml
oc apply -f deployments/qdrant-vector-db-deployment.yaml
oc apply -f services/minio-service.yaml
oc apply -f services/qdrant-vector-db-service.yaml

# 8. Deploy LLM Services
echo "🤖 Deploying LLM services (this may take several minutes)..."
oc apply -f deployments/ollama-llm-embedding-deployment.yaml
oc apply -f deployments/ollama-llm-chat-deployment.yaml
oc apply -f services/ollama-llm-embedding-service.yaml
oc apply -f services/ollama-llm-chat-service.yaml

echo "⏳ Waiting for LLM services to be ready (timeout: 10 minutes)..."
oc wait --for=condition=available --timeout=600s deployment/ollama-llm-embedding || echo "⚠️  ollama-llm-embedding may need more time"
oc wait --for=condition=available --timeout=600s deployment/ollama-llm-chat || echo "⚠️  ollama-llm-chat may need more time"

# 9. Deploy Airflow Components
echo "🌬️  Deploying Airflow components..."
oc apply -f deployments/airflow-scheduler-deployment.yaml
oc apply -f deployments/airflow-dag-processor-deployment.yaml
oc apply -f deployments/airflow-api-server-deployment.yaml
oc apply -f services/airflow-api-server-service.yaml

# 10. Deploy Application Services
echo "🚀 Deploying application services..."
oc apply -f deployments/typing-pdf-extractor-service-deployment.yaml
oc apply -f deployments/embedding-service-deployment.yaml
oc apply -f deployments/chat-docs-service-deployment.yaml
oc apply -f deployments/chat-docs-ui-deployment.yaml
oc apply -f services/typing-pdf-extractor-service-service.yaml
oc apply -f services/embedding-service-service.yaml
oc apply -f services/chat-docs-service-service.yaml
oc apply -f services/chat-docs-ui-service.yaml

# 11. Create Routes
echo "🌐 Creating routes for external access..."
oc apply -f routes/airflow-api-server-route.yaml
oc apply -f routes/minio-console-route.yaml
oc apply -f routes/minio-api-route.yaml
oc apply -f routes/chat-docs-ui-route.yaml
oc apply -f routes/chat-docs-service-route.yaml

# 12. Init Airflow
echo "🚀 Creating airflow admin user..."
oc wait --for=condition=available --timeout=600s deployment/airflow-api-server || echo "⚠️  airflow-api-server may need more time"
oc exec -it -n poc-onprem \
  $(oc get pods -n poc-onprem -l app=airflow-api-server -o jsonpath='{.items[0].metadata.name}') \
  -- airflow users create \
      --username admin \
      --password admin \
      --firstname Admin \
      --lastname Admin \
      --role Admin \
      --email admin@example.com

echo ""
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""
echo "📊 Access URLs:"
echo "  Airflow UI:    https://$(oc get route airflow-api-server -o jsonpath='{.spec.host}' 2>/dev/null || echo 'pending')"
echo "  MinIO Console: https://$(oc get route minio-console -o jsonpath='{.spec.host}' 2>/dev/null || echo 'pending')"
echo "  Chat Docs UI:  https://$(oc get route chat-docs-ui -o jsonpath='{.spec.host}' 2>/dev/null || echo 'pending')"
echo ""
echo "📝 Next Steps:"
echo "  1. Monitor deployment: oc get pods -w"
echo "  2. Create Airflow admin user (see README.md)"
echo "  3. Access applications using URLs above"
echo ""
