from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
import time
from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class FileAgent:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.instructions_dir = os.path.join(self.data_dir, 'instructions')
        self.images_dir = os.path.join(self.data_dir, 'images')
        self.trace_file_path = os.path.join(self.instructions_dir, 'trace.md')
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.instructions_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

    def find_lore_file(self):
        lore_file_path = os.path.join(self.instructions_dir, 'Lore.md')
        if os.path.exists(lore_file_path):
            with open(lore_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def get_next_chapter(self, chapter_num):
        chapter_path = os.path.join(self.instructions_dir, f'Chapter_{chapter_num}.md')
        if os.path.exists(chapter_path):
            with open(chapter_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def update_trace(self, message):
        with open(self.trace_file_path, 'a', encoding='utf-8') as trace_file:
            trace_file.write(f"{message}\n")

file_agent = FileAgent()

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/api/chapter/{chapter_num}")
async def get_chapter(chapter_num: int):
    content = file_agent.get_next_chapter(chapter_num)
    if not content:
        raise HTTPException(status_code=404, detail="Chapter not found")
    file_agent.update_trace(f"Requested Chapter {chapter_num}")
    return {"content": content}

@app.post("/api/reset")
async def reset_story():
    with open(file_agent.trace_file_path, 'w', encoding='utf-8') as f:
        f.write("")
    content = file_agent.get_next_chapter(1)
    return {"content": content}

@app.post("/start")
async def start_story():
    reset_story()
    return JSONResponse(content={"message": "Story started"})

@app.post("/next")
async def next_chapter(request: Request):
    data = await request.json()
    chapter_num = data.get("chapter_num", 1)
    skip = data.get("skip", False)
    content = stream_chapter(chapter_num, skip)
    return JSONResponse(content={"content": content})

def stream_chapter(chapter_num, skip=False):
    content = file_agent.get_next_chapter(chapter_num)
    if not content:
        return "Fin de l'histoire."

    full_response = ""
    if skip:
        full_response = content
    else:
        for char in content:
            full_response += char
            time.sleep(0.01)

    file_agent.update_trace(f"Streamed Chapter {chapter_num}")
    return full_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
