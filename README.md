# PFHub App

This is deployed on Heroku.

## Testing

### Local Python tests

Run with

    $ nix-shell --pure
    [nix-shell]$ uvicorn main:app --reload

Test the Python modules with

    [nix-shell]$ py.test test.py

### File downloads

Test the local version with

Start memcache server with `sudo /etc/init.d/memcached restart`.

    $ export MEMCACHIER_SERVERS="127.0.0.1:11211"
    $ export MEMCACHIER_USERNAME="user"
    $ export MEMCACHIER_PASSWORD="password"

    $ url="https://drive.google.com/open?id=19oJVHZ6zaw47TN43E5qk-uGRsqrz0iE7"
    $ curl -L -o out.csv http://localhost:8000/get/?url=$url

    $ url="https://drive.google.com/open?id=1he7ilLH2VTD740OGPJXOq8CSn7utEDf_"
    $ curl -L -o out.png "http://localhost:8000/get/?url=$url"

to test both a binary and non-binary file download.

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
