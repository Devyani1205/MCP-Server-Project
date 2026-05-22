from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth.routes import router as auth_router
from .query.routes import router as query_router
from .orders.routes import router as order_router
from .mcp.routes import router as mcp_router
from .database import init_db, User, DiagnosticTest, Order

app = FastAPI(title="Diagnostic MCP API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables
init_db()

# Include Routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(query_router, prefix="/query", tags=["Query Recommendation"])
app.include_router(order_router, prefix="/order", tags=["Order Placement"])
app.include_router(mcp_router, prefix="/mcp", tags=["MCP Server"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Diagnostic MCP API"}
