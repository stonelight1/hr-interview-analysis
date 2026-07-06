from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

from app.database import engine, Base, get_db
from app.schemas import AnalysisCreate, AnalysisResponse, AnalysisDetailResponse, AnalysisListResponse, AnalysisFilter
from app.crud import create_analysis, get_analysis, get_analysis_list, delete_analysis
from app.services.analysis_service import analyze_candidate
import json

from app.schemas import (
    JobCreate, JobUpdate, JobStatusUpdate, JobResponse, JobDetailResponse, JobListResponse, JobDetailWrapperResponse,
    CandidateCreate, CandidateUpdate, CandidateStatusUpdate, CandidateResponse, CandidateDetailResponse, CandidateListResponse,
    ResumeScreeningRequest, FirstInterviewAnalysisRequest,
    InterviewRecordCreate, InterviewRecordResponse,
    CandidateStatusLogResponse, StageReportResponse, SuccessResponse,
)
from app.crud_new import (
    create_job, get_job, get_job_list, update_job, update_job_status, delete_job,
    create_candidate, get_candidate, get_candidate_list, update_candidate, update_candidate_status, update_candidate_score_summary, delete_candidate,
    create_stage_report, get_stage_report, get_latest_stage_report,
    create_interview_record, get_latest_interview_record, get_interview_records,
    count_candidates_by_status, count_candidates_by_job,
)
from app.services.resume_screening_service import analyze_resume_screening, compute_content_hash
from app.services.first_interview_service import analyze_first_interview
from app import constants

app = FastAPI(title="HR 面试分析系统", version="2.0.0")

# 创建数据库表
Base.metadata.create_all(bind=engine)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== 旧接口兼容 ==============
@app.post("/api/analysis/create", response_model=AnalysisResponse)
async def create_analysis_endpoint(analysis: AnalysisCreate, db: Session = Depends(get_db)):
    try:
        result = await analyze_candidate(
            candidate_name=analysis.candidate_name,
            job_title=analysis.job_title,
            jd_text=analysis.jd_text,
            resume_text=analysis.resume_text,
            interview_text=analysis.interview_text
        )

        overview = result.get("candidate_overview", {})

        db_analysis = create_analysis(
            db=db,
            analysis=analysis,
            analysis_result=json.dumps(result, ensure_ascii=False),
            match_score=overview.get("match_score", 0),
            recommendation=overview.get("recommendation", "暂缓"),
            risk_level=overview.get("risk_level", "中"),
            confidence=overview.get("confidence", "中")
        )

        return db_analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI分析失败，请稍后重试: {str(e)}")


@app.get("/api/analysis/list", response_model=AnalysisListResponse)
def list_analysis_endpoint(
    candidate_name: Optional[str] = Query(None),
    job_title: Optional[str] = Query(None),
    recommendation: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    filters = AnalysisFilter(
        candidate_name=candidate_name,
        job_title=job_title,
        recommendation=recommendation,
        risk_level=risk_level,
        page=page,
        page_size=page_size
    )
    return get_analysis_list(db, filters)


@app.get("/api/analysis/{analysis_id}", response_model=AnalysisDetailResponse)
def get_analysis_endpoint(analysis_id: int, db: Session = Depends(get_db)):
    db_analysis = get_analysis(db, analysis_id)
    if not db_analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return db_analysis


@app.delete("/api/analysis/{analysis_id}")
def delete_analysis_endpoint(analysis_id: int, db: Session = Depends(get_db)):
    success = delete_analysis(db, analysis_id)
    if not success:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return {"success": True}


# ============== 岗位接口 ==============
@app.post("/api/jobs", response_model=JobResponse)
def create_job_endpoint(job_data: JobCreate, db: Session = Depends(get_db)):
    db_job = create_job(db, job_data.model_dump())
    return db_job


@app.get("/api/jobs", response_model=JobListResponse)
def list_jobs_endpoint(
    job_name: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_job_list(db, job_name=job_name, department=department, status=status, page=page, page_size=page_size)


@app.get("/api/jobs/{job_id}", response_model=JobDetailWrapperResponse)
def get_job_endpoint(job_id: int, db: Session = Depends(get_db)):
    db_job = get_job(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    candidate_count = count_candidates_by_job(db, job_id)
    resume_passed = count_candidates_by_status(db, job_id, constants.STATUS_RESUME_PASSED)
    first_interview_passed = count_candidates_by_status(db, job_id, constants.STATUS_FIRST_INTERVIEW_PASSED)
    second_interview_passed = count_candidates_by_status(db, job_id, constants.STATUS_SECOND_INTERVIEW_PASSED)

    job_dict = JobDetailResponse.model_validate(db_job).model_dump()
    job_dict.update({
        "candidate_count": candidate_count,
        "resume_passed_count": resume_passed,
        "first_interview_passed_count": first_interview_passed,
        "second_interview_passed_count": second_interview_passed,
    })
    return job_dict


@app.put("/api/jobs/{job_id}", response_model=JobResponse)
def update_job_endpoint(job_id: int, job_data: JobUpdate, db: Session = Depends(get_db)):
    db_job = update_job(db, job_id, job_data.model_dump())
    if not db_job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return db_job


@app.put("/api/jobs/{job_id}/status", response_model=JobResponse)
def update_job_status_endpoint(job_id: int, data: JobStatusUpdate, db: Session = Depends(get_db)):
    db_job = update_job_status(db, job_id, data.status)
    if not db_job:
        raise HTTPException(status_code=400, detail="岗位不存在或状态值无效")
    return db_job


@app.delete("/api/jobs/{job_id}")
def delete_job_endpoint(job_id: int, db: Session = Depends(get_db)):
    success = delete_job(db, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return {"success": True}


# ============== 候选人接口 ==============
@app.post("/api/candidates", response_model=CandidateResponse)
def create_candidate_endpoint(candidate_data: CandidateCreate, db: Session = Depends(get_db)):
    db_candidate = create_candidate(db, candidate_data.model_dump())
    return db_candidate


@app.get("/api/candidates", response_model=CandidateListResponse)
def list_candidates_endpoint(
    job_id: Optional[int] = Query(None),
    candidate_name: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    current_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_candidate_list(db, job_id=job_id, candidate_name=candidate_name, source=source, current_status=current_status, page=page, page_size=page_size)


@app.get("/api/candidates/{candidate_id}", response_model=CandidateDetailResponse)
def get_candidate_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")

    job = get_job(db, db_candidate.job_id)
    candidate_dict = CandidateDetailResponse.model_validate(db_candidate).model_dump()
    candidate_dict["job_name"] = job.job_name if job else None
    candidate_dict["department"] = job.department if job else None
    return candidate_dict


@app.put("/api/candidates/{candidate_id}", response_model=CandidateResponse)
def update_candidate_endpoint(candidate_id: int, candidate_data: CandidateUpdate, db: Session = Depends(get_db)):
    db_candidate = update_candidate(db, candidate_id, candidate_data.model_dump())
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    return db_candidate


@app.put("/api/candidates/{candidate_id}/status", response_model=CandidateResponse)
def update_candidate_status_endpoint(candidate_id: int, data: CandidateStatusUpdate, db: Session = Depends(get_db)):
    db_candidate = update_candidate_status(db, candidate_id, data.to_status, data.reason, data.operator_name)
    if not db_candidate:
        raise HTTPException(status_code=400, detail="候选人不存在或状态流转非法")
    return db_candidate


@app.delete("/api/candidates/{candidate_id}")
def delete_candidate_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    success = delete_candidate(db, candidate_id)
    if not success:
        raise HTTPException(status_code=404, detail="候选人不存在")
    return {"success": True}


# ============== 简历筛选接口 ==============
@app.post("/api/candidates/{candidate_id}/resume-screening", response_model=StageReportResponse)
async def trigger_resume_screening_endpoint(candidate_id: int, data: ResumeScreeningRequest, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")

    db_job = get_job(db, db_candidate.job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="关联岗位不存在")

    content_hash = compute_content_hash(db_job.jd_text, db_candidate.resume_text)

    if not data.force:
        existing_report = get_latest_stage_report(db, candidate_id, constants.STAGE_RESUME_SCREENING)
        if existing_report and existing_report.content_hash == content_hash:
            return existing_report

    report_version = get_latest_stage_report.__name__  # placeholder
    from app.crud_new import get_next_report_version
    report_version = get_next_report_version(db, candidate_id, constants.STAGE_RESUME_SCREENING)

    input_snapshot = {
        "jd_text": db_job.jd_text,
        "resume_text": db_candidate.resume_text,
        "candidate_name": db_candidate.candidate_name,
        "job_name": db_job.job_name,
    }

    try:
        result = await analyze_resume_screening(db_job.jd_text, db_candidate.resume_text)
        report_json = json.dumps(result, ensure_ascii=False)

        db_report = create_stage_report(
            db=db,
            candidate_id=candidate_id,
            job_id=db_candidate.job_id,
            stage_type=constants.STAGE_RESUME_SCREENING,
            report_version=report_version,
            report_json=report_json,
            input_snapshot_json=json.dumps(input_snapshot, ensure_ascii=False),
            score=result.get("score"),
            suggestion=result.get("suggestion"),
            risk_level=result.get("risk_level"),
            content_hash=content_hash,
            request_id=data.request_id,
            status=constants.REPORT_STATUS_SUCCESS,
        )

        update_candidate_score_summary(
            db=db,
            candidate_id=candidate_id,
            stage_type=constants.STAGE_RESUME_SCREENING,
            score=result.get("score"),
            suggestion=result.get("suggestion"),
        )

        return db_report
    except Exception as e:
        # 记录失败
        create_stage_report(
            db=db,
            candidate_id=candidate_id,
            job_id=db_candidate.job_id,
            stage_type=constants.STAGE_RESUME_SCREENING,
            report_version=report_version,
            report_json="{}",
            input_snapshot_json=json.dumps(input_snapshot, ensure_ascii=False),
            content_hash=content_hash,
            request_id=data.request_id,
            status=constants.REPORT_STATUS_FAILED,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=f"简历筛选失败: {str(e)}")


@app.get("/api/candidates/{candidate_id}/resume-screening/latest", response_model=StageReportResponse)
def get_latest_resume_screening_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_report = get_latest_stage_report(db, candidate_id, constants.STAGE_RESUME_SCREENING)
    if not db_report:
        raise HTTPException(status_code=404, detail="暂无简历筛选报告")
    return db_report


# ============== 初试记录接口 ==============
@app.post("/api/candidates/{candidate_id}/first-interview-record", response_model=InterviewRecordResponse)
def create_first_interview_record_endpoint(candidate_id: int, data: InterviewRecordCreate, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")

    try:
        db_record = create_interview_record(
            db=db,
            candidate_id=candidate_id,
            job_id=db_candidate.job_id,
            round_type=constants.ROUND_TYPE_FIRST,
            record_text=data.record_text,
            interviewer_name=data.interviewer_name,
            interview_time=data.interview_time,
        )
        return db_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/candidates/{candidate_id}/first-interview-record/latest", response_model=InterviewRecordResponse)
def get_latest_first_interview_record_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_record = get_latest_interview_record(db, candidate_id, constants.ROUND_TYPE_FIRST)
    if not db_record:
        raise HTTPException(status_code=404, detail="暂无初试记录")
    return db_record


@app.get("/api/candidates/{candidate_id}/first-interview-record", response_model=dict)
def list_first_interview_records_endpoint(
    candidate_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_interview_records(db, candidate_id, round_type=constants.ROUND_TYPE_FIRST, page=page, page_size=page_size)


# ============== 初试分析接口 ==============
@app.post("/api/candidates/{candidate_id}/first-interview-analysis", response_model=StageReportResponse)
async def trigger_first_interview_analysis_endpoint(candidate_id: int, data: FirstInterviewAnalysisRequest, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")

    db_job = get_job(db, db_candidate.job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="关联岗位不存在")

    from app.crud_new import get_interview_record
    db_record = get_interview_record(db, data.interview_record_id)
    if not db_record or db_record.candidate_id != candidate_id:
        raise HTTPException(status_code=404, detail="初试记录不存在")

    content_hash = compute_content_hash(
        db_job.jd_text,
        db_candidate.resume_text,
        db_record.record_text,
    )

    if not data.force:
        existing_report = get_latest_stage_report(db, candidate_id, constants.STAGE_FIRST_INTERVIEW)
        if existing_report and existing_report.content_hash == content_hash:
            return existing_report

    from app.crud_new import get_next_report_version
    report_version = get_next_report_version(db, candidate_id, constants.STAGE_FIRST_INTERVIEW)

    input_snapshot = {
        "jd_text": db_job.jd_text,
        "resume_text": db_candidate.resume_text,
        "record_text": db_record.record_text,
        "interviewer_name": db_record.interviewer_name,
        "interview_time": str(db_record.interview_time) if db_record.interview_time else None,
    }

    try:
        result = await analyze_first_interview(db_job.jd_text, db_candidate.resume_text, db_record.record_text)
        report_json = json.dumps(result, ensure_ascii=False)

        db_report = create_stage_report(
            db=db,
            candidate_id=candidate_id,
            job_id=db_candidate.job_id,
            stage_type=constants.STAGE_FIRST_INTERVIEW,
            report_version=report_version,
            report_json=report_json,
            input_snapshot_json=json.dumps(input_snapshot, ensure_ascii=False),
            score=result.get("score"),
            suggestion=result.get("suggestion"),
            risk_level=result.get("risk_level"),
            content_hash=content_hash,
            request_id=data.request_id,
            status=constants.REPORT_STATUS_SUCCESS,
        )

        update_candidate_score_summary(
            db=db,
            candidate_id=candidate_id,
            stage_type=constants.STAGE_FIRST_INTERVIEW,
            score=result.get("score"),
            suggestion=result.get("suggestion"),
        )

        return db_report
    except Exception as e:
        create_stage_report(
            db=db,
            candidate_id=candidate_id,
            job_id=db_candidate.job_id,
            stage_type=constants.STAGE_FIRST_INTERVIEW,
            report_version=report_version,
            report_json="{}",
            input_snapshot_json=json.dumps(input_snapshot, ensure_ascii=False),
            content_hash=content_hash,
            request_id=data.request_id,
            status=constants.REPORT_STATUS_FAILED,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=f"初试分析失败: {str(e)}")


@app.get("/api/candidates/{candidate_id}/first-interview-analysis/latest", response_model=StageReportResponse)
def get_latest_first_interview_analysis_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_report = get_latest_stage_report(db, candidate_id, constants.STAGE_FIRST_INTERVIEW)
    if not db_report:
        raise HTTPException(status_code=404, detail="暂无初试分析报告")
    return db_report


# ============== 状态日志接口 ==============
@app.get("/api/candidates/{candidate_id}/status-logs", response_model=list[CandidateStatusLogResponse])
def get_candidate_status_logs_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    logs = db.query(constants.CandidateStatusLog).filter(constants.CandidateStatusLog.candidate_id == candidate_id).all()
    return logs


@app.get("/api/stage-reports/{report_id}", response_model=StageReportResponse)
def get_stage_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    db_report = get_stage_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="阶段报告不存在")
    return db_report


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
