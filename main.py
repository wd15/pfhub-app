"""See the README.md for testing instructions.

To flush the cache use `memcached_client().flush_all()` somewhere that
runs and is outside of a memcached function.

"""

import re
import io
import json
import os
from functools import wraps
from typing import List

from fastapi import FastAPI, Query
import requests
from toolz.curried import curry, get, compose, memoize, identity, pipe
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from pydantic import BaseModel, UrlStr
import archieml
import bmemcached
import pandas
import numpy
from contour import calc_contour_vertices


@memoize
def memcached_client():
    """Get the memcached client.
    """
    client = bmemcached.Client(
        os.environ.get("MEMCACHIER_SERVERS", "").split(","),
        os.environ.get("MEMCACHIER_USERNAME", ""),
        os.environ.get("MEMCACHIER_PASSWORD", ""),
    )
    client.enable_retry_delay(True)  # Enabled by default. Sets retry delay to 5s.
    return client


def sequence(*args):
    """Compose functions in order

    Args:
      args: the functions to compose

    Returns:
      composed functions

    >>> assert sequence(lambda x: x + 1, lambda x: x * 2)(3) == 8
    """
    return compose(*args[::-1])


app = FastAPI()  # pylint: disable=invalid-name


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:4000",
        "https://pages.nist.gov",
        "https//travis-ci.org",
    ],
    # allow_origins=["*"],
    allow_origin_regex=r"https://random-cat-.*\.surge\.sh",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


search = curry(re.search)  # pylint: disable=invalid-name


modify_google = sequence(  # pylint: disable=invalid-name
    search(r"[-\w]{25,}"),
    get(0),
    lambda x: str.format("https://drive.google.com/uc?export=download&id={0}", x),
)


@curry
def if_(if_func, func, arg):
    """Whether to apply a function or not
    """
    if if_func(arg):
        return func(arg)
    return arg


@curry
def memcached(func):
    """Use memcached to cache the results of a function.

    Must have the memcached server running.
    """

    def wrapper(key, *args, **kwargs):
        value = memcached_client().get(key)
        if value is None:
            value = func(key, *args, **kwargs)
            memcached_client().set(key, value)
        return value

    return wraps(func)(wrapper)


@memcached
def download(url: UrlStr, func):
    """Download data from URL.

    Returns a tuple of the content, and content type.
    """
    return sequence(
        if_(search(r"https://drive\.google\.com(.*)"), modify_google),
        requests.get,
        lambda x: (func(x.content), str(x.headers["content-type"])),
    )(url)


def file_response(url: UrlStr, func):
    """Generic function to download a file, process it and stream.

    """
    return pipe(
        download(url, func),
        lambda x: (io.BytesIO(x[0]), x[1]),
        lambda x: StreamingResponse(x[0], media_type=x[1]),
    )


@app.get("/get/")
async def get_binary_file(url: UrlStr):
    """Base endpoint to get binary file
    """
    return file_response(url, identity)


@app.get("/get_contour/")
async def get_contour(
    url: UrlStr,
    contour_value: float = 0.5,
    fill_value: float = 0.0,
    domain: List[float] = Query([-50.0, 50.0]),
    cols: List[str] = Query(["x", "y", "z"]),
):
    """Base endpoint to get a binary csv file and calcuate the zero contour
    """

    # memcached_client().flush_all()
    def to_string(dataframe):
        string_ = io.StringIO()
        dataframe.to_csv(string_, index=False)
        return bytearray(string_.getvalue(), "utf8")

    process = sequence(
        io.BytesIO,
        pandas.read_csv,
        lambda x: x[cols],
        numpy.array,
        calc_contour_vertices(
            domain=domain, fill_value=fill_value, contour_value=contour_value
        ),
        lambda x: pandas.DataFrame(x, columns=["x", "y"]),
        to_string,
    )

    return file_response(url, process)


class CiData(BaseModel):
    """Data from CI required to generate automated comments
    """

    travis_pull_request: int
    surge_domain: UrlStr
    travis_pull_request_branch: str
    travis_repo_slug: str


@curry
def comment_staticman_(ci_data, data):
    """Comment string for Staticman PR
    """
    return f"""
@{data.get("github_id", "")}, thanks for your PFHub upload!

You can view your upload display at

 - {ci_data.surge_domain}/simulations/display/?sim={data.get("upload", "")}

and

 - {ci_data.surge_domain}/simulations/{data.get("benchmark_id", "")}

Please check that the tests pass below and then review and confirm your approval to @pfhub by commenting in this pull request.

If you think there is a mistake in your upload data, then you can resubmit the upload [at this link]({ci_data.surge_domain}/simulations/upload_form/?sim={data.get("upload", "")}).
"""


def comment_general(ci_data):
    """Comment string for non-staticman comment
    """
    return f"""
The new [PFHub live website]({ci_data.surge_domain}) is ready for review.
"""


@curry
def pr_url(ci_data):
    """Build the PR URL to get and write data to the PR comments
    """
    return f"""
https://api.github.com/repos/{ci_data.travis_repo_slug}/issues/{ci_data.travis_pull_request}
"""


@curry
def is_staticman(ci_data):
    """Determine if the PR is generated by Staticman
    """
    return ci_data.travis_pull_request_branch[:9] == "staticman"


@curry
def requests_get(github_token, url):
    """Curried version of requests.get with correct headers for github
    """
    return requests.get(url, headers={"Authorization": f"token {github_token}"})


@curry
def comment_staticman(github_token, ci_data):
    """Sequence of functions to get data from github for staticman comment
    and then write the comment to github
    """
    return sequence(
        pr_url,
        requests_get(github_token),
        lambda x: x.json(),
        get("body"),
        archieml.loads,
        comment_staticman_(ci_data),
    )(ci_data)


@curry
def post(github_token, ci_data, comment_string):
    """Curried version of requests.post to write github comment
    """
    return requests.post(
        pr_url(ci_data) + "/comments",
        data=json.dumps({"body": comment_string}),
        headers={"Authorization": f"token {github_token}"},
    )


def comment_pr_(ci_data, github_token):
    """Write either a staticman comment or non-staticman comment to
    github.
    """
    return sequence(
        (comment_staticman(github_token) if is_staticman(ci_data) else comment_general),
        post(github_token, ci_data),
        lambda x: dict(status_code=x.status_code, json=x.json()),
    )(ci_data)


@app.post("/comment/")
async def comment_pr(ci_data: CiData):
    """Endpoint to post comment to GitHub PR
    """
    print(ci_data)
    return comment_pr_(ci_data, os.environ.get("GITHUB_TOKEN"))


if __name__ == "__main__":
    # run with python main.py to debug
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
