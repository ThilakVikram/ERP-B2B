import os

from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("DB_URI")

# Auth / JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REMEMBER_ME_EXPIRE_MINUTES = int(os.getenv("REMEMBER_ME_EXPIRE_MINUTES", str(60 * 24 * 30)))

# Comma-separated list of allowed frontend origins
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

# Amazon Selling Partner API
# LWA app credentials, shared by all regions unless a region overrides them.
AMAZON_SP_API_CLIENT_ID = os.getenv("AMAZON_SP_API_CLIENT_ID")
AMAZON_SP_API_CLIENT_SECRET = os.getenv("AMAZON_SP_API_CLIENT_SECRET")
AMAZON_SP_API_SANDBOX = os.getenv("AMAZON_SP_API_SANDBOX", "false").lower() in ("1", "true", "yes")
# Region used when none is given: NA | EU | FE
AMAZON_SP_API_DEFAULT_REGION = os.getenv("AMAZON_SP_API_DEFAULT_REGION", "NA").upper()


def _csv_env(name: str) -> list[str]:
    return [v.strip() for v in os.getenv(name, "").split(",") if v.strip()]


# Per-region seller authorization, read from AMAZON_SP_API_<REGION>_<FIELD>, e.g.
#   AMAZON_SP_API_EU_REFRESH_TOKEN=Atzr|...
#   AMAZON_SP_API_EU_MARKETPLACE_IDS=A21TJRUUN4KGV,A1F83G8C2ARO7P
#   AMAZON_SP_API_EU_CLIENT_ID / AMAZON_SP_API_EU_CLIENT_SECRET  (optional overrides)
AMAZON_SP_API_REGIONS = {
    region: {
        "client_id": AMAZON_SP_API_CLIENT_ID,
        "client_secret": AMAZON_SP_API_CLIENT_SECRET,
        "refresh_token": os.getenv(f"AMAZON_SP_API_{region}_REFRESH_TOKEN"),
        "marketplace_ids": _csv_env(f"AMAZON_SP_API_{region}_MARKETPLACE_IDS"),
    }
    for region in ("NA", "EU", "FE")
}

# Reports API: max days one report request may span (also the largest schedule partition). Amazon allows up to 30.
REPORT_MAX_RANGE_DAYS = min(int(os.getenv("REPORT_MAX_RANGE_DAYS", "30")), 30)
