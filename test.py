"""Test main.py
"""

from starlette.testclient import TestClient
from toolz.curried import pipe, curry
from main import app


client = TestClient(app)  # pylint: disable=invalid-name


def get(url):
    """Get the response given a file URL
    """
    return client.get(f"/get/?url={url}")


@curry
def get_contour(colx, coly, colz, url):
    """Get the response given a file URL
    """
    return client.get(f"/get/?url={url}&cols={colx}&cols={coly}&cols={colz}")


def test_csv():
    """Test the response with a CSV file
    """
    assert pipe(
        "https://drive.google.com/file/d/1F2Pzo2IYYPhPmU_mryjR6flz2vUDr5Zy/view?usp=sharing",
        get,
        lambda x: x.text.partition("\n")[0] == "Time,Total_Energy",
    )


def test_image():
    """Test the response with an image file
    """
    assert pipe(
        "https://drive.google.com/file/d/1b51dmOYwspNVMsaSoED2xUT3pfNq563B/view?usp=sharing",
        get,
        lambda x: x.headers["content-type"] == "image/png",
    )


def test_contour():
    """Test the get_contour
    """
    assert pipe(
        "https://gist.githubusercontent.com/wd15/7da4626088f0920d0b5bac5727784ef9/raw/6f39388cab76024a48709aa4dcfeccbef68f0f87/phi_fixed.csv",  # pylint: disable=line-too-long
        get_contour("x", "y", "phi"),
        lambda x: x.text.partition("\n")[0] == "x,y",
    )
