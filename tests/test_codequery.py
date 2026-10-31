import os
import sys
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from app.services.code_parser import parse_python_file, scan_repository
from app.services.code_chunker import create_code_chunks
from app.services.graph_service import (
    build_repository_graph,
    expand_structural_context,
    get_graph_statistics
)
from app.services.vector_store import search_code, get_indexed_repositories
from app.services.rag_service import _extract_citations
from app.main import app
from fastapi.testclient import TestClient


def test_code_parser_extracts_ast_entities(tmp_path):
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        '"""Module docstring."""\n'
        'import os\n'
        'from math import sqrt\n\n'
        'class BaseCalculator:\n'
        '    """Base class doc."""\n'
        '    pass\n\n'
        'class AdvancedCalculator(BaseCalculator):\n'
        '    """Advanced calc doc."""\n'
        '    def calculate(self, x, y):\n'
        '        """Method doc."""\n'
        '        return sqrt(x) + y\n\n'
        'def helper():\n'
        '    c = AdvancedCalculator()\n'
        '    return c.calculate(4, 5)\n'
    )

    parsed = parse_python_file(str(sample_file))
    assert parsed["file"] == str(sample_file)
    assert len(parsed["classes"]) == 2
    assert parsed["classes"][1]["name"] == "AdvancedCalculator"
    assert parsed["classes"][1]["bases"] == ["BaseCalculator"]
    assert len(parsed["functions"]) >= 2
    assert any(fn["name"] == "calculate" for fn in parsed["functions"])


def test_graph_builder_and_expansion(tmp_path):
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        'class BaseService:\n'
        '    pass\n\n'
        'class AuthService(BaseService):\n'
        '    def login(self, user):\n'
        '        return self.verify(user)\n'
        '    def verify(self, user):\n'
        '        return True\n'
    )

    parsed = parse_python_file(str(sample_file))
    G = build_repository_graph([parsed], repo_name="test_repo")

    assert G.number_of_nodes() > 0
    assert G.number_of_edges() > 0

    stats = get_graph_statistics("test_repo")
    assert stats["available"] is True
    assert stats["total_nodes"] > 0

    # Expand structural context around AuthService
    retrieved = [{
        "name": "AuthService.login",
        "type": "method",
        "file": str(sample_file),
        "start_line": 5,
        "end_line": 6
    }]
    expansion = expand_structural_context("test_repo", retrieved)
    assert expansion["has_graph"] is True


def test_chunker_preserves_metadata(tmp_path):
    sample_file = tmp_path / "math_ops.py"
    sample_file.write_text(
        'def multiply(a, b):\n'
        '    """Multiply two numbers."""\n'
        '    return a * b\n'
    )
    parsed = parse_python_file(str(sample_file))
    chunks = create_code_chunks(parsed)
    assert len(chunks) == 1
    assert chunks[0]["name"] == "multiply"
    assert chunks[0]["type"] == "function"
    assert chunks[0]["docstring"] == "Multiply two numbers."


def test_citation_extraction():
    answer_text = (
        "The authentication is handled in [auth.py:42-50] by create_token.\n"
        "It also checks user status in [users.py:100]."
    )
    chunks = [
        {"rel_path": "auth.py", "start_line": 42, "end_line": 50, "code": "def create_token(): pass"},
        {"rel_path": "users.py", "start_line": 100, "end_line": 120, "code": "def check_user(): pass"}
    ]
    citations = _extract_citations(answer_text, chunks)
    assert len(citations) >= 2
    assert any(c["file"] == "auth.py" for c in citations)


def test_api_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["features"]["structural_graph"] is True


def test_api_repositories_endpoint():
    client = TestClient(app)
    response = client.get("/repositories")
    assert response.status_code == 200
    data = response.json()
    assert "repositories" in data
    assert "indexed_names" in data
