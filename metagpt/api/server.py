from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from metagpt.api.routes import company, config, roles, files, stream, conversation, project, agents, bugs, versions, scrum, feedback

app = FastAPI(
    title="MetaGPT-Pro Enterprise API",
    description="Autonomous Software Development Virtual Company API with SCRUM Dashboard",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(company.router, prefix="/v1/company", tags=["Company"])
app.include_router(config.router, prefix="/v1/config", tags=["Configuration"])
app.include_router(roles.router, prefix="/v1/roles", tags=["Roles"])
app.include_router(files.router, prefix="/v1/files", tags=["Files"])
app.include_router(stream.router, prefix="/v1/stream", tags=["Streaming"])
app.include_router(conversation.router, prefix="/v1/conversation", tags=["Conversation"])
app.include_router(project.router, prefix="/v1/project", tags=["Project"])
app.include_router(agents.router, prefix="/v1/agents", tags=["Agent Collaboration"])
app.include_router(bugs.router, prefix="/v1/project", tags=["Bug Tracking"])
app.include_router(versions.router, prefix="/v1/project", tags=["Versioning"])
app.include_router(scrum.router, prefix="/v1/scrum", tags=["SCRUM Ceremonies"])
app.include_router(feedback.router, prefix="/v1/feedback", tags=["Feedback"])

# Static files for web app
WEBAPP_DIR = Path(__file__).parent.parent / "webapp"
if WEBAPP_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEBAPP_DIR)), name="static")

@app.get("/")
async def root():
    """Serve the SCRUM Dashboard web app"""
    index_file = WEBAPP_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Welcome to MetaGPT-Pro Enterprise API", "docs_url": "/docs"}

@app.get("/dashboard")
async def dashboard():
    """Redirect to main dashboard"""
    index_file = WEBAPP_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"error": "Dashboard not found", "docs_url": "/docs"}

@app.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon to prevent 404"""
    from fastapi.responses import Response
    # Return a minimal 1x1 transparent PNG favicon
    return Response(content=b'', media_type="image/x-icon")

def main():
    import uvicorn
    print("🚀 Starting MetaGPT-Pro SCRUM Server...")
    print("📊 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

