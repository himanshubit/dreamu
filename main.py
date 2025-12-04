import shutil
import uuid
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from ai_engine import engine 

app = FastAPI(title="Dreamu API")

# Mount folders for frontend and file serving
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# ----------------------------------------------------------------------------------
# DREAMU PRESET DATABASE (2025 Edition)
# ----------------------------------------------------------------------------------
PRESETS = {
    # --- 🔥 TRENDING (Viral Styles) ---
    "trend_flux": "Amateur smartphone photo, authentic film grain, slight motion blur, harsh flash, candid moment, unedited, raw aesthetic, 4k, highly detailed skin texture.",
    "trend_lomo": "Lomography style, oversaturated colors, heavy vignette, high contrast, cross-processing effect, leaky light, nostalgic 2010s instagram aesthetic.",
    "trend_glitch": "Digital datamoshing, pixel sorting artifacts, CRT monitor scanlines, RGB split, cyberpunk error, distorted reality, glitchcore aesthetic.",
    "trend_holo": "Iridescent holographic texture, translucent foil material, chromatic aberration, futuristic fashion, glowing edge lighting, ethereal prism effects.",

    # --- ⛩️ ANIME & ANIMATION ---
    "anim_spider": "Into the Spider-Verse animation style, comic book halftone dots, chromatic aberration, vibrant neon colors, graffiti aesthetic, exaggerated perspective, Ben-Day dots, expressive ink lines, 3D-2D hybrid.",
    "anim_pixar": "Pixar animation style, cute proportions, subsurface scattering on skin, soft studio lighting, perfectly clean textures, 3D render, expressive eyes, Disney style, 4k.",
    "anim_disney": "Modern Disney animated movie style, 3D render, lush hair textures, expressive faces, magical lighting, Frozen or Moana aesthetic, highly detailed, cinematic composition.",
    "anim_japan": "High-quality modern Japanese anime key visual, Kyoto Animation style, sharp outlines, cel shading, vibrant colors, intricate eyes, cinematic lighting, high quality 2D animation.",

    # --- 📸 PHOTOGRAPHY (Camera Techniques) ---
    "photo_fisheye": "Ultra-wide fisheye lens distortion, 8mm skate video aesthetic, barrel distortion, close-up focus, dynamic perspective, vignette borders.",
    "photo_macro": "Extreme macro photography, microscopic details, water droplets, compound eyes, razor sharp focus, creamy bokeh background, scientific imaging.",
    "photo_drone": "High-altitude drone photography, top-down perspective, geometric landscapes, epic scale, golden hour lighting, wide dynamic range.",
    "photo_thermal": "Thermal imaging camera style, heat map color palette (blue to red/orange), glowing silhouettes, scientific visualization, night vision aesthetic.",
    "photo_double": "Double exposure photography, silhouette of main subject filled with nature landscapes, dreamy overlay, artistic blending, ethereal composition.",

    # --- 🎨 ART & ILLUSTRATION ---
    "art_oil": "Thick impasto oil painting, visible palette knife strokes, vibrant swirling colors, Van Gogh influence, textured canvas, expressive technique.",
    "art_sketch": "Rough charcoal and graphite sketch on textured paper, deep shadows, smudged shading, loose gestural lines, unfinished artistic look.",
    "art_watercolor": "Soft watercolor painting, wet-on-wet technique, pastel color bleeding, paper texture visibility, dreamy and washed out aesthetic.",
    "art_ink": "Detailed ink illustration, cross-hatching, stippling dots, comic book inking, high contrast black and white, fine liner pens.",
    "art_origami": "Paper craft style, folded paper textures, sharp geometric creases, soft paper shadows, layered composition, craft aesthetic.",

    # --- 🧸 3D & RENDER ---
    "render_clay": "Stop-motion claymation, plasticine texture, visible fingerprints, miniature set design, tilt-shift depth of field, Aardman animation style.",
    "render_voxel": "Voxel art style, made of tiny 3D cubes, Minecraft aesthetic, isometric view, colorful blocks, digital lego look.",
    "render_glass": "Translucent glass material, refraction and caustics, glossy smooth surfaces, chromatic dispersion, ray-traced rendering, crystal clear.",
    "render_lowpoly": "Low poly 3D game art, sharp geometric triangles, flat shading, retro PS1 aesthetic, vibrant solid colors, minimalist geometry.",

    # --- 📼 VINTAGE & RETRO ---
    "vint_1920": "1920s silent film era, sepia tone, heavy film scratches, dust particles, soft focus, vignetted edges, daguerreotype texture.",
    "vint_1950": "1950s Technicolor advertisement, saturated pastel colors, mid-century modern aesthetic, american diner vibe, soft film grain, optimistic look.",
    "vint_1980": "1980s synthwave, neon grids, chrome text styling, purple and teal gradient, VHS tracking lines, retro-futuristic sunset.",
    "vint_polaroid": "Vintage Polaroid instant photo, faded colors, soft focus, flash photography, white border frame aesthetic, nostalgic memory.",
    "vint_victorian": "Victorian era portrait photography, stern expressions, antique clothing, lace and velvet textures, metal plate photography look.",

    # --- 🌌 DARK & FANTASY ---
    "dark_gothic": "Gothic horror aesthetic, deep shadows, candlelight, cathedral architecture, crimson and black palette, vampire atmosphere, mysterious.",
    "dark_lovecraft": "Eldritch cosmic horror, impossible geometry, tentacled textures, fog and mist, dark green and grey tones, ominous atmosphere.",
    "dark_cyber": "Dystopian cyberpunk, rain-slicked streets, neon signs reflecting in puddles, high-tech low-life, gritty industrial textures, night time.",
    "dark_souls": "Dark fantasy concept art, decaying ruins, fog walls, muted colors, intricate armor designs, souls-like atmosphere, masterpiece.",

    # --- ✨ AESTHETIC ---
    "aes_vapor": "Vaporwave aesthetic, greek statues, glitch art, windows 95 UI elements, pastel pink and blue, surreal digital dreamscape.",
    "aes_liminal": "Liminal space aesthetic, empty hallways, fluorescent buzzing lights, dreamcore, unsettlingly familiar, soft fuzzy low-quality camera.",
    "aes_cottage": "Cottagecore aesthetic, warm sunlight, blooming flowers, rustic wood textures, peaceful nature, fairy tale vibes, soft focus.",
    "aes_frutiger": "Frutiger Aero aesthetic, glossy water bubbles, lush green grass, bright blue sky, futuristic optimism, 2000s tech UI design.",

    # --- 🌀 ABSTRACT ---
    "abs_fluid": "Fluid acrylic pour painting, marble texture, liquid oil mixing, vibrant psychedelic colors, macro details of paint cells.",
    "abs_geo": "Bauhaus geometric design, simple shapes (circles, triangles), primary colors (red, blue, yellow), clean lines, minimalist composition.",
    "abs_fractal": "Infinite fractal patterns, mandalas, mathematical geometry, trippy psychedelic colors, kaleidoscopic symmetry, detailed complexity.",
    "abs_smoke": "Colorful smoke photography, wispy flowing forms on black background, ethereal movement, silk-like texture, vibrant gradients."
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

    # Run AI
    result_image, title, story = engine.generate(input_path, base_prompt, style)

    if not result_image:
        return {"error": "Dream failed. Try a different image or restart."}

    output_filename = f"dream_{unique_id}.png"
    output_path = f"outputs/{output_filename}"
    result_image.save(output_path)

    return {
        "status": "success",
        "dream_url": f"/outputs/{output_filename}",
        "title": title.strip() if title else "Untitled",
        "story": story.strip() if story else "A generated reality."
    }

if __name__ == "__main__":
    print("🚀 Dreamu Server Starting at http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)