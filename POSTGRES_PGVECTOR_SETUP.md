# PostgreSQL + pgvector Setup

This demo uses PostgreSQL with pgvector for face embeddings.

## Start the database

From `face-attendance-demo`:

```powershell
docker compose up -d
```

The database is exposed on host port `5433` to avoid conflicting with other
local PostgreSQL services.

## Open pgAdmin

Open:

```text
http://localhost:5050
```

Login:

```text
Email: admin@example.com
Password: admin
```

Register the database server in pgAdmin:

```text
Name: face-attendance-demo
Host name/address: db
Port: 5432
Maintenance database: attendance_demo
Username: attendance
Password: attendance
```

## Install Python dependencies

From `face-attendance-demo\backend`:

```powershell
pip install -r requirements-gpu-cu12.txt
```

For CPU-only development:

```powershell
pip install -r requirements.txt
```

## Run the app

From `face-attendance-demo\backend`:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://localhost:8000
```

## Reset demo data

To drop and recreate all demo tables on startup, set this in `backend\.env`:

```env
RESET_DATABASE_ON_START=true
```

Start the app once, then set it back to:

```env
RESET_DATABASE_ON_START=false
```
