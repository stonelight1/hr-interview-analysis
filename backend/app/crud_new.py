import json
import hashlib
import re

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from datetime import datetime

from app.models import (
    Job, Candidate, StageReport, InterviewRecord, CandidateStatusLog,
    CandidateInterviewRound, ScreeningTask, InterviewQuestionItem,
)
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

        # 新增字段
        job_type=data.get("job_type"),
        location=data.get("location"),
        salary_range=data.get("salary_range"),
        education_req=data.get("education_req"),
        experience_req=data.get("experience_req"),
        parsed_jd_json=data.get("parsed_jd_json"),
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

    # 新增字段
    db_job.job_type = data.get("job_type")
    db_job.location = data.get("location")
    db_job.salary_range = data.get("salary_range")
    db_job.education_req = data.get("education_req")
    db_job.experience_req = data.get("experience_req")
    db_job.parsed_jd_json = data.get("parsed_jd_json")

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


def _load_json(value: Optional[str], default):
    if not value:
        return default
    try:
        parsed = json.loads(value)
        return parsed if parsed is not None else default
    except Exception:
        return default


def _dump_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.replace("，", "\n").replace("、", "\n").splitlines() if item.strip()]
    return [value]


def _first_value(data: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, "", []):
            return value
    return None


def _extract_position_lists(parsed_jd: Dict[str, Any]) -> Dict[str, list]:
    return {
        "screening_rules": _as_list(_first_value(parsed_jd, "key_screening_points", "resume_screening_dimensions", "screening_rules")),
        "must_have": _as_list(_first_value(parsed_jd, "must_have", "must_have_skills", "must_have_conditions", "requirements")),
        "nice_to_have": _as_list(_first_value(parsed_jd, "nice_to_have", "nice_to_have_skills", "nice_to_have_conditions")),
        "risk_points": _as_list(_first_value(parsed_jd, "risk_points", "reject_conditions", "deal_breakers")),
        "interview_questions": _as_list(_first_value(parsed_jd, "interview_questions", "suggested_interview_questions")),
    }


def build_job_position_draft_from_parsed(jd_text: str, parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
    lists = _extract_position_lists(parsed_jd or {})
    return {
        "position_name": _first_value(parsed_jd, "job_title", "job_name") or "未命名岗位",
        "position_type": _first_value(parsed_jd, "job_type") or constants.JOB_TYPE_GENERAL,
        "department_name": _first_value(parsed_jd, "department_name", "department") or "未分配",
        "education_requirement": _first_value(parsed_jd, "education_requirement", "education_req") or "",
        "experience_requirement": _first_value(parsed_jd, "experience_requirement", "experience_req") or "",
        "jd_original_text": jd_text,
        "jd_structured_json": parsed_jd or {},
        **lists,
    }


def _job_position_payload(db: Session, job: Job, include_detail: bool = False) -> Dict[str, Any]:
    parsed_jd = _load_json(job.parsed_jd_json, {})
    extracted = _extract_position_lists(parsed_jd if isinstance(parsed_jd, dict) else {})
    payload = {
        "id": job.id,
        "position_name": job.job_name,
        "position_type": job.job_type,
        "department_name": job.department,
        "education_requirement": job.education_req,
        "experience_requirement": job.experience_req,
        "version": job.version or 1,
        "status": job.status,
        "candidate_count": count_screening_resumes_by_job(db, job.id),
        "last_used_time": job.last_used_time,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
    if include_detail:
        payload.update({
            "jd_original_text": job.jd_text,
            "jd_structured_json": parsed_jd if isinstance(parsed_jd, dict) else {},
            "screening_rules": _load_json(job.screening_rules_json, extracted["screening_rules"]),
            "must_have": _load_json(job.must_have_json, extracted["must_have"]),
            "nice_to_have": _load_json(job.nice_to_have_json, extracted["nice_to_have"]),
            "risk_points": _load_json(job.risk_points_json, extracted["risk_points"]),
            "interview_questions": _load_json(job.interview_questions_json, extracted["interview_questions"]),
        })
    return payload


def count_screening_resumes_by_job(db: Session, job_id: int) -> int:
    total = (
        db.query(func.coalesce(func.sum(ScreeningTask.total_resume_count), 0))
        .filter(ScreeningTask.job_position_id == job_id, ScreeningTask.deleted == 0)
        .scalar()
    )
    return int(total or 0)


def has_job_position_screening_history(db: Session, job_id: int) -> bool:
    return (
        db.query(ScreeningTask.id)
        .filter(ScreeningTask.job_position_id == job_id, ScreeningTask.deleted == 0)
        .first()
        is not None
    )


def list_job_positions(
    db: Session,
    keyword: Optional[str] = None,
    position_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    query = db.query(Job).filter(Job.deleted == 0)

    if status:
        if status == "ACTIVE":
            query = query.filter(Job.status != constants.JOB_STATUS_ARCHIVED)
        else:
            query = query.filter(Job.status == status)
    else:
        query = query.filter(Job.status != constants.JOB_STATUS_ARCHIVED)

    if keyword:
        like = f"%{keyword.strip()}%"
        query = query.filter(or_(Job.job_name.ilike(like), Job.job_type.ilike(like), Job.department.ilike(like)))

    if position_type:
        query = query.filter(Job.job_type.ilike(f"%{position_type.strip()}%"))

    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query
        .order_by(Job.last_used_time.is_(None), Job.last_used_time.desc(), Job.updated_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_job_position_payload(db, item, include_detail=False) for item in items],
    }


def get_job_position(db: Session, job_id: int) -> Optional[Dict[str, Any]]:
    db_job = get_job(db, job_id)
    if not db_job:
        return None
    return _job_position_payload(db, db_job, include_detail=True)


def create_job_position(db: Session, data: dict) -> Dict[str, Any]:
    parsed_jd = data.get("jd_structured_json") if isinstance(data.get("jd_structured_json"), dict) else {}
    extracted = _extract_position_lists(parsed_jd)
    db_job = Job(
        job_name=data["position_name"],
        department=data.get("department_name") or "未分配",
        headcount=1,
        jd_text=data["jd_original_text"],
        status=constants.JOB_STATUS_OPEN,
        job_type=data.get("position_type") or _first_value(parsed_jd, "job_type") or constants.JOB_TYPE_GENERAL,
        education_req=data.get("education_requirement") or _first_value(parsed_jd, "education_requirement", "education_req") or "",
        experience_req=data.get("experience_requirement") or _first_value(parsed_jd, "experience_requirement", "experience_req") or "",
        parsed_jd_json=_dump_json(parsed_jd) if parsed_jd else None,
        screening_rules_json=_dump_json(data.get("screening_rules") if data.get("screening_rules") is not None else extracted["screening_rules"]),
        must_have_json=_dump_json(data.get("must_have") if data.get("must_have") is not None else extracted["must_have"]),
        nice_to_have_json=_dump_json(data.get("nice_to_have") if data.get("nice_to_have") is not None else extracted["nice_to_have"]),
        risk_points_json=_dump_json(data.get("risk_points") if data.get("risk_points") is not None else extracted["risk_points"]),
        interview_questions_json=_dump_json(data.get("interview_questions") if data.get("interview_questions") is not None else extracted["interview_questions"]),
        version=1,
        created_by=data.get("created_by"),
        updated_by=data.get("updated_by") or data.get("created_by"),
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return _job_position_payload(db, db_job, include_detail=True)


def update_job_position(db: Session, job_id: int, data: dict) -> Optional[Dict[str, Any]]:
    db_job = get_job(db, job_id)
    if not db_job:
        return None

    save_mode = data.get("save_mode") or "NEW_VERSION"
    jd_related_keys = {
        "jd_original_text", "jd_structured_json", "screening_rules", "must_have",
        "nice_to_have", "risk_points", "interview_questions",
        "education_requirement", "experience_requirement",
    }
    jd_change_requested = any(data.get(key) is not None for key in jd_related_keys)
    has_history = has_job_position_screening_history(db, job_id)

    db_job.job_name = data.get("position_name") or db_job.job_name
    db_job.job_type = data.get("position_type") if data.get("position_type") is not None else db_job.job_type
    db_job.department = data.get("department_name") if data.get("department_name") is not None else db_job.department
    db_job.updated_by = data.get("updated_by") if data.get("updated_by") is not None else db_job.updated_by

    if save_mode != "DISPLAY_ONLY":
        if has_history and jd_change_requested:
            db_job.version = (db_job.version or 1) + 1

        parsed_jd = data.get("jd_structured_json")
        if isinstance(parsed_jd, dict):
            db_job.parsed_jd_json = _dump_json(parsed_jd)
            extracted = _extract_position_lists(parsed_jd)
        else:
            extracted = _extract_position_lists(_load_json(db_job.parsed_jd_json, {}))

        if data.get("jd_original_text") is not None:
            db_job.jd_text = data["jd_original_text"]
        if data.get("education_requirement") is not None:
            db_job.education_req = data["education_requirement"]
        if data.get("experience_requirement") is not None:
            db_job.experience_req = data["experience_requirement"]
        if data.get("screening_rules") is not None:
            db_job.screening_rules_json = _dump_json(data["screening_rules"])
        elif isinstance(parsed_jd, dict):
            db_job.screening_rules_json = _dump_json(extracted["screening_rules"])
        if data.get("must_have") is not None:
            db_job.must_have_json = _dump_json(data["must_have"])
        elif isinstance(parsed_jd, dict):
            db_job.must_have_json = _dump_json(extracted["must_have"])
        if data.get("nice_to_have") is not None:
            db_job.nice_to_have_json = _dump_json(data["nice_to_have"])
        elif isinstance(parsed_jd, dict):
            db_job.nice_to_have_json = _dump_json(extracted["nice_to_have"])
        if data.get("risk_points") is not None:
            db_job.risk_points_json = _dump_json(data["risk_points"])
        elif isinstance(parsed_jd, dict):
            db_job.risk_points_json = _dump_json(extracted["risk_points"])
        if data.get("interview_questions") is not None:
            db_job.interview_questions_json = _dump_json(data["interview_questions"])
        elif isinstance(parsed_jd, dict):
            db_job.interview_questions_json = _dump_json(extracted["interview_questions"])

    db_job.updated_at = datetime.now()
    db.commit()
    db.refresh(db_job)
    return _job_position_payload(db, db_job, include_detail=True)


def archive_job_position(db: Session, job_id: int) -> Optional[Dict[str, Any]]:
    db_job = get_job(db, job_id)
    if not db_job:
        return None
    db_job.status = constants.JOB_STATUS_ARCHIVED
    db_job.updated_at = datetime.now()
    db.commit()
    db.refresh(db_job)
    return _job_position_payload(db, db_job, include_detail=True)


def copy_job_position(db: Session, job_id: int) -> Optional[Dict[str, Any]]:
    db_job = get_job(db, job_id)
    if not db_job:
        return None

    copied_job = Job(
        job_name=f"{db_job.job_name} 副本",
        department=db_job.department,
        headcount=db_job.headcount,
        jd_text=db_job.jd_text,
        status=constants.JOB_STATUS_OPEN,
        job_type=db_job.job_type,
        location=db_job.location,
        salary_range=db_job.salary_range,
        education_req=db_job.education_req,
        experience_req=db_job.experience_req,
        parsed_jd_json=db_job.parsed_jd_json,
        screening_rules_json=db_job.screening_rules_json,
        must_have_json=db_job.must_have_json,
        nice_to_have_json=db_job.nice_to_have_json,
        risk_points_json=db_job.risk_points_json,
        interview_questions_json=db_job.interview_questions_json,
        version=1,
        remark=db_job.remark,
        created_by=db_job.created_by,
        updated_by=db_job.updated_by,
    )
    db.add(copied_job)
    db.commit()
    db.refresh(copied_job)
    return _job_position_payload(db, copied_job, include_detail=True)


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

        # 新增结构化简历字段
        gender=data.get("gender"),
        age=data.get("age"),
        current_city=data.get("current_city"),
        expected_city=data.get("expected_city"),
        job_search_status=data.get("job_search_status"),
        available_date=data.get("available_date"),
        expected_salary=data.get("expected_salary"),
        education_level=data.get("education_level"),
        graduation_school=data.get("graduation_school"),
        major=data.get("major"),
        work_years=data.get("work_years"),
        parsed_resume_json=data.get("parsed_resume_json"),
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

    # 新增结构化简历字段
    db_candidate.gender = data.get("gender")
    db_candidate.age = data.get("age")
    db_candidate.current_city = data.get("current_city")
    db_candidate.expected_city = data.get("expected_city")
    db_candidate.job_search_status = data.get("job_search_status")
    db_candidate.available_date = data.get("available_date")
    db_candidate.expected_salary = data.get("expected_salary")
    db_candidate.education_level = data.get("education_level")
    db_candidate.graduation_school = data.get("graduation_school")
    db_candidate.major = data.get("major")
    db_candidate.work_years = data.get("work_years")
    db_candidate.parsed_resume_json = data.get("parsed_resume_json")

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


def set_candidate_flow_status(
    db: Session,
    db_candidate: Candidate,
    to_status: str,
    *,
    current_round_no: Optional[int] = None,
    final_conclusion: Optional[str] = None,
    reason: Optional[str] = None,
    operator_name: Optional[str] = None,
    commit: bool = True,
) -> Candidate:
    from_status = db_candidate.current_status
    db_candidate.current_status = to_status
    db_candidate.current_round_no = current_round_no
    db_candidate.final_conclusion = final_conclusion
    db_candidate.updated_at = datetime.now()
    if commit:
        db.commit()
        db.refresh(db_candidate)
    else:
        db.flush()

    log_status_change(
        db=db,
        candidate_id=db_candidate.id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        operator_name=operator_name,
        commit=commit,
    )
    return db_candidate


def mark_candidate_waiting_interview_after_screening(db: Session, candidate_id: int) -> Optional[Candidate]:
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return None

    existing_round = (
        db.query(CandidateInterviewRound)
        .filter(
            CandidateInterviewRound.candidate_id == candidate_id,
            CandidateInterviewRound.deleted == 0,
        )
        .first()
    )
    if existing_round:
        return db_candidate

    resumable_statuses = {
        constants.STATUS_RESUME_PENDING,
        constants.STATUS_RESUME_SCREENING,
        constants.STATUS_RESUME_SCREENING_DONE,
        constants.STATUS_RESUME_PASSED,
        constants.STATUS_RESUME_TBD,
        constants.STATUS_RESUME_REJECTED,
    }
    if db_candidate.current_status not in resumable_statuses:
        return db_candidate

    return set_candidate_flow_status(
        db,
        db_candidate,
        constants.STATUS_INTERVIEW_WAITING,
        current_round_no=None,
        final_conclusion=None,
        reason="简历筛选完成，进入待安排面试",
    )


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


# ============== Open Interview Round CRUD ==============
def get_candidate_interview_rounds(db: Session, candidate_id: int) -> list[CandidateInterviewRound]:
    return (
        db.query(CandidateInterviewRound)
        .filter(
            CandidateInterviewRound.candidate_id == candidate_id,
            CandidateInterviewRound.deleted == 0,
        )
        .order_by(CandidateInterviewRound.round_no.asc(), CandidateInterviewRound.created_at.asc())
        .all()
    )


def get_candidate_interview_rounds_by_candidate_ids(
    db: Session,
    candidate_ids: list[int],
) -> dict[int, list[CandidateInterviewRound]]:
    if not candidate_ids:
        return {}

    unique_ids = list(dict.fromkeys(candidate_ids))
    result = {candidate_id: [] for candidate_id in unique_ids}
    rounds = (
        db.query(CandidateInterviewRound)
        .join(Candidate, Candidate.id == CandidateInterviewRound.candidate_id)
        .filter(
            CandidateInterviewRound.candidate_id.in_(unique_ids),
            CandidateInterviewRound.deleted == 0,
            Candidate.deleted == 0,
        )
        .order_by(
            CandidateInterviewRound.candidate_id.asc(),
            CandidateInterviewRound.round_no.asc(),
            CandidateInterviewRound.created_at.asc(),
        )
        .all()
    )
    for interview_round in rounds:
        result.setdefault(interview_round.candidate_id, []).append(interview_round)
    return result


def get_candidate_interview_round(
    db: Session,
    candidate_id: int,
    round_id: int,
) -> Optional[CandidateInterviewRound]:
    return (
        db.query(CandidateInterviewRound)
        .filter(
            CandidateInterviewRound.id == round_id,
            CandidateInterviewRound.candidate_id == candidate_id,
            CandidateInterviewRound.deleted == 0,
        )
        .first()
    )


def get_latest_completed_interview_round(
    db: Session,
    candidate_id: int,
    before_round_no: Optional[int] = None,
) -> Optional[CandidateInterviewRound]:
    query = db.query(CandidateInterviewRound).filter(
        CandidateInterviewRound.candidate_id == candidate_id,
        CandidateInterviewRound.status == constants.INTERVIEW_ROUND_STATUS_COMPLETED,
        CandidateInterviewRound.deleted == 0,
    )
    if before_round_no is not None:
        query = query.filter(CandidateInterviewRound.round_no < before_round_no)
    return query.order_by(CandidateInterviewRound.round_no.desc(), CandidateInterviewRound.updated_at.desc()).first()


def get_next_interview_round_no(db: Session, candidate_id: int) -> int:
    latest = (
        db.query(CandidateInterviewRound)
        .filter(
            CandidateInterviewRound.candidate_id == candidate_id,
            CandidateInterviewRound.deleted == 0,
        )
        .order_by(CandidateInterviewRound.round_no.desc())
        .first()
    )
    return (latest.round_no + 1) if latest else 1


def has_active_interview_round(db: Session, candidate_id: int) -> bool:
    return (
        db.query(CandidateInterviewRound)
        .filter(
            CandidateInterviewRound.candidate_id == candidate_id,
            CandidateInterviewRound.status == constants.INTERVIEW_ROUND_STATUS_SCHEDULED,
            CandidateInterviewRound.deleted == 0,
        )
        .first()
        is not None
    )


def create_candidate_interview_round(
    db: Session,
    db_candidate: Candidate,
    data: dict,
    question_json: str,
    commit: bool = True,
) -> CandidateInterviewRound:
    round_no = data.get("round_no") or get_next_interview_round_no(db, db_candidate.id)
    round_name = data.get("round_name") or f"第 {round_no} 轮面试"

    db_round = CandidateInterviewRound(
        candidate_id=db_candidate.id,
        task_id=data.get("task_id"),
        round_no=round_no,
        round_name=round_name,
        round_type=data.get("round_type"),
        round_focus=data.get("round_focus"),
        status=constants.INTERVIEW_ROUND_STATUS_SCHEDULED,
        scheduled_time=data.get("scheduled_time"),
        interviewer=data.get("interviewer"),
        interview_method=data.get("interview_method"),
        question_json=question_json,
    )
    db.add(db_round)
    if commit:
        db.commit()
        db.refresh(db_round)
    else:
        db.flush()

    set_candidate_flow_status(
        db,
        db_candidate,
        constants.STATUS_INTERVIEW_SCHEDULED,
        current_round_no=round_no,
        final_conclusion=None,
        reason=f"创建{round_name}",
        commit=commit,
    )
    return db_round


def update_candidate_interview_round(
    db: Session,
    db_round: CandidateInterviewRound,
    data: dict,
) -> CandidateInterviewRound:
    for field in ("round_name", "round_type", "round_focus", "scheduled_time", "interviewer", "interview_method"):
        if field in data:
            setattr(db_round, field, data.get(field))
    db_round.updated_at = datetime.now()
    db.commit()
    db.refresh(db_round)
    return db_round


def submit_candidate_interview_record(
    db: Session,
    db_candidate: Candidate,
    db_round: CandidateInterviewRound,
    data: dict,
) -> CandidateInterviewRound:
    db_round.status = constants.INTERVIEW_ROUND_STATUS_COMPLETED
    db_round.record_text = data.get("record_text")
    db_round.score = data.get("score")
    db_round.conclusion = data.get("conclusion")
    db_round.decision = None
    db_round.updated_at = datetime.now()
    db.commit()
    db.refresh(db_round)

    set_candidate_flow_status(
        db,
        db_candidate,
        constants.STATUS_INTERVIEW_DECISION_PENDING,
        current_round_no=db_round.round_no,
        final_conclusion=None,
        reason=f"{db_round.round_name}已完成，等待 HR 决策",
    )
    return db_round


def cancel_candidate_interview_round(
    db: Session,
    db_candidate: Candidate,
    db_round: CandidateInterviewRound,
) -> CandidateInterviewRound:
    db_round.status = constants.INTERVIEW_ROUND_STATUS_CANCELED
    db_round.updated_at = datetime.now()
    db.commit()
    db.refresh(db_round)

    set_candidate_flow_status(
        db,
        db_candidate,
        constants.STATUS_INTERVIEW_WAITING,
        current_round_no=None,
        final_conclusion=None,
        reason=f"取消{db_round.round_name}",
    )
    return db_round


def apply_candidate_interview_decision(
    db: Session,
    db_candidate: Candidate,
    db_round: CandidateInterviewRound,
    decision: str,
    commit: bool = True,
) -> Candidate:
    db_round.decision = decision
    db_round.updated_at = datetime.now()
    if commit:
        db.commit()
        db.refresh(db_round)
    else:
        db.flush()

    if decision == constants.INTERVIEW_DECISION_PASS_END:
        return set_candidate_flow_status(
            db,
            db_candidate,
            constants.STATUS_FINAL_PASSED,
            current_round_no=db_round.round_no,
            final_conclusion=decision,
            reason=f"{db_round.round_name}决策：{decision}",
            commit=commit,
        )
    if decision == constants.INTERVIEW_DECISION_HOLD:
        return set_candidate_flow_status(
            db,
            db_candidate,
            constants.STATUS_ON_HOLD,
            current_round_no=db_round.round_no,
            final_conclusion=decision,
            reason=f"{db_round.round_name}决策：{decision}",
            commit=commit,
        )
    if decision == constants.INTERVIEW_DECISION_REJECT:
        return set_candidate_flow_status(
            db,
            db_candidate,
            constants.STATUS_REJECTED,
            current_round_no=db_round.round_no,
            final_conclusion=decision,
            reason=f"{db_round.round_name}决策：{decision}",
            commit=commit,
        )

    return db_candidate


def reopen_candidate_interview_flow(db: Session, db_candidate: Candidate) -> Candidate:
    return set_candidate_flow_status(
        db,
        db_candidate,
        constants.STATUS_INTERVIEW_WAITING,
        current_round_no=None,
        final_conclusion=None,
        reason="重新打开面试流程",
    )


def update_candidate_interview_questions(
    db: Session,
    db_round: CandidateInterviewRound,
    question_json: str,
) -> CandidateInterviewRound:
    db_round.question_json = question_json
    db_round.updated_at = datetime.now()
    db.commit()
    db.refresh(db_round)
    return db_round


# ============== Status Log CRUD ==============
def log_status_change(
    db: Session,
    candidate_id: int,
    from_status: Optional[str],
    to_status: str,
    reason: Optional[str] = None,
    operator_name: Optional[str] = None,
    commit: bool = True,
) -> CandidateStatusLog:
    db_log = CandidateStatusLog(
        candidate_id=candidate_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        operator_name=operator_name,
    )
    db.add(db_log)
    if commit:
        db.commit()
        db.refresh(db_log)
    else:
        db.flush()
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
    report_key: Optional[str] = None,
    is_current: int = 1,
    round_type: Optional[str] = None,
    round_no: Optional[int] = None,
    generate_type: Optional[str] = None,
    ai_provider: Optional[str] = None,
    ai_model: Optional[str] = None,
    candidate_snapshot_json: Optional[str] = None,
    jd_snapshot_json: Optional[str] = None,
    resume_snapshot_json: Optional[str] = None,
    interview_record_snapshot_json: Optional[str] = None,
    screening_result_snapshot_json: Optional[str] = None,
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
        report_key=report_key,
        is_current=is_current,
        round_type=round_type,
        round_no=round_no,
        generate_type=generate_type,
        ai_provider=ai_provider,
        ai_model=ai_model,
        candidate_snapshot_json=candidate_snapshot_json,
        jd_snapshot_json=jd_snapshot_json,
        resume_snapshot_json=resume_snapshot_json,
        interview_record_snapshot_json=interview_record_snapshot_json,
        screening_result_snapshot_json=screening_result_snapshot_json,
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def normalize_interview_question_text(text: Optional[str]) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^\s*\d+[\.\、\)]\s*", "", cleaned)
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = re.sub(r"[？?。！!，,；;：:\.、]+$", "", cleaned)
    return cleaned


def compute_interview_question_hash(text: Optional[str]) -> str:
    normalized = normalize_interview_question_text(text)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def create_interview_question_items(
    db: Session,
    report: StageReport,
    questions: list[dict],
    resume_id: Optional[int] = None,
) -> list[InterviewQuestionItem]:
    items: list[InterviewQuestionItem] = []
    for question in questions:
        if isinstance(question, str):
            question_text = question.strip()
            dimension = None
            source = None
            is_required = 1
        elif isinstance(question, dict):
            question_text = str(question.get("question") or question.get("title") or question.get("detail") or "").strip()
            dimension = question.get("dimension") or question.get("category")
            source = question.get("source")
            is_required = 0 if question.get("required") is False else 1
        else:
            continue

        question_hash = compute_interview_question_hash(question_text)
        if not question_text or not question_hash:
            continue
        item = InterviewQuestionItem(
            report_id=report.id,
            candidate_id=report.candidate_id,
            job_id=report.job_id,
            resume_id=resume_id,
            round_type=report.round_type,
            round_no=report.round_no,
            question_text=question_text,
            question_hash=question_hash,
            dimension=str(dimension)[:100] if dimension else None,
            source=str(source)[:100] if source else None,
            is_required=is_required,
        )
        db.add(item)
        items.append(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


def backfill_interview_question_items_from_reports(
    db: Session,
    candidate_id: Optional[int] = None,
) -> int:
    query = db.query(StageReport).filter(
        StageReport.stage_type == constants.STAGE_INTERVIEW_QUESTIONS,
        StageReport.status == constants.REPORT_STATUS_SUCCESS,
        StageReport.deleted == 0,
    )
    if candidate_id:
        query = query.filter(StageReport.candidate_id == candidate_id)

    inserted = 0
    for report in query.order_by(StageReport.created_at.asc()).all():
        exists = db.query(InterviewQuestionItem.id).filter(
            InterviewQuestionItem.report_id == report.id,
            InterviewQuestionItem.deleted == 0,
        ).first()
        if exists:
            continue
        parsed = _load_json(report.report_json, {})
        questions = parsed.get("questions") if isinstance(parsed, dict) else []
        if not isinstance(questions, list):
            continue
        if not getattr(report, "round_type", None) and isinstance(parsed, dict) and parsed.get("round_type"):
            report.round_type = parsed.get("round_type")
        if not getattr(report, "round_no", None) and isinstance(parsed, dict) and parsed.get("round_no"):
            report.round_no = parsed.get("round_no")
        items = create_interview_question_items(db, report, questions, resume_id=report.candidate_id)
        inserted += len(items)
    return inserted


def list_interview_question_reports(
    db: Session,
    candidate_id: int,
    round_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    backfill_interview_question_items_from_reports(db, candidate_id=candidate_id)
    query = db.query(StageReport).filter(
        StageReport.candidate_id == candidate_id,
        StageReport.stage_type == constants.STAGE_INTERVIEW_QUESTIONS,
        StageReport.status == constants.REPORT_STATUS_SUCCESS,
        StageReport.deleted == 0,
    )
    if round_type:
        query = query.filter(StageReport.round_type == round_type)

    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query
        .order_by(StageReport.created_at.desc(), StageReport.report_version.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def list_interview_question_stats(
    db: Session,
    candidate_id: Optional[int] = None,
    job_id: Optional[int] = None,
    round_type: Optional[str] = None,
    dimension: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    backfill_interview_question_items_from_reports(db, candidate_id=candidate_id)
    query = db.query(InterviewQuestionItem).filter(InterviewQuestionItem.deleted == 0)
    if candidate_id:
        query = query.filter(InterviewQuestionItem.candidate_id == candidate_id)
    if job_id:
        query = query.filter(InterviewQuestionItem.job_id == job_id)
    if round_type:
        query = query.filter(InterviewQuestionItem.round_type == round_type)
    if dimension:
        query = query.filter(InterviewQuestionItem.dimension == dimension)

    rows = (
        query.with_entities(
            func.max(InterviewQuestionItem.question_text).label("question"),
            func.count(InterviewQuestionItem.id).label("count"),
            InterviewQuestionItem.round_type.label("round_type"),
            InterviewQuestionItem.dimension.label("dimension"),
            func.max(InterviewQuestionItem.source).label("source"),
            func.max(InterviewQuestionItem.created_at).label("latest_generated_at"),
        )
        .filter(InterviewQuestionItem.question_hash != "")
        .group_by(
            InterviewQuestionItem.question_hash,
            InterviewQuestionItem.round_type,
            InterviewQuestionItem.dimension,
        )
        .order_by(func.count(InterviewQuestionItem.id).desc(), func.max(InterviewQuestionItem.created_at).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "question": row.question,
            "count": int(row.count or 0),
            "round_type": row.round_type,
            "dimension": row.dimension,
            "source": row.source,
            "latest_generated_at": row.latest_generated_at,
        }
        for row in rows
    ]


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


def get_existing_current_report_by_key(
    db: Session,
    candidate_id: int,
    report_key: str,
) -> Optional[StageReport]:
    return (
        db.query(StageReport)
        .filter(
            StageReport.candidate_id == candidate_id,
            StageReport.stage_type == constants.STAGE_CANDIDATE_EVALUATION,
            StageReport.report_key == report_key,
            StageReport.is_current == 1,
            StageReport.status == constants.REPORT_STATUS_SUCCESS,
            StageReport.deleted == 0,
        )
        .order_by(StageReport.report_version.desc(), StageReport.created_at.desc())
        .first()
    )


def get_next_report_version_for_key(db: Session, report_key: str) -> int:
    latest = (
        db.query(StageReport)
        .filter(
            StageReport.stage_type == constants.STAGE_CANDIDATE_EVALUATION,
            StageReport.report_key == report_key,
            StageReport.deleted == 0,
        )
        .order_by(StageReport.report_version.desc(), StageReport.created_at.desc())
        .first()
    )
    return (latest.report_version + 1) if latest else 1


def mark_report_versions_not_current(
    db: Session,
    report_key: str,
    exclude_report_id: Optional[int] = None,
) -> None:
    query = db.query(StageReport).filter(
        StageReport.stage_type == constants.STAGE_CANDIDATE_EVALUATION,
        StageReport.report_key == report_key,
        StageReport.deleted == 0,
    )
    if exclude_report_id:
        query = query.filter(StageReport.id != exclude_report_id)

    for report in query.all():
        report.is_current = 0
        report.updated_at = datetime.now()
    db.commit()


def mark_stage_reports_not_current(
    db: Session,
    candidate_id: int,
    stage_type: str,
    report_key: Optional[str] = None,
    exclude_report_id: Optional[int] = None,
) -> None:
    query = db.query(StageReport).filter(
        StageReport.candidate_id == candidate_id,
        StageReport.stage_type == stage_type,
        StageReport.deleted == 0,
    )
    if report_key:
        query = query.filter(StageReport.report_key == report_key)
    if exclude_report_id:
        query = query.filter(StageReport.id != exclude_report_id)

    for report in query.all():
        report.is_current = 0
        report.updated_at = datetime.now()
    db.commit()


def list_candidate_evaluation_reports(
    db: Session,
    candidate_id: Optional[int] = None,
    job_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
):
    query = db.query(StageReport).filter(
        StageReport.stage_type == constants.STAGE_CANDIDATE_EVALUATION,
        StageReport.deleted == 0,
    )
    if candidate_id:
        query = query.filter(StageReport.candidate_id == candidate_id)
    if job_id:
        query = query.filter(StageReport.job_id == job_id)

    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query
        .order_by(StageReport.created_at.desc(), StageReport.report_version.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


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


# ============== Dashboard 统计 ==============
def get_dashboard_stats(db: Session) -> dict:
    """获取工作台统计数据"""
    open_jobs = db.query(Job).filter(Job.deleted == 0, Job.status == constants.JOB_STATUS_OPEN).count()
    total_candidates = db.query(Candidate).filter(Candidate.deleted == 0).count()
    pending_screening = db.query(Candidate).filter(
        Candidate.deleted == 0, Candidate.current_status == constants.STATUS_RESUME_PENDING
    ).count()
    pending_first_interview = db.query(Candidate).filter(
        Candidate.deleted == 0, Candidate.current_status == constants.STATUS_RESUME_PASSED
    ).count()
    pending_second_interview = db.query(Candidate).filter(
        Candidate.deleted == 0, Candidate.current_status == constants.STATUS_FIRST_INTERVIEW_PASSED
    ).count()
    high_risk = db.query(Candidate).filter(
        Candidate.deleted == 0, Candidate.latest_ai_suggestion == "不建议"
    ).count()

    return {
        "open_jobs": open_jobs,
        "total_candidates": total_candidates,
        "pending_screening": pending_screening,
        "pending_first_interview": pending_first_interview,
        "pending_second_interview": pending_second_interview,
        "high_risk": high_risk,
    }
