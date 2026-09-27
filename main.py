"""Convenient entry point for the local Unity Tutor API.

Run with: ``python main.py``
"""

import uvicorn


if __name__ == "__main__":
    # This starts the HTTP server only on the local machine. Importing the app by
    # module path also keeps Uvicorn's optional development reload mode available.
    uvicorn.run("tutor_service.api:app", host="127.0.0.1", port=8765, reload=False)
