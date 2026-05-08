# Docker Quick Start Guide

## Prerequisites

### For CPU Version
- Docker Desktop or Docker Engine
- ~2GB disk space
- Internet connection for initial image build

### For GPU Version
- Docker Desktop or Docker Engine
- **nvidia-docker** runtime
- NVIDIA GPU with CUDA 12.x support
- NVIDIA drivers installed
- ~3GB disk space
- Internet connection for initial image build

---

## Quick Start (Choose One)

### Option 1: CPU Version (Easiest, Recommended for Development)

```bash
# Navigate to project root
cd face-attendance-demo

# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f backend

# Access the application
# Frontend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Performance:** 2-3 FPS  
**Memory:** ~500MB  
**Best For:** Development, testing, portability

---

### Option 2: GPU Version (Production, High Performance)

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your PostgreSQL password
# nano .env  (or edit in your editor)

# Build and start with GPU support
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Access the application
# Frontend: http://localhost:8000
# API Docs: http://localhost:8000/docs
# pgAdmin: http://localhost:5050 (username: admin@example.com)
```

**Performance:** 20-30 FPS  
**Memory:** ~1GB  
**Best For:** Production, real-time processing

---

## Common Commands

### View Running Containers
```bash
docker-compose ps
# or with GPU version
docker-compose -f docker-compose.prod.yml ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f db
```

### Stop Services
```bash
# CPU version
docker-compose down

# GPU version
docker-compose -f docker-compose.prod.yml down
```

### Stop and Remove All Data
```bash
# CPU version
docker-compose down -v

# GPU version (removes volumes)
docker-compose -f docker-compose.prod.yml down -v
```

### Rebuild Image (after code changes)
```bash
# CPU version
docker-compose build
docker-compose up -d

# GPU version
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

---

## Verifying Your Setup

### Check Container Status
```bash
docker-compose ps
```

Expected output (CPU version):
```
NAME                           STATUS          PORTS
face_attendance_backend        Up 2 minutes    0.0.0.0:8000->8000/tcp
```

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-05-08T10:30:45.123456",
  "database": "connected",
  "model": "loaded"
}
```

### Test API
```bash
# Get API documentation
curl http://localhost:8000/docs

# Check people list
curl http://localhost:8000/api/people
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Mac/Linux

# Use different port in docker-compose.yml
# Change: "8000:8000" → "8001:8000"
```

### GPU Not Detected
```bash
# Check GPU availability
docker run --rm --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi

# If this fails, install nvidia-docker runtime
# Windows: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### Model Download Timeout
```bash
# Pre-download model before building
# This will download the InsightFace buffalo_l model
python -c "import insightface; print(insightface.__version__)"

# Then rebuild the image
docker-compose build --no-cache
```

### Database Connection Issues
```bash
# For GPU version, ensure DB is healthy
docker-compose -f docker-compose.prod.yml logs db

# Wait for DB to be ready, then restart backend
docker-compose -f docker-compose.prod.yml restart backend
```

### Out of Disk Space
```bash
# Clean up Docker data
docker system prune -a

# Remove all volumes (WARNING: loses data)
docker volume prune
```

---

## Performance Tuning

### CPU Version - Increase Performance
Edit `docker-compose.yml`:
```yaml
backend:
  # Disable hot-reload in production
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

### GPU Version - Multi-GPU Support
Edit `docker-compose.prod.yml`:
```yaml
backend:
  environment:
    - CUDA_VISIBLE_DEVICES=0,1,2  # Use GPUs 0, 1, 2
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 3  # Use 3 GPUs
```

---

## Database Management (GPU Version)

### Access pgAdmin
```
URL: http://localhost:5050
Email: admin@example.com
Password: (from .env file)
```

### Connect to Database in pgAdmin
1. Open pgAdmin
2. Click "Add New Server"
3. Name: `face_attendance_db`
4. Connection tab:
   - Host: `db`
   - Port: `5432`
   - Username: `attendance`
   - Password: (from .env file)

### Direct Database Access
```bash
# From container
docker-compose -f docker-compose.prod.yml exec db psql -U attendance -d attendance_db

# From host (requires psql installed)
psql -h localhost -U attendance -d attendance_db -p 5432
```

---

## Deploying to Cloud

### AWS ECS
```bash
# Build and push to ECR
docker build -t face-attendance:cpu -f backend/Dockerfile ./backend
docker tag face-attendance:cpu [YOUR_ECR_URI]:latest
docker push [YOUR_ECR_URI]:latest

# Create ECS task definition referencing the image
```

### Azure Container Instances
```bash
# Build and push to ACR
docker build -t face-attendance:cpu ./face-attendance-demo/backend
docker tag face-attendance:cpu [YOUR_ACR].azurecr.io/face-attendance:latest
docker push [YOUR_ACR].azurecr.io/face-attendance:latest

# Deploy using Azure CLI
az container create --resource-group [RG] --name face-attendance \
  --image [YOUR_ACR].azurecr.io/face-attendance:latest \
  --ports 8000
```

### Kubernetes
```bash
# Create deployment
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: face-attendance
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: backend
        image: face-attendance:cpu
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "500Mi"
          limits:
            memory: "1Gi"
EOF

# Expose service
kubectl expose deployment face-attendance --port=8000 --type=LoadBalancer
```

---

## Development Workflow

### Hot Reload (CPU Version)
```bash
# The application auto-reloads when you edit Python files
# Just edit backend code and refresh the browser
```

### Debugging
```bash
# View live logs
docker-compose logs -f backend

# Execute command in running container
docker-compose exec backend bash
```

### Testing
```bash
# Run tests inside container
docker-compose exec backend pytest tests/

# Or mount test directory for development
# volumes:
#   - ./tests:/app/tests
```

---

## Next Steps

1. **Development**: Start with CPU version (`docker-compose up -d`)
2. **Testing**: Verify with `curl http://localhost:8000/health`
3. **Production**: Switch to GPU version with PostgreSQL (`docker-compose.prod.yml`)
4. **Cloud**: Push to registry and deploy to your cloud platform

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Documentation](https://docs.docker.com/compose)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment)
- [pgVector Documentation](https://github.com/pgvector/pgvector)
