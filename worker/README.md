# Instructions

## Start postgres

```bash
docker compose up -d db
```

## Check logs for initialization

```bash
docker compose logs -f db
```

## Use psql in a container

```bash
docker compose exec db psql -U postgres -d postgres -c "\dx"
```

You should see pgvector listed in installed extensions

## Check tables

```bash
docker compose exec db psql -U postgres -d postgres -c "\dt"
# Or query:
docker compose exec db psql -U postgres -d postgres -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
# And quick query:
docker compose exec db psql -U postgres -d postgres -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='chunks';"
```

## Run the worker

```bash
uvicorn main:app --reload --port 8000
```

## Test the PDF ingestion

```bash
curl -X POST "http://localhost:8000/process-pdf" \
  -F "file=data.pdf"
```