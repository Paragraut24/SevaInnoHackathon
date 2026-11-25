"""Build-time model downloader for Render deployments (downloads HF Hub artifacts into backend/model/)."""
import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from huggingface_hub import hf_hub_download  # noqa: E402

from app.classifier import CONFIG_FILENAME, DEFAULT_MODEL_DIR, ONNX_FILENAME, TOKENIZER_FILENAME  # noqa: E402
from app.config import get_settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("sajag.download_model")

REQUIRED_FILES = (ONNX_FILENAME, TOKENIZER_FILENAME, CONFIG_FILENAME)


def download_model() -> None:
    """Download quantized ONNX model artifacts at build time if configured."""
    settings = get_settings()
    repo_id = settings.hf_model_repo.strip()
    if not settings.ml_enabled or not repo_id:
        logger.info("ml_download_skipped ml_enabled=%s repo_configured=%s", settings.ml_enabled, bool(repo_id))
        return

    target_dir = Path(settings.ml_model_dir) if settings.ml_model_dir else DEFAULT_MODEL_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    token = settings.hf_token.strip() or None

    for filename in REQUIRED_FILES:
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(target_dir),
            token=token,
        )
        logger.info("ml_artifact_downloaded file=%s", filename)


if __name__ == "__main__":
    download_model()
