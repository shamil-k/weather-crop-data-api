from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.api import weather
from app.core.database import engine
from app.models import Base

# Create all tables in the database.
# This is a simple approach for this exercise. In a production environment,
# you would use a migration tool like Alembic.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Weather Data API",
    description="A REST API for weather and crop yield data.",
    version="1.0.0"
)

templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(weather.router, prefix="/api", tags=["Weather"])


@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
