from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "MonirBot reset started"}


@app.get("/webhook")
def verify():
    return "MonirBot webhook active"
