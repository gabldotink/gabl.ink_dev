#!/bin/sh
# SPDX-License-Identifier: CC0-1.0
d="$(dirname -- "$0")"
cython -3 --embed --output-file="$d/main.c" -- "$d/main.py"
# shellcheck disable=2046
gcc "$d/main.c" $(python3-config --cflags --embed --ldflags) -O2 -o "$d/main"
rm -f -- "$d/main.c"
strip -- "$d/main"
