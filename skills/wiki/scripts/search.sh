#!/usr/bin/env bash
# Search the wiki with ripgrep. Returns matches with file paths and one line of context. Defaults path to ./wiki.
#
# Usage:
#   search.sh <query> [path]

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "usage: search.sh <query> [path]" >&2
    exit 1
fi

query="$1"
path="${2:-wiki}"

if [ ! -d "$path" ]; then
    echo "error: not a directory: $path" >&2
    exit 1
fi

rg --color=never --heading --line-number --context 1 --type md --smart-case -- "$query" "$path"
