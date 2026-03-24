# ShelfAware Single-Image Docker Deployment

This guide shows how to run ShelfAware as one Docker image where:
- FastAPI serves both backend API and frontend static files.
- Frontend API calls use same-origin routes (for example, `/auth/login`).

## Prerequisites

- Docker installed
- OpenAI API key (optional for scheduler features)
- Cognito and DB environment variables (if your auth/database setup needs them)

## 1. Build the Image

From the repository root:

```bash
docker build -t shelfaware:single .
```

Optional: pass a frontend API base URL at build time.
For single-origin deployment, keep this empty.

```bash
docker build \
  --build-arg VITE_API_BASE_URL="" \
  -t shelfaware:single .
```

## 2. Run the Container

```bash
docker run --name shelfaware \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-key" \
  -e CORS_ORIGINS="http://localhost:8000" \
  shelfaware:single
```

If you rely on external services, also include your required variables, such as:
- `DATABASE_URL`
- `COGNITO_REGION`
- `COGNITO_USER_POOL_ID`
- `COGNITO_CLIENT_ID`

## 3. Verify Deployment

Open these URLs:
- App UI: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

Quick auth route checks:

```bash
curl -X POST http://localhost:8000/auth/registration -H "Content-Type: application/json" -d '{"username":"demo","email":"demo@example.com","password":"Passw0rd!"}'
```

```bash
curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"email":"demo@example.com","password":"Passw0rd!"}'
```

## Why This Avoids Method Not Allowed Errors

In this deployment mode, both frontend and backend live behind the same server origin.
Frontend requests go directly to API paths on the same host, so auth POST requests do not get sent to a static-only frontend container.

## Troubleshooting

1. If login/register returns 405:
- Confirm you are running the root `Dockerfile` image, not `ref_frontend/Dockerfile`.
- Confirm requests are going to `http://<host>:8000/auth/...`.

2. If auth fails with 4xx/5xx:
- Verify Cognito environment variables.
- Check container logs:

```bash
docker logs shelfaware --tail 200
```

3. If frontend loads but API fails:
- Ensure port mapping is correct: `-p 8000:8000`.
- Ensure browser is hitting the same origin as the API (`http://localhost:8000`).
