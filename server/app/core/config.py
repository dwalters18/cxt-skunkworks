"""Environment configuration shared by the API and all workers."""
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

POSTGRES_URL = os.getenv(
    "POSTGRES_URL", "postgresql://lip_user:lip_password@localhost:5432/lip_world"
)
TIMESCALE_URL = os.getenv(
    "TIMESCALE_URL",
    "postgresql://timescale_user:timescale_password@localhost:5433/lip_timeseries",
)
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "lip_graph_password")

# The demo world is single-tenant by design; every event carries this id.
TENANT_ID = os.getenv("LIP_TENANT_ID", "cxt-demo")

# API base URL as seen from inside the compose network (used by the simulator,
# which performs stop arrivals/completions through the action plane, not the DB).
API_BASE_URL = os.getenv("LIP_API_URL", "http://api:8000")

# Simulator tuning
SIM_TICK_SECONDS = float(os.getenv("SIM_TICK_SECONDS", "2.0"))
SIM_SPEED_MPH = float(os.getenv("SIM_SPEED_MPH", "35"))
SIM_SPEED_MULTIPLIER = float(os.getenv("SIM_SPEED_MULTIPLIER", "8"))
SIM_AUTO_START_ROUTES = os.getenv("SIM_AUTO_START_ROUTES", "true").lower() == "true"
SIM_DWELL_SECONDS = float(os.getenv("SIM_DWELL_SECONDS", "6"))
