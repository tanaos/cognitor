<p align="center">
    <a href="https://github.com/tanaos/cognitor">
        <img src="https://raw.githubusercontent.com/tanaos/cognitor/master/assets/hero.png" width="400px" alt="Cognitor | All-in-one semantic search platform for AI and humans.">
    </a>
</p>

# Cognitor

Cognitor is an open-source semantic search platform which automatically chunks, embeds and indexes the entire content of a target folder (and its subfolders), making it easily searchable by both AI agents and humans. It provides a simple API to query the indexed data via natural language, and can be used as a standalone semantic search engine or as a backend for your applications.

Cognitor runs in a Docker container, making it easy to use and deploy on any system, including your local machine for maximum privacy and control over your data.

## How does it work?

Cognitor consists of two main components:

- **Search platform** (this repository): a vector database which stores document embeddings, full text and metadata, and provides a simple REST API to query the indexed information.
- **[Worker](https://github.com/tanaos/cognitor-worker)**: a background process that monitors a specified folder for changes, automatically chunks and embeds the content of the files, and updates the vector database accordingly.

## How to use

Similarly to other vector databases, Cognitor organizes data into *documents* and *collections*.

- ***document***: a piece of content that you want to be searchable. It usually corresponds to a chunk of text extracted from a file (not the entire file).
- ***collection***: a group of related documents. Collections help organize and manage your data within Cognitor. Think of a collection as a table in a traditional database, or as a folder in a file system.

### Use search platform + worker

Configure the following environment variables in your `.env` file (at the root of the project):

- **DOCS_FOLDER**: folder that the worker will keep synchronized with a Cognitor collection.
- **COGNITOR_COLLECTION_NAME**: name of the collection that the worker will use to store the indexed documents.

```bash
# Absolute path on your host machine to ingest
DOCS_FOLDER=/path/to/your/docs
# Name of the collection in which the worker will store the indexed documents
COGNITOR_COLLECTION_NAME=cognitor-worker-documents
```

Start both the search platform and the worker with

```bash
docker compose --profile worker up -d
```

Once the search platform's `GET /health/ready` endpoint returns `"ready"` (indicating that the initial setup is complete), the worker will automatically start indexing the content of the specified folder and keep it up to date with any changes. Use `docker logs cognitor-worker` to check the indexing status and see which files have been processed.

> [!NOTE]
> Check out the [worker repository](https://github.com/tanaos/cognitor-worker) to see which file types are currently supported (we will be adding more soon). Keep in mind that file types that are not supported will be ignored by the worker, but you can still index their content manually through the API.

Once the search platform is running, you can interact with its REST API through the [Swagger UI](http://localhost:7530/docs), the [Python](https://github.com/tanaos/cognitor-python) or [TypeScript](https://github.com/tanaos/cognitor-typescript) SDKs, or directly through HTTP requests.

Stop both the search platform and the worker with

```bash
docker compose --profile worker down --remove-orphans
```

### Use the search platform only

If you prefer to index documents manually through the API instead of using the worker, you can simply start the search platform without the worker:

```bash
docker compose up -d
```

Keep in mind that in this case, document chunking, embedding and indexing will not happen automatically, and you will need to handle that yourself (e.g. by using the SDKs or implementing your own background process).

Stop the search platform with:

```
docker compose down
```

### Integrate with your applications

When its docker container is running, Cognitor exposes a REST API at [`http://localhost:7530`](http://localhost:7530) which you can use to query the indexed data, manage collections and index more documents. You can visit the Swagger UI at [`http://localhost:7530/docs`](http://localhost:7530/docs). We provide client libraries for

- [Python](https://github.com/tanaos/cognitor-python)
- [TypeScript](https://github.com/tanaos/cognitor-typescript)

Below is an example of how to search for documents in a collection using the Python SDK:

Install the SDK:

```bash
pip install cognitor
```

Use it in your code:

```python
from cognitor import Cognitor

with Cognitor("http://localhost:7530", api_key="your-api-key") as client:
    # Check if the search platform is ready to accept requests
    print(client.health_ready())  # "ready" or "loading"

    # Search by text query
    response = client.search("my-collection", query_text="Hello", top_k=10)
    print(response)
```

See the [Python SDK page](https://github.com/tanaos/cognitor-python) for more examples and documentation.

## No data? No problem.

If you don't have your own data to test with, you can use the included script to seed the database with a sample e-commerce products collection:

```bash
python scripts/dev/seed_ecommerce.py
```

## Contributing

We welcome contributions of any kind! If you want to contribute, please read our [contributing guidelines](CONTRIBUTING.md) and feel free to open an issue or a pull request.

## Security & Privacy

### Telemetry

By default, we gather a small amount of anonymous usage data which helps us improve Cognitor. This does not include any personally identifiable information (PII) or sensitive data. You can inspect the exact fields we collect [from this file](src/telemetry/events.py).

If you wish to opt out of telemetry, you can do so by setting the `TELEMETRY_ENABLED=false` environment variable.