import os
import gc
import torch
from diffusers import StableDiffusionXLImg2ImgPipeline, DPMSolverMultistepScheduler
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
from io import BytesIO

# --- CONFIGURATION ---
os.environ["HF_HOME"] = "Y:/dreamu_model"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
load_dotenv()
# ---------------------

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
        """
        Uses Gemini Vision to look at the user's image and merge it with the style.
        """
        if not self.client:
            return style_preset # Fallback if no API key

        try:
            # We convert the PIL image to bytes for Gemini
            img_byte_arr = BytesIO()
            pil_image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

            prompt = (
                f"Look at this image. Identify the main subject and composition briefly. "
                f"Then, rewrite this style description to apply specifically to that subject: '{style_preset}'. "
                f"Keep it under 40 words. Focus on visual description."
            )

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    prompt
                ]
            )
            
            enhanced_prompt = response.text
            print(f"🤖 Gemini Enhanced Prompt: {enhanced_prompt}")
            return enhanced_prompt
        except Exception as e:
            print(f"⚠️ Gemini Vision Error: {e}")
            return style_preset

    def interpret_dream(self, style_name):
        """
        Generates a creative title and story.
        """
        if not self.client:
            return "Untitled Dream", "A generated reality."

        try:
            prompt = (
                f"Generate a short, mysterious, 5-word title and a one-sentence cryptic 'dream interpretation' "
                f"for an artwork created in the style of {style_name}. "
                "Format: Title | Story"
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            text = response.text.strip()
            if "|" in text:
                return text.split("|", 1)
            return text, "A vision from the machine."
        except:
            return "Untitled", "Processing complete."

class DreamuEngine:
    def __init__(self):
        print(f"💻 Loading RealVisXL (SDXL) from: {os.environ.get('HF_HOME')}")
        
        # Initialize Gemini
        self.gemini = GeminiBrain()
        
        model_id = "SG161222/RealVisXL_V4.0"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load SDXL
        self.pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16",
            add_watermarker=False,
            low_cpu_mem_usage=True 
        )

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
            # Memory Cleanup
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()

            init_image = Image.open(image_path).convert("RGB")
            
            # Smart Resize
            width, height = init_image.size
            aspect_ratio = width / height
            if width > height:
                new_width = 1024
                new_height = int(1024 / aspect_ratio)
            else:
                new_height = 1024
                new_width = int(new_height * aspect_ratio)
            new_width = new_width - (new_width % 8)
            new_height = new_height - (new_height % 8)
            init_image = init_image.resize((new_width, new_height), Image.LANCZOS)

            # 1. Ask Gemini to write the perfect prompt based on the image
            magic_prompt = self.gemini.enhance_prompt(init_image, style_prompt)
            
            # Add technical quality boosters
            final_prompt = f"{magic_prompt}, masterpiece, best quality, 8k uhd, high fidelity"
            negative_prompt = "(octane render, render, drawing, anime, bad photo, bad photography:1.3), (worst quality, low quality, blurry:1.2), (bad hands, missing fingers, missing limbs:1.1), text, watermark"

            print(f"🎨 Generating...")

            # 2. Generate Image
            image = self.pipe(
                prompt=final_prompt,
                negative_prompt=negative_prompt,
                image=init_image,
                strength=0.55, # 0.55 allows style change while keeping subject
                guidance_scale=5.0,
                num_inference_steps=40
            ).images[0]

            # 3. Get Creative Title from Gemini
            title, story = self.gemini.interpret_dream(style_name)

            return image, title, story

        except Exception as e:
            print(f"❌ Generation Error: {e}")
            return None, None, None

engine = DreamuEngine()