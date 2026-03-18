import requests
from fastapi import HTTPException, status
from app.core.config import settings

DEVOPS_SYSTEM_PROMPT = """You are an expert DevOps AI Assistant dedicated to helping engineers with all aspects of modern DevOps and platform engineering. Your specialisations include:

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

# VISION_MODELS = ["gpt-4o", "gpt-4o-mini", "llava", "vision-model"]

def cloud_chat(messages, model: str | None = None, image_base64: str | None = None) -> tuple[str, int]:
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    model_name = model or settings['CLOUD_MODEL']

    if image_base64:
        # if model_name not in VISION_MODELS:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Model '{model_name}' does not support image input"
        #     )

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": messages[0]["content"]},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                }
            ]
        }]

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
                "model": model_name,
                "messages": payload_messages,
                "stream": False,
            },
            timeout=int(settings['CLOUD_TIMEOUT']),
        )
        response.raise_for_status()

    except requests.Timeout:
        raise HTTPException(504, "AI timeout")

    except requests.ConnectionError:
        raise HTTPException(503, "AI connection failed")

    except requests.HTTPError:
        raise HTTPException(502, "AI service error")

    try:
        data = response.json()
        content: str = data["message"]["content"]
        tokens: int = data.get("eval_count", 0)
        return content, tokens

    except (KeyError, ValueError):
        raise HTTPException(500, "Invalid AI response format")
    
def get_cloud_models() -> list[str]:
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