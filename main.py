from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = FastAPI()

# Database connection details
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Models
class PotCreate(BaseModel):
    name: str
    location: Optional[str] = None

class SensorDataCreate(BaseModel):
    pot_id: int
    moisture: float
    light: float
    temperature: float

class Pot(BaseModel):
    id: int
    name: str
    location: Optional[str]
    created_at: datetime

class SensorData(BaseModel):
    id: int
    pot_id: int
    moisture: float
    light: float
    temperature: float
    timestamp: datetime

# Create a new GIA Pot
@app.post("/pots/", response_model=Pot)
def create_pot(pot: PotCreate):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO pots (name, location, created_at)
                VALUES (%s, %s, %s)
                RETURNING id, name, location, created_at
                """,
                (pot.name, pot.location, datetime.utcnow())
            )
            new_pot = cursor.fetchone()
            conn.commit()
        return new_pot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

# Receive and store sensor data
@app.post("/sensor-data/", response_model=SensorData)
def create_sensor_data(sensor_data: SensorDataCreate):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sensor_data (pot_id, moisture, light, temperature, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, pot_id, moisture, light, temperature, timestamp
                """,
                (sensor_data.pot_id, sensor_data.moisture, sensor_data.light, sensor_data.temperature, datetime.utcnow())
            )
            new_sensor_data = cursor.fetchone()
            conn.commit()
        return new_sensor_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

# Get all sensor data for a specific pot
@app.get("/pots/{pot_id}/sensor-data/", response_model=List[SensorData])
def get_sensor_data(pot_id: int):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM sensor_data WHERE pot_id = %s ORDER BY timestamp DESC
                """,
                (pot_id,)
            )
            sensor_data = cursor.fetchall()
        return sensor_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "GIA Smart Pot API is running"}
