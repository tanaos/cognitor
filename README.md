# Cognitor

<img src="https://raw.githubusercontent.com/tanaos/cognitor/master/assets/hero.png" alt="Cognitor – Small Language Model observability, evaluation and optimization" width="600">

Cognitor is a **Small Language Model observability platform** that allows developers to monitor, test, evaluate and optimize their SLM applications in a unified environment. It can be self-hosted in minutes and provides a powerful dashboard for visualizing and analyzing your model's performance and behavior.

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

<img src="https://raw.githubusercontent.com/tanaos/cognitor/master/assets/dashboard.png" alt="Cognitor – Small Language Model observability, evaluation and optimization" width="600">

- **SLM Application Monitoring**: Instrument your app and start tracking inference calls, training runs and data quality metrics for your self-hosted SLM applications.
- **Unified Dashboard**: Visualize and analyze your model's performance, behavior, and data quality in a single, intuitive dashboard. Identify trends, outliers and areas for improvement with visualizations and analytics.
- **Inference Logging**: Capture detailed logs of inference calls, including input data, output, latency, tokens, resource usage and outlier values. Spot performance drift and model behavior changes with comprehensive inference logging.
- **Inference Errors**: Capture and analyze inference errors, including error type, message, stack trace and frequency.
- **Training Run Tracking**: Monitor training runs, including hyperparameters, train and eval loss, accuracy and resource usage. Identify issues and optimize your training process with detailed run tracking.

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
from cognitor import Cognitor
from transformers import AutoTokenizer, pipeline

# Initialize your model and tokenizer
model_name = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
pipe = pipeline("text-generation", model=model_name, tokenizer=tokenizer)

cognitor = Cognitor(
    model_name=model_name,
    tokenizer=tokenizer
)

# Run inference within the monitor context
with cognitor.monitor() as m:
    input_text = "Once upon a time,"
    with m.track():
        output = pipe(input_text, max_length=50)
    m.capture(input_data=input_text, output=output)
```

Want to track training metrics? Check out the [cognitor-py SDK GitHub repo](https://github.com/tanaos/cognitor-py) for more examples and documentation.

### 3️⃣ Explore the dashboard

See your logged data in the Cognitor dashboard at `http://localhost:3000`.

<img src="https://raw.githubusercontent.com/tanaos/cognitor/master/assets/inference-logs.png" alt="Cognitor – Small Language Model observability, evaluation and optimization" width="600">

## Contributing

Contributions are welcome! Whether it's a bug fix or a new feature you want to add, we'd love your help. Check out our [Contribution Guidelines](CONTRIBUTING.md) to get started.