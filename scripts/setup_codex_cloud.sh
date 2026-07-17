#!/usr/bin/env bash

set -euo pipefail

python -m pip install --disable-pip-version-check -r requirements-tools.txt
python scripts/validate_events.py
python -m unittest discover -s tests -v
