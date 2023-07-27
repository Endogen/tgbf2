import uvicorn

from fastapi import FastAPI, APIRouter


class WebAppWrapper:

    def __init__(self, router: APIRouter = None, port: int = 5000):
        self.router = router if router else APIRouter()
        self.port = port
        self.app = FastAPI()
        self.app.include_router(self.router)

    def start(self):
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
