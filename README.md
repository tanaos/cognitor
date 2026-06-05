<p align="center">
    <a href="https://github.com/tanaos/cognitor">
        <img src="https://raw.githubusercontent.com/tanaos/cognitor/master/assets/hero.png" width="400px" alt="Cognitor | All-in-one semantic search platform for AI and humans.">
    </a>
</p>

## How to use

### Search platform only

```bash
docker compose up -d
docker compose down
```

### Search platform + worker

Configure the folder that the worker will keep synchronized with a Cognitor collection, by setting the path in your `.env` (at the root of the project):

```bash
# Absolute path on your host machine to ingest
DOCS_FOLDER=/path/to/your/docs
```

Start both the search platform and the worker with

```bash
docker compose --profile worker up -d
```

Stop them with

```bash
docker compose --profile worker down --remove-orphans
```

### Search platform + local worker source (development)

If you have both repositories side-by-side:

- `.../cognitor`
- `.../cognitor-worker`

you can build and run the worker from local source (instead of pulling from `ghcr.io`) by adding the local override file:

```bash
docker compose \
    -f docker-compose.yml \
    -f docker-compose.worker-local.yml \
    --profile worker up -d --build
```

Stop the stack with:

```bash
docker compose \
    -f docker-compose.yml \
    -f docker-compose.worker-local.yml \
    --profile worker down --remove-orphans
```

## 🔒 Security & Privacy

### Telemetry

By default, we gather a small amount of anonymous usage data which helps us improve Cognitor. This does not include any personally identifiable information (PII) or sensitive data. You can inspect the exact fields we collect [from this file](src/telemetry/events.py).

If you wish to opt out of telemetry, you can do so by setting `TELEMETRY_ENABLED=false` in your environment variables or configuration file.