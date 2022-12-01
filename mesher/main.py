from fastapi import FastAPI, UploadFile

app = FastAPI()

@app.post('/convert')
async def convert(file: UploadFile):
    data = await file.read()

