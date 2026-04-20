# DreamU: Universal Image Generation Engine

```text
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ██████╗ ██████╗ ███████╗ █████╗ ███╗   ███╗██╗   ██╗    ║
    ║   ██╔══██╗██╔══██╗██╔════╝██╔══██╗████╗ ████║██║   ██║    ║
    ║   ██║  ██║██████╔╝█████╗  ███████║██╔████╔██║██║   ██║    ║
    ║   ██║  ██║██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║██║   ██║    ║
    ║   ██████╔╝██║  ██║███████╗██║  ██║██║ ╚═╝ ██║╚██████╔╝    ║
    ║   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝     ║
    ║                                                           ║
    ║            T H E   F U T U R E   I S   O P E N            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
```

**DreamU** is a modular, high-performance, universal image generation API backend powered by FastAPI and PyTorch. It features a config-driven architecture that seamlessly loads multiple model pipelines while strictly adhering to hardware constraints like our **6GB VRAM target**.

---

## ⚡ Why DreamU?

### 🚀 Simplified Model Management
DreamU takes the complexity out of open-source AI. Instead of manually configuring weights, pipelines, and dependencies for every new model release, DreamU provides a unified orchestration layer. Whether you're interested in the detail of **FLUX.1**, the versatility of **OmniGen**, or the speed of **SDXL Lightning**, DreamU handles the heavy lifting—from automated weight fusion to hardware-specific quantization—with a single, streamlined workflow.

### 🍱 The Pre-Configured Pantry
Don't waste time hunting for the right prompt modifiers. DreamU comes packed with a comprehensive library of **Style Presets** (Cinema, Anime, Photography, 3D Render, etc.) that instantly tune your prompts for professional results. Every aesthetic is a one-click choice, allowing you to iterate faster and reach your vision without mastering complex prompt engineering.

### 💎 A Dashboard That Inspires
Say goodbye to cluttered, technical interfaces. DreamU features a stunning **Glassmorphic Dashboard** designed for modern creators.
- **Real-Time Evolution**: Watch your image emerge with live generation previews.
- **Reactive Environment**: A dynamic "Game of Life" background that lives and breathes around your dashboard.
- **Power User Tweaks**: Complex technical optimizations like VAE Tiling, Slicing, and CPU Offloading are presented as simple toggles, putting enterprise-grade control in the palm of your hand.

---

## 🛠️ Installation & Setup

1. **Clone & Explore:**
   ```powershell
   git clone https://github.com/himanshubit/dreamu
   cd dreamu
   ```

2. **The One-Click Dependency Sync:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **GPU Ignition:**
   ```powershell
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

4. **The Setup Wizard:**
   Run our intelligence-driven configuration script to map your system:
   ```powershell
   python setup.py
   ```

---

## 🚀 Igniting the Future

Launch the FastAPI server and step into your new creative hub:

```powershell
uvicorn main:app --reload
```
Visit: `http://127.0.0.1:8000`

---

## 🛑 Pro Tips for Creators

* **QuickEdit Mode**: If the terminal hangs, press `Enter`. QuickEdit can pause background downloads!
* **Optimized for 6GB**: Use the setup wizard to enable **Nuclear VRAM Unload**—specifically designed to keep 4050-class cards stable under heavy load.
* **Unified Flow**: Switch between Text-to-Image and Image-to-Image modes seamlessly within the same modern interface.

---
*Created by the future, for the creators.*
