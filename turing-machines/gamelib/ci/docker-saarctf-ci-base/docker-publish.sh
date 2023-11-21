#!/bin/bash

set -e

(docker system info 2>/dev/null | grep -q 'Username: saarsec') || docker login -u saarsec

docker build -t saarsec/saarctf-ci-base .
docker tag saarsec/saarctf-ci-base:latest saarsec/saarctf-ci-base:bookworm
docker push saarsec/saarctf-ci-base:latest
docker push saarsec/saarctf-ci-base:bookworm

echo "[DONE] Image pushed. You can now log out again (docker logout)"
