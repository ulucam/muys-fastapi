from fastapi import Request, HTTPException, status


def yetki_kontrol(izinli_roller):

    def kontrol(request: Request):

        rol = request.session.get(
            "rol",
            ""
        )


        if rol not in izinli_roller:

            raise HTTPException(
                status_code=403,
                detail="Bu sayfaya erişim yetkiniz yok."
            )


        return True


    return kontrol