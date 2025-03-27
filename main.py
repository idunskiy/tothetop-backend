from fastapi import FastAPI
from routes import router 

app = FastAPI(
    title="Tothetop.ai SEO Crawler",
    description="A powerful SEO crawler that extracts structured data from websites",
    version="1.0.0"
)

app.include_router(router)  # Add this line to include your routes

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 