# Chatweb Backend

Django REST API + WebSockets for private watch-together rooms.

## Stack

- Django 5 + DRF
- Django Channels (Daphne ASGI)
- JWT (SimpleJWT)
- PostgreSQL (production) / SQLite (local)
- Optional: Redis (`REDIS_URL`) for multi-instance WebSockets
- Optional: Cloudinary for uploads

## Local setup

```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_users
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

API: `http://localhost:8000`  
Health: `GET /`

## Seed users

```bash
python manage.py seed_users
```

Creates `user1@chatweb.com` and `user2@chatweb.com` (password `password123`). Change passwords in production.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Production | Django secret (required when `DEBUG=False`) |
| `DEBUG` | No | `True` / `False` (default `True`) |
| `DATABASE_URL` | Production | PostgreSQL URL (Render provides this) |
| `REDIS_URL` | Recommended prod | Enables Redis channel layer for WebSockets |
| `ALLOWED_HOSTS` | Production | Comma-separated hosts |
| `CORS_ALLOWED_ORIGINS` | Production | Frontend origin(s) |
| `CLOUDINARY_*` | Optional | Cloud name, API key, secret for CDN uploads |

## API overview

| Endpoint | Method | Auth |
|----------|--------|------|
| `/api/accounts/login/` | POST | Public |
| `/api/accounts/token/refresh/` | POST | Refresh token |
| `/api/accounts/signup/` | POST | Public |
| `/api/rooms/create/` | POST | JWT |
| `/api/rooms/{uuid}/` | GET | JWT |
| `/api/rooms/{uuid}/join/` | POST | JWT |
| `/api/rooms/{uuid}/chat/` | GET | JWT |
| `/api/rooms/{uuid}/media/` | GET | JWT |
| `/api/rooms/upload/` | POST | JWT |
| `ws/room/{uuid}/?token=` | WS | JWT query param |

## Room access

- **Shared hall** (`00000000-0000-0000-0000-000000000000`): any logged-in user
- **Private rooms**: only host (`created_by`) and partner (`joined_by` after `/join/`)

## Deploy (Render)

1. Set `SECRET_KEY`, `DATABASE_URL`, `DEBUG=False`
2. Add `REDIS_URL` from Render Redis for reliable WebSockets
3. Run migrations on deploy
4. Optionally configure Cloudinary for persistent uploads
