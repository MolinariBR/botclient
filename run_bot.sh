#!/bin/bash

# Script para executar o bot

cd "$(dirname "$0")"

# Ativar ambiente virtual
source venv/bin/activate

# Executar o bot
PYTHONPATH="$(pwd)/src:$PYTHONPATH" python src/main.py