from fastapi import Request

from app.version import guncel_surumu_al


def template_data(request: Request):

    return {

        "request": request,

        "kullanici_adi": request.session.get(
            "kullanici_adi",
            "Misafir"
        ),

        "kullanici_rol": request.session.get(
            "rol",
            ""
        ),

        "firma_adi": getattr(request.state, "firma_adi", "MÜYS"),
        "firma_logo_yolu": getattr(request.state, "firma_logo_yolu", ""),
        "uygulama_surumu": guncel_surumu_al(),

    }
