from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import kullanici_dogrula
from app.services.ayarlar_service import bakim_modu_aktif_mi
from app.models.rol_sinifi import RolSinifi


router = APIRouter()


templates = Jinja2Templates(
    directory="app/templates"
)



# =====================================================
# LOGIN SAYFASI
# =====================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "hata": "Sistem bakım modunda. Lütfen daha sonra tekrar deneyin." if request.query_params.get("bakim") else None,
        }
    )



# =====================================================
# LOGIN KONTROL
# =====================================================

@router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db)
):

    form = await request.form()


    kullanici_adi = form.get("kullanici_adi")
    sifre = form.get("sifre")



    # sadece kullanıcı adına göre buluyoruz
    user = kullanici_dogrula(db, kullanici_adi, sifre)



    # kullanıcı var mı ve şifre doğru mu?
    if user:



        if user.rol != "Admin" and bakim_modu_aktif_mi(db):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "hata": "Sistem bakım modunda. Yalnızca yönetici erişebilir."},
            )

        # pasif kullanıcı kontrolü

        if not user.aktif:

            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "hata": "Bu kullanıcı pasif durumda. Sistem yöneticisi ile görüşün."
                }
            )



        # oturum bilgileri

        request.session["user_id"] = user.id

        request.session["kullanici_adi"] = user.kullanici_adi

        request.session["rol"] = user.rol

        rol_sinifi = db.query(RolSinifi).filter(RolSinifi.adi == user.rol).first()
        request.session["kullanici_ekleyebilir"] = bool(user.rol == "Admin" or (rol_sinifi and rol_sinifi.kullanici_ekleyebilir))



        return RedirectResponse(
            "/",
            status_code=303
        )



    # kullanıcı yok veya şifre yanlış

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "hata": "Kullanıcı adı veya şifre hatalı"
        }
    )



# =====================================================
# LOGOUT
# =====================================================

@router.get("/logout")
async def logout(request: Request):

    request.session.clear()


    return RedirectResponse(
        "/login",
        status_code=303
    )
