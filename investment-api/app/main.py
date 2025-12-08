from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import costs, portfolio, simulation

app = FastAPI(
    title="Investment Portfolio API",
    description="Professional-grade life plan and investment strategy API",
    version="1.0.0",
)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(costs.router)
app.include_router(portfolio.router)
app.include_router(simulation.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {
        "message": "Investment Portfolio API",
        "version": "1.0.0",
        "docs": "/docs",
    }
