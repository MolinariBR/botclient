#!/bin/bash

# Script de inicialização para SquareCloud
# Este script é executado automaticamente pela SquareCloud

# Configurar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/container/src"

# Executar o bot
cd /home/container
python src/main.py