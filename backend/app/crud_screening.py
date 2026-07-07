import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app import constants
from app.models import (
    Candidate,
    CandidateProfile,
    CandidateStatusLog,
    Job,
    ResumeFile,
    ScreeningResult,
    ScreeningTask,
    StageReport,
)
from app.services.file_text_extractor import compute_resume_text_hash, extract_resume_identity


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


def _build_job_position_snapshot(job: Job, structured_jd: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_position_id": job.id,
        "job_position_version": job.version or 1,
        "position_name": job.job_name,
        "position_type": job.job_type,
        "department_name": job.department,
        "education_requirement": job.education_req,
        "experience_requirement": job.experience_req,
        "jd_original_text": job.jd_text,
        "jd_structured_json": structured_jd,
        "screening_rules": _load_json(job.screening_rules_json, []),
        "must_have": _load_json(job.must_have_json, []),
        "nice_to_have": _load_json(job.nice_to_have_json, []),
        "risk_points": _load_json(job.risk_points_json, []),
        "interview_questions": _load_json(job.interview_questions_json, []),
        "snapshot_time": datetime.now().isoformat(),
    }


def create_screening_task(db: Session, data: dict) -> ScreeningTask:
    job = None
    if data.get("job_position_id"):
        job = (
            db.query(Job)
            .filter(Job.id == data["job_position_id"], Job.deleted == 0, Job.status != constants.JOB_STATUS_ARCHIVED)
            .first()
        )
        if not job:
            raise ValueError("岗位不存在或已归档")

    structured_jd = data.get("jd_structured_json") if isinstance(data.get("jd_structured_json"), dict) else {}
    if job:
        if not structured_jd:
            structured_jd = _load_json(job.parsed_jd_json, {})
        snapshot = data.get("jd_snapshot_json") if isinstance(data.get("jd_snapshot_json"), dict) else _build_job_position_snapshot(job, structured_jd)
        jd_text = job.jd_text
        job_title = structured_jd.get("job_title") or structured_jd.get("job_name") or job.job_name
        job_type = data.get("job_type") or structured_jd.get("job_type") or job.job_type
        work_location = structured_jd.get("work_location") or structured_jd.get("location") or job.location
        experience_requirement = structured_jd.get("experience_requirement") or structured_jd.get("experience_req") or job.experience_req
        education_requirement = structured_jd.get("education_requirement") or structured_jd.get("education_req") or job.education_req
    else:
        jd_text = data.get("jd_text")
        if not jd_text:
            raise ValueError("请先选择岗位或提供 JD")
        snapshot = data.get("jd_snapshot_json") if isinstance(data.get("jd_snapshot_json"), dict) else None
        job_title = structured_jd.get("job_title") or structured_jd.get("job_name")
        job_type = data.get("job_type") or structured_jd.get("job_type")
        work_location = structured_jd.get("work_location") or structured_jd.get("location")
        experience_requirement = structured_jd.get("experience_requirement") or structured_jd.get("experience_req")
        education_requirement = structured_jd.get("education_requirement") or structured_jd.get("education_req")

    db_task = ScreeningTask(
        task_name=data.get("task_name") or (f"{job.job_name} 初筛" if job else "岗位初筛任务"),
        job_title=job_title,
        job_type=job_type,
        work_location=work_location,
        experience_requirement=experience_requirement,
        education_requirement=education_requirement,
        job_position_id=job.id if job else data.get("job_position_id"),
        job_position_version=(job.version or 1) if job else data.get("job_position_version"),
        jd_text=jd_text,
        jd_structured_json=_dump_json(structured_jd) if structured_jd else None,
        jd_snapshot_json=_dump_json(snapshot) if snapshot else None,
        status=constants.SCREENING_TASK_DRAFT,
    )
    if job:
        job.last_used_time = datetime.now()
        job.updated_at = datetime.now()
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_screening_task(db: Session, task_id: int) -> Optional[ScreeningTask]:
    return db.query(ScreeningTask).filter(ScreeningTask.id == task_id, ScreeningTask.deleted == 0).first()


def list_screening_tasks(
    db: Session,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    job_position_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    query = db.query(ScreeningTask).filter(ScreeningTask.deleted == 0)

    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                ScreeningTask.task_name.ilike(pattern),
                ScreeningTask.job_title.ilike(pattern),
                ScreeningTask.job_type.ilike(pattern),
            )
        )
    if status:
        query = query.filter(ScreeningTask.status == status)
    if job_position_id:
        query = query.filter(ScreeningTask.job_position_id == job_position_id)

    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query
        .order_by(ScreeningTask.updated_at.desc(), ScreeningTask.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def update_task_from_parsed_jd(db: Session, task: ScreeningTask, parsed_jd: Dict[str, Any]) -> ScreeningTask:
    task.job_title = parsed_jd.get("job_title") or parsed_jd.get("job_name") or task.job_title
    task.job_type = parsed_jd.get("job_type") or task.job_type
    task.work_location = parsed_jd.get("work_location") or parsed_jd.get("location") or task.work_location
    task.experience_requirement = parsed_jd.get("experience_requirement") or parsed_jd.get("experience_req") or task.experience_requirement
    task.education_requirement = parsed_jd.get("education_requirement") or parsed_jd.get("education_req") or task.education_requirement
    task.jd_structured_json = json.dumps(parsed_jd, ensure_ascii=False)
    task.updated_at = datetime.now()
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task: ScreeningTask, status: str) -> ScreeningTask:
    task.status = status
    task.updated_at = datetime.now()
    db.commit()
    db.refresh(task)
    return task


def create_resume_file_record(
    db: Session,
    task_id: int,
    file_name: str,
    file_type: str,
    file_hash: str,
    raw_text: Optional[str],
    parse_status: str,
    parse_error_message: Optional[str] = None,
    text_hash: Optional[str] = None,
    reuse_source: Optional[str] = None,
    reused_resume_file_id: Optional[int] = None,
    reused_profile_id: Optional[int] = None,
) -> ResumeFile:
    db_file = ResumeFile(
        task_id=task_id,
        file_name=file_name,
        file_type=file_type,
        file_hash=file_hash,
        text_hash=text_hash,
        reuse_source=reuse_source,
        reused_resume_file_id=reused_resume_file_id,
        reused_profile_id=reused_profile_id,
        raw_text=raw_text,
        parse_status=parse_status,
        parse_error_message=parse_error_message,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_resume_file(db: Session, resume_file_id: int) -> Optional[ResumeFile]:
    return db.query(ResumeFile).filter(ResumeFile.id == resume_file_id, ResumeFile.deleted == 0).first()


def get_resume_files(db: Session, task_id: int):
    return (
        db.query(ResumeFile)
        .filter(ResumeFile.task_id == task_id, ResumeFile.deleted == 0)
        .order_by(ResumeFile.created_at.asc())
        .all()
    )


def list_resume_parse_records(
    db: Session,
    keyword: Optional[str] = None,
    parse_status: Optional[str] = None,
    reuse_source: Optional[str] = None,
    task_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    query = (
        db.query(ResumeFile, ScreeningTask, CandidateProfile, ScreeningResult, Job)
        .join(ScreeningTask, ResumeFile.task_id == ScreeningTask.id)
        .outerjoin(CandidateProfile, CandidateProfile.resume_file_id == ResumeFile.id)
        .outerjoin(
            ScreeningResult,
            and_(
                ScreeningResult.resume_file_id == ResumeFile.id,
                ScreeningResult.deleted == 0,
            ),
        )
        .outerjoin(Job, ScreeningTask.job_position_id == Job.id)
        .filter(ResumeFile.deleted == 0, ScreeningTask.deleted == 0)
    )

    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                ResumeFile.file_name.ilike(pattern),
                ScreeningTask.task_name.ilike(pattern),
                ScreeningTask.job_title.ilike(pattern),
                CandidateProfile.name.ilike(pattern),
                CandidateProfile.phone.ilike(pattern),
                CandidateProfile.email.ilike(pattern),
                Job.job_name.ilike(pattern),
            )
        )
    if parse_status:
        query = query.filter(ResumeFile.parse_status == parse_status)
    if reuse_source:
        query = query.filter(ResumeFile.reuse_source == reuse_source)
    if task_id:
        query = query.filter(ResumeFile.task_id == task_id)

    total = query.count()
    rows = (
        query
        .order_by(ResumeFile.updated_at.desc(), ResumeFile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            _build_resume_parse_record_row(resume_file, task, profile, result)
            for resume_file, task, profile, result, _job in rows
        ],
    }


def get_resume_parse_record_detail(db: Session, resume_file_id: int) -> Optional[Dict[str, Any]]:
    row = (
        db.query(ResumeFile, ScreeningTask, CandidateProfile, ScreeningResult, Job)
        .join(ScreeningTask, ResumeFile.task_id == ScreeningTask.id)
        .outerjoin(CandidateProfile, CandidateProfile.resume_file_id == ResumeFile.id)
        .outerjoin(
            ScreeningResult,
            and_(
                ScreeningResult.resume_file_id == ResumeFile.id,
                ScreeningResult.deleted == 0,
            ),
        )
        .outerjoin(Job, ScreeningTask.job_position_id == Job.id)
        .filter(
            ResumeFile.id == resume_file_id,
            ResumeFile.deleted == 0,
            ScreeningTask.deleted == 0,
        )
        .first()
    )
    if not row:
        return None

    resume_file, task, profile, result, job = row
    job_position = None
    if job:
        job_position = {
            "id": job.id,
            "position_name": job.job_name,
            "position_type": job.job_type,
            "department_name": job.department,
            "education_requirement": job.education_req,
            "experience_requirement": job.experience_req,
            "version": job.version or 1,
            "status": job.status,
        }

    return {
        "resume_file": resume_file,
        "task": task,
        "job_position": job_position,
        "candidate_profile": profile,
        "screening_result": _build_screening_result_payload(result) if result else None,
    }


def update_resume_file(
    db: Session,
    resume_file: ResumeFile,
    parse_status: Optional[str] = None,
    parse_error_message: Optional[str] = None,
    raw_text: Optional[str] = None,
    text_hash: Optional[str] = None,
    reuse_source: Optional[str] = None,
    reused_resume_file_id: Optional[int] = None,
    reused_profile_id: Optional[int] = None,
) -> ResumeFile:
    if parse_status:
        resume_file.parse_status = parse_status
    resume_file.parse_error_message = parse_error_message
    if raw_text is not None:
        resume_file.raw_text = raw_text
    if text_hash is not None:
        resume_file.text_hash = text_hash
    if reuse_source is not None:
        resume_file.reuse_source = reuse_source
    if reused_resume_file_id is not None:
        resume_file.reused_resume_file_id = reused_resume_file_id
    if reused_profile_id is not None:
        resume_file.reused_profile_id = reused_profile_id
    resume_file.updated_at = datetime.now()
    db.commit()
    db.refresh(resume_file)
    return resume_file


def upsert_candidate_profile(
    db: Session,
    resume_file_id: int,
    parsed_resume: Dict[str, Any],
    data_source: str = "resume_parse",
) -> CandidateProfile:
    db_profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.resume_file_id == resume_file_id)
        .first()
    )
    if not db_profile:
        db_profile = CandidateProfile(resume_file_id=resume_file_id)
        db.add(db_profile)

    work_experience = parsed_resume.get("work_experience") if isinstance(parsed_resume.get("work_experience"), list) else []
    project_experience = parsed_resume.get("project_experience") if isinstance(parsed_resume.get("project_experience"), list) else []
    skills = parsed_resume.get("skills") if isinstance(parsed_resume.get("skills"), list) else []
    past_companies = parsed_resume.get("past_companies") if isinstance(parsed_resume.get("past_companies"), list) else []

    db_profile.name = parsed_resume.get("name") or "简历未体现"
    db_profile.phone = parsed_resume.get("phone") or ""
    db_profile.email = parsed_resume.get("email") or ""
    db_profile.gender = parsed_resume.get("gender") or ""
    db_profile.age = str(parsed_resume.get("age") or "")
    db_profile.city = parsed_resume.get("city") or parsed_resume.get("current_city") or ""
    db_profile.expected_city = parsed_resume.get("expected_city") or ""
    db_profile.education = parsed_resume.get("education") or parsed_resume.get("education_level") or ""
    db_profile.school = parsed_resume.get("school") or parsed_resume.get("graduation_school") or ""
    db_profile.major = parsed_resume.get("major") or ""
    db_profile.graduation_year = parsed_resume.get("graduation_year") or ""
    db_profile.work_years = str(parsed_resume.get("work_years") or "")
    db_profile.latest_company = parsed_resume.get("latest_company") or ""
    db_profile.latest_position = parsed_resume.get("latest_position") or ""
    db_profile.past_companies = json.dumps(past_companies, ensure_ascii=False)
    db_profile.skills_json = json.dumps(skills, ensure_ascii=False)
    db_profile.work_experience_json = json.dumps(work_experience, ensure_ascii=False)
    db_profile.project_experience_json = json.dumps(project_experience, ensure_ascii=False)
    db_profile.industry_experience = parsed_resume.get("industry_experience") or ""
    db_profile.salary_expectation = parsed_resume.get("salary_expectation") or parsed_resume.get("expected_salary") or ""
    db_profile.available_time = parsed_resume.get("available_time") or parsed_resume.get("available_date") or ""
    db_profile.profile_json = json.dumps(parsed_resume, ensure_ascii=False)
    db_profile.data_source = data_source
    db_profile.updated_at = datetime.now()

    db.commit()
    db.refresh(db_profile)
    return db_profile


def upsert_screening_result(
    db: Session,
    task_id: int,
    candidate_id: int,
    resume_file_id: int,
    result: Dict[str, Any],
    result_source: str = constants.SCREENING_RESULT_SOURCE_AI,
    reused_from_result_id: Optional[int] = None,
) -> ScreeningResult:
    db_result = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.resume_file_id == resume_file_id, ScreeningResult.deleted == 0)
        .first()
    )
    if not db_result:
        db_result = ScreeningResult(
            task_id=task_id,
            candidate_id=candidate_id,
            resume_file_id=resume_file_id,
        )
        db.add(db_result)

    conclusion = result.get("conclusion") or constants.SCREENING_CONCLUSION_PENDING
    db_result.score = result.get("score")
    db_result.conclusion = conclusion
    db_result.match_highlights_json = json.dumps(result.get("match_highlights") or [], ensure_ascii=False)
    db_result.risk_points_json = json.dumps(result.get("risk_points") or [], ensure_ascii=False)
    db_result.interview_questions_json = json.dumps(result.get("interview_questions") or [], ensure_ascii=False)
    db_result.dimension_scores_json = json.dumps(result.get("dimension_scores") or {}, ensure_ascii=False)
    db_result.confidence = result.get("confidence")
    db_result.ai_reason = result.get("ai_reason") or ""
    db_result.status = conclusion
    db_result.result_source = result_source
    db_result.reused_from_result_id = reused_from_result_id
    db_result.updated_at = datetime.now()

    db.commit()
    db.refresh(db_result)
    _sync_screening_result_to_candidate_library(db, db_result, result)
    return db_result


def find_reusable_resume_profile(
    db: Session,
    resume_file: ResumeFile,
) -> Optional[Tuple[ResumeFile, CandidateProfile, str]]:
    if not resume_file.raw_text:
        return None

    if resume_file.file_hash:
        match = _find_profile_by_resume_file(
            db,
            ResumeFile.file_hash == resume_file.file_hash,
            resume_file.id,
        )
        if match:
            return match[0], match[1], constants.RESUME_REUSE_SOURCE_FILE_HASH

    text_hash = resume_file.text_hash or compute_resume_text_hash(resume_file.raw_text)
    if text_hash:
        match = _find_profile_by_resume_file(
            db,
            ResumeFile.text_hash == text_hash,
            resume_file.id,
        )
        if match:
            return match[0], match[1], constants.RESUME_REUSE_SOURCE_TEXT_HASH

        # 兼容旧数据：历史 resume_files 可能没有 text_hash，但保留了 raw_text。
        legacy_files = (
            db.query(ResumeFile, CandidateProfile)
            .join(CandidateProfile, CandidateProfile.resume_file_id == ResumeFile.id)
            .filter(
                ResumeFile.id != resume_file.id,
                ResumeFile.deleted == 0,
                ResumeFile.raw_text.isnot(None),
                CandidateProfile.profile_json.isnot(None),
            )
            .order_by(ResumeFile.updated_at.desc())
            .all()
        )
        for source_file, source_profile in legacy_files:
            if compute_resume_text_hash(source_file.raw_text or "") == text_hash:
                return source_file, source_profile, constants.RESUME_REUSE_SOURCE_TEXT_HASH

    identity = extract_resume_identity(resume_file.raw_text)
    identity_filters = []
    if identity.get("phone"):
        identity_filters.append(CandidateProfile.phone == identity["phone"])
    if identity.get("email"):
        identity_filters.append(CandidateProfile.email == identity["email"])
    if not identity_filters:
        return None

    match = (
        db.query(ResumeFile, CandidateProfile)
        .join(CandidateProfile, CandidateProfile.resume_file_id == ResumeFile.id)
        .filter(
            ResumeFile.id != resume_file.id,
            ResumeFile.deleted == 0,
            CandidateProfile.profile_json.isnot(None),
            or_(*identity_filters),
        )
        .order_by(ResumeFile.updated_at.desc())
        .first()
    )
    if not match:
        return None
    return match[0], match[1], constants.RESUME_REUSE_SOURCE_IDENTITY


def _find_profile_by_resume_file(
    db: Session,
    resume_filter,
    exclude_resume_file_id: int,
) -> Optional[Tuple[ResumeFile, CandidateProfile]]:
    match = (
        db.query(ResumeFile, CandidateProfile)
        .join(CandidateProfile, CandidateProfile.resume_file_id == ResumeFile.id)
        .filter(
            ResumeFile.id != exclude_resume_file_id,
            ResumeFile.deleted == 0,
            CandidateProfile.profile_json.isnot(None),
            resume_filter,
        )
        .order_by(ResumeFile.updated_at.desc())
        .first()
    )
    if not match:
        return None
    return match[0], match[1]


def reuse_candidate_profile_from_history(
    db: Session,
    resume_file: ResumeFile,
    source_file: ResumeFile,
    source_profile: CandidateProfile,
    reuse_source: str,
) -> Tuple[CandidateProfile, Dict[str, Any]]:
    parsed_resume = _load_json(source_profile.profile_json, {})
    parsed_resume.setdefault("resume_text", resume_file.raw_text or source_file.raw_text or "")
    profile = upsert_candidate_profile(
        db,
        resume_file_id=resume_file.id,
        parsed_resume=parsed_resume,
        data_source=f"resume_reuse:{reuse_source}",
    )
    update_resume_file(
        db,
        resume_file,
        parse_status=constants.RESUME_FILE_SCREENING,
        parse_error_message=_resume_reuse_message(reuse_source),
        reuse_source=reuse_source,
        reused_resume_file_id=source_file.id,
        reused_profile_id=source_profile.id,
    )
    return profile, parsed_resume


def find_reusable_screening_result(
    db: Session,
    task: ScreeningTask,
    resume_file: ResumeFile,
) -> Optional[ScreeningResult]:
    identity_filters = []
    if resume_file.text_hash:
        identity_filters.append(ResumeFile.text_hash == resume_file.text_hash)
    if resume_file.file_hash:
        identity_filters.append(ResumeFile.file_hash == resume_file.file_hash)
    if not identity_filters:
        return None

    query = (
        db.query(ScreeningResult)
        .join(ResumeFile, ScreeningResult.resume_file_id == ResumeFile.id)
        .join(ScreeningTask, ScreeningResult.task_id == ScreeningTask.id)
        .filter(
            ScreeningResult.deleted == 0,
            ScreeningResult.resume_file_id != resume_file.id,
            ResumeFile.deleted == 0,
            ScreeningTask.deleted == 0,
            or_(*identity_filters),
        )
    )
    if task.job_position_id:
        query = query.filter(
            ScreeningTask.job_position_id == task.job_position_id,
            ScreeningTask.job_position_version == task.job_position_version,
        )
    else:
        query = query.filter(
            ScreeningTask.job_position_id.is_(None),
            ScreeningTask.jd_text == task.jd_text,
        )
    return query.order_by(ScreeningResult.updated_at.desc()).first()


def copy_screening_result_from_history(
    db: Session,
    task_id: int,
    candidate_id: int,
    resume_file_id: int,
    source_result: ScreeningResult,
) -> ScreeningResult:
    return upsert_screening_result(
        db,
        task_id=task_id,
        candidate_id=candidate_id,
        resume_file_id=resume_file_id,
        result=_screening_result_to_payload(source_result),
        result_source=constants.SCREENING_RESULT_SOURCE_REUSED,
        reused_from_result_id=source_result.id,
    )


def _screening_result_to_payload(result: ScreeningResult) -> Dict[str, Any]:
    return {
        "score": result.score,
        "conclusion": result.conclusion,
        "confidence": result.confidence,
        "ai_reason": result.ai_reason,
        "match_highlights": _load_json(result.match_highlights_json, []),
        "risk_points": _load_json(result.risk_points_json, []),
        "interview_questions": _load_json(result.interview_questions_json, []),
        "dimension_scores": _load_json(result.dimension_scores_json, {}),
    }


def _resume_reuse_message(reuse_source: str) -> str:
    labels = {
        constants.RESUME_REUSE_SOURCE_FILE_HASH: "复用历史简历解析结果：文件完全一致",
        constants.RESUME_REUSE_SOURCE_TEXT_HASH: "复用历史简历解析结果：简历内容一致",
        constants.RESUME_REUSE_SOURCE_IDENTITY: "复用历史简历解析结果：手机号或邮箱一致",
    }
    return labels.get(reuse_source, "复用历史简历解析结果")


def _sync_screening_result_to_candidate_library(
    db: Session,
    db_result: ScreeningResult,
    result: Dict[str, Any],
) -> Optional[Candidate]:
    task = get_screening_task(db, db_result.task_id)
    resume_file = get_resume_file(db, db_result.resume_file_id)
    profile = get_candidate_profile(db, db_result.candidate_id)
    if not task or not resume_file or not profile:
        return None
    if not task.job_position_id:
        return None
    if not resume_file.raw_text:
        return None

    job = (
        db.query(Job)
        .filter(Job.id == task.job_position_id, Job.deleted == 0)
        .first()
    )
    if not job:
        return None

    parsed_resume = _load_json(profile.profile_json, {})
    candidate = _find_existing_candidate_for_profile(db, job.id, profile, resume_file.raw_text)
    is_new = candidate is None
    from_status = candidate.current_status if candidate else None

    if not candidate:
        candidate = Candidate(job_id=job.id, candidate_name=profile.name or "简历未体现", resume_text=resume_file.raw_text)
        db.add(candidate)

    candidate.candidate_name = profile.name or "简历未体现"
    candidate.phone = profile.phone or None
    candidate.email = profile.email or None
    candidate.source = "岗位初筛导入"
    candidate.resume_text = resume_file.raw_text
    candidate.resume_match_score = result.get("score")
    candidate.latest_ai_suggestion = _screening_suggestion(result.get("conclusion"))
    candidate.gender = profile.gender or None
    candidate.age = _parse_int_or_none(profile.age)
    candidate.current_city = profile.city or None
    candidate.expected_city = profile.expected_city or None
    candidate.available_date = profile.available_time or None
    candidate.expected_salary = profile.salary_expectation or None
    candidate.education_level = profile.education or None
    candidate.graduation_school = profile.school or None
    candidate.major = profile.major or None
    candidate.work_years = _parse_int_or_none(profile.work_years)
    candidate.parsed_resume_json = profile.profile_json or json.dumps(parsed_resume, ensure_ascii=False)

    if is_new or _can_move_to_waiting_interview(candidate.current_status):
        candidate.current_status = constants.STATUS_INTERVIEW_WAITING
        candidate.current_round_no = None
        candidate.final_conclusion = None

    candidate.updated_at = datetime.now()
    db.commit()
    db.refresh(candidate)

    if is_new or from_status != candidate.current_status:
        _log_candidate_status_change(
            db=db,
            candidate_id=candidate.id,
            from_status=from_status,
            to_status=candidate.current_status,
            reason="岗位初筛完成，进入待安排面试",
        )

    _upsert_resume_screening_stage_report(
        db=db,
        candidate=candidate,
        job=job,
        resume_text=resume_file.raw_text,
        result=result,
    )
    return candidate


def _find_existing_candidate_for_profile(
    db: Session,
    job_id: int,
    profile: CandidateProfile,
    resume_text: str,
) -> Optional[Candidate]:
    query = db.query(Candidate).filter(Candidate.job_id == job_id, Candidate.deleted == 0)
    identity_filters = []
    if profile.phone:
        identity_filters.append(Candidate.phone == profile.phone)
    if profile.email:
        identity_filters.append(Candidate.email == profile.email)
    if identity_filters:
        existing = query.filter(or_(*identity_filters)).order_by(Candidate.updated_at.desc()).first()
        if existing:
            return existing

    if profile.name:
        return (
            query.filter(
                Candidate.candidate_name == profile.name,
                Candidate.resume_text == resume_text,
            )
            .order_by(Candidate.updated_at.desc())
            .first()
        )
    return None


def _can_move_to_waiting_interview(status: Optional[str]) -> bool:
    return status in {
        constants.STATUS_IMPORTED,
        constants.STATUS_RESUME_IMPORTED,
        constants.STATUS_RESUME_PARSING,
        constants.STATUS_RESUME_PARSE_FAILED,
        constants.STATUS_RESUME_PENDING,
        constants.STATUS_RESUME_SCREENING,
        constants.STATUS_RESUME_SCREENING_DONE,
        constants.STATUS_RESUME_PASSED,
        constants.STATUS_RESUME_TBD,
        constants.STATUS_RESUME_REJECTED,
    }


def _log_candidate_status_change(
    db: Session,
    candidate_id: int,
    from_status: Optional[str],
    to_status: str,
    reason: Optional[str] = None,
) -> None:
    db.add(
        CandidateStatusLog(
            candidate_id=candidate_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
        )
    )
    db.commit()


def _upsert_resume_screening_stage_report(
    db: Session,
    candidate: Candidate,
    job: Job,
    resume_text: str,
    result: Dict[str, Any],
) -> Optional[StageReport]:
    content_hash = _content_hash(job.jd_text, resume_text)
    existing = (
        db.query(StageReport)
        .filter(
            StageReport.candidate_id == candidate.id,
            StageReport.stage_type == constants.STAGE_RESUME_SCREENING,
            StageReport.content_hash == content_hash,
            StageReport.status == constants.REPORT_STATUS_SUCCESS,
            StageReport.deleted == 0,
        )
        .order_by(StageReport.created_at.desc())
        .first()
    )
    if existing:
        return existing

    latest = (
        db.query(StageReport)
        .filter(
            StageReport.candidate_id == candidate.id,
            StageReport.stage_type == constants.STAGE_RESUME_SCREENING,
            StageReport.deleted == 0,
        )
        .order_by(StageReport.report_version.desc())
        .first()
    )
    report = StageReport(
        candidate_id=candidate.id,
        job_id=job.id,
        stage_type=constants.STAGE_RESUME_SCREENING,
        report_version=(latest.report_version + 1) if latest else 1,
        score=result.get("score"),
        suggestion=_screening_suggestion(result.get("conclusion")),
        risk_level=_screening_risk_level(result),
        report_json=json.dumps(_build_stage_report_json(result), ensure_ascii=False),
        input_snapshot_json=json.dumps(
            {
                "jd_text": job.jd_text,
                "resume_text": resume_text,
                "candidate_name": candidate.candidate_name,
                "job_name": job.job_name,
                "source": "screening_task",
            },
            ensure_ascii=False,
        ),
        content_hash=content_hash,
        status=constants.REPORT_STATUS_SUCCESS,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _build_stage_report_json(result: Dict[str, Any]) -> Dict[str, Any]:
    risk_level = _screening_risk_level(result)
    return {
        "stage": constants.STAGE_RESUME_SCREENING,
        "score": result.get("score"),
        "suggestion": _screening_suggestion(result.get("conclusion")),
        "risk_level": risk_level,
        "summary": result.get("ai_reason") or constants.SCREENING_CONCLUSION_LABELS.get(result.get("conclusion"), ""),
        "strengths": [
            {"title": item, "detail": item, "evidence": ""}
            for item in (result.get("match_highlights") or [])
        ],
        "mismatches": [],
        "risk_points": [
            {"risk": item, "level": risk_level, "detail": item}
            for item in (result.get("risk_points") or [])
        ],
        "follow_up_questions": [
            {"question": item, "purpose": "初筛建议追问"}
            for item in (result.get("interview_questions") or [])
        ],
        "task_screening": {
            "conclusion": result.get("conclusion"),
            "confidence": result.get("confidence"),
            "dimension_scores": result.get("dimension_scores") or {},
        },
    }


def _screening_suggestion(conclusion: Optional[str]) -> str:
    if conclusion == constants.SCREENING_CONCLUSION_RECOMMENDED:
        return "建议约初试"
    if conclusion == constants.SCREENING_CONCLUSION_REJECTED:
        return "建议淘汰"
    return "人才库储备"


def _screening_risk_level(result: Dict[str, Any]) -> str:
    dimensions = result.get("dimension_scores") if isinstance(result.get("dimension_scores"), dict) else {}
    overall_risk = _parse_int_or_none(dimensions.get("overall_risk"))
    if overall_risk is not None:
        if overall_risk >= 70:
            return "高"
        if overall_risk >= 40:
            return "中"
        return "低"
    conclusion = result.get("conclusion")
    if conclusion == constants.SCREENING_CONCLUSION_REJECTED:
        return "高"
    if conclusion == constants.SCREENING_CONCLUSION_PENDING:
        return "中"
    return "低"


def _content_hash(*parts: str) -> str:
    combined = "|".join(part or "" for part in parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def _parse_int_or_none(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    text = str(value).strip().replace("年", "")
    digits = ""
    for char in text:
        if char.isdigit():
            digits += char
        elif digits:
            break
    if not digits:
        return None
    return int(digits)


def get_screening_result(db: Session, result_id: int) -> Optional[ScreeningResult]:
    return db.query(ScreeningResult).filter(ScreeningResult.id == result_id, ScreeningResult.deleted == 0).first()


def sync_all_screening_results_to_candidate_library(db: Session, task_id: Optional[int] = None) -> int:
    query = db.query(ScreeningResult).filter(ScreeningResult.deleted == 0)
    if task_id:
        query = query.filter(ScreeningResult.task_id == task_id)

    synced_count = 0
    for db_result in query.order_by(ScreeningResult.created_at.asc()).all():
        result_payload = {
            "score": db_result.score,
            "conclusion": db_result.conclusion,
            "confidence": db_result.confidence,
            "ai_reason": db_result.ai_reason,
            "match_highlights": _load_json(db_result.match_highlights_json, []),
            "risk_points": _load_json(db_result.risk_points_json, []),
            "interview_questions": _load_json(db_result.interview_questions_json, []),
            "dimension_scores": _load_json(db_result.dimension_scores_json, {}),
        }
        if _sync_screening_result_to_candidate_library(db, db_result, result_payload):
            synced_count += 1
    return synced_count


def get_candidate_profile(db: Session, candidate_id: int) -> Optional[CandidateProfile]:
    return db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()


def update_screening_result_status(db: Session, result_id: int, status: str) -> Optional[ScreeningResult]:
    if status not in constants.VALID_SCREENING_RESULT_STATUSES:
        return None
    db_result = get_screening_result(db, result_id)
    if not db_result:
        return None
    db_result.status = status
    db_result.updated_at = datetime.now()
    db.commit()
    db.refresh(db_result)
    refresh_screening_task_counts(db, db_result.task_id)
    return db_result


def refresh_screening_task_counts(db: Session, task_id: int) -> Optional[ScreeningTask]:
    task = get_screening_task(db, task_id)
    if not task:
        return None

    files = get_resume_files(db, task_id)
    results = db.query(ScreeningResult).filter(ScreeningResult.task_id == task_id, ScreeningResult.deleted == 0).all()

    task.total_resume_count = len(files)
    task.parsed_success_count = sum(1 for item in files if item.parse_status == constants.RESUME_FILE_COMPLETED)
    task.parsed_failed_count = sum(1 for item in files if item.parse_status == constants.RESUME_FILE_FAILED)
    task.recommended_count = sum(1 for item in results if item.conclusion == constants.SCREENING_CONCLUSION_RECOMMENDED)
    task.pending_count = sum(1 for item in results if item.conclusion == constants.SCREENING_CONCLUSION_PENDING)
    task.rejected_count = sum(1 for item in results if item.conclusion == constants.SCREENING_CONCLUSION_REJECTED)
    task.updated_at = datetime.now()
    db.commit()
    db.refresh(task)
    return task


def list_screening_result_items(db: Session, task_id: int, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    filters = filters or {}
    task = get_screening_task(db, task_id)
    if not task:
        return {"total": 0, "items": []}

    files = get_resume_files(db, task_id)
    results = {
        item.resume_file_id: item
        for item in db.query(ScreeningResult).filter(ScreeningResult.task_id == task_id, ScreeningResult.deleted == 0).all()
    }
    profiles = {
        item.resume_file_id: item
        for item in db.query(CandidateProfile)
        .join(ResumeFile, CandidateProfile.resume_file_id == ResumeFile.id)
        .filter(ResumeFile.task_id == task_id, ResumeFile.deleted == 0)
        .all()
    }

    rows = []
    for resume_file in files:
        result = results.get(resume_file.id)
        profile = profiles.get(resume_file.id)
        if result and profile:
            rows.append(_build_result_row(task, resume_file, profile, result))
        elif resume_file.parse_status == constants.RESUME_FILE_FAILED:
            rows.append(_build_failed_row(task, resume_file))

    rows = _apply_filters(rows, filters)
    scored_rows = [row for row in rows if row.get("score") is not None]
    scored_rows.sort(key=lambda row: row.get("score") or 0, reverse=True)
    failed_rows = [row for row in rows if row.get("score") is None]

    ranked = []
    for index, row in enumerate(scored_rows, start=1):
        row["rank"] = index
        ranked.append(row)
    ranked.extend(failed_rows)
    return {"total": len(ranked), "items": ranked}


def build_screening_result_detail(db: Session, result_id: int) -> Optional[Dict[str, Any]]:
    result = get_screening_result(db, result_id)
    if not result:
        return None
    task = get_screening_task(db, result.task_id)
    resume_file = get_resume_file(db, result.resume_file_id)
    profile = get_candidate_profile(db, result.candidate_id)
    if not task or not resume_file or not profile:
        return None

    result_payload = {
        "id": result.id,
        "task_id": result.task_id,
        "candidate_id": result.candidate_id,
        "resume_file_id": result.resume_file_id,
        "score": result.score,
        "conclusion": result.conclusion,
        "conclusion_label": constants.SCREENING_CONCLUSION_LABELS.get(result.conclusion, result.conclusion),
        "status": result.status,
        "match_highlights": _load_json(result.match_highlights_json, []),
        "risk_points": _load_json(result.risk_points_json, []),
        "interview_questions": _load_json(result.interview_questions_json, []),
        "dimension_scores": _load_json(result.dimension_scores_json, {}),
        "confidence": result.confidence,
        "ai_reason": result.ai_reason,
        "result_source": result.result_source,
        "reused_from_result_id": result.reused_from_result_id,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
    }
    return {
        "task": task,
        "resume_file": resume_file,
        "candidate_profile": profile,
        "result": result_payload,
    }


def _build_resume_parse_record_row(
    resume_file: ResumeFile,
    task: ScreeningTask,
    profile: Optional[CandidateProfile],
    result: Optional[ScreeningResult],
) -> Dict[str, Any]:
    return {
        "id": resume_file.id,
        "task_id": resume_file.task_id,
        "task_name": task.task_name,
        "job_title": task.job_title,
        "job_position_id": task.job_position_id,
        "job_position_version": task.job_position_version,
        "file_name": resume_file.file_name,
        "file_type": resume_file.file_type,
        "file_hash": resume_file.file_hash,
        "text_hash": resume_file.text_hash,
        "parse_status": resume_file.parse_status,
        "parse_error_message": resume_file.parse_error_message,
        "reuse_source": resume_file.reuse_source,
        "reused_resume_file_id": resume_file.reused_resume_file_id,
        "reused_profile_id": resume_file.reused_profile_id,
        "candidate_profile_id": profile.id if profile else None,
        "candidate_name": profile.name if profile else None,
        "phone": profile.phone if profile else None,
        "email": profile.email if profile else None,
        "education": profile.education if profile else None,
        "work_years": profile.work_years if profile else None,
        "latest_company": profile.latest_company if profile else None,
        "latest_position": profile.latest_position if profile else None,
        "screening_result_id": result.id if result else None,
        "screening_score": result.score if result else None,
        "screening_conclusion": result.conclusion if result else None,
        "screening_status": result.status if result else None,
        "result_source": result.result_source if result else None,
        "reused_from_result_id": result.reused_from_result_id if result else None,
        "created_at": resume_file.created_at,
        "updated_at": resume_file.updated_at,
    }


def _build_screening_result_payload(result: ScreeningResult) -> Dict[str, Any]:
    return {
        "id": result.id,
        "task_id": result.task_id,
        "candidate_id": result.candidate_id,
        "resume_file_id": result.resume_file_id,
        "score": result.score,
        "conclusion": result.conclusion,
        "conclusion_label": constants.SCREENING_CONCLUSION_LABELS.get(result.conclusion, result.conclusion),
        "status": result.status,
        "match_highlights": _load_json(result.match_highlights_json, []),
        "risk_points": _load_json(result.risk_points_json, []),
        "interview_questions": _load_json(result.interview_questions_json, []),
        "dimension_scores": _load_json(result.dimension_scores_json, {}),
        "confidence": result.confidence,
        "ai_reason": result.ai_reason,
        "result_source": result.result_source,
        "reused_from_result_id": result.reused_from_result_id,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
    }


def _build_result_row(task: ScreeningTask, resume_file: ResumeFile, profile: CandidateProfile, result: ScreeningResult) -> Dict[str, Any]:
    return {
        "row_type": "result",
        "rank": None,
        "task_id": task.id,
        "resume_file_id": resume_file.id,
        "result_id": result.id,
        "candidate_id": profile.id,
        "file_name": resume_file.file_name,
        "parse_status": resume_file.parse_status,
        "parse_error_message": resume_file.parse_error_message,
        "candidate_name": profile.name or "简历未体现",
        "latest_position": profile.latest_position or "简历未体现",
        "work_years": profile.work_years or "简历未体现",
        "education": profile.education or "简历未体现",
        "city": profile.city or "简历未体现",
        "score": result.score,
        "conclusion": result.conclusion,
        "conclusion_label": constants.SCREENING_CONCLUSION_LABELS.get(result.conclusion, result.conclusion),
        "status": result.status,
        "match_highlights": _load_json(result.match_highlights_json, []),
        "risk_points": _load_json(result.risk_points_json, []),
        "result_source": result.result_source,
        "reused_from_result_id": result.reused_from_result_id,
        "job_type": task.job_type,
        "updated_at": result.updated_at,
    }


def _build_failed_row(task: ScreeningTask, resume_file: ResumeFile) -> Dict[str, Any]:
    return {
        "row_type": "failed",
        "rank": None,
        "task_id": task.id,
        "resume_file_id": resume_file.id,
        "result_id": None,
        "candidate_id": None,
        "file_name": resume_file.file_name,
        "parse_status": resume_file.parse_status,
        "parse_error_message": resume_file.parse_error_message,
        "candidate_name": "解析失败",
        "latest_position": None,
        "work_years": None,
        "education": None,
        "city": None,
        "score": None,
        "conclusion": None,
        "conclusion_label": "解析失败",
        "status": constants.RESUME_FILE_FAILED,
        "match_highlights": [],
        "risk_points": [resume_file.parse_error_message] if resume_file.parse_error_message else [],
        "job_type": task.job_type,
        "updated_at": resume_file.updated_at,
    }


def _apply_filters(rows: list, filters: Dict[str, Any]) -> list:
    conclusion = filters.get("conclusion")
    if conclusion:
        rows = [row for row in rows if row.get("conclusion") == conclusion]

    parse_status = filters.get("parse_status")
    if parse_status:
        rows = [row for row in rows if row.get("parse_status") == parse_status]

    job_type = filters.get("job_type")
    if job_type:
        rows = [row for row in rows if row.get("job_type") == job_type]

    education = filters.get("education")
    if education:
        rows = [row for row in rows if education in str(row.get("education") or "")]

    score_min = filters.get("score_min")
    if score_min is not None:
        rows = [row for row in rows if row.get("score") is not None and row["score"] >= int(score_min)]

    score_max = filters.get("score_max")
    if score_max is not None:
        rows = [row for row in rows if row.get("score") is not None and row["score"] <= int(score_max)]

    work_years_min = filters.get("work_years_min")
    if work_years_min is not None:
        rows = [row for row in rows if _parse_years(row.get("work_years")) >= float(work_years_min)]

    return rows


def _load_json(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _parse_years(value: Any) -> float:
    if value in (None, "", "简历未体现"):
        return 0
    try:
        return float(str(value).replace("年", "").strip())
    except ValueError:
        return 0
