"""Integration tests for the upload workflow."""

from fastapi.testclient import TestClient
from backend.api.main import app
import json

client = TestClient(app)

def test_upload_success_and_formatter_bypass():
    # 1. Upload valid JSON
    upload_payload = {
        "format": "json",
        "content": json.dumps({
            "reaction_type": "Buchwald-Hartwig amination",
            "reactants": ["Aniline", "Bromobenzene"],
            "reagents": ["Sodium tert-butoxide"],
            "catalysts": ["Pd2(dba)3"],
            "products": ["Diphenylamine"],
            "temperature_c": 100,
            "yield_percent": 82
        })
    }
    
    upload_res = client.post("/experiments/compare", json=upload_payload)
    assert upload_res.status_code == 200
    
    data = upload_res.json()
    assert "comparisons" in data
    assert len(data["comparisons"]) == 1
    
    report = data["comparisons"][0]
    assert report["is_valid"] is True
    
    # 2. Verify similarities return 0 (due to Diphenylamine missing)
    assert report["comparisons"]["similar_reactions"]["total_matching"] == 0
    
    # 3. Verify yield classification is present
    assert report["comparisons"]["optimal_conditions"]["yield_classification"] in ["Comparable", "Excellent Match", "Slightly Below Optimal", "Suboptimal"]
    
    # 4. Trigger formatter bypass in chat
    chat_payload = {
        "message": "Summarize this upload",
        "tool_result_override": report,
        "tool_name_override": "upload_comparison"
    }
    
    chat_res = client.post("/chat", json=chat_payload)
    assert chat_res.status_code == 200
    
    # Just verify that it streamed and bypassed planner
    text_content = chat_res.text
    assert "tool_selected" in text_content
    assert "upload_comparison" in text_content

def test_upload_failure():
    # Upload missing required fields
    upload_payload = {
        "format": "json",
        "content": json.dumps({
            "reaction_type": "Buchwald-Hartwig amination"
        })
    }
    
    upload_res = client.post("/experiments/compare", json=upload_payload)
    assert upload_res.status_code == 200
    
    data = upload_res.json()
    report = data["comparisons"][0]
    assert report["is_valid"] is False
    assert len(report["warnings"]) > 0
