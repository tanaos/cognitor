# Cognitor

<p align="center">
    <a href="https://github.com/tanaos/cognitor">
        <img src="https://raw.githubusercontent.com/tanaos/cognitor/master/assets/hero.png" alt="Cognitor – Small Language Model observability, evaluation and optimization" width="600">
    </a>
</p>

Cognitor is a **Small Language Model observability platform** that allows developers to monitor, test, evaluate and optimize their SLM applications in a unified environment.

## Why a SLM observability platform?

SLMs present unique challenges that traditional LLM observability platforms are not designed to handle:

- **Self-Hosted**: SLMs are almost always self-hosted, making traditional API-based monitoring solutions ineffective.
- **Overfitting**: with small models, overfitting isn't just a risk, it's a common occurrence. 
- **Data Quality**: the quality of training data has a disproportionate impact on small models, making data monitoring crucial.
- **Resource Constraints**: small models often run in resource-constrained environments, requiring efficient monitoring solutions (CPU, memory, storage).
- **Behavior Drift**: small models can exhibit significant behavior changes with minor updates, making continuous monitoring essential.
- **Rapid Iteration**: developers of small models often iterate quickly, necessitating a platform that can keep up with fast development cycles.

Unique challenges require unique solutions, and Cognitor is designed to address the specific needs of SLM developers, providing them with the tools they need to succeed in this rapidly evolving field.

## Features

## 🚀 Quickstart

Get a local copy of `cognitor`, instrument your SLM app and start ingesting data in minutes.

### 1️⃣ Start `cognitor` locally

```bash
# Get a copy of the latest Cognitor repository
git clone https://github.com/tanaos/cognitor.git
cd cognitor

# Run the cognitor docker compose
docker compose up
```

### 2️⃣ Log your first SLM call

Use the [`cognitor` Python SDK](https://github.com/tanaos/cognitor-py) to log your SLM calls and start monitoring your model's performance.

```bash
pip install cognitor
```

```python

```