from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date, timezone, timedelta
from dateutil.relativedelta import relativedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Helper functions for MongoDB serialization
def prepare_for_mongo(data):
    if isinstance(data.get('fecha_ingreso'), date):
        data['fecha_ingreso'] = data['fecha_ingreso'].isoformat()
    if isinstance(data.get('fecha_vencimiento'), date):
        data['fecha_vencimiento'] = data['fecha_vencimiento'].isoformat()
    return data

def parse_from_mongo(item):
    if isinstance(item.get('fecha_ingreso'), str):
        item['fecha_ingreso'] = datetime.fromisoformat(item['fecha_ingreso']).date()
    if isinstance(item.get('fecha_vencimiento'), str):
        item['fecha_vencimiento'] = datetime.fromisoformat(item['fecha_vencimiento']).date()
    return item

# Define Models
class Producto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    codigo: str
    descripcion: str
    unidad_venta: str  # "Unidades" o "Cajas"
    stock_actual: int = 0
    precio_venta: float = 0.0
    fecha_ingreso: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductoCreate(BaseModel):
    codigo: str
    descripcion: str
    unidad_venta: str = "Unidades"
    stock_actual: int = 0
    precio_venta: float = 0.0
    fecha_ingreso: Optional[date] = None
    fecha_vencimiento: Optional[date] = None

class ProductoUpdate(BaseModel):
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    unidad_venta: Optional[str] = None
    stock_actual: Optional[int] = None
    precio_venta: Optional[float] = None
    fecha_ingreso: Optional[date] = None
    fecha_vencimiento: Optional[date] = None

class Contacto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    tipo: str = "Proveedor"  # "Proveedor" o "Tienda"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactoCreate(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    tipo: str = "Proveedor"

class ContactoUpdate(BaseModel):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    tipo: Optional[str] = None

class Configuracion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stock_bajo_limite: int = 10
    vencimiento_alerta_meses: int = 2
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConfiguracionUpdate(BaseModel):
    stock_bajo_limite: Optional[int] = None
    vencimiento_alerta_meses: Optional[int] = None

class AlertaProducto(BaseModel):
    id: str
    codigo: str
    descripcion: str
    tipo_alerta: str  # "stock_cero", "stock_bajo", "proximo_vencer"
    stock_actual: int
    fecha_vencimiento: Optional[date]
    dias_para_vencer: Optional[int]

# PRODUCTOS ENDPOINTS
@api_router.post("/productos", response_model=Producto)
async def crear_producto(producto: ProductoCreate):
    producto_dict = producto.dict()
    producto_obj = Producto(**producto_dict)
    # Prepare the dict for MongoDB insertion (convert dates to strings)
    mongo_dict = prepare_for_mongo(producto_obj.dict())
    await db.productos.insert_one(mongo_dict)
    return producto_obj

@api_router.get("/productos", response_model=List[Producto])
async def obtener_productos(skip: int = Query(0, ge=0), limit: int = Query(1000, le=3000)):
    productos = await db.productos.find().skip(skip).limit(limit).to_list(length=None)
    return [Producto(**parse_from_mongo(producto)) for producto in productos]

@api_router.get("/productos/{producto_id}", response_model=Producto)
async def obtener_producto(producto_id: str):
    producto = await db.productos.find_one({"id": producto_id})
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Producto(**parse_from_mongo(producto))

@api_router.put("/productos/{producto_id}", response_model=Producto)
async def actualizar_producto(producto_id: str, producto_update: ProductoUpdate):
    update_dict = {k: v for k, v in producto_update.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    
    update_dict = prepare_for_mongo(update_dict)
    update_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.productos.update_one(
        {"id": producto_id}, 
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    producto_actualizado = await db.productos.find_one({"id": producto_id})
    return Producto(**parse_from_mongo(producto_actualizado))

@api_router.delete("/productos/{producto_id}")
async def eliminar_producto(producto_id: str):
    result = await db.productos.delete_one({"id": producto_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado exitosamente"}

# CONTACTOS ENDPOINTS
@api_router.post("/contactos", response_model=Contacto)
async def crear_contacto(contacto: ContactoCreate):
    contacto_obj = Contacto(**contacto.dict())
    await db.contactos.insert_one(contacto_obj.dict())
    return contacto_obj

@api_router.get("/contactos", response_model=List[Contacto])
async def obtener_contactos():
    contactos = await db.contactos.find().to_list(length=None)
    return [Contacto(**contacto) for contacto in contactos]

@api_router.put("/contactos/{contacto_id}", response_model=Contacto)
async def actualizar_contacto(contacto_id: str, contacto_update: ContactoUpdate):
    update_dict = {k: v for k, v in contacto_update.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    
    result = await db.contactos.update_one(
        {"id": contacto_id}, 
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    
    contacto_actualizado = await db.contactos.find_one({"id": contacto_id})
    return Contacto(**contacto_actualizado)

@api_router.delete("/contactos/{contacto_id}")
async def eliminar_contacto(contacto_id: str):
    result = await db.contactos.delete_one({"id": contacto_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return {"message": "Contacto eliminado exitosamente"}

# CONFIGURACIÓN ENDPOINTS
@api_router.get("/configuracion", response_model=Configuracion)
async def obtener_configuracion():
    config = await db.configuracion.find_one()
    if not config:
        # Crear configuración por defecto
        config_obj = Configuracion()
        await db.configuracion.insert_one(config_obj.dict())
        return config_obj
    return Configuracion(**config)

@api_router.put("/configuracion", response_model=Configuracion)
async def actualizar_configuracion(config_update: ConfiguracionUpdate):
    update_dict = {k: v for k, v in config_update.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    
    update_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Buscar configuración existente
    config_existente = await db.configuracion.find_one()
    if config_existente:
        await db.configuracion.update_one(
            {"id": config_existente["id"]}, 
            {"$set": update_dict}
        )
        config_actualizada = await db.configuracion.find_one({"id": config_existente["id"]})
    else:
        # Crear nueva configuración
        config_obj = Configuracion(**update_dict)
        await db.configuracion.insert_one(config_obj.dict())
        config_actualizada = config_obj.dict()
    
    return Configuracion(**config_actualizada)

# ALERTAS Y RECORDATORIOS ENDPOINT
@api_router.get("/alertas", response_model=List[AlertaProducto])
async def obtener_alertas():
    # Obtener configuración
    config = await db.configuracion.find_one()
    if not config:
        config = Configuracion().dict()
    
    stock_limite = config.get("stock_bajo_limite", 10)
    meses_vencimiento = config.get("vencimiento_alerta_meses", 2)
    
    # Obtener todos los productos
    productos = await db.productos.find().to_list(length=None)
    alertas = []
    
    fecha_limite = datetime.now().date() + relativedelta(months=meses_vencimiento)
    
    for producto in productos:
        producto = parse_from_mongo(producto)
        
        # Alerta de stock cero
        if producto.get("stock_actual", 0) == 0:
            alertas.append(AlertaProducto(
                id=producto["id"],
                codigo=producto["codigo"],
                descripcion=producto["descripcion"],
                tipo_alerta="stock_cero",
                stock_actual=producto.get("stock_actual", 0),
                fecha_vencimiento=producto.get("fecha_vencimiento"),
                dias_para_vencer=None
            ))
        
        # Alerta de stock bajo
        elif producto.get("stock_actual", 0) < stock_limite:
            alertas.append(AlertaProducto(
                id=producto["id"],
                codigo=producto["codigo"],
                descripcion=producto["descripcion"],
                tipo_alerta="stock_bajo",
                stock_actual=producto.get("stock_actual", 0),
                fecha_vencimiento=producto.get("fecha_vencimiento"),
                dias_para_vencer=None
            ))
        
        # Alerta de próximo a vencer
        if producto.get("fecha_vencimiento"):
            if producto["fecha_vencimiento"] <= fecha_limite:
                dias_para_vencer = (producto["fecha_vencimiento"] - datetime.now().date()).days
                alertas.append(AlertaProducto(
                    id=producto["id"],
                    codigo=producto["codigo"],
                    descripcion=producto["descripcion"],
                    tipo_alerta="proximo_vencer",
                    stock_actual=producto.get("stock_actual", 0),
                    fecha_vencimiento=producto["fecha_vencimiento"],
                    dias_para_vencer=dias_para_vencer
                ))
    
    return alertas

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "API de Gestión de Inventario"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
