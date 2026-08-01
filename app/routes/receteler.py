from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.security import yetki_kontrol
from app.database import get_db
from app.roles import RECETE

router = APIRouter(
    prefix="/recete",
    tags=["Reçeteler"]
)


templates = Jinja2Templates(
    directory="app/templates"
)