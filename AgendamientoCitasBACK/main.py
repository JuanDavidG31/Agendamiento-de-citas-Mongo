from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Importamos tu conexión a Neon desde database.py
from database import get_postgres_connection

# ==========================================
# 1. ESQUEMAS DE VALIDACIÓN (PYDANTIC)
# (Esto fue lo primero que te di. Define cómo se ven los datos)
# ==========================================

# --- ESQUEMAS PARA PACIENTES ---
class PacienteBase(BaseModel):
    documento: str
    nombres: str
    apellidos: str
    email: Optional[str] = None  # Reemplazamos telefono por email

class PacienteCreate(PacienteBase):
    pass

class PacienteResponse(PacienteBase):
    id_paciente: int

# --- ESQUEMAS PARA MÉDICOS ---
class MedicoBase(BaseModel):
    nombre: str
    especialidad: str

class MedicoCreate(MedicoBase):
    pass

class MedicoResponse(MedicoBase):
    id_medico: int

# --- ESQUEMAS PARA CITAS ---
class CitaCreate(BaseModel):
    id_paciente: int
    id_medico: int
    fecha_hora: datetime
    consultorio: str

class CitaResponse(BaseModel):
    id_cita: int
    id_paciente: int
    id_medico: int
    fecha_hora: datetime
    consultorio: str
    estado: str


# ==========================================
# 2. INICIALIZACIÓN DE FASTAPI
# ==========================================
app = FastAPI(
    title="Portal Médico de Citas Hospitalarias",
    description="API de Integración Políglota. Control de operaciones CRUD en el núcleo transaccional (PostgreSQL).",
    version="2.0"
)

@app.get("/", tags=["Inicio"])
def home():
    return {"mensaje": "API conectada a Neon lista."}

# ==========================================
# 3. RUTAS CRUD (ENDPOINTS)
# (Esto fue lo segundo que te di. Define las operaciones SQL)
# ==========================================

# --- CRUD DE PACIENTES ---
@app.post("/pacientes", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED, tags=["Pacientes"])
def crear_paciente(paciente: PacienteCreate):
    conn = get_postgres_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO PACIENTES (documento, nombres, apellidos, email) VALUES (%s, %s, %s, %s) RETURNING id_paciente;",
            (paciente.documento, paciente.nombres, paciente.apellidos, paciente.email)
        )
        id_generado = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {**paciente.model_dump(), "id_paciente": id_generado}
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
@app.post("/medicos", response_model=MedicoResponse, status_code=status.HTTP_201_CREATED, tags=["Médicos"])
def crear_medico(medico: MedicoCreate):
    conn = get_postgres_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO MEDICOS (nombre, especialidad) VALUES (%s, %s) RETURNING id_medico;",
            (medico.nombre, medico.especialidad)
        )
        id_generado = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {**medico.model_dump(), "id_medico": id_generado}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/medicos", response_model=List[MedicoResponse], tags=["Médicos"])
def listar_medicos():
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_medico, nombre, especialidad FROM MEDICOS;")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id_medico": f[0], "nombre": f[1], "especialidad": f[2]} for f in filas]


# --- CRUD DE CITAS ---
@app.post("/citas", response_model=CitaResponse, status_code=status.HTTP_201_CREATED, tags=["Agendamiento Citas"])
def agendar_cita(cita: CitaCreate):
    conn = get_postgres_connection()
    try:
        cursor = conn.cursor()
        
        # Validación de Consistencia: Evitar sobreposición de horario para el mismo médico
        cursor.execute(
            "SELECT COUNT(*) FROM CITAS WHERE id_medico = %s AND fecha_hora = %s AND estado = 'Programada';",
            (cita.id_medico, cita.fecha_hora)
        )
        if cursor.fetchone()[0] > 0:
            raise HTTPException(status_code=400, detail="El médico ya cuenta con una cita asignada en ese horario.")

        # Inserción controlada
        cursor.execute(
            """INSERT INTO CITAS (id_paciente, id_medico, fecha_hora, consultorio, estado) 
               VALUES (%s, %s, %s, %s, 'Programada') RETURNING id_cita;""",
            (cita.id_paciente, cita.id_medico, cita.fecha_hora, cita.consultorio)
        )
        id_generado = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "id_cita": id_generado,
            "id_paciente": cita.id_paciente,
            "id_medico": cita.id_medico,
            "fecha_hora": cita.fecha_hora,
            "consultorio": cita.consultorio,
            "estado": "Programada"
        }
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
    cursor.execute("SELECT id_cita, id_paciente, id_medico, fecha_hora, consultorio, estado FROM CITAS;")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{
        "id_cita": f[0], "id_paciente": f[1], "id_medico": f[2],
        "fecha_hora": f[3], "consultorio": f[4], "estado": f[5]
    } for f in filas]

@app.put("/citas/{id_cita}/estado", tags=["Agendamiento Citas"])
def cambiar_estado_cita(id_cita: int, nuevo_estado: str):
    conn = get_postgres_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE CITAS SET estado = %s WHERE id_cita = %s RETURNING id_cita;",
            (nuevo_estado, id_cita)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": f"Cita {id_cita} actualizada a estado '{nuevo_estado}'"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))