#!/bin/bash
echo "BUILD START"
set -e
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
echo "BUILD END"
