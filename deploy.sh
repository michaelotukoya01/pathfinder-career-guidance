#!/usr/bin/env sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
docker compose config --quiet
docker compose up --build --wait
printf '%s\n' 'Pathfinder is available at http://localhost:3000'
