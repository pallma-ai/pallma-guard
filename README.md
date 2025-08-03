# pallma

Pallma is an advanced AI-powered security monitoring platform that leverages OpenTelemetry and state-of-the-art machine learning models to detect, analyze, and predict potential security threats in real-time. By combining distributed tracing with AI capabilities, it provides comprehensive security insights and proactive threat detection for modern applications and infrastructure.

## Prerequisites

Before running pallma, ensure you have the following installed:

- **Python 3.12+**
- **Docker and Docker Compose**
- **uv** (Python package manager)
- **Hugging Face Hub Token** (for the predictor service)

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

# Stop all services
pallma stop

# Display real-time statistics
pallma display
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