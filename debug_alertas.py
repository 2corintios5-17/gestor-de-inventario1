#!/usr/bin/env python3
"""
Debug script to check alertas logic
"""

import requests
import json

# Get backend URL from frontend environment
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except FileNotFoundError:
        return "http://localhost:8001"
    return "http://localhost:8001"

BASE_URL = get_backend_url() + "/api"

# Get all products
response = requests.get(f"{BASE_URL}/productos")
productos = response.json()

print("=== PRODUCTOS IN DATABASE ===")
for producto in productos:
    print(f"ID: {producto['id']}")
    print(f"Codigo: {producto['codigo']}")
    print(f"Descripcion: {producto['descripcion']}")
    print(f"Stock: {producto['stock_actual']}")
    print(f"Fecha vencimiento: {producto.get('fecha_vencimiento', 'None')}")
    print("-" * 40)

# Get configuration
response = requests.get(f"{BASE_URL}/configuracion")
config = response.json()
print(f"=== CONFIGURACION ===")
print(f"Stock bajo limite: {config['stock_bajo_limite']}")
print(f"Vencimiento alerta meses: {config['vencimiento_alerta_meses']}")
print("-" * 40)

# Get alertas
response = requests.get(f"{BASE_URL}/alertas")
alertas = response.json()

print(f"=== ALERTAS ({len(alertas)} total) ===")
for alerta in alertas:
    print(f"Codigo: {alerta['codigo']}")
    print(f"Tipo: {alerta['tipo_alerta']}")
    print(f"Stock: {alerta['stock_actual']}")
    print(f"Fecha vencimiento: {alerta.get('fecha_vencimiento', 'None')}")
    print(f"Dias para vencer: {alerta.get('dias_para_vencer', 'None')}")
    print("-" * 40)