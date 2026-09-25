import asyncio
import importlib
import sys


def test_main_app_loads_without_api_credentials(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    for module_name in ["main", "MarketInsight.components.agent"]:
        sys.modules.pop(module_name, None)

    main_module = importlib.import_module("main")

    payload = asyncio.run(main_module.health_check())
    assert payload["status"] == "ok"
    assert main_module.app is not None
