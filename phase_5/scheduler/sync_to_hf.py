import os
from huggingface_hub import HfApi
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_to_huggingface():
    """
    Syncs the local workspace to the Hugging Face Space using the HfApi.
    This method is more robust than Git for large files and CI environments.
    """
    api = HfApi()
    token = os.getenv("HF_TOKEN")
    repo_id = "Joeyrazor/indmoney-backend"
    
    if not token:
        logger.error("Error: HF_TOKEN environment variable not found.")
        return

    logger.info(f"Starting API-based sync to Hugging Face Space: {repo_id}")
    
    try:
        api.upload_folder(
            folder_path=".",
            repo_id=repo_id,
            repo_type="space",
            token=token,
            # Ignore patterns to avoid uploading unnecessary CI/Git files
            ignore_patterns=[
                ".git/*",
                ".github/*",
                "__pycache__/*",
                "*.pyc",
                ".venv/*",
                "venv/*",
                ".DS_Store"
            ],
            delete_patterns=None  # Set to ["*.json"] if you want to mirror exactly
        )
        logger.info("Successfully synced workspace to Hugging Face via API.")
    except Exception as e:
        logger.error(f"Failed to sync to Hugging Face: {str(e)}")
        raise e

if __name__ == "__main__":
    sync_to_huggingface()
