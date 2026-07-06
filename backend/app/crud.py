from sqlalchemy.orm import Session
from app.models import InterviewAnalysis
from app.schemas import AnalysisCreate, AnalysisFilter
from datetime import datetime


def create_analysis(db: Session, analysis: AnalysisCreate, analysis_result: str,
                    match_score: int, recommendation: str, risk_level: str, confidence: str):
    db_analysis = InterviewAnalysis(
        candidate_name=analysis.candidate_name,
        job_title=analysis.job_title,
        jd_text=analysis.jd_text,
        resume_text=analysis.resume_text,
        interview_text=analysis.interview_text,
        analysis_result=analysis_result,
        match_score=match_score,
        recommendation=recommendation,
        risk_level=risk_level,
        confidence=confidence,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_analysis(db: Session, analysis_id: int):
    return db.query(InterviewAnalysis).filter(
        InterviewAnalysis.id == analysis_id,
        InterviewAnalysis.deleted == 0
    ).first()


def get_analysis_list(db: Session, filters: AnalysisFilter):
    query = db.query(InterviewAnalysis).filter(InterviewAnalysis.deleted == 0)

    if filters.candidate_name:
        query = query.filter(InterviewAnalysis.candidate_name.contains(filters.candidate_name))
    if filters.job_title:
        query = query.filter(InterviewAnalysis.job_title.contains(filters.job_title))
    if filters.recommendation:
        query = query.filter(InterviewAnalysis.recommendation == filters.recommendation)
    if filters.risk_level:
        query = query.filter(InterviewAnalysis.risk_level == filters.risk_level)

    total = query.count()

    offset = (filters.page - 1) * filters.page_size
    items = query.order_by(InterviewAnalysis.created_at.desc()).offset(offset).limit(filters.page_size).all()

    return {
        "total": total,
        "page": filters.page,
        "page_size": filters.page_size,
        "items": items
    }


def delete_analysis(db: Session, analysis_id: int):
    db_analysis = db.query(InterviewAnalysis).filter(InterviewAnalysis.id == analysis_id).first()
    if db_analysis:
        db_analysis.deleted = 1
        db_analysis.updated_at = datetime.now()
        db.commit()
        return True
    return False
