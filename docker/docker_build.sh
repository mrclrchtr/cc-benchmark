#!/bin/bash

set -e

# Build from project root, not docker directory
cd "$(dirname "$0")/.."

docker build \
       --file docker/Dockerfile \
       -t cc-benchmark \
       .
