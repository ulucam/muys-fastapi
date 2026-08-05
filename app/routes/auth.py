from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import kullanici_dogrula


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
            "request": request
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
