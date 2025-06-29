import os
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import requests
import streamlit as st
import yaml

# Historical task storage path
HISTORY_FILE = Path("spo_history.json")

###############################################################################
# -------------------------  COMPATIBILITY HELPERS ------------------------- #
###############################################################################

def safe_rerun() -> None:
    """Call `st.rerun()` if available; fall back to `st.experimental_rerun()` if not."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

###############################################################################
# ----------------------------  HISTORY PERSISTENCE ------------------------ #
###############################################################################

def load_history() -> Dict[str, Any]:
    """Load historical tasks from local files"""
    if HISTORY_FILE.exists():
        try:
            with HISTORY_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history(tasks: Dict[str, Any]) -> None:
    """Save task history to local file"""
    try:
        with HISTORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Failed to save history: {e}")

###############################################################################
# ----------------------------  API HELPER CLASS  --------------------------- #
###############################################################################

class SPOClient:
    """Lightweight client for the SPO FastAPI backend."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def start_optimization(
        self,
        optimization_model: str,
        optimization_temp: float,
        evaluation_model: str,
        evaluation_temp: float,
        execution_model: str,
        execution_temp: float,
        template_path: str,
        initial_round: int = 1,
        max_rounds: int = 10,
        task_name: str | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "optimization_model": {
                "model": optimization_model,
                "temperature": optimization_temp,
            },
            "evaluation_model": {
                "model": evaluation_model,
                "temperature": evaluation_temp,
            },
            "execution_model": {
                "model": execution_model,
                "temperature": execution_temp,
            },
            "template_path": template_path,
            "initial_round": int(initial_round),
            "max_rounds": int(max_rounds),
        }
        if task_name:
            payload["task_name"] = task_name

        res = requests.post(f"{self.base_url}/optimize", json=payload, timeout=30)
        res.raise_for_status()
        return res.json()

    def safe_get_status(self, task_id: str) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/status/{task_id}", timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as exc:  # noqa: BLE001
            return {"task_id": task_id, "status": "error", "error_message": str(exc)}

###############################################################################
# ------------------------------ TEMPLATE UTILS ---------------------------- #
###############################################################################

def generate_template_yaml(
    prompt: str,
    requirements: str,
    qa_list: List[Dict[str, str]],
    output_dir: str | Path = r"settings",
) -> str:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fname = output_dir / f"template_{uuid.uuid4().hex}.yaml"

    yaml_obj = {
        "prompt": prompt,
        "requirements": requirements,
        "count": None,
        "qa": qa_list,
    }

    with fname.open("w", encoding="utf-8") as fp:
        yaml.safe_dump(yaml_obj, fp, allow_unicode=True, sort_keys=False)

    return str(fname.resolve())

###############################################################################
# ----------------------------  STREAMLIT STATE ---------------------------- #
###############################################################################

def init_session_state() -> None:
    # 从历史文件加载任务
    history = load_history()
    st.session_state.setdefault("tasks", history)
    st.session_state.setdefault("selected_task", None)
    st.session_state.setdefault("qa_buffer", [])
    st.session_state.setdefault("current_view", "active")  # active 或 history

###############################################################################
# ----------------------------  SIDEBAR LAYOUT ----------------------------- #
###############################################################################

def sidebar() -> None:
    st.sidebar.title("🗂️ task management")
    
    # 视图切换
    view_choice = st.sidebar.radio("view mode", ["🔄 active Tasks", "📚 historical tasks"])
    st.session_state.current_view = "active" if "active" in view_choice else "history"
    
    tasks = st.session_state.tasks
    
    if st.session_state.current_view == "active":
        # 显示活跃任务（运行中或待刷新的任务）
        active_tasks = {tid: info for tid, info in tasks.items() 
                       if info.get("status") not in {"completed", "failed", "error"}}
        task_labels = ["➕ new task"] + [
            f"{tid[:8]} | {info.get('task_name', 'Unnamed')}" 
            for tid, info in active_tasks.items()
        ]
        choice = st.sidebar.radio("select task:", task_labels, index=0)
        
        if choice == "➕ new task":
            st.session_state.selected_task = None
        else:
            sel_prefix = choice.split(" | ")[0]
            for tid in active_tasks:
                if tid.startswith(sel_prefix):
                    st.session_state.selected_task = tid
                    break
        
        with st.sidebar.expander("🔄 Refresh active tasks", expanded=False):
            if st.button("🔃 Refresh all active task statuses", use_container_width=True):
                client = SPOClient()
                for tid, info in active_tasks.items():
                    updated_info = client.safe_get_status(tid)
                    tasks[tid].update(updated_info)
                save_history(tasks)
                safe_rerun()
    
    else:  # 历史视图
        # 显示所有任务，按创建时间排序
        sorted_tasks = sorted(tasks.items(), 
                            key=lambda x: x[1].get('created_at', ''), reverse=True)
        
        if not sorted_tasks:
            st.sidebar.info("There are currently no historical tasks available")
            st.session_state.selected_task = None
        else:
            task_options = {}
            for tid, info in sorted_tasks:
                status_emoji = {"completed": "✅", "failed": "❌", "error": "⚠️", "running": "🔄"}.get(info.get("status"), "❓")
                label = f"{status_emoji} {tid[:8]} | {info.get('task_name', 'Unnamed')}"
                task_options[label] = tid
            
            choice = st.sidebar.selectbox("Select historical tasks:", list(task_options.keys()))
            if choice:
                st.session_state.selected_task = task_options[choice]
            
            with st.sidebar.expander("🗑️ Manage historical tasks", expanded=False):
                if st.button("🔃 Refresh all task statuses", use_container_width=True):
                    client = SPOClient()
                    for tid, info in tasks.items():
                        if info.get("status") not in {"completed", "failed", "error"}:
                            updated_info = client.safe_get_status(tid)
                            tasks[tid].update(updated_info)
                    save_history(tasks)
                    safe_rerun()
                
                st.markdown("**Delete task:**")
                deletable = [tid for tid, info in tasks.items() 
                           if info.get("status") in {"completed", "failed", "error"}]
                
                if deletable:
                    selected_for_deletion = st.multiselect(
                        "Select the task to delete:",
                        options=deletable,
                        format_func=lambda x: f"{x[:8]} | {tasks[x].get('task_name', 'Unnamed')}"
                    )
                    
                    if selected_for_deletion and st.button("🗑️ Delete selected task", use_container_width=True):
                        for tid in selected_for_deletion:
                            tasks.pop(tid, None)
                        if st.session_state.selected_task in selected_for_deletion:
                            st.session_state.selected_task = None
                        save_history(tasks)
                        safe_rerun()
                else:
                    st.info("There are no tasks that can be deleted")

###############################################################################
# ---------------------------  QA EDITOR HELPER ----------------------------- #
###############################################################################

def show_qa_editor(in_form: bool) -> None:
    qa_list: List[Dict[str, str]] = st.session_state.qa_buffer

    for idx, pair in enumerate(qa_list):
        q, a = st.columns(2)
        pair["question"] = q.text_input(f"Question {idx+1}", value=pair.get("question", ""), key=f"q_{idx}")
        pair["answer"] = a.text_input(f"Answer {idx+1}", value=pair.get("answer", ""), key=f"a_{idx}")

    ctrl = st.columns(3)
    if in_form:
        add = ctrl[0].form_submit_button("➕ Add QA")
        rm = ctrl[1].form_submit_button("➖ Remove the last item")
        clr = ctrl[2].form_submit_button("🧹 Clear")
    else:
        add = ctrl[0].button("➕ Add QA")
        rm = ctrl[1].button("➖ Remove the last item")
        clr = ctrl[2].button("🧹 Clear")

    if add:
        qa_list.append({"question": "", "answer": ""})
    if rm and qa_list:
        qa_list.pop()
    if clr and qa_list:
        qa_list.clear()

###############################################################################
# ---------------------------  NEW TASK LAYOUT ----------------------------- #
###############################################################################

def render_new_task_ui() -> None:
    st.header("🆕 New optimization task")

    with st.form("task_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        task_name = c1.text_input("Task Name", value="my_optimization_task")
        base_url = c2.text_input("API Base URL", value="http://localhost:8000")

        st.subheader("✍️ model selection")
        models = [
            "Qwen1.5-72B-Chat-AWQ",
            "Qwen3-32B-AWQ",
            "gpt-4o",
            "claude-3-5-sonnet-20240620",
            "deepseek-chat",
        ]
        mcol = st.columns(3)
        opt_model = mcol[0].selectbox("Optimization", models, index=0)
        eval_model = mcol[1].selectbox("Evaluation", models, index=3)
        exe_model = mcol[2].selectbox("Execution", models, index=2)

        tcol = st.columns(3)
        opt_temp = tcol[0].slider("Opt Temp", 0.0, 1.0, 0.7, 0.05)
        eval_temp = tcol[1].slider("Eval Temp", 0.0, 1.0, 0.3, 0.05)
        exe_temp = tcol[2].slider("Exec Temp", 0.0, 1.0, 0.0, 0.05)

        st.divider()
        st.subheader("📑 template")
        template_path = st.text_input("template_path")

        with st.expander("🛠️ Create/Edit Template", expanded=False):
            ptxt = st.text_area("Prompt", key="tmp_prompt")
            rtxt = st.text_area("Requirements", key="tmp_req")
            st.markdown("#### QA List")
            show_qa_editor(in_form=True)
            if st.form_submit_button("⏺️ generation template", use_container_width=True):
                if not ptxt or not rtxt:
                    st.warning("Prompt and Requirements cannot be empty!")
                else:
                    BASE_DIR = Path(__file__).resolve().parent
                    output_dir = BASE_DIR.parent.parent / "spo" / "settings"
                    tpath = generate_template_yaml(ptxt, rtxt, st.session_state.qa_buffer,output_dir)
                    st.success(f"Template has been generated: {tpath}")
                    st.session_state.template_path_value = tpath
        
        # autofill
        if "template_path_value" in st.session_state and not template_path:
            template_path = st.session_state.template_path_value

        st.subheader("🔢 Round number setting")
        rcol = st.columns(2)
        init_round = int(rcol[0].number_input("Initial Round", 1, 100, 1))
        max_round = int(rcol[1].number_input("Max Rounds", 1, 100, 10))

        start_clicked = st.form_submit_button("🚀 Start optimization", use_container_width=True)

    # ---- 表单外逻辑 ---- #
    if start_clicked:
        if not template_path:
            st.error("Please provide a template or create a template!")
            st.stop()

        client = SPOClient(base_url)
        with st.spinner("Starting task..."):
            try:
                info = client.start_optimization(
                    opt_model,
                    opt_temp,
                    eval_model,
                    eval_temp,
                    exe_model,
                    exe_temp,
                    template_path,
                    init_round,
                    max_round,
                    task_name=task_name,
                )
            except Exception as e:  # noqa: BLE001
                st.error(f"FAIL TO START: {e}")
                st.stop()
        
        tid = info["task_id"]
        
        # 保存完整的任务信息
        task_info = {
            **info,
            "task_name": task_name,  # 确保保存任务名称
            "base_url": base_url,
            "created_at": datetime.now().isoformat(),
            "config": {
                "optimization_model": opt_model,
                "evaluation_model": eval_model,
                "execution_model": exe_model,
                "optimization_temp": opt_temp,
                "evaluation_temp": eval_temp,
                "execution_temp": exe_temp,
                "template_path": template_path,
                "initial_round": init_round,
                "max_rounds": max_round,
            }
        }
        
        st.session_state.tasks[tid] = task_info
        save_history(st.session_state.tasks)  # 保存到历史文件
        st.session_state.selected_task = tid
        st.success(f"✅ Task created！Task ID: {tid}")
        safe_rerun()

###############################################################################
# -------------------------  TASK DISPLAY LAYOUT --------------------------- #
###############################################################################

def render_task_view(tid: str) -> None:
    task = st.session_state.tasks[tid]
    
    # 任务标题和复制按钮
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"📊 Task: {task.get('task_name', 'Unnamed')}")
    with col2:
        if st.button("📋 Copy Task ID", key=f"copy_{tid}"):
            st.code(tid, language=None)
            st.success("Task ID has been displayed, please manually copy it")
    
    # 基本信息
    status = task.get("status", "unknown")
    status_emoji = {"completed": "✅", "failed": "❌", "error": "⚠️", "running": "🔄"}.get(status, "❓")
    st.markdown(f"**state**: {status_emoji} `{status}`")
    
    # 显示配置信息
    if "config" in task:
        config = task["config"]
        with st.expander("⚙️ Task Configuration", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Model configuration:**")
                st.markdown(f"- optimization model: `{config.get('optimization_model')}`")
                st.markdown(f"- evaluation model: `{config.get('evaluation_model')}`")
                st.markdown(f"- execution model: `{config.get('execution_model')}`")
            with col2:
                st.markdown("**parameter configuration:**")
                st.markdown(f"- Initial number of rounds: `{config.get('initial_round')}`")
                st.markdown(f"- Maximum number of rounds: `{config.get('max_rounds')}`")
                st.markdown(f"- template file: `{Path(config.get('template_path', '')).name}`")
    
    # 刷新按钮
    if st.button("🔃 Refresh the status of this task", key=f"refresh_{tid}"):
        client = SPOClient(task.get("base_url", "http://localhost:8000"))
        updated_info = client.safe_get_status(tid)
        task.update(updated_info)
        save_history(st.session_state.tasks)  # 保存更新后的状态
        safe_rerun()

    # 任务统计
    if status in {"completed", "failed"}:
        st.markdown(
            f"**用时**: {task.get('elapsed_time', 0):.2f}s | **Number of successful rounds**: {task.get('successful_rounds', 0)} / {task.get('total_rounds', 0)}"
        )

    # 结果显示
    if "results" in task and task["results"]:
        st.subheader("📈 Round Details")
        for res in task["results"]:
            emoji = "✅" if res.get("succeed") else "❌"
            with st.expander(f"Round {res['round']} {emoji}"):
                st.markdown("**Prompt**")
                st.code(res.get("prompt", ""), language="text")
                if res.get("answers"):
                    st.markdown("**Q&A Result**")
                    for qa in res.get("answers", []):
                        st.markdown(f"- **{qa['question']}**: {qa['answer']}")
    elif status == "running":
        st.info("The task is running, refresh later to see the results...")
    elif status == "error":
        st.error(f"task exception: {task.get('error_message')}")

###############################################################################
# --------------------------------- MAIN ----------------------------------- #
###############################################################################

def main() -> None:
    st.set_page_config("SPO Prompt Optimizer", layout="wide")
    init_session_state()
    sidebar()
    
    sel = st.session_state.selected_task
    if sel is None:
        if st.session_state.current_view == "active":
            render_new_task_ui()
        else:
            st.info("Please select a historical task from the left to view details")
    else:
        render_task_view(sel)

if __name__ == "__main__":
    main()