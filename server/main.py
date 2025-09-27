from fastapi import FastAPI

app = FastAPI(title="RAGBOT")



@app.get("/test")
async def test():
    return {"message": "RAGBOT is running!"}