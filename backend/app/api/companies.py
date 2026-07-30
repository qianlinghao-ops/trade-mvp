from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.company import Company, CompanyType
import uuid

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("")
async def list_companies(
    company_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Company)
    if company_type:
        q = q.filter(Company.company_type == company_type)
    companies = q.order_by(Company.company_name).all()
    return {
        "total": len(companies),
        "items": [
            {
                "id": c.id,
                "company_name": c.company_name,
                "company_type": c.company_type,
                "country": c.country,
                "contact_name": c.contact_name,
                "contact_email": c.contact_email,
                "contact_phone": c.contact_phone,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in companies
        ]
    }

@router.post("")
async def create_company(body: dict, db: Session = Depends(get_db)):
    company = Company(
        id=str(uuid.uuid4()),
        company_name=body.get("company_name", ""),
        company_type=body.get("company_type", "supplier"),
        country=body.get("country", ""),
        address=body.get("address", ""),
        contact_name=body.get("contact_name", ""),
        contact_email=body.get("contact_email", ""),
        contact_phone=body.get("contact_phone", ""),
        notes=body.get("notes", ""),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return {"id": company.id, "company_name": company.company_name, "company_type": company.company_type}

@router.get("/{company_id}")
async def get_company(company_id: str, db: Session = Depends(get_db)):
    c = db.query(Company).filter(Company.id == company_id).first()
    if not c:
        raise HTTPException(404, "取引先が見つかりません")
    return {
        "id": c.id, "company_name": c.company_name, "company_type": c.company_type,
        "country": c.country, "address": c.address,
        "contact_name": c.contact_name, "contact_email": c.contact_email,
        "contact_phone": c.contact_phone, "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }

@router.put("/{company_id}")
async def update_company(company_id: str, body: dict, db: Session = Depends(get_db)):
    c = db.query(Company).filter(Company.id == company_id).first()
    if not c:
        raise HTTPException(404, "取引先が見つかりません")
    for k, v in body.items():
        if hasattr(c, k):
            setattr(c, k, v)
    db.commit()
    return {"success": True}

@router.delete("/{company_id}")
async def delete_company(company_id: str, db: Session = Depends(get_db)):
    c = db.query(Company).filter(Company.id == company_id).first()
    if not c:
        raise HTTPException(404, "取引先が見つかりません")
    db.delete(c)
    db.commit()
    return {"success": True}