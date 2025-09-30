#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Inventory Management System
Tests all CRUD endpoints for productos, contactos, configuracion, and alertas
"""

import requests
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import os
import sys

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
print(f"Testing backend at: {BASE_URL}")

class InventoryAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = {
            "productos": {"passed": 0, "failed": 0, "errors": []},
            "contactos": {"passed": 0, "failed": 0, "errors": []},
            "configuracion": {"passed": 0, "failed": 0, "errors": []},
            "alertas": {"passed": 0, "failed": 0, "errors": []}
        }
        self.created_productos = []
        self.created_contactos = []

    def log_result(self, category: str, test_name: str, success: bool, error_msg: str = ""):
        if success:
            self.test_results[category]["passed"] += 1
            print(f"✅ {test_name}")
        else:
            self.test_results[category]["failed"] += 1
            self.test_results[category]["errors"].append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name}: {error_msg}")

    def test_api_root(self):
        """Test the root API endpoint"""
        print("\n=== Testing API Root ===")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    print("✅ API Root endpoint working")
                    return True
                else:
                    print("❌ API Root: Invalid response format")
                    return False
            else:
                print(f"❌ API Root: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Root: Connection error - {str(e)}")
            return False

    def test_productos_crud(self):
        """Test all productos CRUD operations"""
        print("\n=== Testing Productos CRUD ===")
        
        # Test data with realistic Spanish inventory items
        test_productos = [
            {
                "codigo": "ARZ001",
                "descripcion": "Arroz Blanco Premium 1kg",
                "unidad_venta": "Unidades",
                "stock_actual": 50,
                "precio_venta": 2.50,
                "fecha_ingreso": "2024-01-15",
                "fecha_vencimiento": "2025-01-15"
            },
            {
                "codigo": "ACE002", 
                "descripcion": "Aceite de Oliva Extra Virgen 500ml",
                "unidad_venta": "Unidades",
                "stock_actual": 0,  # For stock_cero alert testing
                "precio_venta": 8.75,
                "fecha_ingreso": "2024-01-10",
                "fecha_vencimiento": "2024-12-31"
            },
            {
                "codigo": "LEG003",
                "descripcion": "Lentejas Rojas 500g",
                "unidad_venta": "Cajas",
                "stock_actual": 5,  # For stock_bajo alert testing
                "precio_venta": 3.25,
                "fecha_ingreso": "2024-01-20",
                "fecha_vencimiento": "2024-03-15"  # For proximo_vencer alert testing
            }
        ]

        # 1. Test CREATE productos
        for i, producto_data in enumerate(test_productos):
            try:
                response = self.session.post(f"{self.base_url}/productos", json=producto_data)
                if response.status_code == 200:
                    producto = response.json()
                    if "id" in producto and producto["codigo"] == producto_data["codigo"]:
                        self.created_productos.append(producto)
                        self.log_result("productos", f"CREATE producto {i+1} ({producto_data['codigo']})", True)
                    else:
                        self.log_result("productos", f"CREATE producto {i+1}", False, "Invalid response format")
                else:
                    self.log_result("productos", f"CREATE producto {i+1}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("productos", f"CREATE producto {i+1}", False, str(e))

        # 2. Test GET all productos
        try:
            response = self.session.get(f"{self.base_url}/productos")
            if response.status_code == 200:
                productos = response.json()
                if isinstance(productos, list) and len(productos) >= len(self.created_productos):
                    self.log_result("productos", "GET all productos", True)
                else:
                    self.log_result("productos", "GET all productos", False, f"Expected list with at least {len(self.created_productos)} items")
            else:
                self.log_result("productos", "GET all productos", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("productos", "GET all productos", False, str(e))

        # 3. Test GET productos with pagination
        try:
            response = self.session.get(f"{self.base_url}/productos?skip=0&limit=2")
            if response.status_code == 200:
                productos = response.json()
                if isinstance(productos, list) and len(productos) <= 2:
                    self.log_result("productos", "GET productos with pagination", True)
                else:
                    self.log_result("productos", "GET productos with pagination", False, "Pagination not working correctly")
            else:
                self.log_result("productos", "GET productos with pagination", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("productos", "GET productos with pagination", False, str(e))

        # 4. Test GET producto by ID
        if self.created_productos:
            producto_id = self.created_productos[0]["id"]
            try:
                response = self.session.get(f"{self.base_url}/productos/{producto_id}")
                if response.status_code == 200:
                    producto = response.json()
                    if producto["id"] == producto_id:
                        self.log_result("productos", "GET producto by ID", True)
                    else:
                        self.log_result("productos", "GET producto by ID", False, "ID mismatch")
                else:
                    self.log_result("productos", "GET producto by ID", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result("productos", "GET producto by ID", False, str(e))

        # 5. Test UPDATE producto
        if self.created_productos:
            producto_id = self.created_productos[0]["id"]
            update_data = {
                "stock_actual": 75,
                "precio_venta": 2.75
            }
            try:
                response = self.session.put(f"{self.base_url}/productos/{producto_id}", json=update_data)
                if response.status_code == 200:
                    producto = response.json()
                    if producto["stock_actual"] == 75 and producto["precio_venta"] == 2.75:
                        self.log_result("productos", "UPDATE producto", True)
                    else:
                        self.log_result("productos", "UPDATE producto", False, "Update values not reflected")
                else:
                    self.log_result("productos", "UPDATE producto", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result("productos", "UPDATE producto", False, str(e))

        # 6. Test DELETE producto (delete the last one to keep others for alerts testing)
        if len(self.created_productos) > 1:
            producto_id = self.created_productos[-1]["id"]
            try:
                response = self.session.delete(f"{self.base_url}/productos/{producto_id}")
                if response.status_code == 200:
                    # Verify it's actually deleted
                    verify_response = self.session.get(f"{self.base_url}/productos/{producto_id}")
                    if verify_response.status_code == 404:
                        self.log_result("productos", "DELETE producto", True)
                        self.created_productos.pop()  # Remove from our tracking
                    else:
                        self.log_result("productos", "DELETE producto", False, "Product still exists after deletion")
                else:
                    self.log_result("productos", "DELETE producto", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result("productos", "DELETE producto", False, str(e))

    def test_contactos_crud(self):
        """Test all contactos CRUD operations"""
        print("\n=== Testing Contactos CRUD ===")
        
        # Test data with realistic Spanish contacts
        test_contactos = [
            {
                "nombre": "Distribuidora García S.L.",
                "direccion": "Calle Mayor 123, Madrid",
                "telefono": "+34 91 123 4567",
                "correo": "pedidos@distribuidoragarcia.es",
                "tipo": "Proveedor"
            },
            {
                "nombre": "Supermercado El Rincón",
                "direccion": "Avenida de la Paz 45, Barcelona",
                "telefono": "+34 93 987 6543",
                "correo": "compras@elrincon.com",
                "tipo": "Tienda"
            }
        ]

        # 1. Test CREATE contactos
        for i, contacto_data in enumerate(test_contactos):
            try:
                response = self.session.post(f"{self.base_url}/contactos", json=contacto_data)
                if response.status_code == 200:
                    contacto = response.json()
                    if "id" in contacto and contacto["nombre"] == contacto_data["nombre"]:
                        self.created_contactos.append(contacto)
                        self.log_result("contactos", f"CREATE contacto {i+1} ({contacto_data['nombre']})", True)
                    else:
                        self.log_result("contactos", f"CREATE contacto {i+1}", False, "Invalid response format")
                else:
                    self.log_result("contactos", f"CREATE contacto {i+1}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("contactos", f"CREATE contacto {i+1}", False, str(e))

        # 2. Test GET all contactos
        try:
            response = self.session.get(f"{self.base_url}/contactos")
            if response.status_code == 200:
                contactos = response.json()
                if isinstance(contactos, list) and len(contactos) >= len(self.created_contactos):
                    self.log_result("contactos", "GET all contactos", True)
                else:
                    self.log_result("contactos", "GET all contactos", False, f"Expected list with at least {len(self.created_contactos)} items")
            else:
                self.log_result("contactos", "GET all contactos", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("contactos", "GET all contactos", False, str(e))

        # 3. Test UPDATE contacto
        if self.created_contactos:
            contacto_id = self.created_contactos[0]["id"]
            update_data = {
                "telefono": "+34 91 999 8888",
                "correo": "nuevoemail@distribuidoragarcia.es"
            }
            try:
                response = self.session.put(f"{self.base_url}/contactos/{contacto_id}", json=update_data)
                if response.status_code == 200:
                    contacto = response.json()
                    if contacto["telefono"] == update_data["telefono"] and contacto["correo"] == update_data["correo"]:
                        self.log_result("contactos", "UPDATE contacto", True)
                    else:
                        self.log_result("contactos", "UPDATE contacto", False, "Update values not reflected")
                else:
                    self.log_result("contactos", "UPDATE contacto", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result("contactos", "UPDATE contacto", False, str(e))

        # 4. Test DELETE contacto
        if len(self.created_contactos) > 1:
            contacto_id = self.created_contactos[-1]["id"]
            try:
                response = self.session.delete(f"{self.base_url}/contactos/{contacto_id}")
                if response.status_code == 200:
                    # Verify it's actually deleted
                    verify_response = self.session.get(f"{self.base_url}/contactos")
                    if verify_response.status_code == 200:
                        contactos = verify_response.json()
                        if not any(c["id"] == contacto_id for c in contactos):
                            self.log_result("contactos", "DELETE contacto", True)
                            self.created_contactos.pop()  # Remove from our tracking
                        else:
                            self.log_result("contactos", "DELETE contacto", False, "Contact still exists after deletion")
                    else:
                        self.log_result("contactos", "DELETE contacto", False, "Could not verify deletion")
                else:
                    self.log_result("contactos", "DELETE contacto", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result("contactos", "DELETE contacto", False, str(e))

    def test_configuracion_endpoints(self):
        """Test configuracion management endpoints"""
        print("\n=== Testing Configuracion Endpoints ===")

        # 1. Test GET configuracion (should create default if none exists)
        try:
            response = self.session.get(f"{self.base_url}/configuracion")
            if response.status_code == 200:
                config = response.json()
                if "stock_bajo_limite" in config and "vencimiento_alerta_meses" in config:
                    self.log_result("configuracion", "GET configuracion (with default creation)", True)
                    print(f"   Default config: stock_bajo_limite={config['stock_bajo_limite']}, vencimiento_alerta_meses={config['vencimiento_alerta_meses']}")
                else:
                    self.log_result("configuracion", "GET configuracion", False, "Missing required fields")
            else:
                self.log_result("configuracion", "GET configuracion", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("configuracion", "GET configuracion", False, str(e))

        # 2. Test UPDATE configuracion
        update_data = {
            "stock_bajo_limite": 15,
            "vencimiento_alerta_meses": 3
        }
        try:
            response = self.session.put(f"{self.base_url}/configuracion", json=update_data)
            if response.status_code == 200:
                config = response.json()
                if config["stock_bajo_limite"] == 15 and config["vencimiento_alerta_meses"] == 3:
                    self.log_result("configuracion", "UPDATE configuracion", True)
                    print(f"   Updated config: stock_bajo_limite={config['stock_bajo_limite']}, vencimiento_alerta_meses={config['vencimiento_alerta_meses']}")
                else:
                    self.log_result("configuracion", "UPDATE configuracion", False, "Update values not reflected")
            else:
                self.log_result("configuracion", "UPDATE configuracion", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("configuracion", "UPDATE configuracion", False, str(e))

        # 3. Verify the configuration persists
        try:
            response = self.session.get(f"{self.base_url}/configuracion")
            if response.status_code == 200:
                config = response.json()
                if config["stock_bajo_limite"] == 15 and config["vencimiento_alerta_meses"] == 3:
                    self.log_result("configuracion", "Verify configuracion persistence", True)
                else:
                    self.log_result("configuracion", "Verify configuracion persistence", False, "Configuration not persisted")
            else:
                self.log_result("configuracion", "Verify configuracion persistence", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("configuracion", "Verify configuracion persistence", False, str(e))

    def test_alertas_system(self):
        """Test alertas system with different scenarios"""
        print("\n=== Testing Alertas System ===")

        # Test GET alertas
        try:
            response = self.session.get(f"{self.base_url}/alertas")
            if response.status_code == 200:
                alertas = response.json()
                if isinstance(alertas, list):
                    self.log_result("alertas", "GET alertas endpoint", True)
                    
                    # Analyze alert types
                    alert_types = {}
                    for alerta in alertas:
                        tipo = alerta.get("tipo_alerta", "unknown")
                        if tipo not in alert_types:
                            alert_types[tipo] = 0
                        alert_types[tipo] += 1
                    
                    print(f"   Found {len(alertas)} total alerts:")
                    for tipo, count in alert_types.items():
                        print(f"   - {tipo}: {count} alerts")
                    
                    # Verify alert structure
                    if alertas:
                        sample_alert = alertas[0]
                        required_fields = ["id", "codigo", "descripcion", "tipo_alerta", "stock_actual"]
                        if all(field in sample_alert for field in required_fields):
                            self.log_result("alertas", "Alert structure validation", True)
                        else:
                            missing_fields = [f for f in required_fields if f not in sample_alert]
                            self.log_result("alertas", "Alert structure validation", False, f"Missing fields: {missing_fields}")
                    
                    # Test specific alert scenarios based on our test data
                    expected_alerts = {
                        "stock_cero": False,  # ACE002 has stock_actual = 0
                        "stock_bajo": False,  # LEG003 has stock_actual = 5 (below limit of 15)
                        "proximo_vencer": False  # LEG003 expires 2024-03-15
                    }
                    
                    for alerta in alertas:
                        if alerta["tipo_alerta"] in expected_alerts:
                            expected_alerts[alerta["tipo_alerta"]] = True
                    
                    for alert_type, found in expected_alerts.items():
                        if found:
                            self.log_result("alertas", f"Alert scenario: {alert_type}", True)
                        else:
                            self.log_result("alertas", f"Alert scenario: {alert_type}", False, f"Expected {alert_type} alert not found")
                    
                else:
                    self.log_result("alertas", "GET alertas endpoint", False, "Response is not a list")
            else:
                self.log_result("alertas", "GET alertas endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("alertas", "GET alertas endpoint", False, str(e))

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Backend API Testing")
        print("=" * 60)
        
        # Test API connectivity first
        if not self.test_api_root():
            print("\n❌ CRITICAL: Cannot connect to API. Stopping tests.")
            return False
        
        # Run all test suites
        self.test_productos_crud()
        self.test_contactos_crud()
        self.test_configuracion_endpoints()
        self.test_alertas_system()
        
        # Print summary
        self.print_summary()
        return self.get_overall_success()

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results["passed"]
            failed = results["failed"]
            total_passed += passed
            total_failed += failed
            
            status = "✅ PASS" if failed == 0 else "❌ FAIL"
            print(f"{category.upper():15} | {status} | {passed} passed, {failed} failed")
            
            if results["errors"]:
                for error in results["errors"]:
                    print(f"                  ❌ {error}")
        
        print("-" * 60)
        overall_status = "✅ ALL TESTS PASSED" if total_failed == 0 else f"❌ {total_failed} TESTS FAILED"
        print(f"OVERALL RESULT  | {overall_status} | {total_passed} passed, {total_failed} failed")
        print("=" * 60)

    def get_overall_success(self):
        """Return True if all tests passed"""
        return sum(results["failed"] for results in self.test_results.values()) == 0

if __name__ == "__main__":
    tester = InventoryAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All backend API tests completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some backend API tests failed. Check the summary above.")
        sys.exit(1)