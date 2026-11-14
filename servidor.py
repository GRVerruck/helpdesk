import os

from waitress import serve
from api import criar_app


if __name__ == "__main__":
    serve(criar_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), threads=4)
