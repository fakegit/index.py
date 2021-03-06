from http import HTTPStatus
from typing import List

import pytest
from async_asgi_testclient import TestClient
from pydantic import BaseModel

from indexpy import HttpRoute, HttpView, Index, Path, Routes
from indexpy.openapi import describe_extra_docs, describe_response
from indexpy.openapi.application import OpenAPI


@pytest.mark.asyncio
async def test_openapi_page():
    app = Index()
    openapi = OpenAPI("Title", "description", "1.0")
    app.router << "/openapi" // openapi.routes

    @app.router.http("/hello")
    @describe_response(200, content=List[str])
    async def hello(request):
        """
        hello
        """
        pass

    class Username(BaseModel):
        name: str

    @app.router.http("/path/{name}")
    async def path(request, name: str = Path(...)):
        pass

    @app.router.http("/http-view")
    class HTTPClass(HttpView):
        @describe_response(
            HTTPStatus.OK,
            content={
                "text/html": {
                    "schema": {"type": "string"},
                }
            },
        )
        async def get(self):
            """
            ...

            ......
            """

        @describe_response(HTTPStatus.CREATED, content=Username)
        async def post(self):
            """
            ...

            ......
            """

        @describe_response(HTTPStatus.NO_CONTENT)
        async def delete(self):
            """
            ...

            ......
            """

    def just_middleware(endpoint):
        describe_extra_docs(
            endpoint,
            {
                "parameters": [
                    {
                        "name": "Authorization",
                        "in": "header",
                        "description": "JWT Token",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ]
            },
        )
        return endpoint

    middleware_routes = "/middleware" // Routes(
        HttpRoute("/path/{name}", path, "middleware-path"),
        HttpRoute("/http-view", HTTPClass, "middleware-HTTPClass"),
        http_middlewares=[just_middleware],
    )

    app.router << middleware_routes

    client = TestClient(app)
    response = await client.get("/openapi/docs")
    assert response.status_code == 200
    openapi_docs_text = response.text
    assert (
        openapi_docs_text
        == '{"openapi":"3.0.0","info":{"title":"Title","description":"description","version":"1.0"},"paths":{"/http-view":{"get":{"summary":"...","description":"......","responses":{"200":{"description":"Request fulfilled, document follows","content":{"text/html":{"schema":{"type":"string"}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"post":{"summary":"...","description":"......","responses":{"201":{"description":"Document created, URL follows","content":{"application/json":{"schema":{"title":"Username","type":"object","properties":{"name":{"title":"Name","type":"string"}},"required":["name"]}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"delete":{"summary":"...","description":"......","responses":{"204":{"description":"Request fulfilled, nothing follows"}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]}},"/middleware/http-view":{"get":{"summary":"...","description":"......","responses":{"200":{"description":"Request fulfilled, document follows","content":{"text/html":{"schema":{"type":"string"}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"post":{"summary":"...","description":"......","responses":{"201":{"description":"Document created, URL follows","content":{"application/json":{"schema":{"title":"Username","type":"object","properties":{"name":{"title":"Name","type":"string"}},"required":["name"]}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"delete":{"summary":"...","description":"......","responses":{"204":{"description":"Request fulfilled, nothing follows"}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]}}},"tags":[],"servers":[{"url":"http://localhost","description":"Current server"}],"definitions":{}}'
    )
