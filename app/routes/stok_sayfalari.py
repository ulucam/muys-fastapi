from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.models.recete import Recete
from app.models.urun import Urun
from app.roles import STOK
from app.security import yetki_kontrol

router = APIRouter(tags=["Stok"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/urunler", response_class=HTMLResponse)
def urunler(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["urunler"] = db.query(Urun).order_by(Urun.kodu).all()
    return templates.TemplateResponse("stok/urunler.html", data)


@router.get("/receteler", response_class=HTMLResponse)
def receteler(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["receteler"] = db.query(Recete).order_by(Recete.id.desc()).all()
    return templates.TemplateResponse("stok/receteler.html", data)
