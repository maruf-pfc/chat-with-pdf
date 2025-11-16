# Chat With PDF

- Start the DB

```bash
docker compose up -d db
```

- Check pgvector

```bash
docker compose exec db psql -U postgres -d postgres -c "\dx"
```

- Check Tables

```bash
docker compose exec db psql -U postgres -d postgres -c "\dt"
```
