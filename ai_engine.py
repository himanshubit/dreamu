import os
import gc
import random
import torch
from diffusers import StableDiffusionXLImg2ImgPipeline, DPMSolverMultistepScheduler
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
from io import BytesIO

# --- ⚠️ NUCLEAR FIX CONFIGURATION ⚠️ ---
# 1. CHANGED PATH: This forces a fresh download of the model (~6GB)
#    to ensure no corrupted files are causing the "same image" bug.
os.environ["HF_HOME"] = "Y:/dreaemu_engine"

# 2. MEMORY FIX: Essential for 6GB VRAM cards
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
load_dotenv()
# ----------------------------------------

class GeminiBrain:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                print("✨ Gemini Brain Connected!")
            except Exception as e:
                print(f"⚠️ Gemini Connection Failed: {e}")

    def enhance_prompt(self, pil_image, style_preset):
        if not self.client:
            return style_preset 

        try:
            # Convert image for Gemini Vision
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
            print(f"⚠️ Gemini Vision Error: {e}")
            return style_preset

    def interpret_dream(self, style_name):
        if not self.client:
            return "Untitled Dream", "A generated reality."
        try:
            prompt = f"Write a mysterious 3-word title and a 1-sentence story for a {style_name} artwork. Format: Title | Story"
            response = self.client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            text = response.text.strip()
            if "|" in text:
                return text.split("|", 1)
            return text, "A vision from the machine."
        except:
            return "Untitled", "Processing complete."

class DreamuEngine:
    def __init__(self):
        print(f"💻 Loading RealVisXL (FRESH DOWNLOAD) from: {os.environ.get('HF_HOME')}")
        print("⚠️ This will take time! Downloading 6GB fresh model...")
        
        self.gemini = GeminiBrain()
        model_id = "SG161222/RealVisXL_V4.0"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load SDXL Image-to-Image Pipeline
        self.pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16",
            add_watermarker=False,
            low_cpu_mem_usage=True 
        )

        # Best Scheduler for Detail
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config,
            use_karras_sigmas=True,
            algorithm_type="sde-dpmsolver++"
        )

        if self.device == "cuda":
            self.pipe.enable_sequential_cpu_offload()
            self.pipe.enable_vae_slicing()
            self.pipe.enable_vae_tiling()

        print("✨ Dreamu Engine Ready!")

    def generate(self, image_path, style_prompt, style_name="art"):
        try:
            # Aggressive Memory Cleanup
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()

            init_image = Image.open(image_path).convert("RGB")
            
            # Smart Resize (Max 1024 to avoid OOM)
            width, height = init_image.size
            if width > height:
                new_width = 1024
                new_height = int(1024 * (height / width))
            else:
                new_height = 1024
                new_width = int(new_height * (width / height))
            
            # Ensure multiples of 8
            new_width = new_width - (new_width % 8)
            new_height = new_height - (new_height % 8)
            init_image = init_image.resize((new_width, new_height), Image.LANCZOS)

            # 1. Get Enhanced Prompt
            print("🤖 Consulting Gemini Vision...", flush=True)
            magic_prompt = self.gemini.enhance_prompt(init_image, style_prompt)
            
            final_prompt = f"{magic_prompt}, masterpiece, best quality, 8k uhd, high fidelity, (vivid colors:1.2)"
            negative_prompt = "worst quality, low quality, jpeg artifacts, blurry, bad hands, watermark, text, signature, deformed, mutation, ugly"

            # Generate a Random Seed
            seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device="cpu").manual_seed(seed)

            print(f"\n🎨 Generating '{style_name}'", flush=True)
            print(f"📝 Prompt: {final_prompt}", flush=True) 
            print(f"🎲 Seed: {seed}", flush=True)

            # 2. Generate Image
            image = self.pipe(
                prompt=final_prompt,
                negative_prompt=negative_prompt,
                image=init_image,
                # STRENGTH BOOST: 0.65
                # This ensures the AI makes VISIBLE changes to the style
                # while the Gemini prompt keeps the subject correct.
                strength=0.65, 
                guidance_scale=6.0,
                num_inference_steps=35,
                generator=generator
            ).images[0]

            # 3. Get Story
            title, story = self.gemini.interpret_dream(style_name)

            return image, title, story

        except Exception as e:
            print(f"❌ Generation Error: {e}")
            return None, None, None

engine = DreamuEngine()