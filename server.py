from pathlib import Path

import uvicorn

from core.api import create_app
from core.runtime import Runtime


ROOT = Path(__file__).resolve().parent
runtime = Runtime(ROOT)
app = create_app(runtime)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
