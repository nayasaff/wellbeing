#!/bin/sh
set -e
gunicorn wellbeing.wsgi --log-file -