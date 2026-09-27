"""Convenient entry point for the local Unity Tutor API.

Run with: ``python main.py``
"""

import uvicorn


if __name__ == "__main__":
    # Importing by module path also enables Uvicorn's reload mode during development.
    uvicorn.run("tutor_service.api:app", host="127.0.0.1", port=8765, reload=False)
