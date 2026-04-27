from .celery_app import celery_app
import asyncio
import logging
import redis
import json
from metagpt.ext.spo_api_backend.schemas import OptimizationResponse

r = redis.Redis()

def redis_key(task_id: str) -> str:
    return f"task:{task_id}"

def save_task_to_redis(task: OptimizationResponse):
    r.set(redis_key(task.task_id), task.json())

def load_task_from_redis(task_id: str) -> OptimizationResponse | None:
    raw = r.get(redis_key(task_id))
    if raw:
        return OptimizationResponse.parse_raw(raw)
    return None


@celery_app.task(bind=True)
def run_optimization_celery(self, task_id: str, request_dict: dict):
    try:
        from metagpt.ext.spo_api_backend.spo_api import run_optimization_task, OptimizationRequest

        request = OptimizationRequest(**request_dict)
        asyncio.run(run_optimization_task(task_id, request))

        return {"status": "success", "task_id": task_id}

    except Exception as e:
        logging.exception(f"[Celery Task Failed] Task {task_id}: {e}")

        try:
            task = load_task_from_redis(task_id)
            if task:
                task.status = "failed"
                task.error_message = str(e)
                save_task_to_redis(task)
        except Exception:
            logging.warning(f"Couldn't update task in Redis for {task_id}")

        return {"status": "failed", "task_id": task_id, "error": str(e)}


@celery_app.task
def ping():
    return "pong"
