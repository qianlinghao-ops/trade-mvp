import os, json, uuid, shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document, DocumentType, DocumentStatus
from app.services.ocr_service import parse_document
from app.services.document_generator import generate_document
from app.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])
ALLOWED_EXTENSIONS = {".pdf",".jpg",".jpeg",".png",".docx",".doc",".xlsx",".xls"}

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), doc_type: str = Form("po"), db: Session = Depends(get_db)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS: raise HTTPException(400, f"対応していないファイル形式: {ext}")
    stored_name = f"{uuid.uuid4()}{ext}"
    stored_path = settings.UPLOAD_DIR / stored_name
    with open(stored_path, "wb") as f2: shutil.copyfileobj(file.file, f2)
    doc = Document(doc_type=doc_type, status=DocumentStatus.processing, original_filename=file.filename, stored_filename=stored_name)
    db.add(doc); db.commit(); db.refresh(doc)
    try:
        extracted = parse_document(str(stored_path), doc_type)
        doc.extracted_data = json.dumps(extracted, ensure_ascii=False)
        doc.confidence_score = extracted.get("confidence_score", 0.5)
        doc.status = DocumentStatus.review
    except Exception as e:
        doc.status = DocumentStatus.error
        doc.extracted_data = json.dumps({"error": str(e)}, ensure_ascii=False)
    db.commit(); db.refresh(doc)
    return {"document_id": doc.id, "status": doc.status, "original_filename": doc.original_filename, "extracted_data": json.loads(doc.extracted_data) if doc.extracted_data else {}, "confidence_score": doc.confidence_score}

@router.post("/{doc_id}/generate")
async def generate_doc(doc_id: str, data: Optional[dict] = None, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc: raise HTTPException(404, "書類が見つかりません")
    extracted = json.loads(doc.extracted_data) if doc.extracted_data else {}
    if data: extracted.update(data)
    gen_name = f"{doc.doc_type}_{doc_id[:8]}.pdf"
    try:
        generate_document(doc.doc_type, extracted, gen_name)
        doc.generated_filename = gen_name; doc.status = DocumentStatus.completed; db.commit()
    except Exception as e: raise HTTPException(500, f"書類生成エラー: {str(e)}")
    return {"document_id": doc.id, "status": doc.status, "generated_filename": gen_name, "download_url": f"/api/documents/{doc_id}/download"}

@router.post("/generate-manual")
async def generate_manual(body: dict, db: Session = Depends(get_db)):
    doc_type = body.get("doc_type","po"); data = body.get("data",{})
    doc = Document(doc_type=doc_type, status=DocumentStatus.completed, original_filename="手動入力", stored_filename="", extracted_data=json.dumps(data, ensure_ascii=False), confidence_score=1.0)
    db.add(doc); db.commit(); db.refresh(doc)
    gen_name = f"{doc_type}_{doc.id[:8]}.pdf"
    try:
        generate_document(doc_type, data, gen_name); doc.generated_filename = gen_name; db.commit()
    except Exception as e: raise HTTPException(500, f"書類生成エラー: {str(e)}")
    return {"document_id": doc.id, "status": "completed", "generated_filename": gen_name, "download_url": f"/api/documents/{doc.id}/download"}

@router.get("/{doc_id}/download")
async def download_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc or not doc.generated_filename: raise HTTPException(404, "生成済み書類が見つかりません")
    file_path = settings.GENERATED_DIR / doc.generated_filename
    if not file_path.exists(): raise HTTPException(404, "ファイルが存在しません")
    return FileResponse(path=str(file_path), media_type="application/pdf", filename=doc.generated_filename)

@router.get("")
async def list_documents(skip: int = 0, limit: int = 50, doc_type: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Document)
    if doc_type: q = q.filter(Document.doc_type == doc_type)
    total = q.count()
    docs = q.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [{"id": d.id, "doc_type": d.doc_type, "status": d.status, "original_filename": d.original_filename, "confidence_score": d.confidence_score, "created_at": d.created_at.isoformat() if d.created_at else None, "has_generated": bool(d.generated_filename)} for d in docs]}

@router.get("/{doc_id}")
async def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc: raise HTTPException(404, "書類が見つかりません")
    return {"id": doc.id, "doc_type": doc.doc_type, "status": doc.status, "original_filename": doc.original_filename, "extracted_data": json.loads(doc.extracted_data) if doc.extracted_data else {}, "confidence_score": doc.confidence_score, "generated_filename": doc.generated_filename, "created_at": doc.created_at.isoformat() if doc.created_at else None}

@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc: raise HTTPException(404, "書類が見つかりません")
    db.delete(doc); db.commit(); return {"success": True}
