# Cognitor

## How to use

Start a local instance of Cognitor with Docker:

```bash
docker build -t cognitor .
docker run -p 7530:7530 -v cognitor_storage:/app/storage cognitor
```

Install the [Python client](https://github.com/tanaos/cognitor-python):

```bash
pip install cognitor
```