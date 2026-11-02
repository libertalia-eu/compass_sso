#!/usr/bin/env bash
# Unit tests without a bench: needs PyJWT and cryptography (both are Frappe dependencies).
# With Docker, run them in the Frappe image: IMAGE=libertalia-frappe:version-15 ./run-tests.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
if [ -n "${IMAGE:-}" ]; then
  exec docker run --rm --entrypoint bash -v "$PWD:/app:ro" -w /app "$IMAGE" -c \
    '/home/frappe/frappe-bench/env/bin/python -B -m unittest discover -s tests -t . -v'
fi
exec python3 -B -m unittest discover -s tests -t . -v
