import requests
from fastapi import HTTPException, status

from app.core.config import settings

# DevOps System Prompt

DEVOPS_SYSTEM_PROMPT = """You are an expert DevOps AI Assistant dedicated to helping \
engineers with all aspects of modern DevOps and platform engineering. Your specialisations include:

- CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins, CircleCI, ArgoCD)
- Containerisation & orchestration (Docker, Kubernetes, Helm, Kustomize)
- Cloud platforms & services (AWS, GCP, Azure — infra, networking, IAM, cost)
- Infrastructure as Code (Terraform, Pulumi, Ansible, CloudFormation)
- Monitoring, observability & alerting (Prometheus, Grafana, ELK/OpenSearch, Datadog, PagerDuty)
- Secrets management (Vault, AWS Secrets Manager, Sealed Secrets)
- Networking (DNS, TLS, load balancing, service meshes like Istio/Linkerd)
- Security & compliance (SAST, DAST, image scanning, RBAC, CIS benchmarks)
- Site Reliability Engineering (SLOs, SLIs, incident response, chaos engineering)

Guidelines:
- Provide clear, concise, technically accurate answers.
- Always include practical commands, code snippets, or YAML/HCL examples where relevant.
- Call out common pitfalls and production best practices.
- When multiple approaches exist, briefly compare them and recommend the best fit.
- If a question is outside DevOps scope, politely redirect the user."""


#  Cloud AI Client 

def cloud_chat(
    messages: list[dict],
    model: str | None = None,
) -> tuple[str, int]:
    """
    Send a conversation to the cloud AI endpoint and return (response_text, tokens_used).

    ``messages`` should be a list of ``{"role": "user"|"assistant", "content": "..."}``
    dicts representing the full conversation history up to and including the latest
    user turn. The DevOps system prompt is prepended automatically.
    """
    payload_messages = [
        {"role": "system", "content": DEVOPS_SYSTEM_PROMPT},
        *messages,
    ]

    try:
        response = requests.post(
            f"{settings['CLOUD_API_BASE_URL']}/api/chat",
            headers={
                "Authorization": f"Bearer {settings['CLOUD_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or settings['CLOUD_MODEL'],
                "messages": payload_messages,
                "stream": False,
            },
            timeout=int(settings['CLOUD_TIMEOUT']),
        )

    except requests.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI service did not respond in time. Please try again.",
        )

    except requests.ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect to the AI service.",
        )

    except requests.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service returned an unexpected error.",
        )

    try:
        print("Raw response from AI service:", response.json())  # Debug log
        data = response.json()
        print("Received response from AI service:", data)  # Debug log
        content: str = data["message"]["content"]
        tokens: int = data.get("eval_count", 0)
        return content, tokens

    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Received an unrecognised response format from the AI service.",
        )


def get_cloud_models() -> list[str]:
    """Return the list of model names available on the cloud endpoint."""
    try:
        response = requests.get(
            f"{settings['CLOUD_API_BASE_URL']}/api/tags",
            headers={"Authorization": f"Bearer {settings['CLOUD_API_KEY']}"},
            timeout=int(settings['CLOUD_TIMEOUT']),
        )
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]

    except requests.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timed out while fetching available models.",
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not retrieve the model list from the AI service.",
        )