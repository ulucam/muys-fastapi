from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill
from app.database import get_db
from app.models import Musteri, Siparis, User
from app.auth import get_current_user

router = APIRouter(prefix="/api/excel", tags=["excel"])

@router.get("/musteriler")
def excel_musteriler(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Musteriler"
    
    basliklar = ['ID', 'Firma Kodu', 'Firma Adı', 'Yetkili', 'Telefon', 'Email', 'İl', 'İlçe']
    for col, baslik in enumerate(basliklar, 1):
        cell = ws.cell(row=1, column=col, value=baslik)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    musteriler = db.query(Musteri).all()
    for row_idx, m in enumerate(musteriler, 2):
        ws.cell(row=row_idx, column=1, value=m.id)
        ws.cell(row=row_idx, column=2, value=m.firma_kodu)
        ws.cell(row=row_idx, column=3, value=m.firma_adi)
        ws.cell(row=row_idx, column=4, value=m.yetkili or '')
        ws.cell(row=row_idx, column=5, value=m.telefon or '')
        ws.cell(row=row_idx, column=6, value=m.email or '')
        ws.cell(row=row_idx, column=7, value=m.il or '')
        ws.cell(row=row_idx, column=8, value=m.ilce or '')
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=musteriler.xlsx"}
    )
