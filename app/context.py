from fastapi import Request


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
        )

    }