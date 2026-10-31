from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.demo_web import attach_demo_web


def test_downloaded_demo_build_serves_pages_and_assets():
    build = Path(__file__).resolve().parents[2] / "demo-web"
    app = FastAPI()
    attach_demo_web(app, str(build))
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert "Остров Денег" in client.get("/auth").text
    assert client.get("/island").status_code == 200
    assert client.get("/api/missing").status_code == 404
    assert client.get("/missing.js").status_code == 404
    assert client.get("/favicon.ico").headers["content-type"].startswith("image/x-icon")
    assert client.get("/favicon.svg").headers["content-type"].startswith("image/svg+xml")
    for asset in (build / "assets").iterdir():
        assert client.get(f"/assets/{asset.name}").status_code == 200
