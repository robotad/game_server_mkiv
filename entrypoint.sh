#!/bin/bash

if [ "${DEV_PROFILE}" == "True" ]; then
  timeout -s INT 60s python -m cProfile -o /server.cprof app/server.py
  tail -f /entrypoint.sh
else
  python -m app.server
fi

