import asyncio
import uuid
import time
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import yaml
from loguru import logger
import nest_asyncio
nest_asyncio.apply() 
from fastapi.background import BackgroundTasks
import redis
#from .tasks import run_optimization_celery
import json
from metagpt.ext.spo_api_backend.tasks import run_optimization_celery
from metagpt.ext.spo_api_backend.schemas import OptimizationResponse, TaskStatus, RoundResult

r = redis.Redis(decode_responses=True)




def save_task_to_redis(task: OptimizationResponse):
    r.set(f"task:{task.task_id}", task.json())


def load_task_from_redis(task_id: str) -> Optional[OptimizationResponse]:
    raw = r.get(f"task:{task_id}")
    if not raw:
        return None
    return OptimizationResponse.parse_raw(raw)



# Startup script for solving path problems
def setup_metagpt_environment():
    """Set up MetaGPT environment"""
    current_file = Path(__file__).absolute()
    
    # Try multiple possible MetaGPT root directory locations
    possible_roots = [
        current_file.parent.parent.parent,  # if in metagpt/ext/spo/ 
        current_file.parent.parent.parent.parent,  # If deeper
        Path.cwd(),  # 当Previous Work Catalog
        Path.cwd().parent,  # parent directory
    ]
    
    metagpt_root = None
    for root in possible_roots:
        if (root / "metagpt" / "__init__.py").exists():
            metagpt_root = root
            break
    
    if metagpt_root is None:
        # If not found, use the parent directory of the current directory
        metagpt_root = current_file.parent.parent.parent
        print(f"Warning: Could not auto-detect MetaGPT root, using: {metagpt_root}")
    
    # 添加到 Python 路径
    if str(metagpt_root) not in sys.path:
        sys.path.insert(0, str(metagpt_root))
    
    # 设置环境变量
    os.environ['METAGPT_ROOT'] = str(metagpt_root)
    
    return metagpt_root

# 设置环境
METAGPT_ROOT = setup_metagpt_environment()

# 尝试导入 MetaGPT 模块
try:
    from metagpt.ext.spo.components.optimizer import PromptOptimizer
    from metagpt.ext.spo.utils.llm_client import SPO_LLM
    print("✓ Successfully imported MetaGPT modules")
except ImportError as e:
    print(f"❌ Failed to import MetaGPT modules: {e}")
    print(f"Current directory: {Path.cwd()}")
    print(f"Script directory: {Path(__file__).parent}")
    print(f"MetaGPT root: {METAGPT_ROOT}")
    print(f"Python path: {sys.path[:3]}...")  # 只显示前几个路径
    
    # 提供详细的错误信息和解决方案
    print("\n🔧 Troubleshooting steps:")
    print("1. Make sure you're running this script from the correct directory")
    print("2. Check if MetaGPT is properly installed")
    print("3. Try running: pip install -e . (from MetaGPT root directory)")
    print("4. Or set PYTHONPATH manually: export PYTHONPATH=/path/to/MetaGPT:$PYTHONPATH")
    
    raise SystemExit(1)


# Pydantic Models
class ModelConfig(BaseModel):
    model: str
    temperature: float = Field(ge=0.0, le=1.0)


class OptimizationRequest(BaseModel):
    optimization_model: ModelConfig
    evaluation_model: ModelConfig
    execution_model: ModelConfig
    template_path: str
    initial_round: int = Field(ge=1, le=100, default=1)
    max_rounds: int = Field(ge=1, le=100, default=10)
    task_name: Optional[str] = None


class RoundResult(BaseModel):
    round: int
    prompt: str
    succeed: bool
    tokens: Optional[int] = None
    answers: Optional[List[Dict]] = None


class OptimizationResponse(BaseModel):
    task_id: str
    status: str  # "running", "completed", "failed"
    results: List[RoundResult] = []
    last_successful_prompt: Optional[str] = None
    last_successful_round: Optional[int] = None
    total_rounds: int = 0
    successful_rounds: int = 0
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    elapsed_time: Optional[float] = None


class TaskStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Global storage for tasks (in production, use Redis or database)
task_storage: Dict[str, OptimizationResponse] = {}


# FastAPI app
app = FastAPI(
    title="SPO API - Self-Supervised Prompt Optimization",
    description="API for running prompt optimization tasks concurrently",
    version="1.0.0"
)


def load_yaml_template(template_path: Path) -> Dict:
    """Load YAML template from file path"""
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    raise FileNotFoundError(f"Template file not found: {template_path}")


async def run_optimization_task(task_id: str, request: OptimizationRequest):
    """Run the optimization task asynchronously"""
    try:
        # Update task status to running
        task = load_task_from_redis(task_id)
        if task:
            task.status = TaskStatus.RUNNING
            task.start_time = time.time()
            save_task_to_redis(task)
        
        logger.info(f"Starting optimization task {task_id}")
        
        # Validate template path
        template_path = Path(request.template_path)
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Initialize LLM
        SPO_LLM.initialize(
            optimize_kwargs={
                "model": request.optimization_model.model,
                "temperature": request.optimization_model.temperature
            },
            evaluate_kwargs={
                "model": request.evaluation_model.model,
                "temperature": request.evaluation_model.temperature
            },
            execute_kwargs={
                "model": request.execution_model.model,
                "temperature": request.execution_model.temperature
            },
        )
        
        # Extract template name from path
        template_name = template_path.stem
        
        # Create workspace directory
        workspace_path = f"workspace_{task_id}"
        workspace_dir = Path(workspace_path)
        workspace_dir.mkdir(exist_ok=True)
        
        # Create optimizer instance
        optimizer = PromptOptimizer(
            optimized_path=workspace_path,
            initial_round=request.initial_round,
            max_rounds=request.max_rounds,
            template=template_path.name,
            name=request.task_name or template_name,
        )
        
        # Copy template to optimizer's settings directory if needed
        optimizer_template_path = optimizer.root_path / "settings" / template_path.name
        optimizer_template_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not optimizer_template_path.exists():
            import shutil
            shutil.copy2(template_path, optimizer_template_path)
        
        # Run optimization
        if hasattr(optimizer, 'aoptimize'):
            await optimizer.aoptimize()  # 使用异步版本
        else:
            # 如果异步版本不存在，在后台线程中运行同步版本
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, optimizer.optimize)
        
        # Load results
        prompt_path = optimizer.root_path / "prompts"
        result_data = optimizer.data_utils.load_results(prompt_path)
        
        # Process results
        results = []
        last_successful_prompt = None
        last_successful_round = None
        successful_rounds = 0
        
        for result in result_data:
            round_result = RoundResult(
                round=result["round"],
                prompt=result["prompt"],
                succeed=result["succeed"],
                tokens=result.get("tokens"),
                answers=result.get("answers", [])
            )
            results.append(round_result)
            
            if result["succeed"]:
                successful_rounds += 1
                last_successful_prompt = result["prompt"]
                last_successful_round = result["round"]
        
        # Update task with results
        end_time = time.time()
        task = load_task_from_redis(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.results = results
            task.last_successful_prompt = last_successful_prompt
            task.last_successful_round = last_successful_round
            task.total_rounds = len(results)
            task.successful_rounds = successful_rounds
            task.end_time = end_time
            task.elapsed_time = end_time - task.start_time
            save_task_to_redis(task)
        
        logger.info(f"Optimization task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Optimization task {task_id} failed: {str(e)}")
        task = load_task_from_redis(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.end_time = time.time()
            if task.start_time:
                task.elapsed_time = task.end_time - task.start_time
            save_task_to_redis(task)


@app.post("/optimize", response_model=OptimizationResponse)
async def start_optimization(request: OptimizationRequest):
    task_id = str(uuid.uuid4())

    task = OptimizationResponse(
        task_id=task_id,
        status=TaskStatus.RUNNING
    )
    
    save_task_to_redis(task)

    run_optimization_celery.delay(task_id, request.dict())

    return task



@app.get("/status/{task_id}", response_model=OptimizationResponse)
async def get_task_status(task_id: str):
    """Get the status of an optimization task"""
    
    task = load_task_from_redis(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task



@app.get("/tasks", response_model=List[OptimizationResponse])
async def list_all_tasks():
    """List all optimization tasks"""
    keys = r.keys("task:*")
    tasks = [OptimizationResponse.parse_raw(r.get(k)) for k in keys]
    return tasks


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    if not r.exists(f"task:{task_id}"):
        raise HTTPException(status_code=404, detail="Task not found")
    r.delete(f"task:{task_id}")
    return {"message": f"Task {task_id} deleted successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "metagpt_root": str(METAGPT_ROOT),
        "current_dir": str(Path.cwd())
    }


@app.get("/debug")
async def debug_info():
    """Debug information endpoint"""
    return {
        "current_directory": str(Path.cwd()),
        "script_directory": str(Path(__file__).parent),
        "metagpt_root": str(METAGPT_ROOT),
        "python_path": sys.path[:5],  # 只显示前5个路径
        "environment_vars": {
            "METAGPT_ROOT": os.environ.get("METAGPT_ROOT"),
            "PYTHONPATH": os.environ.get("PYTHONPATH", "Not set")
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print(f"🚀 Starting SPO API server...")
    print(f"📁 MetaGPT root: {METAGPT_ROOT}")
    print(f"📍 Current directory: {Path.cwd()}")
    print(f"🌐 API docs will be available at: http://localhost:8000/docs")
    
    # 创建日志目录
    log_dir = METAGPT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)