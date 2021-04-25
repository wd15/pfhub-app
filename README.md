# PFHub App

This is deployed on Heroku.

## Testing

### Local Python tests

Start memcache server with `sudo /etc/init.d/memcached restart`.


Run with

    $ nix-shell --pure
    [nix-shell]$ export MEMCACHIER_SERVERS="127.0.0.1:11211"
    [nix-shell]$ export MEMCACHIER_USERNAME="user"
    [nix-shell]$ export MEMCACHIER_PASSWORD="password"
    [nix-shell]$ uvicorn main:app --reload

Test the Python modules with

    [nix-shell]$ py.test --doctest-modules test.py contour.py

### File downloads

Test the local version with

    $ url="https://drive.google.com/open?id=19oJVHZ6zaw47TN43E5qk-uGRsqrz0iE7"
    $ curl -L -o out.csv http://localhost:8000/get/?url=$url

    $ url="https://drive.google.com/open?id=1he7ilLH2VTD740OGPJXOq8CSn7utEDf_"
    $ curl -L -o out.png "http://localhost:8000/get/?url=$url"

to test both a binary and non-binary file download.

Test zero contour calcuation

    $ url="https://gist.githubusercontent.com/wd15/7da4626088f0920d0b5bac5727784ef9/raw/6f39388cab76024a48709aa4dcfeccbef68f0f87/phi_fixed.csv"
    $ curl -L -o out.csv "http://localhost:8000/get_contour/?url=$url&z_col=phi"


### Commenting

Open up a test PR in the repository and set the app location

    $ export TRAVIS_PULL_REQUEST_BRANCH="branch_name"
    $ export APP_URL="https://pfhub.herokuapp.com"

Set up a payload. `payload.json` uses these variables.

    $ export TRAVIS_PULL_REQUEST="1114"
    $ export TRAVIS_REPO_SLUG="usnistgov/pfhub"
    $ export DOMAIN="random-cat-1114.surge.sh"

Test it.

    $ curl ${APP_URL}/comment/ \
      -H "Content-Type: application/json" \
      -X POST -d "$( envsubst < payload.json )"

A comment should appear in the PR and some JSON should be returned
with the comment in the "body".
