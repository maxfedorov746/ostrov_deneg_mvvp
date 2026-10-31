"""Serve the checked-in demo build when the Docker-free launcher requests it."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def attach_demo_web(app: FastAPI, directory: str) -> None:
    build = Path(directory).resolve()
    index = build / "index.html"
    assets = build / "assets"
    if not index.is_file() or not assets.is_dir():
        raise RuntimeError(f"Demo web build is missing: {build}")

    app.mount("/assets", StaticFiles(directory=assets), name="demo-assets")

    @app.get("/favicon.ico", include_in_schema=False)
    def demo_favicon_ico():
        return FileResponse(build / "favicon.ico", media_type="image/x-icon")

    @app.get("/favicon.svg", include_in_schema=False)
    def demo_favicon_svg():
        return FileResponse(build / "favicon.svg", media_type="image/svg+xml")

    @app.get("/", include_in_schema=False)
    def demo_index():
        return FileResponse(index)

    @app.get("/{path:path}", include_in_schema=False)
    def demo_route(path: str):
        # React Router owns extensionless pages. Missing API and asset paths stay 404.
        if path == "api" or path.startswith("api/") or "." in Path(path).name:
            raise HTTPException(404, "Not found")
        return FileResponse(index)
