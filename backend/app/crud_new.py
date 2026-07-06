from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.models import Job, Candidate, StageReport, InterviewRecord, CandidateStatusLog
from app import constants


# ============== Job CRUD ==============
def create_job(db: Session, data: dict) -> Job:
    db_job = Job(
        job_name=data["job_name"],
        department=data["department"],
        headcount=data["headcount"],
        jd_text=data["jd_text"],
        status=constants.JOB_STATUS_OPEN,
        remark=data.get("remark"),
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def get_job(db: Session, job_id: int) -> Optional[Job]:
    return db.query(Job).filter(Job.id == job_id, Job.deleted == 0).first()


def get_job_list(
    db: Session,
    job_name: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
):
    query = db.query(Job).filter(Job.deleted == 0)

    if job_name:
        query = query.filter(Job.job_name.contains(job_name))
    if department:
        query = query.filter(Job.department.contains(department))
    if status:
        query = query.filter(Job.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(Job.created_at.desc()).offset(offset).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "items": items}


def update_job(db: Session, job_id: int, data: dict) -> Optional[Job]:
    db_job = get_job(db, job_id)
    if not db_job:
        return None

    db_job.job_name = data["job_name"]
    db_job.department = data["department"]
    db_job.headcount = data["headcount"]
    db_job.jd_text = data["jd_text"]
    db_job.remark = data.get("remark")
    db_job.updated_at = datetime.now()

    db.commit()
    db.refresh(db_job)
    return db_job


def update_job_status(db: Session, job_id: int, status: str) -> Optional[Job]:
    if status not in constants.VALID_JOB_STATUSES:
        return None

    db_job = get_job(db, job_id)
    if not db_job:
        return None

    db_job.status = status
    db_job.updated_at = datetime.now()

    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job(db: Session, job_id: int) -> bool:
    db_job = get_job(db, job_id)
    if not db_job:
        return False

    db_job.deleted = 1
    db_job.updated_at = datetime.now()
    db.commit()
    return True


# ============== Candidate CRUD ==============
def create_candidate(db: Session, data: dict) -> Candidate:
    db_candidate = Candidate(
        job_id=data["job_id"],
        candidate_name=data["candidate_name"],
        phone=data.get("phone"),
        email=data.get("email"),
        source=data.get("source"),
        resume_text=data["resume_text"],
        current_status=constants.STATUS_RESUME_PENDING,
        remark=data.get("remark"),
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)

    # 记录初始状态流转
    log_status_change(
        db=db,
        candidate_id=db_candidate.id,
        from_status=None,
        to_status=db_candidate.current_status,
        reason="候选人导入",
        operator_name=None,
    )

    return db_candidate


def get_candidate(db: Session, candidate_id: int) -> Optional[Candidate]:
    return db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.deleted == 0).first()


def get_candidate_with_job(db: Session, candidate_id: int) -> Optional[Candidate]:
    return db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.deleted == 0).first()


def get_candidate_list(
    db: Session,
    job_id: Optional[int] = None,
    candidate_name: Optional[str] = None,
    source: Optional[str] = None,
    current_status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
):
    query = db.query(Candidate).filter(Candidate.deleted == 0)

    if job_id:
        query = query.filter(Candidate.job_id == job_id)
    if candidate_name:
        query = query.filter(Candidate.candidate_name.contains(candidate_name))
    if source:
        query = query.filter(Candidate.source == source)
    if current_status:
        query = query.filter(Candidate.current_status == current_status)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(Candidate.updated_at.desc()).offset(offset).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "items": items}


def update_candidate(db: Session, candidate_id: int, data: dict) -> Optional[Candidate]:
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return None

    db_candidate.candidate_name = data["candidate_name"]
    db_candidate.phone = data.get("phone")
    db_candidate.email = data.get("email")
    db_candidate.source = data.get("source")
    db_candidate.resume_text = data["resume_text"]
    db_candidate.remark = data.get("remark")
    db_candidate.updated_at = datetime.now()

    db.commit()
    db.refresh(db_candidate)
    return db_candidate


def update_candidate_status(
    db: Session,
    candidate_id: int,
    to_status: str,
    reason: Optional[str] = None,
    operator_name: Optional[str] = None,
) -> Optional[Candidate]:
    if to_status not in constants.VALID_CANDIDATE_STATUSES:
        return None

    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return None

    from_status = db_candidate.current_status

    # 校验状态流转
    allowed = constants.ALLOWED_STATUS_TRANSITIONS.get(from_status, set())
    if from_status == to_status or to_status in allowed:
        pass
    else:
        return None

    db_candidate.current_status = to_status
    db_candidate.updated_at = datetime.now()

    db.commit()
    db.refresh(db_candidate)

    log_status_change(
        db=db,
        candidate_id=candidate_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        operator_name=operator_name,
    )

    return db_candidate


def update_candidate_score_summary(
    db: Session,
    candidate_id: int,
    stage_type: str,
    score: Optional[int] = None,
    suggestion: Optional[str] = None,
) -> Optional[Candidate]:
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return None

    if stage_type == constants.STAGE_RESUME_SCREENING:
        db_candidate.resume_match_score = score
    elif stage_type == constants.STAGE_FIRST_INTERVIEW:
        db_candidate.first_interview_score = score
    elif stage_type == constants.STAGE_SECOND_INTERVIEW:
        db_candidate.second_interview_score = score

    db_candidate.latest_ai_suggestion = suggestion
    db_candidate.updated_at = datetime.now()

    db.commit()
    db.refresh(db_candidate)
    return db_candidate


def delete_candidate(db: Session, candidate_id: int) -> bool:
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return False

    db_candidate.deleted = 1
    db_candidate.updated_at = datetime.now()
    db.commit()
    return True


# ============== Status Log CRUD ==============
def log_status_change(
    db: Session,
    candidate_id: int,
    from_status: Optional[str],
    to_status: str,
    reason: Optional[str] = None,
    operator_name: Optional[str] = None,
) -> CandidateStatusLog:
    db_log = CandidateStatusLog(
        candidate_id=candidate_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        operator_name=operator_name,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_status_logs(db: Session, candidate_id: int):
    return (
        db.query(CandidateStatusLog)
        .filter(CandidateStatusLog.candidate_id == candidate_id)
        .order_by(CandidateStatusLog.created_at.desc())
        .all()
    )


# ============== Stage Report CRUD ==============
def create_stage_report(
    db: Session,
    candidate_id: int,
    job_id: int,
    stage_type: str,
    report_version: int,
    report_json: str,
    input_snapshot_json: str,
    score: Optional[int] = None,
    suggestion: Optional[str] = None,
    risk_level: Optional[str] = None,
    content_hash: Optional[str] = None,
    request_id: Optional[str] = None,
    status: str = constants.REPORT_STATUS_SUCCESS,
    error_message: Optional[str] = None,
) -> StageReport:
    db_report = StageReport(
        candidate_id=candidate_id,
        job_id=job_id,
        stage_type=stage_type,
        report_version=report_version,
        report_json=report_json,
        input_snapshot_json=input_snapshot_json,
        score=score,
        suggestion=suggestion,
        risk_level=risk_level,
        content_hash=content_hash,
        request_id=request_id,
        status=status,
        error_message=error_message,
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def get_stage_report(db: Session, report_id: int) -> Optional[StageReport]:
    return db.query(StageReport).filter(StageReport.id == report_id, StageReport.deleted == 0).first()


def get_latest_stage_report(
    db: Session, candidate_id: int, stage_type: str
) -> Optional[StageReport]:
    return (
        db.query(StageReport)
        .filter(
            StageReport.candidate_id == candidate_id,
            StageReport.stage_type == stage_type,
            StageReport.status == constants.REPORT_STATUS_SUCCESS,
            StageReport.deleted == 0,
        )
        .order_by(StageReport.created_at.desc())
        .first()
    )


def get_existing_report_by_hash(
    db: Session, candidate_id: int, stage_type: str, content_hash: str
) -> Optional[StageReport]:
    return (
        db.query(StageReport)
        .filter(
            StageReport.candidate_id == candidate_id,
            StageReport.stage_type == stage_type,
            StageReport.content_hash == content_hash,
            StageReport.status == constants.REPORT_STATUS_SUCCESS,
            StageReport.deleted == 0,
        )
        .order_by(StageReport.created_at.desc())
        .first()
    )


def get_next_report_version(db: Session, candidate_id: int, stage_type: str) -> int:
    latest = (
        db.query(StageReport)
        .filter(
            StageReport.candidate_id == candidate_id,
            StageReport.stage_type == stage_type,
            StageReport.deleted == 0,
        )
        .order_by(StageReport.report_version.desc())
        .first()
    )
    return (latest.report_version + 1) if latest else 1


# ============== Interview Record CRUD ==============
def create_interview_record(
    db: Session,
    candidate_id: int,
    job_id: int,
    round_type: str,
    record_text: str,
    interviewer_name: Optional[str] = None,
    interview_time: Optional[datetime] = None,
) -> InterviewRecord:
    if round_type not in constants.VALID_ROUND_TYPES:
        raise ValueError(f"无效的面试轮次类型: {round_type}")

    db_record = InterviewRecord(
        candidate_id=candidate_id,
        job_id=job_id,
        round_type=round_type,
        record_text=record_text,
        interviewer_name=interviewer_name,
        interview_time=interview_time,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def get_interview_record(db: Session, record_id: int) -> Optional[InterviewRecord]:
    return db.query(InterviewRecord).filter(InterviewRecord.id == record_id, InterviewRecord.deleted == 0).first()


def get_latest_interview_record(
    db: Session, candidate_id: int, round_type: str
) -> Optional[InterviewRecord]:
    return (
        db.query(InterviewRecord)
        .filter(
            InterviewRecord.candidate_id == candidate_id,
            InterviewRecord.round_type == round_type,
            InterviewRecord.deleted == 0,
        )
        .order_by(InterviewRecord.created_at.desc())
        .first()
    )


def get_interview_records(
    db: Session,
    candidate_id: int,
    round_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
):
    query = db.query(InterviewRecord).filter(
        InterviewRecord.candidate_id == candidate_id,
        InterviewRecord.deleted == 0,
    )

    if round_type:
        query = query.filter(InterviewRecord.round_type == round_type)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(InterviewRecord.created_at.desc()).offset(offset).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "items": items}


def delete_interview_record(db: Session, record_id: int) -> bool:
    db_record = get_interview_record(db, record_id)
    if not db_record:
        return False

    db_record.deleted = 1
    db_record.updated_at = datetime.now()
    db.commit()
    return True


# ============== 通用辅助：按岗位统计候选人数 ==============
def count_candidates_by_status(db: Session, job_id: int, status: str) -> int:
    return (
        db.query(Candidate)
        .filter(Candidate.job_id == job_id, Candidate.current_status == status, Candidate.deleted == 0)
        .count()
    )


def count_candidates_by_job(db: Session, job_id: int) -> int:
    return db.query(Candidate).filter(Candidate.job_id == job_id, Candidate.deleted == 0).count()
