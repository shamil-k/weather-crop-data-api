from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.api import weather
from app.core.database import engine
from app.models import Base

# This is the main entry point for the FastAPI application.
# It brings together the API router, database initialization, and the frontend dashboard.


# Database table initialization.
# `Base.metadata.create_all(bind=engine)` checks for the existence of tables
# before creating them, making it safe to run on every application startup.
# For production environments, a more robust migration tool like Alembic
# would be used to manage schema changes over time.
Base.metadata.create_all(bind=engine)


# Initialize the FastAPI app with metadata for the OpenAPI documentation.
app = FastAPI(
    title="Weather Data API",
    description="An API for accessing and analyzing weather data records.",
    version="1.0.0"
)

# Setup for the HTML template rendering for the root dashboard page.
templates = Jinja2Templates(directory="app/templates")


# The API router is included with a prefix, organizing all weather-related
# endpoints under `/api`. This is a good practice for versioning and clarity.
app.include_router(weather.router, prefix="/api", tags=["Weather"])


@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def read_root(request: Request):
    """
    Serves the main HTML page, which acts as a simple dashboard for
    visualizing the weather data.
    """
    return templates.TemplateResponse("index.html", {"request": request})
