#!/usr/bin/env bash
# build.sh

set -o errexit
set -o pipefail
set -o nounset

# Install Python dependencies
pip install -r requirements.txt