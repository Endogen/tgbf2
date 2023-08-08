import uvicorn

from pathlib import Path
from threading import Thread
from fastapi import FastAPI, APIRouter
from starlette.responses import FileResponse, RedirectResponse


class StarletteHTTPException:
    pass


class WebAppWrapper(Thread):

    def __init__(self, root_html: Path, port: int = 5000):
        self.router = APIRouter()
        self.root_html = root_html
        self.port = port
        self.app = None

        Thread.__init__(self)

    def add_endpoint(self, path, endpoint):
        if self.app:
            self.app.add_api_route(path, endpoint)
        else:
            self.router.add_api_route(path, endpoint)

    def remove_endpoint(self, path):
        for route in self.router.routes:
            if route.path == path:
                if self.app:
                    self.app.routes.remove(route)
                else:
                    self.router.routes.remove(route)

    def run(self):
        self.app = FastAPI(title='TGBF2')
        self.app.include_router(self.router)

        @self.app.exception_handler(404)
        async def ex(_, __): return RedirectResponse('/')

        @self.app.get('/', include_in_schema=False)
        async def root(): return FileResponse(self.root_html)

        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
