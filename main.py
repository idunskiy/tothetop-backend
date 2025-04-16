from fastapi import FastAPI
from routes import router 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Tothetop.ai SEO Crawler",
    description="A powerful SEO crawler that extracts structured data from websites",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://195.201.32.246", "https://tothetop.ai", "https://tothetop.cloud"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(router)  # Add this line to include your routes

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 