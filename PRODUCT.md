# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Local AI enthusiasts, creators, and developers running consumer-grade hardware (specifically targeting 6GB VRAM GPUs) who want to generate high-quality images without relying on cloud services.

## Product Purpose

DreamU is a modular, high-performance, universal image generation API backend and interface. It exists to democratize access to advanced open-source AI image generation models by orchestrating their execution within strict hardware constraints.

## Positioning

An AI image generation engine specifically optimized to run top-tier models (like FLUX, SDXL Lightning, and OmniGen) entirely within a 6GB VRAM envelope through aggressive CPU offloading, memory fragmentation optimization, and quantization.

## Operating Context

Users run the application locally on personal computers with limited GPU resources. They interact via a web browser (HTML/JS/CSS frontend) connecting to a local FastAPI server, selecting models, presets, and generating images interactively.

## Capabilities and Constraints

**Capabilities:**
- Text-to-Image (T2I) and Image-to-Image (I2I) generation.
- Dynamic lazy loading of models.
- Support for 8-bit and 4-bit (NF4) quantization.
- Broad model support (Juggernaut XL, DreamShaper XL, SDXL Lightning, FLUX.1 [schnell], OmniGen, Stable Cascade, PixArt-Σ).

**Constraints:**
- Must operate within a 6GB VRAM limit.
- Heavy reliance on CPU offloading and VAE slicing/tiling which impacts speed compared to unconstrained environments.

## Brand Commitments

- **Name:** Dreamu / DreamU

## Evidence on Hand

- Fully functional FastAPI backend (`main.py`) and orchestration engine (`ai_engine.py`).
- Pre-configured `config.json` defining supported models and memory management settings.
- Existing vanilla web frontend (`static/index.html`).

## Product Principles

1. **Hardware Inclusivity:** Advanced AI should be accessible on consumer-grade (6GB VRAM) hardware.
2. **Modular Architecture:** Models and pipelines must be easily configurable and interchangeable via configuration.
3. **Graceful Resource Management:** System stability and memory safety (preventing OOM errors) take precedence over raw speed.
