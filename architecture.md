# DreamU Architecture

DreamU is a modular, high-performance, universal image generation API backend. It acts as an orchestration layer for various open-source image generation models (Text-to-Image and Image-to-Image), optimized for consumer-grade hardware (specifically targeting 6GB VRAM GPUs).

## Core Technologies
- **Web Framework:** FastAPI with Uvicorn server.
- **AI/ML Engine:** PyTorch, Diffusers, Transformers.
- **Configuration:** JSON-based config-driven architecture.

## Project Structure

The project is structured around two main Python modules and a configuration file:

### 1. `main.py` (API Layer)
This file serves as the entry point and API gateway.
- Initializes the **FastAPI** application and mounts static assets/output directories.
- Manages the lifecycle of the `DreamuEngine` using an asynchronous context manager (`lifespan`).
- Exposes REST endpoints:
  - `GET /api/models`: Returns available T2I and I2I models based on the config.
  - `GET /api/presets`: Returns a categorized list of style presets.
  - `GET /api/status`: Returns current engine status, loaded model, and VRAM usage.
  - `POST /api/generate`: Accepts form data (prompt, negative_prompt, model_id, etc.) and optional image uploads, orchestrates the generation process via `DreamuEngine`, and saves the output.

### 2. `ai_engine.py` (Orchestration & Generation Layer)
This file contains the core AI logic, managing model loading, VRAM, and generation.
- **`DreamuEngine` Class:** The heart of the image generation pipeline.
  - **Model Registry:** Dynamically loads model configurations from `config.json`.
  - **Lazy Loading:** Models are loaded into memory only when requested.
  - **Memory Management:** Implements garbage collection (`gc.collect()`), CUDA cache clearing, and advanced offloading techniques (Sequential CPU Offload, VAE Slicing/Tiling).
  - **Pipeline Support:** Supports multiple specialized Diffusers pipelines (e.g., `AutoPipelineForText2Image`, `FluxPipeline`, `OmniGenPipeline`, `PixArtSigmaPipeline`).
  - **Quantization:** Supports loading models in 8-bit or NF4 (4-bit) for low VRAM usage.
  - **Generation Process:** Handles prompt construction, image resizing (for I2I), and invokes the underlying diffusers pipeline.

### 3. `config.json` (Configuration)
Defines the operational parameters and available models.
- Specifies default models, VRAM offload toggles, and max resolution.
- Lists `t2i_models` (Text-to-Image) and `i2i_models` (Image-to-Image) along with their Hugging Face repo IDs, default steps, guidance scales, and quantization requirements.

## Supported Models

The configuration defines a curated set of models tailored to run within the 6GB VRAM constraint using aggressive offloading and quantization.

### Text-to-Image (T2I)
- **Juggernaut XL Lightning** (`RunDiffusion/Juggernaut-XL-Lightning`): Top-tier general purpose and photorealism (4 steps).
- **DreamShaper XL Lightning** (`Lykon/dreamshaper-xl-lightning`): Best for art, anime, and illustration (4-8 steps).
- **SDXL Lightning** (`ByteDance/SDXL-Lightning`): Ultra-fast generic SDXL baseline (2-4 steps).
- **FLUX.1 [schnell] via NF4** (`sayakpaul/flux.1-schnell-nf4`): Exceptional prompt adherence, compressed to 4-bit.
- **OmniGen** (`shitao/OmniGen-v1`): Unified VRAM saver running in 8-bit.
- **Stable Cascade** (`stabilityai/stable-cascade`): Highly compressed latent space model.
- **PixArt-Σ (Sigma)** (`PixArt-alpha/PixArt-Sigma-XL-2-1024-MS`): Highly efficient Transformer-based model.

### Image-to-Image (I2I)
- **Juggernaut XL Lightning** (`RunDiffusion/Juggernaut-XL-Lightning`): High-quality transformations with lightning speeds.
- **DreamShaper XL Lightning** (`Lykon/dreamshaper-xl-lightning`): Artistic transformations.
- **RealVisXL V4.0** (`SG161222/RealVisXL_V4.0`): Photorealistic, best quality standard img2img.
- **SDXL Base 1.0** (`stabilityai/stable-diffusion-xl-base-1.0`): Baseline SDXL capability.
- **OmniGen** (`shitao/OmniGen-v1`): 8-bit unified generation.
- **SDXL Lightning** (`ByteDance/SDXL-Lightning`): Ultra-fast generic img2img.

## Data Flow (Generation Request)

1. **Client Request:** User sends a POST request to `/api/generate` with a prompt, optional image (for I2I), style preset, and model selection.
2. **API Layer (`main.py`):** 
   - Validates the request and saves any uploaded images to the `uploads/` directory.
   - Appends the selected preset's keywords to the prompt.
   - Calls `engine.generate()`.
3. **Engine Layer (`ai_engine.py`):**
   - **VRAM Prep:** Cleans up VRAM if another model was previously loaded.
   - **Model Loading:** Dynamically loads the requested model pipeline into memory (applying quantization and CPU offloading if configured).
   - **Inference:** Executes the diffusers pipeline to generate the image.
4. **Response:** 
   - Image is returned to `main.py`, saved to the `outputs/` directory.
   - Metadata (URL, seed, title, story) is returned to the client as JSON.

## Key Hardware Optimizations
- **Expandable Segments:** Uses `PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"` to optimize memory fragmentation.
- **Quantization:** Integration with `bitsandbytes` to load large models (like FLUX and OmniGen) in 4-bit (NF4) or 8-bit formats.
- **Diffusers Offloading:** Native integration of `enable_sequential_cpu_offload`, `enable_vae_slicing`, and `enable_vae_tiling` to fit generation into the 6GB VRAM target.
