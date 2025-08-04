
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from moviepy.editor import VideoFileClip, CompositeVideoClip

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoLink(BaseModel):
    url: str
    start_sec: Optional[int] = 10
    duration_range: Optional[str] = "medium"

@app.get("/", response_class=HTMLResponse)
async def root():
    gameplay_dir = "gameplays"
    gameplay_files = [f for f in os.listdir(gameplay_dir) if f.endswith(".mp4")]
    gameplay_html = "".join([f"<option value='{f}'>{f}</option>" for f in gameplay_files])
    return f"""
    <html>
        <body>
            <h2>Generatore Shorts</h2>
            <form action="/upload-video/" method="post" enctype="multipart/form-data">
                Carica video: <input type="file" name="file" accept="video/*" required><br><br>
                Seleziona gameplay: 
                <select name="gameplay_file">
                    {gameplay_html}
                </select><br><br>
                Inizio (secondi): <input type="number" name="start_sec" value="10"><br><br>
                Durata clip:
                <select name="duration_range">
                    <option value="short">Meno di 10s</option>
                    <option value="medium" selected>10-30s</option>
                    <option value="long">30-60s</option>
                </select><br><br>
                <button type="submit">Genera Clip</button>
            </form>
        </body>
    </html>
    """

@app.post("/upload-video/")
async def upload_video(
    file: UploadFile = File(...),
    gameplay_file: str = Form(...),
    start_sec: int = Form(10),
    duration_range: str = Form("medium")
):
    duration_map = {
        "short": 8,
        "medium": 20,
        "long": 45
    }
    duration_sec = duration_map.get(duration_range, 20)

    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    input_path = os.path.join(temp_dir, file.filename)
    with open(input_path, "wb") as f:
        f.write(await file.read())

    gameplay_path = os.path.join("gameplays", gameplay_file)
    output_path = os.path.join(temp_dir, "output.mp4")

    # Processa video
    try:
        main_clip = VideoFileClip(input_path).subclip(start_sec, start_sec + duration_sec)
        gameplay_clip = VideoFileClip(gameplay_path).subclip(0, duration_sec).resize(height=main_clip.h // 2)

        final_video = CompositeVideoClip([
            main_clip.set_position(("center", "top")),
            gameplay_clip.set_position(("center", "bottom"))
        ], size=(main_clip.w, main_clip.h + gameplay_clip.h))

        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    except Exception as e:
        return {"error": str(e)}

    return FileResponse(output_path, media_type="video/mp4", filename="short_output.mp4")
