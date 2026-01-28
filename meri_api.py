from fastapi import FastAPI

# 1. API ka main engine (app) banate hain
app = FastAPI()

# 2. Pehla "Route" - Jab koi aapki site par aayega
@app.get("/")
def read_root():
    return {"message": "Bhai, congratulations! Aapki pehli API Ubuntu par live hai 🚀"}

# 3. Dusra "Route" - Dynamic data ke liye
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "status": "Success", "note": "Ye data API se aa raha hai!"}
