import os
import zipfile
import io
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.config2 import config

router = APIRouter()

def get_workspace_root() -> Path:
    # Use config workspace path or default
    return Path(config.workspace.path) if config.workspace.path else DEFAULT_WORKSPACE_ROOT


@router.get("/tree")
async def list_files(path: str = ""):
    """List files in the workspace (directory tree)"""
    root = get_workspace_root()
    target = root / path
    
    # Security check
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: Path outside workspace.")
    
    if not target.exists():
         raise HTTPException(status_code=404, detail="Path not found.")
    
    if not target.is_dir():
        return {"type": "file", "name": target.name, "size": target.stat().st_size}
        
    items = []
    for item in target.iterdir():
        stat = item.stat()
        items.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "size": stat.st_size if item.is_file() else 0,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    return {"path": str(path), "items": sorted(items, key=lambda x: (x["type"] != "directory", x["name"]))}


@router.get("/content")
async def get_file_content(path: str):
    """Read file content"""
    root = get_workspace_root()
    target = root / path
    
    # Security check
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: Path outside workspace.")
        
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
        
    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        return {"path": path, "content": content, "size": target.stat().st_size}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Cannot read binary file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}/tree")
async def get_project_files(project_id: str, path: str = ""):
    """Get file tree for a specific project"""
    root = get_workspace_root() / "projects" / project_id
    
    if not root.exists():
        raise HTTPException(status_code=404, detail="Project workspace not found.")
    
    target = root / path if path else root
    
    # Security check
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: Path outside project workspace.")
    
    if not target.exists():
        return {"path": path, "items": [], "project_id": project_id}
    
    if not target.is_dir():
        stat = target.stat()
        return {
            "type": "file",
            "name": target.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    
    items = []
    for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
        if not item.name.startswith('.'):
            stat = item.stat()
            items.append({
                "name": item.name,
                "path": str(item.relative_to(root)),
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else 0,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": item.suffix if item.is_file() else None
            })
    
    return {
        "project_id": project_id,
        "path": path,
        "items": items
    }


@router.get("/project/{project_id}/content")
async def get_project_file_content(project_id: str, path: str):
    """Get content of a file in a project workspace"""
    root = get_workspace_root() / "projects" / project_id
    
    if not root.exists():
        raise HTTPException(status_code=404, detail="Project workspace not found.")
    
    target = root / path
    
    # Security check
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: Path outside project workspace.")
    
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    
    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        stat = target.stat()
        return {
            "project_id": project_id,
            "path": path,
            "name": target.name,
            "content": content,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": target.suffix
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Cannot read binary file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}/download")
async def download_project(project_id: str):
    """Download entire project as a ZIP file"""
    root = get_workspace_root() / "projects" / project_id
    
    if not root.exists():
        raise HTTPException(status_code=404, detail="Project workspace not found.")
    
    # Create zip in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in root.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                arc_name = file_path.relative_to(root)
                zip_file.write(file_path, arc_name)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={project_id}.zip"
        }
    )


@router.get("/project/{project_id}/artifacts")
async def get_project_artifacts(project_id: str):
    """Get list of project artifacts (documents, designs, etc.)"""
    root = get_workspace_root() / "projects" / project_id
    
    if not root.exists():
        return {"project_id": project_id, "artifacts": []}
    
    artifacts = []
    
    # Documents
    docs_dir = root / "docs"
    if docs_dir.exists():
        for item in docs_dir.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                stat = item.stat()
                artifacts.append({
                    "name": item.name,
                    "path": f"docs/{item.name}",
                    "type": "document",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    # Source code
    src_dir = root / "src"
    if src_dir.exists():
        for item in src_dir.rglob('*'):
            if item.is_file() and not item.name.startswith('.'):
                stat = item.stat()
                artifacts.append({
                    "name": item.name,
                    "path": str(item.relative_to(root)),
                    "type": "source",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    # Tests
    tests_dir = root / "tests"
    if tests_dir.exists():
        for item in tests_dir.rglob('*'):
            if item.is_file() and not item.name.startswith('.'):
                stat = item.stat()
                artifacts.append({
                    "name": item.name,
                    "path": str(item.relative_to(root)),
                    "type": "test",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    # Artifacts (sprint reviews, etc.)
    artifacts_dir = root / "artifacts"
    if artifacts_dir.exists():
        for item in artifacts_dir.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                stat = item.stat()
                artifacts.append({
                    "name": item.name,
                    "path": f"artifacts/{item.name}",
                    "type": "artifact",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    return {
        "project_id": project_id,
        "artifacts": sorted(artifacts, key=lambda x: x["modified"], reverse=True)
    }
