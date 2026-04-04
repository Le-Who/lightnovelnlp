# Northflank Deployment Configuration

This repository is optimized for deployment on Northflank (or similar PaaS providers). To deploy the Light Novel NLP infrastructure, you will need to configure three services and two add-ons.

## 1. Add-ons

**PostgreSQL (Managed)**
- **Type**: PostgreSQL 16+ with `pgvector`
- **Networking**: Export connection URI. We recommend disabling public IP access and restricting to internal cluster traffic.

**Redis (Managed)**
- **Type**: Redis 7+
- **Usage**: Message broker for Celery backend tasks and cache system.
- **Networking**: Export connection URI. Disable public traffic.

## 2. Services

Both services below build from the `backend` Dockerfile but have different execution commands.

### Service A: API Web Server
- **Build Path**: `./backend`
- **Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Ports**: Expose `8000` (HTTP) publicly.
- **Health Check**: `/health` endpoint internally checks PostgreSQL (`SELECT 1`) and Redis (`PING`).
- **Scale**: 1+ Instances. Auto-scaling can be tuned based on CPU load.

### Service B: Celery Worker
- **Build Path**: `./backend`
- **Command**: `celery -A app.core.celery_app worker --loglevel=info`
- **Ports**: None publicly exposed.
- **Health Check**: None needed (relies on container state).
- **Scale**: 1+ Instances. Scales based on queue depth. Since Gemini API bounds IO speed, memory consumption is relatively steady. This service offloads all processing spikes away from the main Web API.

### Service C: Frontend React App
- **Build Path**: `./frontend`
- **Command**: (Dependent on deployment mode—if Vercel, link the GitHub module directly. If Northflank, use standard `npm run preview` on `0.0.0.0`).
- **Env**: Make sure `VITE_API_URL` points to the public URL of Service A.

## Environment Variables

The following ENV variables must be injected precisely into BOTH Service A and Service B:

```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://user:pass@host:port
GEMINI_API_KEYS_RAW="[...]" # Or define GEMINI_API_KEYS as array natively if supported
FRONTEND_URL=https://your-frontend-domain.com
```

## Security Considerations

The Celery tasks queue ML payloads. The worker container inherently pulls from Redis. Redis instances exposed to any network must absolutely require authentication masks, as injected payloads could be susceptible to deserialization compromises if `task_serializer="json"` was violated. We strictly enforce `accept_content=["json"]` inside `celery_app.py` for this reason.
