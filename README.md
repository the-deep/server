# DEEP Server

[![Build Status](https://github.com/the-deep/server/actions/workflows/ci.yml/badge.svg)](https://github.com/the-deep/server/actions) [![Maintainability](https://api.codeclimate.com/v1/badges/abcc581f9fca8a5864dc/maintainability)](https://codeclimate.com/github/the-deep/server/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/abcc581f9fca8a5864dc/test_coverage)](https://codeclimate.com/github/the-deep/server/test_coverage) [![codecov](https://codecov.io/gh/the-deep/server/branch/develop/graph/badge.svg)](https://codecov.io/gh/the-deep/server)

[![codecov](https://codecov.io/gh/the-deep/server/branch/develop/graphs/tree.svg)](https://blog.thedeep.io/server/)

## Git hooks for pre-commit
Add this to your `.git/hooks/pre-commit` to generate latest graphql schema before each commit.
```
#!/bin/sh

echo "pre-commit: Generating graphql schema."
if [ -z `docker ps -q --no-trunc | grep $(docker-compose ps -q web)` ]; then
    docker compose run --rm web ./manage.py graphql_schema --out schema.graphql
else
    docker compose exec -T web ./manage.py graphql_schema --out schema.graphql
fi
```
FYI: If hooks aren't working https://stackoverflow.com/questions/49912695/git-pre-and-post-commit-hooks-not-running
