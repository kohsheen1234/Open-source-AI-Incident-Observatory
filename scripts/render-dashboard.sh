#!/bin/sh
# Dashboard entrypoint: run the Streamlit app.
set -e
exec streamlit run dashboard/app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true
