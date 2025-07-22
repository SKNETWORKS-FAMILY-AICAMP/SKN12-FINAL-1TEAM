from routers.document_router import router as document_router
from routers.user_router import router as user_router
from routers.admin_router import router as admin_router
from routers.qa_router import router as qa_router
from fastapi import FastAPI

app = FastAPI()
app.include_router(document_router, prefix="", tags=["Documents"])
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(qa_router, prefix="/qa", tags=["QA"])

@app.get("/")
def root():
    return {"message": "Welcome to the Database API!"}

@app.get("/ping")
def ping():
    return {"message": "pong"}

# Only keep root and ping endpoints here, all others should be in routers 