# Self-Healing Kubernetes AI Agent 🚀

An autonomous AI-powered Kubernetes troubleshooting and self-healing agent. This agent listens for Kubernetes alerts, automatically collects logs from failing pods, uses a Large Language Model (LLM) to diagnose the root cause, and takes remediation actions such as restarting pods or rolling back deployments.

## Features ✨
- **Automated Alerting**: Integrates with Alertmanager to receive real-time webhook alerts from Kubernetes.
- **AI Diagnostics**: Uses LangChain/LangGraph and OpenAI models (via OpenRouter) to analyze pod logs and determine whether a crash is due to a temporary error or a bad deployment.
- **Self-Healing Actions**: Automatically executes remediation based on the AI's decision (e.g., restarting a Deployment or executing a Helm rollback).
- **Slack Notifications**: Sends detailed diagnostic reports and actions taken directly to a Slack channel.
- **CI/CD Integrated**: Includes GitHub Actions workflows for automated Docker image building and deployment to AWS EKS.

## Architecture 🏗️
- **Backend**: FastAPI (Python)
- **AI Engine**: LangGraph & `ChatOpenAI`
- **Infrastructure**: Kubernetes, Terraform, Helm
- **Monitoring**: Prometheus & Alertmanager

## Project Structure 📁
- `agent/`: Contains the FastAPI application, AI logic, and Dockerfile.
- `app/`: Sample application and tests.
- `helm/`: Helm charts for deploying both the AI Agent and the Sample App.
- `terraform/`: Infrastructure as Code (IaC) to provision cloud resources (e.g., AWS EKS).
- `.github/workflows/`: CI/CD pipelines.

## Setup & Installation 🛠️

### 1. Prerequisites
- A running Kubernetes cluster
- `kubectl` and `helm` installed locally
- API Keys for OpenRouter (OpenAI) and a Slack Webhook URL

### 2. Configure Secrets
Before deploying, make sure to configure your secrets.
- Edit `helm/ai-agent/values.yaml` and set your `openaiApiKey`.
- Set your `SLACK_WEBHOOK_URL` environment variable for Slack alerts.

### 3. Deploy via Helm
Deploy the AI agent to your Kubernetes cluster:
```bash
helm upgrade --install ai-agent ./helm/ai-agent -n app --create-namespace
```

Deploy the sample application to test the agent:
```bash
helm upgrade --install sample-app ./helm/sample-app -n app
```

## Contributing 🤝
Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

## License 📄
This project is licensed under the MIT License.
