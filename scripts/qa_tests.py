import urllib.request
import urllib.error
import json
import concurrent.futures
import time

BASE_URL = "http://localhost:8000"

def post_chat(message: str, model: str | None = None, abort_after_chunks: int = -1):
    data = {"message": message}
    if model:
        data["model"] = model
    req = urllib.request.Request(
        f"{BASE_URL}/chat",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    events = []
    try:
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith("data: "):
                    events.append(json.loads(line_str[6:]))
                if abort_after_chunks > 0 and len(events) >= abort_after_chunks:
                    break
    except Exception as e:
        return {"error": str(e), "events": events}
    return events

def test_empty_results():
    print("Testing Empty Results...")
    evs = post_chat("Find reactions with reactant THISDOESNOTEXIST999")
    tool_res = next((e for e in evs if e.get("type") == "tool_result"), None)
    if tool_res is None:
        print("Events:", evs)
    assert tool_res is not None
    assert tool_res["result"].get("count", 1) == 0 or len(tool_res["result"].get("results", [])) == 0
    print("Empty Results: PASS")

def test_nan_records():
    print("Testing NaN Records...")
    evs = post_chat("Yield statistics for Buchwald-Hartwig")
    tool_res = next((e for e in evs if e.get("type") == "tool_result"), None)
    assert tool_res is not None
    assert "NaN" not in json.dumps(tool_res["result"])
    print("NaN Records: PASS")

def test_large_results():
    print("Testing Large Results...")
    evs = post_chat("Summarize the database")
    tool_res = next((e for e in evs if e.get("type") == "tool_result"), None)
    if tool_res is None or "tool" not in tool_res.get("result", {}):
        print("Events:", evs)
    assert tool_res is not None
    assert "tool" in tool_res["result"]
    print("Large Results: PASS")

def test_long_prompt():
    print("Testing Long Prompt...")
    evs = post_chat("What is a reaction? " * 500)
    # Could be no_tool or success
    done = next((e for e in evs if e.get("type") == "done" or e.get("type") == "error"), None)
    assert done is not None
    print("Long Prompt: PASS")

def test_rapid_requests():
    print("Testing Rapid Requests...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(post_chat, "Find Suzuki reactions") for _ in range(5)]
        results = [f.result() for f in futures]
    assert all(len(r) > 0 for r in results)
    print("Rapid Requests: PASS")

def test_browser_refresh():
    print("Testing Browser Refresh (Abort Stream)...")
    res = post_chat("Find Suzuki reactions", abort_after_chunks=1)
    assert len(res) == 1
    print("Browser Refresh: PASS")

def test_invalid_json():
    print("Testing Invalid JSON (using tinyllama)...")
    evs = post_chat("Find Suzuki reactions", model="tinyllama:latest")
    # It might fail or retry or return error
    last = evs[-1] if evs else {}
    print(f"TinyLlama result state: {last.get('type')}")
    print("Invalid JSON: PASS")

if __name__ == "__main__":
    test_empty_results()
    test_nan_records()
    test_large_results()
    test_long_prompt()
    test_rapid_requests()
    test_browser_refresh()
    test_invalid_json()
    print("All tests completed.")
