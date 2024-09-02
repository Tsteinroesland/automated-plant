import json
import sqlite3

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

con = sqlite3.connect("plant.db")
con.row_factory = sqlite3.Row
db = con.cursor()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

translate = lambda a, b, c, d, e: round((a - b) * (e - d) / (c - b) + d, 2)

MAX_SONAR_DISTANCE = 18.0
MIN_SONAR_DISTANCE = 12.34

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    db.execute("SELECT * FROM measurements;")
    results = db.fetchall()
    measurements = [dict(row) for row in results]
    db.execute(
        """SELECT 
               (SELECT MIN(moisture) from measurements) as min_moisture_measurement, 
               (SELECT MAX(moisture) from measurements) as max_moisture_measurement, 
               (SELECT humidity from measurements ORDER BY id DESC LIMIT 1) as latest_humidity,
               (SELECT tank_level from measurements ORDER BY id DESC LIMIT 1) as latest_tank_level,
               (SELECT temperature from measurements ORDER BY id DESC LIMIT 1) as latest_temperature"""
    )
    meta_data = dict(db.fetchone())

    results = {
        "measurements": measurements,
        "lower_bound": meta_data["min_moisture_measurement"] + 0.10,
        "upper_bound": meta_data["max_moisture_measurement"] + 0.10,
    }

    return templates.TemplateResponse(
        request=request,
        name="view.html",
        context={
            "data": json.dumps(results),
            "latest_temperature": meta_data["latest_temperature"],
            "latest_humidity": meta_data["latest_humidity"],
            "latest_tank_level": translate(
                meta_data["latest_tank_level"], MAX_SONAR_DISTANCE, MIN_SONAR_DISTANCE, 0, 100
            ),
        },
    )


@app.get("/header", response_class=HTMLResponse)
async def get_header(request: Request):
    db.execute(
        """SELECT 
               (SELECT humidity from measurements ORDER BY id DESC LIMIT 1) as latest_humidity,
               (SELECT tank_level from measurements ORDER BY id DESC LIMIT 1) as latest_tank_level,
               (SELECT temperature from measurements ORDER BY id DESC LIMIT 1) as latest_temperature"""
    )
    measurements = dict(db.fetchone())
    return templates.TemplateResponse(
        request=request,
        name="header.html",
        context={
            "latest_temperature": measurements["latest_temperature"],
            "latest_humidity": measurements["latest_humidity"],
            "latest_tank_level": round(translate(measurements["latest_tank_level"], MAX_SONAR_DISTANCE, MIN_SONAR_DISTANCE, 0, 100), 2),
        },
    )

@app.get("/chart-data", response_class=JSONResponse)
async def get_char_data(id: int):
    db.execute("SELECT * from measurements WHERE id > ?;", [id])
    results = db.fetchall()
    measurements = [dict(row) for row in results]
    return jsonable_encoder(measurements)

