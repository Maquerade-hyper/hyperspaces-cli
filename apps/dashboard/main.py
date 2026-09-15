from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(
    title="Hyperspace Dashboard",
    version="0.1.0",
    description="Hyperspace control dashboard",
)


app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


@app.get("/")
def dashboard():
    return FileResponse(
        STATIC_DIR / "index.html"
    )


@app.get("/health")
def health():
    return {
        "status": "online",
        "service": "hyperspace-dashboard",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
    )