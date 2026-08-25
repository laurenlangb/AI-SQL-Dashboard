"""FastAPI app: routes for login, logout, data, and chat."""
import logging
import sqlite3

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

logger = logging.getLogger("app.main")

from app.auth import (
    COOKIE_NAME,
    SESSION_HOURS,
    check_credentials,
    create_token,
    get_current_user,
    require_user,
)
from app.database import TABLE_NAME, fetch_rows
from app.gemini import answer_question


class ChatRequest(BaseModel):
    message: str


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")



@app.get("/")
def root():
    # /dashboard redirects on to /login when there is no valid session.
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if get_current_user(request) is not None:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        "data_table.html",
        {
            "request": request,
            "user_name": user["name"],
            "table": {"head": TABLE_NAME},
        },
    )



@app.post("/api/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    if not check_credentials(email, password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password."},
            status_code=401,
        )

    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        COOKIE_NAME,
        create_token(),
        httponly=True,
        samesite="lax",
        max_age=SESSION_HOURS * 3600,
    )
    return response


@app.post("/api/logout")
def logout():
    # Drop the session cookie and send the user back to the login screen.
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response



@app.get("/api/data", dependencies=[Depends(require_user)])
def get_data():
    try:
        return {"data": fetch_rows()}
    except sqlite3.Error as error:
        logger.warning("Failed to fetch data: %s", error)
        raise HTTPException(status_code=503, detail="Could not read the data right now.")


@app.post("/api/chat", dependencies=[Depends(require_user)])
def chat(payload: ChatRequest):
    question = payload.message.strip()
    if not question:
        return {"answer": "Please type a question."}

    # answer_question runs the whole pipeline question pipeline
    return {"answer": answer_question(question)}
