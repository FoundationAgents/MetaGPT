#!/usr/bin/env python3
"""
测试多行 JSON 解析修复效果
验证 Ollama 流式响应的多行 JSON 能否正确解析
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from metagpt.provider.ollama_api import OllamaMessageBase
from metagpt.provider.general_api_requestor import OpenAIResponse

def test_multiline_json_parsing():
    """测试多行 JSON 解析"""
    print("=== 测试多行 JSON 解析修复 ===")
    
    # 创建测试实例
    test_instance = OllamaMessageBase("test-model")
    
    # 模拟 Ollama 的多行 JSON 流式响应
    multiline_json = '''{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.077785192Z","message":{"role":"assistant","content":"```"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.171392192Z","message":{"role":"assistant","content":"```python"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.265999192Z","message":{"role":"assistant","content":"```python\n"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.360606192Z","message":{"role":"assistant","content":"```python\n# "},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.455213192Z","message":{"role":"assistant","content":"```python\n# P"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.549820192Z","message":{"role":"assistant","content":"```python\n# Pr"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.644427192Z","message":{"role":"assistant","content":"```python\n# Pro"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.739034192Z","message":{"role":"assistant","content":"```python\n# Proj"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.833641192Z","message":{"role":"assistant","content":"```python\n# Proje"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:46.928248192Z","message":{"role":"assistant","content":"```python\n# Projec"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.022855192Z","message":{"role":"assistant","content":"```python\n# Project"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.117462192Z","message":{"role":"assistant","content":"```python\n# Project "},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.212069192Z","message":{"role":"assistant","content":"```python\n# Project P"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.306676192Z","message":{"role":"assistant","content":"```python\n# Project Pl"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.401283192Z","message":{"role":"assistant","content":"```python\n# Project Pla"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.495890192Z","message":{"role":"assistant","content":"```python\n# Project Plan"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.590497192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.685104192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\n"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.779711192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nT"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.874318192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nTh"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:47.968925192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThi"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.063532192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.158139192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis "},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.252746192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis i"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.347353192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.441960192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is "},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.536567192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.631174192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a "},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.725781192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a p"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.820388192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a pr"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:48.914995192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a pro"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.009602192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a proj"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.104209192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a proje"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.198816192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a projec"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.293423192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.388030192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project "},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.482637192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project p"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.577244192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project pl"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.671851192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project pla"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.766458192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.861065192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan "},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:49.955672192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan f"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.050279192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan fo"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.144886192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.239493192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for "},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.334100192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for t"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.428707192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for te"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.523314192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for tes"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.617921192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.712528192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.807135192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_p"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.901742192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_pr"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:50.996349192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_pro"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.090956192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_proj"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.185563192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_proje"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.280170192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_projec"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.374777192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.469384192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project."},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.563991192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.658598192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.753205192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n##"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.847812192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## "},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:51.942419192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## O"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.037026192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Ov"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.131633192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Ove"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.226240192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Over"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.320847192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overv"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.415454192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvi"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.510061192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.604668192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.699275192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.793882192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.888489192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:52.983096192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.077703192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.172310192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.266917192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.361524192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.456131192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.550738192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.645345192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.739952192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.834559192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.5:14b","created_at":"2025-07-17T17:06:53.929166192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overvie"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.023773192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.118380192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.212987192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\n"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.307594192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\nT"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.402201192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\nTh"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.496808192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\nThi"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.591415192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\nThis"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.686022192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\nThis "},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.780629192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\nThis p"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.875236192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\nThis pr"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:54.969843192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.064450192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.159057192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.253664192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.348271192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.442878192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.537485192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.632092192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.726699192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.821306192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:55.915913192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","created_at":"2025-07-17T17:06:56.010520192Z","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis\n\n## Overview\n\nThis pro"},"done":false}
{"model":"qwen2.7:14b","message":{"role":"assistant","content":"```python\n# Project Plan\n\nThis is a project plan for test_project.\n\n## Overview\n\nThis project will implement a simple login and registration system using Flask, SQLite, and Python. The system will include both backend API endpoints and frontend interfaces.\n\n## Features\n\n1. User Registration\n2. User Login\n3. Database Management\n4. Frontend Interface\n5. Testing and Bug Fixes\n\n## Technology Stack\n\n- Backend: Flask (Python)\n- Database: SQLite\n- Frontend: HTML/CSS/JavaScript\n- Testing: Unit tests and integration tests\n\n## Project Structure\n\n```\ntest_project/\n├── app.py\n├── database.py\n├── models.py\n├── routes.py\n├── templates/\n│   ├── login.html\n│   ├── register.html\n│   └── dashboard.html\n├── static/\n│   ├── css/\n│   └── js/\n├── tests/\n└── requirements.txt\n```\n\n## Implementation Steps\n\n1. Set up Flask application structure\n2. Create SQLite database and models\n3. Implement authentication routes\n4. Create frontend templates\n5. Add styling and JavaScript\n6. Implement testing\n7. Bug fixes and optimization\n\n## Testing Strategy\n\n- Unit tests for each component\n- Integration tests for API endpoints\n- User acceptance testing\n- Security testing\n- Performance testing\n\n## Deployment\n\n- Local development server\n- Production-ready configuration\n- Documentation\n\nThis plan provides a comprehensive approach to building a complete login and registration system with proper testing and deployment considerations."},"done":true}'''
    
    multiline_response = OpenAIResponse(multiline_json.encode('utf-8'), {})
    
    try:
        # 测试多行 JSON 解析
        result = test_instance.decode(multiline_response)
        print(f"✅ 多行 JSON 解析成功")
        print(f"解析结果类型: {type(result)}")
        
        if isinstance(result, dict):
            if "message" in result:
                content = result["message"].get("content", "")
                print(f"✅ 提取到内容: {content[:100]}...")
            elif "error" in result:
                print(f"❌ 解析错误: {result['error']}")
            else:
                print(f"⚠️ 未知响应格式: {result}")
        else:
            print(f"⚠️ 意外响应类型: {type(result)}")
            
    except Exception as e:
        print(f"❌ 多行 JSON 解析测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_single_json_parsing():
    """测试单行 JSON 解析"""
    print("\n=== 测试单行 JSON 解析 ===")
    
    from metagpt.provider.ollama_api import OllamaMessageBase
    from metagpt.provider.general_api_requestor import OpenAIResponse
    
    # 模拟单行 JSON 响应
    single_json = '{"model":"qwen2.5:14b","message":{"role":"assistant","content":"Hello, this is a test response."},"done":true}'
    single_response = OpenAIResponse(single_json.encode('utf-8'), {})
    
    # 创建测试实例
    test_instance = OllamaMessageBase("test-model")
    
    try:
        # 测试单行 JSON 解析
        result = test_instance.decode(single_response)
        print(f"✅ 单行 JSON 解析成功: {result}")
        
    except Exception as e:
        print(f"❌ 单行 JSON 解析测试失败: {e}")

if __name__ == "__main__":
    print("开始测试多行 JSON 解析修复效果...")
    
    # 测试单行 JSON 解析
    test_single_json_parsing()
    
    # 测试多行 JSON 解析
    test_multiline_json_parsing()
    
    print("\n🎉 测试完成！") 