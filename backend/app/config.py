from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "SS_"}

    # CORS — which frontend origins can call this API
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Upload limits
    max_file_size_mb: int = 50

    # DSP parameters
    n_fft: int = 4096
    hop_length: int = 1024
    freq_threshold_hz: int = 10000
    sample_rate: int = 22050

    # Adversarial PGD parameters
    pgd_steps: int = 50
    pgd_epsilon: float = 0.01
    pgd_alpha: float = 0.001


settings = Settings()
