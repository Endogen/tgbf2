import uvicorn

from threading import Thread
from fastapi import FastAPI, APIRouter


class WebAppWrapper(Thread):

    def __init__(self, router: APIRouter = None, port: int = 5000):
        self.router = router if router else APIRouter()
        self.port = port
        self.app = FastAPI()
        self.app.include_router(self.router)

        Thread.__init__(self)

    # FIXME: Not working...
    async def add_endpoint(self, name: str, action):
        self.router.add_api_route(name, action)

    # FIXME: Not working...
    def remove_endpoint(self, name: str):
        for route in self.router.routes:
            if route.path == name:
                self.router.routes.remove(route)

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
