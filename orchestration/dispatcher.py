from typing import Dict, Any, List, Optional
import json
import os

try:
    from google.cloud import pubsub_v1
except Exception:  # Package may not be installed yet
    pubsub_v1 = None

try:
    from google.cloud import tasks_v2
    from google.protobuf import timestamp_pb2
except Exception:
    tasks_v2 = None
    timestamp_pb2 = None


class DispatchResult:
    def __init__(self, step_id: str, ok: bool, method: str, detail: Optional[str] = None):
        self.step_id = step_id
        self.ok = ok
        self.method = method
        self.detail = detail

    def dict(self) -> Dict[str, Any]:
        return {"step_id": self.step_id, "ok": self.ok, "method": self.method, "detail": self.detail}


def _get_project_id() -> Optional[str]:
    return os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")


def _pubsub_topic_path(topic_name: str) -> Optional[str]:
    project = _get_project_id()
    if not project or not topic_name:
        return None
    return f"projects/{project}/topics/{topic_name}"


def dispatch_via_pubsub(workflow_id: str, step: Dict[str, Any]) -> DispatchResult:
    topic_name = os.environ.get("WORKFLOW_PUBSUB_TOPIC")
    if not topic_name:
        return DispatchResult(step_id=step.get("id", ""), ok=False, method="pubsub", detail="WORKFLOW_PUBSUB_TOPIC not set")
    if not pubsub_v1:
        return DispatchResult(step_id=step.get("id", ""), ok=False, method="pubsub", detail="google-cloud-pubsub not installed")
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = _pubsub_topic_path(topic_name)
        data = json.dumps({"workflow_id": workflow_id, "step": step}, ensure_ascii=False).encode("utf-8")
        future = publisher.publish(topic_path, data=data, workflow_id=workflow_id, step_id=str(step.get("id", "")))
        future.result(timeout=10)
        return DispatchResult(step_id=step.get("id", ""), ok=True, method="pubsub", detail=f"Published to {topic_name}")
    except Exception as e:
        return DispatchResult(step_id=step.get("id", ""), ok=False, method="pubsub", detail=str(e))


def dispatch_via_cloud_tasks(workflow_id: str, step: Dict[str, Any]) -> DispatchResult:
    queue_name = os.environ.get("DISPATCH_QUEUE")
    region = os.environ.get("GOOGLE_CLOUD_REGION") or os.environ.get("LOCATION") or "europe-west1"
    target_url_base = os.environ.get("TARGET_URL_BASE")  # e.g., service URL if calling back to self
    if not queue_name:
        return DispatchResult(step_id=step.get("id", ""), ok=False, method="cloud_tasks", detail="DISPATCH_QUEUE not set")
    if not tasks_v2:
        return DispatchResult(step_id=step.get("id", ""), ok=False, method="cloud_tasks", detail="google-cloud-tasks not installed")
    if not target_url_base:
        return DispatchResult(step_id=step.get("id", ""), ok=False, method="cloud_tasks", detail="TARGET_URL_BASE not set")
    try:
        client = tasks_v2.CloudTasksClient()
        project = _get_project_id()
        parent = client.queue_path(project, region, queue_name)
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target_url_base}/api/flows/{workflow_id}/step",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(step).encode("utf-8"),
            }
        }
        response = client.create_task(parent=parent, task=task)
        return DispatchResult(step_id=step.get("id", ""), ok=True, method="cloud_tasks", detail=f"Enqueued task {response.name}")
    except Exception as e:
        return DispatchResult(step_id=step.get("id", ""), ok=False, method="cloud_tasks", detail=str(e))


def dispatch_steps(workflow_id: str, steps: List[Dict[str, Any]]) -> List[DispatchResult]:
    results: List[DispatchResult] = []
    for step in steps:
        # First try Pub/Sub, then Cloud Tasks
        r_pubsub = dispatch_via_pubsub(workflow_id, step)
        results.append(r_pubsub)
        if not r_pubsub.ok:
            r_tasks = dispatch_via_cloud_tasks(workflow_id, step)
            results.append(r_tasks)
    return results