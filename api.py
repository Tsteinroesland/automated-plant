from fastapi import FastAPI
import sqlite3


con = sqlite3.connect("plant.db")
con.row_factory = sqlite3.Row
db = con.cursor()

app = FastAPI()


@app.get("/")
async def root():
    db.execute("SELECT * FROM measurements;")
    results = db.fetchall()
    return results 
