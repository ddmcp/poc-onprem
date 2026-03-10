#!/bin/bash
set -e

echo "🗑️  Starting OpenShift Cleanup for poc-onprem..."
echo "=================================================="
echo "⚠️  WARNING: This will delete ALL resources including persistent data!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo ""
echo "🔄 Switching to poc-onprem namespace..."
oc project poc-onprem 2>/dev/null || echo "Namespace may not exist"

# 1. Delete Routes
echo "🌐 Deleting routes..."
oc delete -f routes/ --ignore-not-found=true

# 2. Delete Services
echo "🔌 Deleting services..."
oc delete -f services/ --ignore-not-found=true

# 3. Delete Deployments
echo "📦 Deleting deployments..."
oc delete -f deployments/ --ignore-not-found=true

echo "⏳ Waiting for pods to terminate..."
oc wait --for=delete pod --all --timeout=120s 2>/dev/null || echo "Some pods may still be terminating"

# 4. Delete ConfigMaps
echo "⚙️  Deleting ConfigMaps..."
oc delete -f configmaps/ --ignore-not-found=true

# 5. Delete Secrets
echo "🔐 Deleting secrets..."
oc delete -f secrets/ --ignore-not-found=true

# 6. Delete PVCs (this will delete all persistent data)
echo "💾 Deleting PersistentVolumeClaims and data..."
oc delete -f pvcs/ --ignore-not-found=true

# 7. Delete ServiceAccount
echo "👤 Deleting ServiceAccount..."
oc delete -f serviceaccount.yaml --ignore-not-found=true

# 8. Delete Namespace
# echo "📁 Deleting namespace..."
# oc delete -f namespace.yaml --ignore-not-found=true

echo ""
echo "✅ Cleanup Complete!"
echo "=================================================="
echo "All resources have been removed from the cluster."
echo ""
