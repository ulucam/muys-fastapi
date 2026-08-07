from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.push_service import abonelik_durumu, abonelik_kaydet, abonelik_sil

router = APIRouter(tags=["Web Push"])


def _kullanici_id(request: Request) -> int:
    kullanici_id = request.session.get("user_id")
    if not kullanici_id:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    return int(kullanici_id)


def _istemci_istegini_dogrula(request: Request) -> None:
    if request.headers.get("x-requested-with") != "MUYS-PWA":
        raise HTTPException(status_code=403, detail="Geçersiz istek")


@router.get("/sw.js", include_in_schema=False)
def service_worker():
    return FileResponse("app/static/sw.js", media_type="application/javascript", headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})


@router.get("/api/push/durum", response_class=JSONResponse)
def push_durum(request: Request, db: Session = Depends(get_db)):
    return abonelik_durumu(db, _kullanici_id(request))


@router.post("/api/push/abone-ol", response_class=JSONResponse)
async def push_abone_ol(request: Request, db: Session = Depends(get_db)):
    _istemci_istegini_dogrula(request)
    veri = await request.json()
    try:
        abonelik = abonelik_kaydet(db, _kullanici_id(request), veri.get("subscription") or {}, veri.get("cihaz_adi") or "")
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail="Geçersiz abonelik bilgisi")
    return {"aktif": True, "id": abonelik.id}


@router.post("/api/push/abonelikten-cik", response_class=JSONResponse)
async def push_abonelikten_cik(request: Request, db: Session = Depends(get_db)):
    _istemci_istegini_dogrula(request)
    veri = await request.json()
    return {"kapatildi": abonelik_sil(db, _kullanici_id(request), str(veri.get("endpoint") or ""))}
