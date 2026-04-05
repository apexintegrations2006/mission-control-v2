#!/bin/bash
cd "$(dirname "$0")"
git add .
git commit -m "auto: $1"
git push origin main
