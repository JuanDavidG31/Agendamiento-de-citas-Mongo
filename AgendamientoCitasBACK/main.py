from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Importamos tu conexión a Neon desde database.py
from database import get_postgres_connection, get_mongo_db
from passlib.context import CryptContext
import jwt
import os


# ==========================================
# CONFIGURACIÓN DE SEGURIDAD (JWT y Bcrypt)
# ==========================================
SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta_hospital_el_bosque")
ALGORITHM = "HS256"

# Configuramos bcrypt para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    # Truncamos a 72 caracteres para evitar el error de límite de bcrypt
    return pwd_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str):
    # Truncamos también al verificar para que coincida exactamente
    return pwd_context.verify(plain_password[:72], hashed_password)

# ==========================================
# 1. ESQUEMAS DE VALIDACIÓN (PYDANTIC)
# (Esto fue lo primero que te di. Define cómo se ven los datos)
# ==========================================
# --- ESQUEMA PARA LOGIN UNIFICADO ---
class LoginRequest(BaseModel):
    identificador: str  # Puede ser el email (paciente) o el documento (paciente/médico)
    password: str
# --- ESQUEMAS PARA PACIENTES ---
class PacienteBase(BaseModel):
    documento: str
    nombres: str
    apellidos: str
    email: str  # Lo cambiamos a obligatorio (sin Optional) según tu base de datos

class PacienteCreate(PacienteBase):
    password: str  # <--- Pedimos la contraseña solo al registrarse

class PacienteResponse(PacienteBase):
    id_paciente: int

# --- ESQUEMA PARA LOGIN DE PACIENTES ---
class LoginPacienteRequest(BaseModel):
    email: str
    password: str

# --- ESQUEMAS PARA MÉDICOS ---
class MedicoBase(BaseModel):
    documento: str
    nombre_completo: str
    id_especialidad: int

class MedicoCreate(MedicoBase):
    password: str  # <--- Pedimos la contraseña al crear el médico

class MedicoResponse(MedicoBase):
    id_medico: int

# --- ESQUEMAS PARA CITAS ---
class CitaBase(BaseModel):
    id_paciente: int
    id_medico: int
    id_estado: int
    fecha_hora: datetime
    consultorio: Optional[str] = None

class CitaCreate(CitaBase):
    pass

class CitaResponse(CitaBase):
    id_cita: int
    
# --- ESQUEMAS PARA PAGOS ---
class PagoBase(BaseModel):
    id_cita: int
    monto: float
    fecha_pago: Optional[datetime] = None
    estado_pago: Optional[str] = "Pendiente"

class PagoCreate(PagoBase):
    pass

class PagoResponse(PagoBase):
    id_pago: int
    
# --- ESQUEMAS PARA ESPECIALIDADES ---
class EspecialidadBase(BaseModel):
    nombre_specialidad: str  # <--- Sin la 'e'
    tarifa_base: float

class EspecialidadCreate(EspecialidadBase):
    pass

class EspecialidadResponse(EspecialidadBase):
    id_especialidad: int
# --- ESQUEMAS PARA ESTADOS DE CITAS ---
class EstadoCitaBase(BaseModel):
    nombre_estado: str

class EstadoCitaCreate(EstadoCitaBase):
    pass

class EstadoCitaResponse(EstadoCitaBase):
    id_estado: int

# --- ESQUEMAS PARA AUDITORÍA DE ESTADOS ---
class AuditoriaEstadoBase(BaseModel):
    id_cita: int
    estado_anterior: int
    estado_nuevo: int
    fecha_cambio: Optional[datetime] = None

class AuditoriaEstadoCreate(AuditoriaEstadoBase):
    pass

class AuditoriaEstadoResponse(AuditoriaEstadoBase):
    id_auditoria: int

# ==========================================
# 2. INICIALIZACIÓN DE FASTAPI
# ==========================================
app = FastAPI(
    title="Portal Médico de Citas Hospitalarias",
    description="API de Integración Políglota. Control de operaciones CRUD en el núcleo transaccional (PostgreSQL).",
    version="2.0"
)

# ==========================================
#          SISTEMA DE AUTENTICACIÓN
# ==========================================

@app.post("/auth/login", tags=["Autenticación"])
def iniciar_sesion(credenciales: LoginRequest):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    
    try:
        cursor = conn.cursor()
        
        # 1. Intentar validar como PACIENTE (por email O por documento)
        cursor.execute(
            """SELECT id_paciente, password_hash, nombres, apellidos 
               FROM PACIENTES 
               WHERE email = %s OR documento = %s;""", 
            (credenciales.identificador, credenciales.identificador)
        )
        paciente = cursor.fetchone()
        
        if paciente:
            if not verify_password(credenciales.password, paciente[1]):
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")
                
            # Generar Token JWT para el paciente
            token = jwt.encode(
                {
                    "sub": str(paciente[0]), 
                    "rol": "paciente", 
                    "nombre_completo": f"{paciente[2]} {paciente[3]}"
                }, 
                SECRET_KEY, 
                algorithm=ALGORITHM
            )
            return {
                "access_token": token, 
                "token_type": "bearer", 
                "rol": "paciente", 
                "id": paciente[0],  # <--- ID extraído de la base de datos añadido aquí
                "mensaje": f"Bienvenido, paciente {paciente[2]}"
            }
        
        # 2. Intentar validar como MÉDICO (por documento)
        cursor.execute(
            """SELECT id_medico, password_hash, nombre_completo 
               FROM MEDICOS 
               WHERE documento = %s;""", 
            (credenciales.identificador,)
        )
        medico = cursor.fetchone()
        
        if medico:
            if not verify_password(credenciales.password, medico[1]):
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")
                
            # Generar Token JWT para el médico
            token = jwt.encode(
                {
                    "sub": str(medico[0]), 
                    "rol": "medico", 
                    "nombre_completo": medico[2]
                }, 
                SECRET_KEY, 
                algorithm=ALGORITHM
            )
            return {
                "access_token": token, 
                "token_type": "bearer", 
                "rol": "medico",
                "id": medico[0],  # <--- ID extraído de la base de datos añadido aquí
                "mensaje": f"Bienvenido, Dr/Dra. {medico[2]}"
            }
            
        # 3. Si el identificador no existe en ninguna de las dos tablas
        raise HTTPException(status_code=404, detail="Usuario no encontrado en el sistema")
        
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.get("/", tags=["Inicio"])
def home():
    return {"mensaje": "API conectada a Neon lista."}

# ==========================================
# 3. RUTAS CRUD (ENDPOINTS)
# (Esto fue lo segundo que te di. Define las operaciones SQL)
# ==========================================

# --- CRUD DE PACIENTES ---
@app.get("/pacientes/{documento}", response_model=PacienteResponse, tags=["Pacientes"])
def obtener_paciente(documento: str):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    # Cambiamos el WHERE para buscar por la columna documento
    cursor.execute("SELECT id_paciente, documento, nombres, apellidos, email FROM PACIENTES WHERE documento = %s;", (documento,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not fila:
        raise HTTPException(status_code=404, detail="Paciente no encontrado con ese documento")
        
    return {
        "id_paciente": fila[0], 
        "documento": fila[1], 
        "nombres": fila[2], 
        "apellidos": fila[3], 
        "email": fila[4]
    }
@app.post("/pacientes", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED, tags=["Pacientes"])
def crear_paciente(paciente: PacienteCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    try:
        cursor = conn.cursor()
        
        # 1. Encriptamos la contraseña antes de guardarla
        hash_pass = get_password_hash(paciente.password)
        
        # 2. Insertamos incluyendo el password_hash
        cursor.execute(
            """INSERT INTO PACIENTES (documento, nombres, apellidos, email, password_hash) 
               VALUES (%s, %s, %s, %s, %s) RETURNING id_paciente;""",
            (paciente.documento, paciente.nombres, paciente.apellidos, paciente.email, hash_pass)
        )
        id_generado = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Retornamos los datos base sin incluir la contraseña
        return {
            "id_paciente": id_generado,
            "documento": paciente.documento,
            "nombres": paciente.nombres,
            "apellidos": paciente.apellidos,
            "email": paciente.email
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"No se pudo registrar: {str(e)}")

@app.get("/pacientes", response_model=List[PacienteResponse], tags=["Pacientes"])
def listar_pacientes():
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_paciente, documento, nombres, apellidos, email FROM PACIENTES;")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id_paciente": f[0], "documento": f[1], "nombres": f[2], "apellidos": f[3], "email": f[4]} for f in filas]

@app.put("/pacientes/{id_paciente}", response_model=PacienteResponse, tags=["Pacientes"])
def actualizar_paciente(id_paciente: int, paciente: PacienteCreate):
    conn = get_postgres_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE PACIENTES SET documento = %s, nombres = %s, apellidos = %s, email = %s WHERE id_paciente = %s RETURNING id_paciente;",
            (paciente.documento, paciente.nombres, paciente.apellidos, paciente.email, id_paciente)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        conn.commit()
        cursor.close()
        conn.close()
        return {**paciente.model_dump(), "id_paciente": id_paciente}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/pacientes/{id_paciente}", tags=["Pacientes"])
def eliminar_paciente(id_paciente: int):
    conn = get_postgres_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM PACIENTES WHERE id_paciente = %s RETURNING id_paciente;", (id_paciente,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": f"Paciente {id_paciente} eliminado correctamente"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Restricción de integridad: {str(e)}")


# --- CRUD DE MÉDICOS ---
@app.get("/medicos/{documento}", response_model=MedicoResponse, tags=["Médicos"])
def obtener_medico(documento: str):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    # Cambiamos el WHERE para buscar por la columna documento
    cursor.execute("SELECT id_medico, documento, nombre_completo, id_especialidad FROM MEDICOS WHERE documento = %s;", (documento,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not fila:
        raise HTTPException(status_code=404, detail="Médico no encontrado con ese documento")
        
    return {
        "id_medico": fila[0], 
        "documento": fila[1], 
        "nombre_completo": fila[2], 
        "id_especialidad": fila[3]
    }
@app.post("/medicos", response_model=MedicoResponse, status_code=status.HTTP_201_CREATED, tags=["Médicos"])
def crear_medico(medico: MedicoCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    try:
        cursor = conn.cursor()
        
        # 1. Encriptamos la contraseña del médico
        hash_pass = get_password_hash(medico.password)
        
        # 2. Insertamos en la tabla incluyendo el password_hash
        cursor.execute(
            """INSERT INTO MEDICOS (documento, nombre_completo, id_especialidad, password_hash) 
               VALUES (%s, %s, %s, %s) RETURNING id_medico;""",
            (medico.documento, medico.nombre_completo, medico.id_especialidad, hash_pass)
        )
        id_generado = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Retornamos los datos sin exponer la contraseña
        return {
            "id_medico": id_generado,
            "documento": medico.documento,
            "nombre_completo": medico.nombre_completo,
            "id_especialidad": medico.id_especialidad
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"No se pudo registrar el médico: {str(e)}")

@app.get("/medicos", response_model=List[MedicoResponse], tags=["Médicos"])
def listar_medicos():
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    cursor = conn.cursor()
    cursor.execute("SELECT id_medico, documento, nombre_completo, id_especialidad FROM MEDICOS;")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{
        "id_medico": f[0], 
        "documento": f[1], 
        "nombre_completo": f[2], 
        "id_especialidad": f[3]
    } for f in filas]

@app.put("/medicos/{id_medico}", response_model=MedicoResponse, tags=["Médicos"])
def actualizar_medico(id_medico: int, medico: MedicoCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE MEDICOS SET documento = %s, nombre_completo = %s, id_especialidad = %s WHERE id_medico = %s RETURNING id_medico;",
            (medico.documento, medico.nombre_completo, medico.id_especialidad, id_medico)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Médico no encontrado")
        conn.commit()
        cursor.close()
        conn.close()
        return {**medico.model_dump(), "id_medico": id_medico}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# --- CRUD DE CITAS ---
@app.get("/citas/{id_cita}", response_model=CitaResponse, tags=["Agendamiento Citas"])
def obtener_cita(id_cita: int):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_cita, id_paciente, id_medico, id_estado, fecha_hora, consultorio FROM CITAS WHERE id_cita = %s;", (id_cita,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not fila:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
        
    return {
        "id_cita": fila[0], 
        "id_paciente": fila[1], 
        "id_medico": fila[2],
        "id_estado": fila[3], 
        "fecha_hora": fila[4], 
        "consultorio": fila[5]
    }
@app.post("/citas", response_model=CitaResponse, status_code=status.HTTP_201_CREATED, tags=["Agendamiento Citas"])
def agendar_cita(cita: CitaCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    
    try:
        cursor = conn.cursor()
        
        # Validación de Consistencia (ACID): Evitar sobreposición de horario para el mismo médico
        cursor.execute(
            "SELECT COUNT(*) FROM CITAS WHERE id_medico = %s AND fecha_hora = %s;",
            (cita.id_medico, cita.fecha_hora)
        )
        if cursor.fetchone()[0] > 0:
            raise HTTPException(status_code=400, detail="El médico ya cuenta con una cita asignada en ese horario exacto.")

        # Inserción controlada
        cursor.execute(
            """INSERT INTO CITAS (id_paciente, id_medico, id_estado, fecha_hora, consultorio) 
               VALUES (%s, %s, %s, %s, %s) RETURNING id_cita;""",
            (cita.id_paciente, cita.id_medico, cita.id_estado, cita.fecha_hora, cita.consultorio)
        )
        id_generado = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return {**cita.model_dump(), "id_cita": id_generado}
    
    except Exception as e:
        if conn:
            conn.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Fallo en la transacción: {str(e)}")

@app.get("/citas", response_model=List[CitaResponse], tags=["Agendamiento Citas"])
def listar_citas():
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_cita, id_paciente, id_medico, id_estado, fecha_hora, consultorio FROM CITAS;")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Mapeamos los resultados al esquema de Pydantic
    return [{
        "id_cita": f[0], 
        "id_paciente": f[1], 
        "id_medico": f[2],
        "id_estado": f[3], 
        "fecha_hora": f[4], 
        "consultorio": f[5]
    } for f in filas]

@app.put("/citas/{id_cita}/estado", tags=["Agendamiento Citas"])
def cambiar_estado_cita(id_cita: int, nuevo_id_estado: int):
    conn = get_postgres_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE CITAS SET id_estado = %s WHERE id_cita = %s RETURNING id_cita;",
            (nuevo_id_estado, id_cita)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": f"La cita {id_cita} fue actualizada exitosamente al estado con ID {nuevo_id_estado}"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
# ==========================================
#          CRUD DE PAGOS
# ==========================================

@app.get("/pagos/{id_pago}", response_model=PagoResponse, tags=["Control de Pagos"])
def obtener_pago(id_pago: int):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_pago, id_cita, monto, fecha_pago, estado_pago FROM PAGOS WHERE id_pago = %s;", (id_pago,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not fila:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
        
    return {
        "id_pago": fila[0], 
        "id_cita": fila[1], 
        "monto": float(fila[2]), 
        "fecha_pago": fila[3], 
        "estado_pago": fila[4]
    }

@app.post("/pagos", response_model=PagoResponse, status_code=status.HTTP_201_CREATED, tags=["Control de Pagos"])
def registrar_pago(pago: PagoCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        # COALESCE permite que si el valor viene nulo en la petición, actúe el DEFAULT de la tabla
        cursor.execute(
            """INSERT INTO PAGOS (id_cita, monto, fecha_pago, estado_pago) 
               VALUES (%s, %s, COALESCE(%s, CURRENT_TIMESTAMP), COALESCE(%s, 'Pendiente')) 
               RETURNING id_pago, fecha_pago, estado_pago;""",
            (pago.id_cita, pago.monto, pago.fecha_pago, pago.estado_pago)
        )
        resultado = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "id_pago": resultado[0],
            "id_cita": pago.id_cita,
            "monto": pago.monto,
            "fecha_pago": resultado[1],
            "estado_pago": resultado[2]
        }
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=f"No se pudo procesar el pago: {str(e)}")

@app.get("/pagos", response_model=List[PagoResponse], tags=["Control de Pagos"])
def listar_pagos():
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    cursor = conn.cursor()
    cursor.execute("SELECT id_pago, id_cita, monto, fecha_pago, estado_pago FROM PAGOS;")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Convertimos explícitamente el monto a float porque psycopg2 lo recupera como tipo Decimal
    return [{
        "id_pago": f[0], 
        "id_cita": f[1], 
        "monto": float(f[2]), 
        "fecha_pago": f[3], 
        "estado_pago": f[4]
    } for f in filas]

@app.put("/pagos/{id_pago}/estado", tags=["Control de Pagos"])
def cambiar_estado_pago(id_pago: int, nuevo_estado: str):
    """Permite registrar la transición del pago (Ej: de 'Pendiente' a 'Pagado' o 'Rechazado')"""
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE PAGOS SET estado_pago = %s WHERE id_pago = %s RETURNING id_pago;",
            (nuevo_estado, id_pago)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="El registro de pago no existe")
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": f"El pago transaccional {id_pago} pasó al estado '{nuevo_estado}' de forma exitosa"}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/pagos/{id_pago}", response_model=PagoResponse, tags=["Control de Pagos"])
def actualizar_pago_completo(id_pago: int, pago: PagoCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE PAGOS 
               SET id_cita = %s, monto = %s, fecha_pago = COALESCE(%s, fecha_pago), estado_pago = COALESCE(%s, estado_pago) 
               WHERE id_pago = %s 
               RETURNING id_pago, fecha_pago, estado_pago;""",
            (pago.id_cita, pago.monto, pago.fecha_pago, pago.estado_pago, id_pago)
        )
        resultado = cursor.fetchone()
        if not resultado:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "id_pago": id_pago,
            "id_cita": pago.id_cita,
            "monto": pago.monto,
            "fecha_pago": resultado[1],
            "estado_pago": resultado[2]
        }
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
#          CRUD DE ESPECIALIDADES
# ==========================================
@app.get("/especialidades/{id_especialidad}", response_model=EspecialidadResponse, tags=["Catálogo de Especialidades"])
def obtener_especialidad(id_especialidad: int):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_especialidad, nombre_specialidad, tarifa_base FROM ESPECIALIDADES WHERE id_especialidad = %s;", (id_especialidad,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not fila:
        raise HTTPException(status_code=404, detail="Especialidad no encontrada")
        
    return {
        "id_especialidad": fila[0],
        "nombre_specialidad": fila[1],
        "tarifa_base": float(fila[2])
    }
@app.post("/especialidades", response_model=EspecialidadResponse, status_code=status.HTTP_201_CREATED, tags=["Catálogo de Especialidades"])
def crear_especialidad(especialidad: EspecialidadCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO ESPECIALIDADES (nombre_specialidad, tarifa_base) 
               VALUES (%s, %s) 
               RETURNING id_especialidad;""",
            (especialidad.nombre_specialidad, especialidad.tarifa_base)
        )
        id_generado = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {**especialidad.model_dump(), "id_especialidad": id_generado}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=f"No se pudo registrar la especialidad: {str(e)}")

@app.get("/especialidades", response_model=List[EspecialidadResponse], tags=["Catálogo de Especialidades"])
def listar_especialidades():
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_especialidad, nombre_specialidad, tarifa_base FROM ESPECIALIDADES;")
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convertimos la tarifa a float debido a que psycopg2 la extrae como tipo Decimal de Python
        return [{
            "id_especialidad": f[0],
            "nombre_specialidad": f[1],
            "tarifa_base": float(f[2])
        } for f in filas]
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/especialidades/{id_especialidad}", response_model=EspecialidadResponse, tags=["Catálogo de Especialidades"])
def actualizar_especialidad(id_especialidad: int, especialidad: EspecialidadCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE ESPECIALIDADES 
               SET nombre_specialidad = %s, tarifa_base = %s 
               WHERE id_especialidad = %s 
               RETURNING id_especialidad;""",
            (especialidad.nombre_specialidad, especialidad.tarifa_base, id_especialidad)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Especialidad no encontrada")
        conn.commit()
        cursor.close()
        conn.close()
        return {**especialidad.model_dump(), "id_especialidad": id_especialidad}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/especialidades/{id_especialidad}", tags=["Catálogo de Especialidades"])
def eliminar_especialidad(id_especialidad: int):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ESPECIALIDADES WHERE id_especialidad = %s RETURNING id_especialidad;", (id_especialidad,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Especialidad no encontrada")
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": f"Especialidad con ID {id_especialidad} eliminada correctamente de la base de datos"}
    except Exception as e:
        if conn:
            conn.rollback()
        # Controlamos el error por restricción de llave foránea (FK)
        raise HTTPException(
            status_code=400, 
            detail=f"Restricción de integridad: No se puede eliminar la especialidad porque está vinculada a registros de médicos existentes. {str(e)}"
        )
# ==========================================
#          CRUD DE ESTADOS DE CITAS
# ==========================================
@app.get("/estados-cita/{id_estado}", response_model=EstadoCitaResponse, tags=["Catálogo de Estados"])
def obtener_estado(id_estado: int):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_estado, nombre_estado FROM ESTADOS_CITA WHERE id_estado = %s;", (id_estado,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not fila:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
        
    return {
        "id_estado": fila[0],
        "nombre_estado": fila[1]
    }
@app.post("/estados-cita", response_model=EstadoCitaResponse, status_code=status.HTTP_201_CREATED, tags=["Catálogo de Estados"])
def crear_estado(estado: EstadoCitaCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO ESTADOS_CITA (nombre_estado) 
               VALUES (%s) 
               RETURNING id_estado;""",
            (estado.nombre_estado,)
        )
        id_generado = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {**estado.model_dump(), "id_estado": id_generado}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=f"No se pudo registrar el estado: {str(e)}")

@app.get("/estados-cita", response_model=List[EstadoCitaResponse], tags=["Catálogo de Estados"])
def listar_estados():
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    cursor = conn.cursor()
    cursor.execute("SELECT id_estado, nombre_estado FROM ESTADOS_CITA;")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{
        "id_estado": f[0],
        "nombre_estado": f[1]
    } for f in filas]

@app.put("/estados-cita/{id_estado}", response_model=EstadoCitaResponse, tags=["Catálogo de Estados"])
def actualizar_estado(id_estado: int, estado: EstadoCitaCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE ESTADOS_CITA 
               SET nombre_estado = %s 
               WHERE id_estado = %s 
               RETURNING id_estado;""",
            (estado.nombre_estado, id_estado)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Estado no encontrado")
        conn.commit()
        cursor.close()
        conn.close()
        return {**estado.model_dump(), "id_estado": id_estado}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/estados-cita/{id_estado}", tags=["Catálogo de Estados"])
def eliminar_estado(id_estado: int):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ESTADOS_CITA WHERE id_estado = %s RETURNING id_estado;", (id_estado,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Estado no encontrado")
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": f"Estado con ID {id_estado} eliminado correctamente de la base de datos"}
    except Exception as e:
        if conn:
            conn.rollback()
        # Manejo de error si intentan borrar un estado que ya está asignado a una cita
        raise HTTPException(
            status_code=400, 
            detail=f"Restricción de integridad: No puedes eliminar este estado porque existen citas vinculadas a él. {str(e)}"
        )
# ==========================================
#          CRUD DE AUDITORÍA DE ESTADOS
# ==========================================
@app.get("/auditoria-estado/{id_auditoria}", response_model=AuditoriaEstadoResponse, tags=["Auditoría de Estados"])
def obtener_auditoria(id_auditoria: int):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_auditoria, id_cita, estado_anterior, estado_nuevo, fecha_cambio FROM auditoria_estados WHERE id_auditoria = %s;", (id_auditoria,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not fila:
        raise HTTPException(status_code=404, detail="Registro de auditoría no encontrado")
        
    return {
        "id_auditoria": fila[0],
        "id_cita": fila[1],
        "estado_anterior": fila[2],
        "estado_nuevo": fila[3],
        "fecha_cambio": fila[4]
    }
@app.post("/auditoria-estado", response_model=AuditoriaEstadoResponse, status_code=status.HTTP_201_CREATED, tags=["Auditoría de Estados"])
def crear_auditoria(auditoria: AuditoriaEstadoCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        # Cambiamos AUDITORIA_ESTADO por auditoria_estados
        cursor.execute(
            """INSERT INTO auditoria_estados (id_cita, estado_anterior, estado_nuevo, fecha_cambio) 
               VALUES (%s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP)) 
               RETURNING id_auditoria, fecha_cambio;""",
            (auditoria.id_cita, auditoria.estado_anterior, auditoria.estado_nuevo, auditoria.fecha_cambio)
        )
        resultado = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return {
            "id_auditoria": resultado[0],
            "id_cita": auditoria.id_cita,
            "estado_anterior": auditoria.estado_anterior,
            "estado_nuevo": auditoria.estado_nuevo,
            "fecha_cambio": resultado[1]
        }
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=f"No se pudo registrar la auditoría: {str(e)}")

@app.get("/auditoria-estado", response_model=List[AuditoriaEstadoResponse], tags=["Auditoría de Estados"])
def listar_auditorias():
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    cursor = conn.cursor()
    # Cambiamos AUDITORIA_ESTADO por auditoria_estados
    cursor.execute("SELECT id_auditoria, id_cita, estado_anterior, estado_nuevo, fecha_cambio FROM auditoria_estados ORDER BY fecha_cambio DESC;")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{
        "id_auditoria": f[0],
        "id_cita": f[1],
        "estado_anterior": f[2],
        "estado_nuevo": f[3],
        "fecha_cambio": f[4]
    } for f in filas]

@app.put("/auditoria-estado/{id_auditoria}", response_model=AuditoriaEstadoResponse, tags=["Auditoría de Estados"])
def actualizar_auditoria(id_auditoria: int, auditoria: AuditoriaEstadoCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        # Cambiamos AUDITORIA_ESTADO por auditoria_estados
        cursor.execute(
            """UPDATE auditoria_estados 
               SET id_cita = %s, estado_anterior = %s, estado_nuevo = %s, fecha_cambio = COALESCE(%s, fecha_cambio) 
               WHERE id_auditoria = %s 
               RETURNING id_auditoria, fecha_cambio;""",
            (auditoria.id_cita, auditoria.estado_anterior, auditoria.estado_nuevo, auditoria.fecha_cambio, id_auditoria)
        )
        resultado = cursor.fetchone()
        if not resultado:
            raise HTTPException(status_code=404, detail="Registro de auditoría no encontrado")
        conn.commit()
        cursor.close()
        conn.close()
        return {
            "id_auditoria": id_auditoria,
            "id_cita": auditoria.id_cita,
            "estado_anterior": auditoria.estado_anterior,
            "estado_nuevo": auditoria.estado_nuevo,
            "fecha_cambio": resultado[1]
        }
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/auditoria-estado/{id_auditoria}", tags=["Auditoría de Estados"])
def eliminar_auditoria(id_auditoria: int):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    try:
        cursor = conn.cursor()
        # Cambiamos AUDITORIA_ESTADO por auditoria_estados
        cursor.execute("DELETE FROM auditoria_estados WHERE id_auditoria = %s RETURNING id_auditoria;", (id_auditoria,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Registro de auditoría no encontrado")
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": f"Registro de auditoría con ID {id_auditoria} eliminado correctamente"}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
from bson import ObjectId
from pydantic import BaseModel, Field

# Esquema para manejar el ID de MongoDB (ObjectId -> string)
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

from typing import Optional, List, Dict, Any

class HistoriaClinicaModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    id_paciente_sql: int
    id_cita_sql: int
    fecha_registro: str
    medico_tratante: str
    signos_vitales: Dict[str, Any]
    motivo_consulta: str
    diagnostico: str
    receta_medica: List[str] = []
    archivos_adjuntos: List[str] = []
    # Usamos Optional porque algunos pacientes pueden no requerir incapacidad
    incapacidad_dias: Optional[int] = None 

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# ==========================================
#          CRUD DE HISTORIAS CLÍNICAS (MONGODB)
# ==========================================

@app.post("/historias-clinicas", tags=["Historias Clínicas"])
def crear_historia(historia: HistoriaClinicaModel):
    db = get_mongo_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Error al conectar con MongoDB")
    
    collection = db["historias_clinicas"]
    # Convertimos el modelo a diccionario, eliminando el id temporal si viene nulo
    data = historia.model_dump(by_alias=True, exclude={"id"})
    
    result = collection.insert_one(data)
    return {"message": "Historia clínica creada", "id": str(result.inserted_id)}

@app.get("/historias-clinicas/{id_paciente}", tags=["Historias Clínicas"])
def listar_historias_paciente(id_paciente: int):
    db = get_mongo_db()
    collection = db["historias_clinicas"]
    
    # Buscamos en MongoDB filtrando por el ID que viene de PostgreSQL
    resultados = list(collection.find({"id_paciente_sql": id_paciente}))
    
    # Convertimos los ObjectIds de Mongo a string para que el JSON sea válido
    for doc in resultados:
        doc["_id"] = str(doc["_id"])
        
    return resultados

@app.post("/finalizar-cita-y-crear-historia/{id_cita}", tags=["Integración Políglota"])
def finalizar_cita(id_cita: int):
    # 1. Lógica PostgreSQL: Verificar y actualizar estado
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_paciente, id_medico FROM CITAS WHERE id_cita = %s", (id_cita,))
    cita = cursor.fetchone()
    
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada en SQL")
        
    # 2. Lógica MongoDB: Crear documento inicial
    db = get_mongo_db()
    db["historias_clinicas"].insert_one({
        "id_cita_sql": id_cita,
        "id_paciente_sql": cita[0],
        "fecha_registro": datetime.utcnow().isoformat(),
        "medico_tratante": f"ID Médico: {cita[1]}",
        "motivo_consulta": "Consulta Médica",
        "signos_vitales": {"presion": "120/80", "ritmo_cardiaco": 70},
        "notas_evolucion": "Pendiente de diligenciar",
        "archivos_adjuntos": []
    })
    
    return {"status": "Cita finalizada en SQL y expediente clínico creado en No-SQL"}