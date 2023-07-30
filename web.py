import uvicorn

from threading import Thread
from fastapi import FastAPI, APIRouter


class WebAppWrapper(Thread):

    def __init__(self, port: int = 5000):
        self.router = APIRouter()
        self.port = port
        self.app = None

        Thread.__init__(self)

    def add_endpoint(self, path, endpoint):
        self.router.add_api_route(path, endpoint)

    def remove_endpoint(self, path):
        for route in self.router.routes:
            if route.path == path:
                self.router.routes.remove(route)

    def run(self):
        self.app = FastAPI()
        self.app.include_router(self.router)

        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
