import importlib, os, sys

def test_main_import_triggers_sentry_block(monkeypatch):
    # 設一個 dummy DSN，避免網路呼叫（sentry_sdk.init 只做本地配置）
    monkeypatch.setenv("SENTRY_DSN", "https://examplePublicKey@o0.ingest.sentry.io/0")
    # 確保每次都重新執行 module-level 邏輯
    if "src.main" in sys.modules:
        del sys.modules["src.main"]
    m = importlib.import_module("src.main")
    # 斷言 app 物件存在（代表 Flask app 與 blueprint 註冊流程已執行）
    assert hasattr(m, "app")
