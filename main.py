import shutil
import uuid
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from ai_engine import engine 

app = FastAPI(title="Dreamu API")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# MAX POWER PRESETS (12 Styles)
# Short descriptions are expanded by Gemini in ai_engine.py
PRESETS = {
    "real": "hyper-realistic photography, 85mm lens, cinematic lighting, raw photo",
    "cyber": "futuristic cyberpunk style, neon lighting, high-tech atmosphere",
    "cinematic": "cinematic movie scene, dramatic lighting, teal and orange grading",
    "ghibli": "Studio Ghibli anime style, hand-drawn textures, peaceful atmosphere",
    "oil": "oil painting, thick impasto brushstrokes, Van Gogh style",
    "sketch": "charcoal sketch on paper, dramatic shading, monochrome",
    "pixar": "Pixar 3D character style, cute, soft lighting, 4k render",
    "fantasy": "epic high fantasy painting, magical atmosphere, intricate details",
    "vapor": "retro 80s vaporwave aesthetic, neon grid, synthwave",
    "macro": "macro photography, extreme close-up, bokeh background",
    "gothic": "dark gothic aesthetic, heavy shadows, mysterious atmosphere",
    "popart": "Pop Art illustration, bold outlines, halftone dots, Andy Warhol style"
}

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.post("/api/dream")
async def create_dream(file: UploadFile = File(...), style: str = Form(...)):
    unique_id = str(uuid.uuid4())[:8]
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    input_path = f"uploads/{unique_id}.{file_ext}"

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return {"error": f"File upload failed: {e}"}

    # Get base prompt
    base_prompt = PRESETS.get(style, "artistic style")

    # Run AI with Gemini Enhancement
    # We pass the style name (e.g., 'cyber') for the story generation
    # engine.generate now returns 3 values: image, title, story
    result_image, title, story = engine.generate(input_path, base_prompt, style)

    if not result_image:
        return {"error": "Dream failed. Try a different image or restart."}

    output_filename = f"dream_{unique_id}.png"
    output_path = f"outputs/{output_filename}"
    result_image.save(output_path)

    return {
        "status": "success",
        "dream_url": f"/outputs/{output_filename}",
        "title": title.strip(),
        "story": story.strip()
    }

if __name__ == "__main__":
    print("🚀 Dreamu Server Starting at http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)