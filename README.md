# Cognitor

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

## 🔒 Security & Privacy

### Telemetry

By default, we gather anonymous usage data and statistics to help us improve Cognitor. The telemetry data does not include any personally identifiable information (PII) or sensitive data. You can inspect the exact fields we collect [from this file](src/telemetry/events.py).

If you wish to opt out of telemetry, you can do so by setting `TELEMETRY_ENABLED=false` in your environment variables or configuration file.