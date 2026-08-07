from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "SS_"}

    # CORS — which frontend origins can call this API
    # Accepts a comma-separated string, e.g. "https://example.com,http://localhost:3000"
    allowed_origins: str = "http://localhost:3000,https://signalshield.up.railway.app"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    # Upload limits
    max_file_size_mb: int = 50

    # DSP parameters
    n_fft: int = 4096
    hop_length: int = 1024
    freq_threshold_hz: int = 10000
    sample_rate: int = 22050

    # Adversarial PGD parameters
    pgd_steps: int = 50
    pgd_epsilon: float = 0.002
    pgd_alpha: float = 0.0004

    # Startup warmup — SS_WARMUP=true|false toggles loading models into RAM at boot.
    # SS_WARMUP_ENCODERS picks which models (comma-separated) when warmup is on.
    warmup: bool = True
    warmup_encoders: str = "resemblyzer"

    @property
    def warmup_encoders_list(self) -> list[str]:
        return [e.strip() for e in self.warmup_encoders.split(",") if e.strip()]
    # PyTorch thread count (0 = auto-detect via os.cpu_count())
    torch_threads: int = 0


settings = Settings()
