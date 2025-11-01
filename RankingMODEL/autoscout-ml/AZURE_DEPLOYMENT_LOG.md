# Azure Container Apps Deployment Log

## Latest Deployment: v5-hybrid (Hybrid Ranking Engine)

**Date:** October 30, 2025  
**Status:** ✅ DEPLOYED & VERIFIED

---

## Deployment Summary

### What Changed:
- Integrated **hybrid ranking engine** (`ranking_pipeline.py`)
- Updated Dockerfile to include new ranking system alongside Flask app
- Built for **linux/amd64** platform for Azure compatibility

### Files Deployed:
```dockerfile
COPY src/app_flask.py ./app.py
COPY src/similarity_engine.py ./similarity_engine.py
COPY src/ranking_pipeline.py ./ranking_pipeline.py  ← NEW
COPY src/__init__.py ./__init__.py
```

### Hybrid Ranking Components:
1. **Similarity Score** (60%): Age, mileage, power, body type, transmission, fuel, color, drivetrain
2. **Deal Score** (35%): Price positioning vs market, mileage value
3. **Preference Score** (5%): User preference boosts

---

## Azure Configuration

| Setting | Value |
|---------|-------|
| **Container App** | `carma-ml-api` |
| **Resource Group** | `carma` |
| **Container Registry** | `carmaregistry.azurecr.io` |
| **Environment** | `carma-environment` |
| **Region** | North Europe |
| **Public URL** | `https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io` |

### Current Deployment:
- **Image:** `carmaregistry.azurecr.io/carma-api:v5-hybrid`
- **Revision:** `carma-ml-api--0000015`
- **Status:** ✅ Running
- **Database:** Azure PostgreSQL (263,594 vehicles)

---

## Deployment Commands

### 1. Build for Linux/AMD64
```bash
cd /Users/marchaupter/Desktop/C1

docker build --platform linux/amd64 \
  -f RankingMODEL/autoscout-ml/Dockerfile.flask \
  -t carma-api:latest \
  RankingMODEL/autoscout-ml
```

### 2. Tag for Azure Container Registry
```bash
docker tag carma-api:latest carmaregistry.azurecr.io/carma-api:v5-hybrid
```

### 3. Login to ACR
```bash
az acr login --name carmaregistry
```

### 4. Push to Registry
```bash
docker push carmaregistry.azurecr.io/carma-api:v5-hybrid
```

### 5. Update Container App
```bash
az containerapp update \
  --name carma-ml-api \
  --resource-group carma \
  --image carmaregistry.azurecr.io/carma-api:v5-hybrid
```

### 6. Verify Deployment
```bash
curl https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io/health
```

---

## Deployment Verification

### Health Check Response:
```json
{
    "database_connected": true,
    "similarity_engine": "v3.0-strict-filters",
    "status": "healthy",
    "timestamp": "2025-10-30T16:34:35.938285",
    "total_vehicles": 263594
}
```

### API Endpoints:
- `GET /health` - Health check
- `GET /stats` - Vehicle statistics
- `GET /listings/:id` - Vehicle details
- `GET /listings/:id/comparables` - Comparable vehicles (uses hybrid ranking)

---

## Version History

| Version | Date | Description | Image Tag |
|---------|------|-------------|-----------|
| v5-hybrid | Oct 30, 2025 | Hybrid ranking engine integration | `carma-api:v5-hybrid` |
| v4-practical | Oct 25, 2025 | Previous version | `carma-ml-api:v4-practical` |

---

## Future Deployments

For subsequent deployments, increment the version tag:

```bash
# Example for v6
docker build --platform linux/amd64 -f RankingMODEL/autoscout-ml/Dockerfile.flask -t carma-api:latest RankingMODEL/autoscout-ml
docker tag carma-api:latest carmaregistry.azurecr.io/carma-api:v6
docker push carmaregistry.azurecr.io/carma-api:v6
az containerapp update --name carma-ml-api --resource-group carma --image carmaregistry.azurecr.io/carma-api:v6
```

---

## Rollback Procedure

If issues arise, rollback to previous version:

```bash
az containerapp update \
  --name carma-ml-api \
  --resource-group carma \
  --image carmaregistry.azurecr.io/carma-ml-api:v4-practical
```

---

## Notes

- **Platform:** Always build with `--platform linux/amd64` on macOS (ARM64 won't work on Azure)
- **Registry:** Use `carmaregistry.azurecr.io` for all images
- **Naming:** Container app is `carma-ml-api`, but images can use `carma-api` or `carma-ml-api`
- **Scaling:** Configured for 1-10 replicas (auto-scaling enabled)
- **Resources:** 0.25 CPU, 0.5 GB RAM per instance

---

## Contact & Resources

- **Azure Subscription:** Azure subscription 1
- **Account:** marchaupter@outlook.com
- **Tenant:** marchaupteroutlook.onmicrosoft.com

### Useful Commands:

```bash
# View logs
az containerapp logs show --name carma-ml-api --resource-group carma --follow

# List revisions
az containerapp revision list --name carma-ml-api --resource-group carma --output table

# Check current image
az containerapp show --name carma-ml-api --resource-group carma --query 'properties.template.containers[0].image'

# View environment variables
az containerapp show --name carma-ml-api --resource-group carma --query 'properties.template.containers[0].env'
```

---

**✅ Deployment completed successfully on October 30, 2025**

