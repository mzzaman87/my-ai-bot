from fastapi import FastAPI

app = FastAPI()

# ================= HOME =================
@app.get("/")
def home():
    return {"status": "MonirBot running clean version"}

# ================= WEBHOOK VERIFY =================
@app.get("/webhook")
def verify():
    return "MonirBot webhook active"
