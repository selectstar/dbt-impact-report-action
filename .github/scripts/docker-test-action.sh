#!/bin/bash
set -eux
docker run --rm test-image python -m unittest
