import os
import sys
import json

if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

T2I_MODELS = [
    {
        "id": "sdxl-lightning",
        "name": "SDXL Lightning",
        "repo": "ByteDance/SDXL-Lightning",
        "desc": "Ultra-fast — 2-4 steps",
        "default_steps": 4,
        "default_guidance": 0.0,
        "quantization": None,
    },
    {
        "id": "flux-nf4",
        "name": "FLUX.1 [schnell] via NF4",
        "repo": "sayakpaul/flux.1-schnell-nf4",
        "desc": "Best Adherence, 4-bit compressed",
        "default_steps": 4,
        "default_guidance": 0.0,
        "quantization": "nf4",
    },
    {
        "id": "omnigen",
        "name": "OmniGen",
        "repo": "shitao/OmniGen-v1",
        "desc": "Unified VRAM Saver, 8-bit",
        "default_steps": 20,
        "default_guidance": 4.5,
        "quantization": "8bit",
    },
    {
        "id": "stable-cascade",
        "name": "Stable Cascade",
        "repo": "stabilityai/stable-cascade",
        "desc": "Highly compressed latent space",
        "default_steps": 20,
        "default_guidance": 4.0,
        "quantization": None,
    },
    {
        "id": "pixart-sigma",
        "name": "PixArt-Σ (Sigma)",
        "repo": "PixArt-alpha/PixArt-Sigma-XL-2-1024-MS",
        "desc": "Efficient Transformer",
        "default_steps": 20,
        "default_guidance": 4.5,
        "quantization": None,
    },
]

I2I_MODELS = [
    {
        "id": "realvis-v4",
        "name": "RealVisXL V4.0",
        "repo": "SG161222/RealVisXL_V4.0",
        "desc": "Photorealistic — Best quality img2img",
        "default_steps": 35,
        "default_guidance": 6.0,
        "default_strength": 0.65,
        "quantization": None,
    },
    {
        "id": "sdxl-base",
        "name": "SDXL Base 1.0",
        "repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "desc": "General Purpose — Baseline SDXL",
        "default_steps": 30,
        "default_guidance": 7.0,
        "default_strength": 0.60,
        "quantization": None,
    },
    {
        "id": "omnigen",
        "name": "OmniGen",
        "repo": "shitao/OmniGen-v1",
        "desc": "Unified VRAM Saver, 8-bit",
        "default_steps": 20,
        "default_guidance": 4.5,
        "quantization": "8bit",
    },
    {
        "id": "sdxl-lightning",
        "name": "SDXL Lightning",
        "repo": "ByteDance/SDXL-Lightning",
        "desc": "Ultra-fast — 2-4 steps",
        "default_steps": 4,
        "default_guidance": 0.0,
        "quantization": None,
    },
]

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

PURPLE = "\033[38;5;141m"
CYAN = "\033[38;5;87m"
DIM = "\033[2m"
BOLD = "\033[1m"
GREEN = "\033[38;5;114m"
YELLOW = "\033[38;5;221m"
RED = "\033[38;5;203m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"


def clear_screen():
    print(CLEAR, end="")


def print_header():
    header = f"""
{PURPLE}{BOLD}
    ╔══════════════════════════════════════════════════╗
    ║                                                  ║
    ║       ██████╗ ██████╗ ███████╗ █████╗ ███╗   ███╗║
    ║       ██╔══██╗██╔══██╗██╔════╝██╔══██╗████╗ ████║║
    ║       ██║  ██║██████╔╝█████╗  ███████║██╔████╔██║║
    ║       ██║  ██║██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║║
    ║       ██████╔╝██║  ██║███████╗██║  ██║██║ ╚═╝ ██║║
    ║       ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝║
    ║                                                  ║
    ║         {CYAN}I N I T I A L I Z A T I O N{PURPLE}              ║
    ║                                                  ║
    ╚══════════════════════════════════════════════════╝
{RESET}
    {DIM}Universal Image Generation Engine — Setup Wizard{RESET}
    {DIM}Target Hardware: NVIDIA RTX 4050 (6GB VRAM){RESET}
"""
    print(header)


def print_divider(label=""):
    if label:
        print(f"\n  {PURPLE}{'━' * 4} {BOLD}{label} {RESET}{PURPLE}{'━' * 40}{RESET}\n")
    else:
        print(f"  {DIM}{'─' * 50}{RESET}\n")


def prompt_choice(options, prompt_text):
    for i, opt in enumerate(options, 1):
        marker = f"{CYAN}[{i}]{RESET}"
        name = f"{BOLD}{opt['name']}{RESET}"
        desc = f"{DIM}{opt['desc']}{RESET}"
        print(f"    {marker}  {name}")
        print(f"         {desc}\n")

    while True:
        try:
            raw = input(f"  {YELLOW}▸ {prompt_text} [1-{len(options)}]: {RESET}").strip()
            choice = int(raw)
            if 1 <= choice <= len(options):
                selected = options[choice - 1]
                print(f"    {GREEN}✓ Selected: {selected['name']}{RESET}\n")
                return selected
            else:
                print(f"    {RED}✗ Please enter a number between 1 and {len(options)}.{RESET}")
        except ValueError:
            print(f"    {RED}✗ Invalid input. Enter a number.{RESET}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {RED}Setup cancelled.{RESET}\n")
            sys.exit(1)


def prompt_yesno(question, default=False):
    hint = "[y/N]" if not default else "[Y/n]"
    try:
        raw = input(f"  {YELLOW}▸ {question} {hint}: {RESET}").strip().lower()
        if raw == "":
            return default
        return raw in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {RED}Setup cancelled.{RESET}\n")
        sys.exit(1)


def run_setup():
    clear_screen()
    print_header()

    print_divider("STEP 1 — Default Text-to-Image Model")
    t2i = prompt_choice(T2I_MODELS, "Choose your default T2I model")

    print_divider("STEP 2 — Default Image-to-Image Model")
    i2i = prompt_choice(I2I_MODELS, "Choose your default I2I model")

    print_divider("STEP 3 — VRAM Configuration")
    force_offload = prompt_yesno(
        "Force Sequential CPU Offloading on startup? (Recommended for 6GB)", default=True
    )

    vae_slicing = prompt_yesno(
        "Enable VAE Slicing? (Reduces VRAM at slight speed cost)", default=True
    )

    vae_tiling = prompt_yesno(
        "Enable VAE Tiling? (Enables higher resolutions)", default=True
    )

    print_divider("STEP 4 — Model Cache")
    default_cache = os.environ.get("HF_HOME", "Y:/dreaemu_engine")
    print(f"    {DIM}Current HF cache directory: {default_cache}{RESET}")
    try:
        custom_cache = input(
            f"  {YELLOW}▸ Cache directory (Enter to keep \"{default_cache}\"): {RESET}"
        ).strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {RED}Setup cancelled.{RESET}\n")
        sys.exit(1)

    cache_dir = custom_cache if custom_cache else default_cache

    config = {
        "default_t2i_model": t2i["id"],
        "default_i2i_model": i2i["id"],
        "force_vram_offload": force_offload,
        "enable_vae_slicing": vae_slicing,
        "enable_vae_tiling": vae_tiling,
        "max_resolution": 768,
        "hf_cache_dir": cache_dir,
        "t2i_models": T2I_MODELS,
        "i2i_models": I2I_MODELS,
    }

    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"\n  {RED}✗ Failed to write config: {e}{RESET}\n")
        sys.exit(1)

    print_divider("CONFIGURATION SAVED")
    print(f"""
    {GREEN}{BOLD}✓ Config written to:{RESET} {DIM}{CONFIG_PATH}{RESET}

    {BOLD}Your Configuration:{RESET}
    ┌──────────────────────────────────────────┐
    │  Text-to-Image:   {CYAN}{t2i['name']:.<25}{RESET}│
    │  Image-to-Image:  {CYAN}{i2i['name']:.<25}{RESET}│
    │  CPU Offloading:  {GREEN if force_offload else RED}{'Enabled' if force_offload else 'Disabled':.<25}{RESET}│
    │  VAE Slicing:     {GREEN if vae_slicing else RED}{'Enabled' if vae_slicing else 'Disabled':.<25}{RESET}│
    │  VAE Tiling:      {GREEN if vae_tiling else RED}{'Enabled' if vae_tiling else 'Disabled':.<25}{RESET}│
    │  Max Resolution:  {'768px':.<25}│
    │  Cache Dir:       {DIM}{cache_dir[:25]:.<25}{RESET}│
    └──────────────────────────────────────────┘

    {PURPLE}▸ Start the server with:{RESET}  {BOLD}uvicorn main:app --reload{RESET}
    {PURPLE}▸ Reconfigure anytime:{RESET}    {BOLD}python setup.py{RESET}
""")


if __name__ == "__main__":
    run_setup()
