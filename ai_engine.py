"""
DreamU AI Engine — Universal Model Loader & Generator
══════════════════════════════════════════════════════
Supports dynamic model switching with strict 6GB VRAM management.
Reads configuration from config.json written by setup.py.
"""

import os
import gc
import json
import random
import time
import inspect
from io import BytesIO

try:
    import torch
    HAS_TORCH = True
except ImportError:
    torch = None
    HAS_TORCH = False
    print("WARNING: PyTorch not installed. Generation will be unavailable.")
    print("   Install with: pip install torch --index-url https://download.pytorch.org/whl/cu121")

try:
    from PIL import Image
except ImportError:
    Image = None
    print("WARNING: Pillow not installed. Install with: pip install pillow")

from dotenv import load_dotenv

# ── Environment ──────────────────────────────────────
load_dotenv()

# ── Config Loading ───────────────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    """Load config.json, returning defaults if not found."""
    defaults = {
        "default_t2i_model": "sdxl-turbo",
        "default_i2i_model": "realvis-v4",
        "force_vram_offload": True,
        "enable_vae_slicing": True,
        "enable_vae_tiling": True,
        "max_resolution": 768,
        "hf_cache_dir": "Y:/dreaemu_engine",
        "t2i_models": [],
        "i2i_models": [],
    }
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            defaults.update(data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"WARNING: Config not found or invalid ({e}). Using defaults.")
        print("   Run 'python setup.py' to configure DreamU.")
    return defaults


CONFIG = load_config()

# Apply environment vars from config
os.environ["HF_HOME"] = CONFIG["hf_cache_dir"]
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"


# ── Model Registry ───────────────────────────────────
# Combines t2i and i2i models from config into a flat lookup dict

# Initialize registry with empty lists for each ID to handle shared IDs
MODEL_REGISTRY = {}

def register_models(models, mtype):
    for m in models:
        mid = m["id"]
        if mid not in MODEL_REGISTRY:
            MODEL_REGISTRY[mid] = {**m, "types": [mtype]}
        else:
            if mtype not in MODEL_REGISTRY[mid]["types"]:
                MODEL_REGISTRY[mid]["types"].append(mtype)
        # Store for backward compatibility and metadata
        MODEL_REGISTRY[mid].update(m)

register_models(CONFIG.get("t2i_models", []), "t2i")
register_models(CONFIG.get("i2i_models", []), "i2i")

# Hardcoded fallbacks in case config has no model lists
if not MODEL_REGISTRY:
    MODEL_REGISTRY = {
        "sdxl-lightning": {
            "id": "sdxl-lightning",
            "name": "SDXL Lightning",
            "repo": "ByteDance/SDXL-Lightning",
            "types": ["t2i", "i2i"],
            "default_steps": 4,
            "default_guidance": 0.0,
            "quantization": None,
        },
        "omnigen": {
            "id": "omnigen",
            "name": "OmniGen",
            "repo": "shitao/OmniGen-v1",
            "type": "t2i",
            "default_steps": 20,
            "default_guidance": 4.5,
            "quantization": "8bit",
        },
    }


# ── Gemini Brain (Preserved) ────────────────────────

class GeminiBrain:
    """Optional Gemini Vision integration for prompt enhancement."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print("Gemini Brain Connected!")
            except Exception as e:
                print(f"Gemini Connection Failed: {e}")

    def enhance_prompt(self, pil_image, style_preset):
        """Use Gemini Vision to analyze an image and create a detailed prompt."""
        if not self.client:
            return style_preset

        try:
            from google.genai import types

            img_byte_arr = BytesIO()
            pil_image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

            prompt = (
                f"Analyze the main subject, pose, and composition of this image in detail. "
                f"Then write a Stable Diffusion prompt to recreate this exact subject in the style of: '{style_preset}'. "
                f"Include keywords for lighting, texture, and atmosphere. Keep it under 50 words."
            )

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    prompt
                ]
            )
            return response.text.strip()
        except Exception as e:
            print(f"Gemini Vision Error: {e}")
            return style_preset

    def interpret_dream(self, style_name):
        """Generate a creative title and story for the generated image."""
        if not self.client:
            return "Untitled Dream", "A generated reality."
        try:
            prompt = f"Write a mysterious 3-word title and a 1-sentence story for a {style_name} artwork. Format: Title | Story"
            response = self.client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            text = response.text.strip()
            if "|" in text:
                return text.split("|", 1)
            return text, "A vision from the machine."
        except Exception:
            return "Untitled", "Processing complete."


# ── DreamU Engine ────────────────────────────────────

class DreamuEngine:
    """
    Universal image generation engine with dynamic model switching
    and strict VRAM management for 6GB GPUs.
    """

    def __init__(self):
        print("=" * 55)
        print("  DreamU Engine -- Initializing")
        print(f"  Cache: {CONFIG['hf_cache_dir']}")
        print(f"  VRAM Offload: {'Enabled' if CONFIG['force_vram_offload'] else 'Disabled'}")
        print("=" * 55)

        self.pipe = None
        self.current_model_id = None
        self.gemini = GeminiBrain()
        self.max_resolution = CONFIG.get("max_resolution", 768)
        self.generation_available = HAS_TORCH

        if HAS_TORCH:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"  Device: {self.device}")
            if self.device == "cuda":
                gpu_name = torch.cuda.get_device_name(0)
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                print(f"  GPU: {gpu_name} ({gpu_mem:.1f} GB)")
        else:
            self.device = "cpu"
            print("  Device: CPU (torch not installed, generation unavailable)")

        print("  Engine Ready -- No model loaded yet (lazy loading).\n")

    # ── VRAM Management ──────────────────────────────

    def unload_model(self):
        """Nuclear VRAM cleanup: delete pipeline and flush all caches."""
        if self.pipe is not None:
            print(f"Unloading model: {self.current_model_id}...")
            del self.pipe
            self.pipe = None

        self.current_model_id = None
        gc.collect()

        if HAS_TORCH and self.device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            allocated = torch.cuda.memory_allocated() / (1024 ** 2)
            print(f"VRAM after cleanup: {allocated:.0f} MB")

    def get_vram_usage(self):
        """Return current VRAM usage in MB, or 0 if CPU."""
        if HAS_TORCH and self.device == "cuda":
            return torch.cuda.memory_allocated() / (1024 ** 2)
        return 0.0

    # ── Model Loading ────────────────────────────────

    def load_model(self, model_id, mode="t2i"):
        """
        Dynamically load a model by its registry ID and mode.
        Unloads the previous model first to free VRAM.
        """
        # Distinguish between text/img variants of the same model ID
        full_session_id = f"{model_id}_{mode}"
        if self.current_model_id == full_session_id and self.pipe is not None:
            return True

        # Look up model in registry
        model_info = MODEL_REGISTRY.get(model_id)
        if not model_info:
            print(f"Error: Unknown model ID: '{model_id}'")
            return False

        # Unload any current model first
        self.unload_model()

        repo = model_info["repo"]
        # Use requested mode if supported, otherwise fallback to first available
        actual_type = mode if mode in model_info.get("types", []) else model_info["types"][0]
        
        print(f"Loading: {model_info['name']} ({repo})")
        print(f"   Mode: {'Text-to-Image' if actual_type == 't2i' else 'Image-to-Image'}")

        try:
            quantization = model_info.get("quantization")
            quant_kwargs = {}
            # ... quantization logic ...
            if quantization == "8bit":
                quant_kwargs["load_in_8bit"] = True
            elif quantization == "nf4":
                from transformers import BitsAndBytesConfig
                quant_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16
                )

            # ── Select the correct pipeline class ────
            if model_id == "flux-nf4":
                pipe = self._load_flux(repo, **quant_kwargs)
            elif model_id == "omnigen":
                pipe = self._load_omnigen(repo, **quant_kwargs)
            elif model_id == "stable-cascade":
                pipe = self._load_stable_cascade(repo, **quant_kwargs)
            elif model_id == "pixart-sigma":
                pipe = self._load_pixart(repo, **quant_kwargs)
            elif actual_type == "i2i":
                pipe = self._load_sdxl_img2img(repo, **quant_kwargs)
            else:
                pipe = self._load_sdxl_text2img(repo, **quant_kwargs)

            if pipe is None:
                return False
            
            # ... (VRAM optimizations) ...
            if self.device == "cuda":
                if CONFIG.get("force_vram_offload", True):
                    pipe.enable_sequential_cpu_offload()
                    print("   [SAFE] Sequential CPU Offload enabled")

                if CONFIG.get("enable_vae_slicing", True):
                    try:
                        pipe.enable_vae_slicing()
                        print("   [SAFE] VAE Slicing enabled")
                    except Exception:
                        pass

                if CONFIG.get("enable_vae_tiling", True):
                    try:
                        pipe.enable_vae_tiling()
                        print("   [SAFE] VAE Tiling enabled")
                    except Exception:
                        pass

            self.pipe = pipe
            self.current_model_id = full_session_id
            
            vram = self.get_vram_usage()
            print(f"Model loaded! Mode: {actual_type} | VRAM: {vram:.0f} MB\n")
            return True

        except Exception as e:
            print(f"Error: Failed to load model '{model_id}': {e}")
            self.unload_model()
            return False

    def _load_sdxl_text2img(self, repo, **kwargs):
        """Load a standard SDXL/Lightning text-to-image pipeline."""
        from diffusers import AutoPipelineForText2Image, DPMSolverMultistepScheduler

        is_lightning_repo = (repo == "ByteDance/SDXL-Lightning")
        actual_repo = "stabilityai/stable-diffusion-xl-base-1.0" if is_lightning_repo else repo

        if is_lightning_repo:
            from diffusers import EulerDiscreteScheduler
            print("   Loading Base SDXL Pipeline (cached)...")
            pipe = AutoPipelineForText2Image.from_pretrained(
                actual_repo,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16",
                add_watermarker=False,
                low_cpu_mem_usage=True,
                **kwargs
            )
            
            print("   Applying Ultra-Fast Lightning LoRA (160MB)...")
            pipe.load_lora_weights(repo, weight_name="sdxl_lightning_4step_lora.safetensors")
            pipe.fuse_lora()
            pipe.unload_lora_weights() # Cleanup RAM
            
            pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
        else:
            pipe = AutoPipelineForText2Image.from_pretrained(
                actual_repo,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16",
                add_watermarker=False,
                low_cpu_mem_usage=True,
                **kwargs
            )
            # Better scheduler for detail
            try:
                pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                    pipe.scheduler.config,
                    use_karras_sigmas=True,
                    algorithm_type="sde-dpmsolver++",
                )
            except Exception:
                pass

        return pipe

    def _load_sdxl_img2img(self, repo, **kwargs):
        """Load a standard SDXL image-to-image pipeline."""
        from diffusers import AutoPipelineForImage2Image, DPMSolverMultistepScheduler

        is_lightning_repo = (repo == "ByteDance/SDXL-Lightning")
        actual_repo = "stabilityai/stable-diffusion-xl-base-1.0" if is_lightning_repo else repo

        if is_lightning_repo:
            from diffusers import EulerDiscreteScheduler
            print("   Loading Base SDXL Pipeline (cached)...")
            pipe = AutoPipelineForImage2Image.from_pretrained(
                actual_repo,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16",
                add_watermarker=False,
                low_cpu_mem_usage=True,
                **kwargs
            )
            
            print("   Applying Ultra-Fast Lightning LoRA (160MB)...")
            pipe.load_lora_weights(repo, weight_name="sdxl_lightning_4step_lora.safetensors")
            pipe.fuse_lora()
            pipe.unload_lora_weights() # Cleanup RAM
            
            pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
        else:
            pipe = AutoPipelineForImage2Image.from_pretrained(
                actual_repo,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16",
                add_watermarker=False,
                low_cpu_mem_usage=True,
                **kwargs
            )
            try:
                pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                    pipe.scheduler.config,
                    use_karras_sigmas=True,
                    algorithm_type="sde-dpmsolver++",
                )
            except Exception:
                pass

        return pipe

    def _load_pixart(self, repo, **kwargs):
        """Load PixArt-Sigma pipeline."""
        try:
            from diffusers import PixArtSigmaPipeline

            pipe = PixArtSigmaPipeline.from_pretrained(
                repo,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                low_cpu_mem_usage=True,
                **kwargs
            )
            return pipe
        except ImportError:
            print("   WARNING: PixArt pipeline not available in this diffusers version.")
            print("   Falling back to AutoPipeline...")
            return self._load_sdxl_text2img(repo, **kwargs)

    def _load_flux(self, repo, **kwargs):
        """Load FLUX.1 NF4 quantized model."""
        try:
            from diffusers import FluxPipeline

            pipe = FluxPipeline.from_pretrained(
                repo,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                low_cpu_mem_usage=True,
                **kwargs
            )
            return pipe
        except Exception as e:
            print(f"   WARNING: FLUX loading failed: {e}")
            return None

    def _load_omnigen(self, repo, **kwargs):
        """Load OmniGen Pipeline."""
        try:
            from diffusers import OmniGenPipeline
            pipe = OmniGenPipeline.from_pretrained(
                repo,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                low_cpu_mem_usage=True,
                **kwargs
            )
            return pipe
        except Exception as e:
            print(f"   WARNING: OmniGen loading failed: {e}")
            return None

    def _load_stable_cascade(self, repo, **kwargs):
        """Load Stable Cascade Pipeline."""
        try:
            from diffusers import AutoPipelineForText2Image
            pipe = AutoPipelineForText2Image.from_pretrained(
                repo,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                low_cpu_mem_usage=True,
                **kwargs
            )
            return pipe
        except Exception as e:
            print(f"   WARNING: Stable Cascade loading failed: {e}")
            return None

    def _get_pipe_params(self, params):
        """Filter params to only include those supported by the current self.pipe."""
        if not self.pipe:
            return params
        
        sig = inspect.signature(self.pipe.__call__)
        supported = sig.parameters.keys()
        
        filtered = {k: v for k, v in params.items() if k in supported}
        
        dropped = set(params.keys()) - set(filtered.keys())
        if dropped:
            print(f"   [ROUTER] Note: Pipeline {type(self.pipe).__name__} does not support: {dropped}")
            
        return filtered

    # ── Image Utilities ──────────────────────────────

    def _resize_image(self, image):
        """
        Resize image to fit within max_resolution while maintaining
        aspect ratio. Ensures dimensions are multiples of 8.
        """
        max_dim = self.max_resolution
        width, height = image.size

        if width > height:
            new_width = min(width, max_dim)
            new_height = int(new_width * (height / width))
        else:
            new_height = min(height, max_dim)
            new_width = int(new_height * (width / height))

        # Force multiples of 8 (required by SD)
        new_width = new_width - (new_width % 8)
        new_height = new_height - (new_height % 8)

        # Minimum size guard
        new_width = max(new_width, 64)
        new_height = max(new_height, 64)

        return image.resize((new_width, new_height), Image.LANCZOS)

    # ── Generation ───────────────────────────────────

    def generate(self, **kwargs):
        """
        Universal generation function.

        Kwargs:
            prompt (str):               The text prompt
            negative_prompt (str):      Negative prompt
            model_id (str):             Model registry ID
            strength (float):           Img2img strength (0.1-1.0)
            guidance_scale (float):     CFG scale
            num_inference_steps (int):  Number of denoising steps
            seed (int):                 RNG seed (-1 = random)
            image_path (str|None):      Path to source image for img2img
            preset (str|None):          Preset key for Gemini enhancement
        Returns:
            dict: {image, seed, model_id, time_seconds, title, story, error}
        """
        start_time = time.time()

        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt",
            "worst quality, low quality, jpeg artifacts, blurry, bad hands, "
            "watermark, text, signature, deformed, mutation, ugly"
        )
        model_id = kwargs.get("model_id", CONFIG["default_t2i_model"])
        strength = kwargs.get("strength", 0.65)
        guidance_scale = kwargs.get("guidance_scale", 7.0)
        num_inference_steps = kwargs.get("num_inference_steps", 20)
        seed = kwargs.get("seed", -1)
        image_path = kwargs.get("image_path", None)
        preset = kwargs.get("preset", None)

        try:
            # ── Pre-generation VRAM cleanup ──────────
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()

            # ── Load model if needed ─────────────────
            # Dynamically determine the mode based on presence of init_image
            target_mode = "i2i" if image_path else "t2i"
            if not self.load_model(model_id, mode=target_mode):
                return {"error": f"Failed to load model '{model_id}' in {target_mode} mode."}

            model_info = MODEL_REGISTRY.get(model_id, {})

            model_type = target_mode

            # ── Prepare seed ─────────────────────────
            if seed < 0:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device="cpu").manual_seed(seed)

            # ── Handle source image for img2img ──────
            init_image = None
            if image_path and target_mode == "i2i":
                init_image = Image.open(image_path).convert("RGB")
                init_image = self._resize_image(init_image)

            # ── Gemini prompt enhancement ────────────
            title, story = None, None
            if preset and init_image:
                print("Consulting Gemini Vision...", flush=True)
                enhanced = self.gemini.enhance_prompt(init_image, preset)
                prompt = f"{enhanced}, masterpiece, best quality, 8k uhd, high fidelity, (vivid colors:1.2)"
                title, story = self.gemini.interpret_dream(preset)

            # -- Ensure prompt is not empty -----------
            if not prompt.strip():
                prompt = "masterpiece, best quality, highly detailed"

            print(f"Generating with '{model_id}'", flush=True)
            print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}", flush=True)
            print(f"Seed: {seed}", flush=True)

            # -- Execute pipeline ---------------------
            pipe_kwargs = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_inference_steps,
                "generator": generator,
            }

            # ── Special Model Routing ───────────────
            is_omnigen = "OmniGen" in type(self.pipe).__name__

            if init_image is not None:
                if is_omnigen:
                    pipe_kwargs["input_images"] = [init_image]
                    # Auto-inject image tags if missing
                    if "<img>" not in prompt:
                        pipe_kwargs["prompt"] = f"<img><|image_1|></img> {prompt}"
                    pipe_kwargs["use_input_image_size_as_output"] = True
                else:
                    pipe_kwargs["image"] = init_image
                    pipe_kwargs["strength"] = strength
            else:
                # Text-to-Image dimensions
                if not is_omnigen: # OmniGen often infers size or uses defaults
                    pipe_kwargs["width"] = self.max_resolution
                    pipe_kwargs["height"] = self.max_resolution

            # Final safety: strip anything the model doesn't understand
            pipe_kwargs = self._get_pipe_params(pipe_kwargs)

            result = self.pipe(**pipe_kwargs)
            image = result.images[0]

            elapsed = time.time() - start_time
            vram = self.get_vram_usage()
            print(f"DONE in {elapsed:.1f}s | VRAM: {vram:.0f} MB\n", flush=True)

            return {
                "image": image,
                "seed": seed,
                "model_id": model_id,
                "time_seconds": round(elapsed, 2),
                "title": title.strip() if title else None,
                "story": story.strip() if story else None,
                "error": None,
            }

        except torch.cuda.OutOfMemoryError:
            print("OOM Error! Unloading model and flushing VRAM...", flush=True)
            self.unload_model()
            return {"error": "Out of VRAM. Model unloaded. Try fewer steps or a smaller model."}

        except Exception as e:
            print(f"Error: Generation Error: {e}", flush=True)
            return {"error": str(e)}