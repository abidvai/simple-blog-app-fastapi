# Simple Blog App (FastAPI)

A fully-featured async REST API for a blog application built with FastAPI, PostgreSQL, and Redis. Features include JWT authentication, posts CRUD, category support, comment system, post likes with Redis counters, and token blacklisting on logout.

---

## Prerequisites

- Python 3.13+
- PostgreSQL
- Redis

---

## Local Setup

### 1. Clone the repository and setup virtual environment
```bash
git clone https://github.com/abidvai/simple-blog-app-fastapi.git
cd simple-blog-app-fastapi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql+asyncpg://your_db_user:your_db_password@localhost:5432/your_db_name
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_generated_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_NAME=Blog API
DEBUG=False
```

### 3. Run Database Migrations
```bash
alembic revision --autogenerate -m "Initial migrations"
alembic upgrade head
```

### 4. Start the Application
```bash
uvicorn app.main:app --reload
```
Access the Swagger documentation at `http://localhost:8000/docs`.

---

## Testing

Run the test suite using pytest. The test suite uses an in-memory SQLite database and a mock Redis client:
```bash
pytest
```

---

## DevOps & Production Deployment Guide

### 1. Production ASGI Server Run Command
In production, run the application using `uvicorn` with multiple workers:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop --http httptools
```

### 2. Nginx Reverse Proxy Configuration
Configure Nginx as a reverse proxy to handle SSL termination and forward requests:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Systemd Service Configuration
Create a systemd service file `/etc/systemd/system/fastapi.service`:
```ini
[Unit]
Description=FastAPI Blog API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/simple-blog-app-fastapi
ExecStart=/home/ubuntu/simple-blog-app-fastapi/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
```

### 4. Database & Cache Considerations
- Ensure PostgreSQL connection pooling is tuned.
- Run `alembic upgrade head` as part of your CI/CD deployment pipeline before starting/restarting the application service.
- Keep Redis persistent storage configured if using post caching and token blacklists in production.
