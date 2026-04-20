import os
os.environ["HF_HOME"] = "Y:/dreaemu_engine"
from diffusers import PixArtSigmaPipeline
print("Loading...")
try:
    pipe = PixArtSigmaPipeline.from_pretrained(
        "PixArt-alpha/PixArt-Sigma-XL-2-1024-MS",
        use_safetensors=True,
        low_cpu_mem_usage=True,
        device_map="balanced",
    )
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
