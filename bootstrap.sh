#/bin/sh

python -m venv .
./bin/pip install -r requirements.txt
./bin/buildout -c $1
