from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.musteri import Musteri
from app.models.urun import Urun
from app.models.siparis import Siparis


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):

    toplam_siparis = db.query(Siparis).count()
    toplam_musteri = db.query(Musteri).count()
    toplam_urun = db.query(Urun).count()


    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "toplam_siparis": toplam_siparis,
            "toplam_musteri": toplam_musteri,
            "toplam_urun": toplam_urun
        }
    )