from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


router = APIRouter()


templates = Jinja2Templates(
    directory="app/templates"
)



# LOGIN SAYFASI

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request
        }
    )



# LOGIN KONTROL

@router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db)
):

    form = await request.form()


    kullanici_adi = form.get("kullanici_adi")
    sifre = form.get("sifre")


    user = db.query(User).filter(
        User.kullanici_adi == kullanici_adi,
        User.sifre == sifre
    ).first()



    if user:


        request.session["user_id"] = user.id

        request.session["kullanici_adi"] = user.kullanici_adi

        request.session["rol"] = user.rol



        return RedirectResponse(
            "/",
            status_code=303
        )



    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "hata": "Kullanıcı adı veya şifre hatalı"
        }
    )




# LOGOUT

@router.get("/logout")
async def logout(request: Request):


    request.session.clear()


    return RedirectResponse(
        "/login",
        status_code=303
    )