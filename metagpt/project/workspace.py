"""
Workspace Manager for MetaGPT-Pro
Handles file persistence for agent outputs including code, documents, and artifacts.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from metagpt.const import DEFAULT_WORKSPACE_ROOT


class WorkspaceManager:
    """Manages project workspace and file operations for agent outputs."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.workspace_root = DEFAULT_WORKSPACE_ROOT / "projects" / project_id
        self._ensure_structure()
        
    def _ensure_structure(self):
        """Create the standard project directory structure."""
        directories = [
            self.workspace_root,
            self.workspace_root / "docs",
            self.workspace_root / "src",
            self.workspace_root / "tests",
            self.workspace_root / "artifacts",
            self.workspace_root / "sprints",
        ]
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Workspace initialized: {self.workspace_root}")
            
    @property
    def docs_dir(self) -> Path:
        return self.workspace_root / "docs"
    
    @property
    def src_dir(self) -> Path:
        return self.workspace_root / "src"
    
    @property
    def tests_dir(self) -> Path:
        return self.workspace_root / "tests"
    
    @property
    def artifacts_dir(self) -> Path:
        return self.workspace_root / "artifacts"
    
    @property
    def sprints_dir(self) -> Path:
        return self.workspace_root / "sprints"
    
    def save_prd(self, content: str, metadata: Optional[Dict] = None) -> Path:
        """Save Product Requirements Document."""
        file_path = self.docs_dir / "PRD.md"
        self._write_file(file_path, content)
        if metadata:
            self._save_metadata(file_path, metadata)
        logger.info(f"PRD saved: {file_path}")
        return file_path
    
    def save_system_design(self, content: str, metadata: Optional[Dict] = None) -> Path:
        """Save System Design Document."""
        file_path = self.docs_dir / "SYSTEM_DESIGN.md"
        self._write_file(file_path, content)
        if metadata:
            self._save_metadata(file_path, metadata)
        logger.info(f"System Design saved: {file_path}")
        return file_path
    
    def save_api_spec(self, content: str, metadata: Optional[Dict] = None) -> Path:
        """Save API Specification Document."""
        file_path = self.docs_dir / "API_SPEC.md"
        self._write_file(file_path, content)
        if metadata:
            self._save_metadata(file_path, metadata)
        logger.info(f"API Spec saved: {file_path}")
        return file_path
    
    def save_source_file(self, filename: str, content: str, subdirectory: str = "") -> Path:
        """Save a source code file."""
        if subdirectory:
            target_dir = self.src_dir / subdirectory
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.src_dir
        file_path = target_dir / filename
        self._write_file(file_path, content)
        logger.info(f"Source file saved: {file_path}")
        return file_path
    
    def save_test_file(self, filename: str, content: str, subdirectory: str = "") -> Path:
        """Save a test file."""
        if subdirectory:
            target_dir = self.tests_dir / subdirectory
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.tests_dir
        file_path = target_dir / filename
        self._write_file(file_path, content)
        logger.info(f"Test file saved: {file_path}")
        return file_path
    
    def save_artifact(self, name: str, content: str, artifact_type: str = "general") -> Path:
        """Save a general artifact (sprint reviews, meeting notes, etc.)."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{artifact_type}_{name}_{timestamp}.md"
        file_path = self.artifacts_dir / filename
        self._write_file(file_path, content)
        logger.info(f"Artifact saved: {file_path}")
        return file_path
    
    def save_sprint_data(self, sprint_id: str, data: Dict[str, Any]) -> Path:
        """Save sprint data as JSON."""
        file_path = self.sprints_dir / f"{sprint_id}.json"
        self._write_json(file_path, data)
        logger.info(f"Sprint data saved: {file_path}")
        return file_path
    
    def save_backlog(self, stories: List[Dict[str, Any]]) -> Path:
        """Save backlog stories."""
        file_path = self.workspace_root / "backlog.json"
        self._write_json(file_path, {"stories": stories, "updated_at": datetime.now().isoformat()})
        logger.info(f"Backlog saved: {file_path}")
        return file_path
    
    def save_project_manifest(self, manifest: Dict[str, Any]) -> Path:
        """Save project manifest/metadata."""
        file_path = self.workspace_root / "project.json"
        manifest["updated_at"] = datetime.now().isoformat()
        self._write_json(file_path, manifest)
        logger.info(f"Project manifest saved: {file_path}")
        return file_path
    
    def get_file_tree(self) -> Dict[str, Any]:
        """Get the file tree structure of the workspace."""
        return self._build_tree(self.workspace_root)
    
    def get_file_content(self, relative_path: str) -> Optional[str]:
        """Get content of a file by relative path."""
        file_path = self.workspace_root / relative_path
        if file_path.exists() and file_path.is_file():
            return file_path.read_text(encoding='utf-8')
        return None
    
    def list_files(self, directory: str = "") -> List[Dict[str, Any]]:
        """List files in a directory with metadata."""
        target_dir = self.workspace_root / directory if directory else self.workspace_root
        if not target_dir.exists():
            return []
        
        files = []
        for item in target_dir.iterdir():
            stat = item.stat()
            files.append({
                "name": item.name,
                "path": str(item.relative_to(self.workspace_root)),
                "is_directory": item.is_dir(),
                "size": stat.st_size if item.is_file() else 0,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        return sorted(files, key=lambda x: (not x["is_directory"], x["name"]))
    
    def _write_file(self, path: Path, content: str):
        """Write content to a file."""
        path.write_text(content, encoding='utf-8')
        
    def _write_json(self, path: Path, data: Dict[str, Any]):
        """Write JSON data to a file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
            
    def _save_metadata(self, file_path: Path, metadata: Dict):
        """Save metadata alongside a file."""
        meta_path = file_path.with_suffix(file_path.suffix + '.meta.json')
        metadata['saved_at'] = datetime.now().isoformat()
        self._write_json(meta_path, metadata)
        
    def _build_tree(self, path: Path, prefix: str = "") -> Dict[str, Any]:
        """Recursively build a file tree structure."""
        tree = {
            "name": path.name,
            "path": str(path.relative_to(self.workspace_root)) if path != self.workspace_root else "",
            "type": "directory" if path.is_dir() else "file",
        }
        
        if path.is_dir():
            tree["children"] = []
            for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
                if not item.name.startswith('.'):
                    tree["children"].append(self._build_tree(item))
        else:
            tree["size"] = path.stat().st_size
            tree["extension"] = path.suffix
            
        return tree


# Global workspace cache
_workspace_cache: Dict[str, WorkspaceManager] = {}


def get_workspace(project_id: str) -> WorkspaceManager:
    """Get or create a workspace manager for a project."""
    if project_id not in _workspace_cache:
        _workspace_cache[project_id] = WorkspaceManager(project_id)
    return _workspace_cache[project_id]


def clear_workspace_cache():
    """Clear the workspace cache."""
    _workspace_cache.clear()
