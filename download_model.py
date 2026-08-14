import os
from huggingface_hub import snapshot_download

MODEL_REPO_ID = "gaganmadan/IndicTrans2-preprint-ct2_int8"
LOCAL_DIR = "./indictrans2_ct2"

def download_model():
    print(f"Starting download of {MODEL_REPO_ID} to {LOCAL_DIR}...")
    snapshot_download(
        repo_id=MODEL_REPO_ID,
        local_dir=LOCAL_DIR,
        allow_patterns=["config.json", "model.bin", "vocab/*"]
    )
    print("Download successfully complete! The IndicTrans2 model is now configured.")

if __name__ == "__main__":
    download_model()
