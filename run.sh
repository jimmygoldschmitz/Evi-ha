#!/bin/sh
cd /app
uvicorn main:app --host 0.0.0.0 --port 5001 --log-level info

