from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.roles import STOK
from app.security import yetki_kontrol
from app.services.stok_service import hammaddeleri_listele, receteleri_listele

router = APIRouter(tags=["Stok"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/urunler", response_class=HTMLResponse)
def urunler(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["urunler"] = hammaddeleri_listele(db)
    return templates.TemplateResponse("stok/urunler.html", data)


@router.get("/receteler", response_class=HTMLResponse)
def receteler(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["receteler"] = receteleri_listele(db)
    return templates.TemplateResponse("stok/receteler.html", data)
