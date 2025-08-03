# pallma

Pallma is an advanced AI-powered security monitoring platform that leverages OpenTelemetry and state-of-the-art machine learning models to detect, analyze, and predict potential security threats in real-time. By combining distributed tracing with AI capabilities, it provides comprehensive security insights and proactive threat detection for modern applications and infrastructure.

## Prerequisites

Before running pallma, ensure you have the following installed:

- **Python 3.12+**
- **Docker and Docker Compose**
- **uv** (Python package manager)
- **Hugging Face Hub Token** (for the predictor service), with permission to access the [model on HuggingFace](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-22M).

## Requesting access to the model

1. Request access to the [model](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-22M) on HuggingFace. [Log in](https://huggingface.co/login) to HuggingFace (create an account if you don't have one). You’ll see a form at the top of the [model page](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-22M) - fill it out and wait for access, this might take some time.
![hf-acccess](assets/images/hf-access.png)

2. Create a token to download the model. Create one in the [tokens section of your HuggingFace account](https://huggingface.co/settings/tokens). Read-only token should be enough:
![hf-token](assets/images/generate-token.png)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pallma-ai/pallma.git
   cd pallma
   ```

2. **Install dependencies:**
   
   Install all dependencies (CLI + SDK):
   ```bash
   make install-all
   ```
3. **Activate the virtual environment:**
   
   ```bash
   source .venv/bin/activate
   ```

## Configuration


### Environment Variables

Set the following environment variable for the predictor service:

```bash
export HUGGINGFACE_HUB_TOKEN="your_huggingface_token_here"
```

You can get a Hugging Face token from [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

## Running the Application

The project includes a CLI tool for easy management:

```bash
# Start all services
pallma start

# Display real-time statistics
pallma display

# Stop all services
pallma stop
```

The display command shows real-time statistics including:
- Total number of messages
- Percentage of allow/block decisions
- Real-time updates as messages arrive

## Services

The application consists of the following services:

- **Zookeeper**: Apache Kafka dependency
- **Kafka**: Message broker for telemetry data
- **OpenTelemetry Collector**: Collects and forwards telemetry data to Kafka
- **Processor**: Processes telemetry data from Kafka
- **Predictor**: ML service for predictions (requires Hugging Face token)

## Development

### Development Commands

```bash
# Install development dependencies
make install-dev

# Run linting
make lint

# Install specific dependency groups
make install-cli
make install-sdk
```

## Troubleshooting

1. **Network issues**: Ensure the `pallma-network` Docker network exists
2. **Hugging Face token**: Make sure `HUGGINGFACE_HUB_TOKEN` is set
3. **Port conflicts**: Check if ports 2181, 9092, 4317, 4318 are available
4. **Service health**: Use `docker-compose ps` to check service status

## License

See [LICENSE](LICENSE) file for details.