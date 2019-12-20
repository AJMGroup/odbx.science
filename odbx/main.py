""" Lines suffixed with "# odbx" indicate that this line differs from
the reference implementation or does not exist in the reference
implementation.

"""

import json
from pathlib import Path

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from starlette.staticfiles import StaticFiles  # odbx

from optimade.server.entry_collections import MongoCollection
from optimade.server.config import CONFIG
from optimade.server.routers import info, links, references, structures
from optimade.server.routers.utils import get_providers

import optimade.server.exception_handlers as exc_handlers

from . import odbx_routers  # odbx

app = FastAPI(
    title="OPTiMaDe API",
    description=(
        "The [Open Databases Integration for Materials Design (OPTiMaDe) consortium]"
        "(http://http://www.optimade.org/) aims to make materials databases interoperational "
        "by developing a common REST API."
    ),
    version=CONFIG.version,
    docs_url="/optimade/extensions/docs",
    redoc_url="/optimade/extensions/redoc",
    openapi_url="/optimade/extensions/openapi.json",
)


app.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
app.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
app.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
app.add_exception_handler(Exception, exc_handlers.general_exception_handler)


# Create the following prefixes:
#   /optimade
#   /optimade/vMajor (but only if Major >= 1)
#   /optimade/vMajor.Minor
#   /optimade/vMajor.Minor.Patch
valid_prefixes = ["/optimade"]
version = [int(_) for _ in CONFIG.version.split(".")]
while version:
    if version[0] or len(version) >= 2:
        valid_prefixes.append(
            "/optimade/v{}".format(".".join([str(_) for _ in version]))
        )
    version.pop(-1)

for prefix in valid_prefixes:
    app.include_router(info.router, prefix=prefix)
    app.include_router(links.router, prefix=prefix)
    app.include_router(references.router, prefix=prefix)
    app.include_router(structures.router, prefix=prefix)

rich_prefix = ""  # odbx
app.include_router(odbx_routers.structures.router, prefix=rich_prefix)  # odbx
app.include_router(odbx_routers.home.router, prefix=rich_prefix)  # odbx

js_dir = Path(__file__).parent.joinpath("js")  # odbx
css_dir = Path(__file__).parent.joinpath("css")  # odbx
app.mount("/js", StaticFiles(directory=js_dir), name="js")  # odbx
app.mount("/css", StaticFiles(directory=css_dir), name="css")  # odbx


def update_schema(app):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    with open("local_openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)


@app.on_event("startup")
async def startup_event():
    update_schema(app)
