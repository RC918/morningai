#!/usr/bin/env bash
set -euo pipefail
APP=morningai-web
cd "$(dirname "$0")"
yes | flyctl deploy . -c fly.toml
flyctl status -a "$APP"
