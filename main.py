"""
DreamU API Server
=================
FastAPI backend with config-driven defaults, dynamic model management,
and universal generation endpoint.
"""

import os
import json
import shutil
import uuid
import time
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# -- Config Loading -----------------------------------
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    """Load config.json written by setup.py."""
    defaults = {
        "default_t2i_model": "sdxl-turbo",
        "default_i2i_model": "realvis-v4",
        "force_vram_offload": True,
        "max_resolution": 768,
        "hf_cache_dir": "Y:/dreaemu_engine",
        "t2i_models": [],
        "i2i_models": [],
    }
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            defaults.update(data)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return defaults

CONFIG = load_config()

# -- Ensure directories exist -------------------------
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# -- Engine (lazy init) -------------------------------
engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lazy-initialize the DreamU engine on server startup."""
    global engine
    from ai_engine import DreamuEngine
    engine = DreamuEngine()
    print("DreamU Server Ready!")
    yield
    # Cleanup on shutdown
    if engine:
        engine.unload_model()
    print("DreamU Server Stopped.")


app = FastAPI(
    title="DreamU API",
    description="Universal Image Generation Engine",
    version="2.0.0",
    lifespan=lifespan,
)

# -- Static file mounts -------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


# -- Preset Database ----------------------------------
PRESETS = {
    # --- TRENDING ---
    "trend_flux": {"label": "Flux Raw", "category": "Trending", "prompt": "Amateur smartphone photo, authentic film grain, slight motion blur, harsh flash, candid moment, unedited, raw aesthetic, 4k, highly detailed skin texture."},
    "trend_lomo": {"label": "Lomo", "category": "Trending", "prompt": "Lomography style, oversaturated colors, heavy vignette, high contrast, cross-processing effect, leaky light, nostalgic 2010s instagram aesthetic."},
    "trend_glitch": {"label": "Glitch", "category": "Trending", "prompt": "Digital datamoshing, pixel sorting artifacts, CRT monitor scanlines, RGB split, cyberpunk error, distorted reality, glitchcore aesthetic."},
    "trend_holo": {"label": "Holo", "category": "Trending", "prompt": "Iridescent holographic texture, translucent foil material, chromatic aberration, futuristic fashion, glowing edge lighting, ethereal prism effects."},

    # --- ANIME ---
    "anim_spider": {"label": "SpiderVS", "category": "Anime", "prompt": "Into the Spider-Verse animation style, comic book halftone dots, chromatic aberration, vibrant neon colors, graffiti aesthetic, exaggerated perspective, Ben-Day dots, expressive ink lines."},
    "anim_pixar": {"label": "Pixar", "category": "Anime", "prompt": "Pixar animation style, cute proportions, subsurface scattering on skin, soft studio lighting, perfectly clean textures, 3D render, expressive eyes, Disney style, 4k."},
    "anim_disney": {"label": "Disney", "category": "Anime", "prompt": "Modern Disney animated movie style, 3D render, lush hair textures, expressive faces, magical lighting, Frozen or Moana aesthetic, highly detailed, cinematic composition."},
    "anim_japan": {"label": "Anime", "category": "Anime", "prompt": "High-quality modern Japanese anime key visual, Kyoto Animation style, sharp outlines, cel shading, vibrant colors, intricate eyes, cinematic lighting, high quality 2D animation."},

    # --- PHOTOGRAPHY ---
    "photo_fisheye": {"label": "Fisheye", "category": "Photo", "prompt": "Ultra-wide fisheye lens distortion, 8mm skate video aesthetic, barrel distortion, close-up focus, dynamic perspective, vignette borders."},
    "photo_macro": {"label": "Macro", "category": "Photo", "prompt": "Extreme macro photography, microscopic details, water droplets, compound eyes, razor sharp focus, creamy bokeh background, scientific imaging."},
    "photo_drone": {"label": "Drone", "category": "Photo", "prompt": "High-altitude drone photography, top-down perspective, geometric landscapes, epic scale, golden hour lighting, wide dynamic range."},
    "photo_thermal": {"label": "Thermal", "category": "Photo", "prompt": "Thermal imaging camera style, heat map color palette (blue to red/orange), glowing silhouettes, scientific visualization, night vision aesthetic."},
    "photo_double": {"label": "Double Exp.", "category": "Photo", "prompt": "Double exposure photography, silhouette of main subject filled with nature landscapes, dreamy overlay, artistic blending, ethereal composition."},

    # --- ART ---
    "art_oil": {"label": "Oil Paint", "category": "Art", "prompt": "Thick impasto oil painting, visible palette knife strokes, vibrant swirling colors, Van Gogh influence, textured canvas, expressive technique."},
    "art_sketch": {"label": "Sketch", "category": "Art", "prompt": "Rough charcoal and graphite sketch on textured paper, deep shadows, smudged shading, loose gestural lines, unfinished artistic look."},
    "art_watercolor": {"label": "Watercolor", "category": "Art", "prompt": "Soft watercolor painting, wet-on-wet technique, pastel color bleeding, paper texture visibility, dreamy and washed out aesthetic."},
    "art_ink": {"label": "Ink", "category": "Art", "prompt": "Detailed ink illustration, cross-hatching, stippling dots, comic book inking, high contrast black and white, fine liner pens."},
    "art_origami": {"label": "Origami", "category": "Art", "prompt": "Paper craft style, folded paper textures, sharp geometric creases, soft paper shadows, layered composition, craft aesthetic."},

    # --- 3D & RENDER ---
    "render_clay": {"label": "Claymation", "category": "3D Render", "prompt": "Stop-motion claymation, plasticine texture, visible fingerprints, miniature set design, tilt-shift depth of field, Aardman animation style."},
    "render_voxel": {"label": "Voxel", "category": "3D Render", "prompt": "Voxel art style, made of tiny 3D cubes, Minecraft aesthetic, isometric view, colorful blocks, digital lego look."},
    "render_glass": {"label": "Glass", "category": "3D Render", "prompt": "Translucent glass material, refraction and caustics, glossy smooth surfaces, chromatic dispersion, ray-traced rendering, crystal clear."},
    "render_lowpoly": {"label": "Low Poly", "category": "3D Render", "prompt": "Low poly 3D game art, sharp geometric triangles, flat shading, retro PS1 aesthetic, vibrant solid colors, minimalist geometry."},

    # --- VINTAGE ---
    "vint_1920": {"label": "1920s", "category": "Vintage", "prompt": "1920s silent film era, sepia tone, heavy film scratches, dust particles, soft focus, vignetted edges, daguerreotype texture."},
    "vint_1950": {"label": "1950s", "category": "Vintage", "prompt": "1950s Technicolor advertisement, saturated pastel colors, mid-century modern aesthetic, american diner vibe, soft film grain, optimistic look."},
    "vint_1980": {"label": "Synthwave", "category": "Vintage", "prompt": "1980s synthwave, neon grids, chrome text styling, purple and teal gradient, VHS tracking lines, retro-futuristic sunset."},
    "vint_polaroid": {"label": "Polaroid", "category": "Vintage", "prompt": "Vintage Polaroid instant photo, faded colors, soft focus, flash photography, white border frame aesthetic, nostalgic memory."},
    "vint_victorian": {"label": "Victorian", "category": "Vintage", "prompt": "Victorian era portrait photography, stern expressions, antique clothing, lace and velvet textures, metal plate photography look."},

    # --- DARK & FANTASY ---
    "dark_gothic": {"label": "Gothic", "category": "Dark", "prompt": "Gothic horror aesthetic, deep shadows, candlelight, cathedral architecture, crimson and black palette, vampire atmosphere, mysterious."},
    "dark_lovecraft": {"label": "Lovecraft", "category": "Dark", "prompt": "Eldritch cosmic horror, impossible geometry, tentacled textures, fog and mist, dark green and grey tones, ominous atmosphere."},
    "dark_cyber": {"label": "Dystopia", "category": "Dark", "prompt": "Dystopian cyberpunk, rain-slicked streets, neon signs reflecting in puddles, high-tech low-life, gritty industrial textures, night time."},
    "dark_souls": {"label": "Dark Souls", "category": "Dark", "prompt": "Dark fantasy concept art, decaying ruins, fog walls, muted colors, intricate armor designs, souls-like atmosphere, masterpiece."},

    # --- AESTHETIC ---
    "aes_vapor": {"label": "Vaporwave", "category": "Aesthetic", "prompt": "Vaporwave aesthetic, greek statues, glitch art, windows 95 UI elements, pastel pink and blue, surreal digital dreamscape."},
    "aes_liminal": {"label": "Liminal", "category": "Aesthetic", "prompt": "Liminal space aesthetic, empty hallways, fluorescent buzzing lights, dreamcore, unsettlingly familiar, soft fuzzy low-quality camera."},
    "aes_cottage": {"label": "Cottagecore", "category": "Aesthetic", "prompt": "Cottagecore aesthetic, warm sunlight, blooming flowers, rustic wood textures, peaceful nature, fairy tale vibes, soft focus."},
    "aes_frutiger": {"label": "Frutiger Aero", "category": "Aesthetic", "prompt": "Frutiger Aero aesthetic, glossy water bubbles, lush green grass, bright blue sky, futuristic optimism, 2000s tech UI design."},

    # --- ABSTRACT ---
    "abs_fluid": {"label": "Fluid", "category": "Abstract", "prompt": "Fluid acrylic pour painting, marble texture, liquid oil mixing, vibrant psychedelic colors, macro details of paint cells."},
    "abs_geo": {"label": "Geometric", "category": "Abstract", "prompt": "Bauhaus geometric design, simple shapes (circles, triangles), primary colors (red, blue, yellow), clean lines, minimalist composition."},
    "abs_fractal": {"label": "Fractal", "category": "Abstract", "prompt": "Infinite fractal patterns, mandalas, mathematical geometry, trippy psychedelic colors, kaleidoscopic symmetry, detailed complexity."},
    "abs_smoke": {"label": "Smoke", "category": "Abstract", "prompt": "Colorful smoke photography, wispy flowing forms on black background, ethereal movement, silk-like texture, vibrant gradients."},
}


# -- Pydantic Schemas ---------------------------------

class GenerationRequest(BaseModel):
    """Schema for the /api/generate endpoint."""
    prompt: str = ""
    negative_prompt: str = ""
    model_id: str = CONFIG.get("default_t2i_model", "sdxl-turbo")
    strength: float = 0.65
    guidance_scale: float = 7.0
    num_inference_steps: int = 20
    seed: int = -1
    preset: Optional[str] = None


# -- Routes -------------------------------------------

@app.get("/")
async def serve_index():
    """Serve the main WebUI."""
    return FileResponse("static/index.html")


@app.get("/api/models")
async def get_models():
    """
    Return all available models grouped by type,
    with the config-default highlighted.
    """
    t2i_list = CONFIG.get("t2i_models", [])
    i2i_list = CONFIG.get("i2i_models", [])

    return {
        "default_t2i": CONFIG.get("default_t2i_model", "sdxl-turbo"),
        "default_i2i": CONFIG.get("default_i2i_model", "realvis-v4"),
        "t2i": [
            {
                "id": m["id"],
                "name": m["name"],
                "desc": m.get("desc", ""),
                "default_steps": m.get("default_steps", 20),
                "default_guidance": m.get("default_guidance", 7.0),
            }
            for m in t2i_list
        ],
        "i2i": [
            {
                "id": m["id"],
                "name": m["name"],
                "desc": m.get("desc", ""),
                "default_steps": m.get("default_steps", 30),
                "default_guidance": m.get("default_guidance", 7.0),
                "default_strength": m.get("default_strength", 0.65),
            }
            for m in i2i_list
        ],
    }


@app.get("/api/presets")
async def get_presets():
    """Return all style presets grouped by category."""
    grouped = {}
    for key, val in PRESETS.items():
        cat = val["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({
            "id": key,
            "label": val["label"],
        })

    return {
        "categories": grouped,
        "all": [
            {"id": k, "label": v["label"], "category": v["category"]}
            for k, v in PRESETS.items()
        ],
    }


@app.get("/api/status")
async def get_status():
    """Return current engine status and VRAM usage."""
    if engine is None:
        return {"status": "initializing", "model": None, "vram_mb": 0}

    return {
        "status": "ready",
        "model": engine.current_model_id,
        "vram_mb": round(engine.get_vram_usage(), 1),
        "device": engine.device,
        "config": {
            "default_t2i": CONFIG.get("default_t2i_model"),
            "default_i2i": CONFIG.get("default_i2i_model"),
            "force_offload": CONFIG.get("force_vram_offload"),
            "max_resolution": CONFIG.get("max_resolution"),
        },
    }


@app.post("/api/generate")
async def generate_image(
    prompt: str = Form(""),
    negative_prompt: str = Form(""),
    model_id: str = Form(CONFIG.get("default_t2i_model", "sdxl-turbo")),
    strength: float = Form(0.65),
    guidance_scale: float = Form(7.0),
    num_inference_steps: int = Form(20),
    seed: int = Form(-1),
    preset: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Universal generation endpoint.
    Accepts multipart form data: generation parameters + optional source image.
    """
    if engine is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Engine is still initializing. Please wait."},
        )

    # -- Handle file upload -----------------------
    image_path = None
    if file and file.filename:
        unique_id = str(uuid.uuid4())[:8]
        file_ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        image_path = f"uploads/{unique_id}.{file_ext}"
        try:
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"File upload failed: {e}"},
            )

    # -- Merge preset prompt if selected ----------
    final_prompt = prompt
    preset_key = preset
    if preset_key and preset_key in PRESETS:
        preset_prompt = PRESETS[preset_key]["prompt"]
        if final_prompt.strip():
            final_prompt = f"{final_prompt}, {preset_prompt}"
        else:
            final_prompt = preset_prompt

    # -- Call engine ------------------------------
    result = engine.generate(
        prompt=final_prompt,
        negative_prompt=negative_prompt,
        model_id=model_id,
        strength=strength,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
        seed=seed,
        image_path=image_path,
        preset=preset_key if (preset_key and image_path) else None,
    )

    # -- Handle errors ----------------------------
    if result.get("error"):
        return JSONResponse(
            status_code=500,
            content={"error": result["error"]},
        )

    # -- Save output image ------------------------
    output_image = result.get("image")
    if output_image is None:
        return JSONResponse(
            status_code=500,
            content={"error": "Generation produced no image."},
        )

    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"dream_{unique_id}.png"
    output_path = f"outputs/{output_filename}"
    output_image.save(output_path)

    return {
        "status": "success",
        "image_url": f"/outputs/{output_filename}",
        "seed": result.get("seed"),
        "model_id": result.get("model_id"),
        "time_seconds": result.get("time_seconds"),
        "title": result.get("title"),
        "story": result.get("story"),
    }


# -- Entry Point --------------------------------------

# Server reload triggered for theme changes
if __name__ == "__main__":
    # Run the server
    print("DreamU Server Starting at http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
# Server reload triggered for ai_engine.py changes