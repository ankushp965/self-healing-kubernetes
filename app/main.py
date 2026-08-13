from fastapi import FastAPI
import os
import time

app = FastAPI(title="Kubernetes Troubleshooting Demo")

@app.get("/")
def home():
    return {"message":"Application is healthy"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/crash")
def crash():
    os._exit(1)

@app.get("/error")
def error():
    return {"status":"Internal Server Error"}

@app.get("/cpu-spike")
def cpu_spike():
    start = time.time()
    while (time.time() - start < 30):
        pass
    return {"message":"CPU spike completed"}
