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

# Security configurations
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

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

# Authentication helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.usuarios.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return Usuario(**user)

# Define Models
class Usuario(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    nombre_completo: str
    hashed_password: str
    activo: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UsuarioCreate(BaseModel):
    username: str
    nombre_completo: str
    password: str

class UsuarioLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

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

# AUTHENTICATION ENDPOINTS
@api_router.post("/register", response_model=dict)
async def register(user: UsuarioCreate):
    # Check if user already exists
    existing_user = await db.usuarios.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya existe"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "id": str(uuid.uuid4()),
        "username": user.username,
        "nombre_completo": user.nombre_completo,
        "hashed_password": hashed_password,
        "activo": True,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.usuarios.insert_one(user_dict)
    return {"message": "Usuario registrado exitosamente"}

@api_router.post("/login", response_model=Token)
async def login(user: UsuarioLogin):
    # Check if user exists
    db_user = await db.usuarios.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not db_user["activo"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": db_user["username"],
            "nombre_completo": db_user["nombre_completo"]
        }
    }

@api_router.get("/me", response_model=dict)
async def read_users_me(current_user: Usuario = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "nombre_completo": current_user.nombre_completo,
        "activo": current_user.activo
    }

# PRODUCTOS ENDPOINTS
@api_router.post("/productos", response_model=Producto)
async def crear_producto(producto: ProductoCreate, current_user: Usuario = Depends(get_current_user)):
    producto_dict = producto.dict()
    producto_obj = Producto(**producto_dict)
    # Prepare the dict for MongoDB insertion (convert dates to strings)
    mongo_dict = prepare_for_mongo(producto_obj.dict())
    await db.productos.insert_one(mongo_dict)
    return producto_obj

@api_router.get("/productos", response_model=List[Producto])
async def obtener_productos(skip: int = Query(0, ge=0), limit: int = Query(1000, le=3000), current_user: Usuario = Depends(get_current_user)):
    productos = await db.productos.find().skip(skip).limit(limit).to_list(length=None)
    return [Producto(**parse_from_mongo(producto)) for producto in productos]

@api_router.get("/productos/{producto_id}", response_model=Producto)
async def obtener_producto(producto_id: str, current_user: Usuario = Depends(get_current_user)):
    producto = await db.productos.find_one({"id": producto_id})
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Producto(**parse_from_mongo(producto))

@api_router.put("/productos/{producto_id}", response_model=Producto)
async def actualizar_producto(producto_id: str, producto_update: ProductoUpdate, current_user: Usuario = Depends(get_current_user)):
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
async def eliminar_producto(producto_id: str, current_user: Usuario = Depends(get_current_user)):
    result = await db.productos.delete_one({"id": producto_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado exitosamente"}

# CONTACTOS ENDPOINTS
@api_router.post("/contactos", response_model=Contacto)
async def crear_contacto(contacto: ContactoCreate, current_user: Usuario = Depends(get_current_user)):
    contacto_obj = Contacto(**contacto.dict())
    await db.contactos.insert_one(contacto_obj.dict())
    return contacto_obj

@api_router.get("/contactos", response_model=List[Contacto])
async def obtener_contactos(current_user: Usuario = Depends(get_current_user)):
    contactos = await db.contactos.find().to_list(length=None)
    return [Contacto(**contacto) for contacto in contactos]

@api_router.put("/contactos/{contacto_id}", response_model=Contacto)
async def actualizar_contacto(contacto_id: str, contacto_update: ContactoUpdate, current_user: Usuario = Depends(get_current_user)):
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
async def eliminar_contacto(contacto_id: str, current_user: Usuario = Depends(get_current_user)):
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
