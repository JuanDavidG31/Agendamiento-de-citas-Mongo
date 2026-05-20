from fastapi import FastAPI, HTTPException
from database import get_postgres_connection, get_mongo_db
from datetime import datetime

# Autores: Juan Camilo Beltrán, Diego Bonza, Juan Pablo Cuervo, Juan David González
app = FastAPI(title="API Gestión Médica Políglota")

@app.get("/")
def home():
    return {"mensaje": "API de Integración PostgreSQL + MongoDB funcionando."}

@app.post("/completar-cita/{id_cita}")
def completar_cita_y_crear_historia(id_cita: int):
    pg_conn = get_postgres_connection()
    if not pg_conn:
        raise HTTPException(status_code=500, detail="Error de conexión con PostgreSQL")
    
    try:
        pg_cursor = pg_conn.cursor()
        
        # Validamos que la cita exista en PostgreSQL
        pg_cursor.execute("SELECT ID_Paciente, ID_Medico, Consultorio FROM CITAS WHERE ID_Cita = %s", (id_cita,))
        cita_data = pg_cursor.fetchone()
        
        if not cita_data:
            raise HTTPException(status_code=404, detail="Cita no encontrada en PostgreSQL")
            
        id_paciente_sql, id_medico_sql, consultorio = cita_data
        pg_conn.close()

        # Nos conectamos a MongoDB para crear el documento de historia clínica
        mongo_db = get_mongo_db()
        historias_collection = mongo_db["historias_clinicas"]
        
        nuevo_documento = {
            "id_cita_sql": id_cita,
            "id_paciente_sql": id_paciente_sql,
            "fecha_registro": datetime.utcnow().isoformat(),
            "medico_tratante": f"Médico ID: {id_medico_sql}",
            "motivo_consulta": "Consulta General Programada",
            "signos_vitales": {
                "presion": "120/80",
                "ritmo_cardiaco": 75
            },
            "notas_evolucion": "Documento base generado automáticamente por el integrador.",
            "archivos_adjuntos": ["Ninguno"]
        }
        
        result = historias_collection.insert_one(nuevo_documento)
        
        return {
            "status": "Transacción finalizada",
            "postgres": f"Cita {id_cita} verificada en el núcleo ACID.",
            "mongodb": f"Documento creado en modelo BASE con _id: {str(result.inserted_id)}"
        }

    except Exception as e:
        if pg_conn:
            pg_conn.rollback() 
        raise HTTPException(status_code=500, detail=str(e))