from fastapi import FastAPI, Form, File, UploadFile
from typing import Optional, List
from fastapi.testclient import TestClient

app = FastAPI()

@app.post("/test1")
async def test1(mediaFiles: Optional[List[UploadFile]] = File(None)):
    return {"len": len(mediaFiles) if mediaFiles else 0}

@app.post("/test2")
async def test2(mediaFiles: List[UploadFile] = File(default=[])):
    return {"len": len(mediaFiles) if mediaFiles else 0}

client = TestClient(app)
print("test1 with 2 files:", client.post("/test1", files=[("mediaFiles", ("a.jpg", b"a")), ("mediaFiles", ("b.jpg", b"b"))]).json())
print("test2 with 2 files:", client.post("/test2", files=[("mediaFiles", ("a.jpg", b"a")), ("mediaFiles", ("b.jpg", b"b"))]).json())
print("test1 with 0 files:", client.post("/test1", data={"dummy": "1"}).json())
print("test2 with 0 files:", client.post("/test2", data={"dummy": "1"}).json())
