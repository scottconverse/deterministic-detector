import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_claude_and_codex_manifests_share_identity():
    claude = read_json(".claude-plugin/plugin.json")
    codex = read_json(".codex-plugin/plugin.json")
    for field in ("name", "version", "description", "author", "repository", "license"):
        assert codex[field] == claude[field]


def test_codex_manifest_wires_all_plugin_components():
    manifest = read_json(".codex-plugin/plugin.json")
    assert manifest["skills"] == "./skills/"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert manifest["hooks"] == "./hooks/hooks.codex.json"
    for field in ("skills", "mcpServers", "hooks"):
        assert (ROOT / manifest[field]).exists()


def test_claude_and_codex_share_the_mcp_config():
    manifest = read_json(".codex-plugin/plugin.json")
    config = read_json(manifest["mcpServers"])
    assert set(config) == {"mcpServers"}
    code_graph = config["mcpServers"]["code-graph"]
    assert code_graph["command"] == "uvx"
    assert "code-review-graph==2.3.7" in code_graph["args"]


def test_codex_hook_uses_python3_and_plugin_root():
    config = read_json("hooks/hooks.codex.json")
    hook = config["hooks"]["PostToolUse"][0]["hooks"][0]
    assert hook["command"].startswith("python3 ")
    assert "${PLUGIN_ROOT}" in hook["command"]


def test_repo_marketplace_exposes_the_root_plugin():
    marketplace = read_json(".agents/plugins/marketplace.json")
    assert marketplace["name"] == "deterministic-detector"
    entry = marketplace["plugins"][0]
    assert entry["name"] == "deterministic-detector"
    assert entry["source"] == {"source": "local", "path": "./"}
    assert entry["policy"]["installation"] == "AVAILABLE"
