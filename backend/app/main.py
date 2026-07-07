from fastapi import FastAPI, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session
from typing import Any, Optional
import hashlib
import ipaddress
import secrets
from datetime import datetime

from app.database import engine, Base, get_db
from app.schemas import AnalysisCreate, AnalysisResponse, AnalysisDetailResponse, AnalysisListResponse, AnalysisFilter
from app.crud import create_analysis, get_analysis, get_analysis_list, delete_analysis
from app.services.analysis_service import analyze_candidate
import json

from app.schemas import (
    JobCreate, JobUpdate, JobStatusUpdate, JobResponse, JobDetailResponse, JobListResponse, JobDetailWrapperResponse,
    JobPositionCreate, JobPositionUpdate, JobPositionListResponse, JobPositionDetailResponse,
    JobPositionParseJDRequest, JobPositionParseJDResponse,
    JobTypeConfigCreate, JobTypeConfigUpdate, JobTypeConfigListResponse, JobTypeConfigResponse,
    AiPromptTemplateCreate, AiPromptTemplateUpdate, AiPromptTemplateListResponse, AiPromptTemplateResponse,
    CandidateCreate, CandidateUpdate, CandidateStatusUpdate, CandidateResponse, CandidateDetailResponse, CandidateListResponse,
    ResumeScreeningRequest, FirstInterviewAnalysisRequest,
    InterviewRecordCreate, InterviewRecordResponse,
    CandidateInterviewRoundCreate, CandidateInterviewRoundUpdate,
    CandidateInterviewRecordSubmit, CandidateInterviewDecisionSubmit,
    CandidateInterviewRoundResponse, CandidateInterviewFlowResponse,
    CandidateInterviewRoundsBatchRequest, CandidateInterviewRoundsBatchResponse,
    CandidateInterviewQuestionsGenerateRequest, CandidateInterviewQuestionsResponse,
    CandidateInterviewQuestionsListResponse, InterviewQuestionStatsResponse,
    CandidateStatusLogResponse, StageReportResponse, SuccessResponse,
    ReportCandidateListResponse, ReportCandidateContextResponse,
    ReportGenerateRequest, CandidateEvaluationReportResponse,
    CandidateEvaluationReportListResponse,
    ParseJDRequest, ParseResumeRequest,
    ScreeningTaskCreate, ScreeningTaskProgressResponse, ScreeningTaskResponse, ScreeningTaskListResponse,
    ScreeningJDParseRequest, ScreeningJDParseResponse, ResumeFileResponse,
    ResumeParseRecordListResponse, ResumeParseRecordDetailResponse,
    ScreeningResultListResponse, ScreeningResultDetailResponse, ScreeningResultStatusUpdate,
)
from app.crud_new import (
    create_job, get_job, get_job_list, update_job, update_job_status, delete_job,
    list_job_positions, get_job_position, create_job_position, update_job_position,
    archive_job_position, copy_job_position, build_job_position_draft_from_parsed,
    create_candidate, get_candidate, get_candidate_list, update_candidate, update_candidate_status, update_candidate_score_summary, delete_candidate,
    mark_candidate_waiting_interview_after_screening,
    create_stage_report, get_stage_report, get_latest_stage_report,
    get_existing_current_report_by_key, get_next_report_version, get_next_report_version_for_key,
    mark_report_versions_not_current, mark_stage_reports_not_current, list_candidate_evaluation_reports,
    create_interview_question_items, list_interview_question_reports, list_interview_question_stats,
    create_interview_record, get_latest_interview_record, get_interview_records,
    get_candidate_interview_rounds, get_candidate_interview_round, get_latest_completed_interview_round,
    get_candidate_interview_rounds_by_candidate_ids,
    get_next_interview_round_no, has_active_interview_round,
    create_candidate_interview_round, update_candidate_interview_round,
    submit_candidate_interview_record, cancel_candidate_interview_round,
    apply_candidate_interview_decision, reopen_candidate_interview_flow,
    update_candidate_interview_questions,
    count_candidates_by_status, count_candidates_by_job,
    get_dashboard_stats,
)
from app.config import get_settings
from app.models import Candidate, CandidateInterviewRound, InterviewRecord, Job, StageReport
from app.services.resume_screening_service import analyze_resume_screening, compute_content_hash
from app.services.first_interview_service import analyze_first_interview
from app.services.second_interview_service import analyze_second_interview
from app.services.jd_parsing_service import parse_job_description, build_job_update_from_parsed
from app.services.resume_parsing_service import parse_resume, build_candidate_update_from_parsed
from app.services.file_text_extractor import compute_resume_text_hash, extract_text_from_bytes, get_file_type
from app.services.task_screening_service import analyze_task_screening
from app.services.interview_question_service import generate_candidate_questions, generate_round_questions
from app.crud_screening import (
    create_screening_task, get_screening_task, list_screening_tasks, update_task_from_parsed_jd, update_task_status,
    get_resume_file,
    create_resume_file_record, get_resume_files, update_resume_file, upsert_candidate_profile,
    upsert_screening_result, refresh_screening_task_counts, list_screening_result_items,
    build_screening_result_detail, update_screening_result_status,
    find_reusable_resume_profile, reuse_candidate_profile_from_history,
    find_reusable_screening_result, copy_screening_result_from_history,
    list_resume_parse_records, get_resume_parse_record_detail,
)
from app.crud_settings import (
    activate_ai_prompt_template, archive_ai_prompt_template, archive_job_type_config,
    copy_ai_prompt_template, create_ai_prompt_template, create_job_type_config,
    get_active_prompt_pair, get_enabled_job_types, list_ai_prompt_templates,
    list_job_type_configs, reset_ai_prompt_template, update_ai_prompt_template,
    update_job_type_config,
)
from app import constants

app = FastAPI(title="AI 招聘筛选与面试评估系统", version="2.0.0")
app_settings = get_settings()

# 创建数据库表
Base.metadata.create_all(bind=engine)
try:
    from app.migrate_add_new_fields import migrate as migrate_existing_db
    migrate_existing_db()
except Exception as e:
    print(f"数据库增量迁移检查失败: {e}")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _is_loopback_host(host: Optional[str]) -> bool:
    if not host:
        return False
    if host in {"localhost", "testclient"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


@app.middleware("http")
async def api_key_auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or not request.url.path.startswith("/api"):
        return await call_next(request)

    settings = get_settings()
    if settings.hr_api_key:
        request_api_key = request.headers.get("x-api-key", "")
        if not secrets.compare_digest(request_api_key, settings.hr_api_key):
            return JSONResponse(status_code=401, content={"detail": "缺少或无效的 API Key"})
    elif not (settings.allow_unauthenticated_local and _is_loopback_host(request.client.host if request.client else None)):
        return JSONResponse(status_code=403, content={"detail": "未配置 HR_API_KEY，已拒绝非本机访问"})

    return await call_next(request)


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


# ============== 工作台 Dashboard 接口 ==============
@app.get("/api/dashboard/stats")
def get_dashboard_stats_endpoint(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)


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


@app.get("/api/job-types")
def get_job_types(db: Session = Depends(get_db)):
    """获取所有岗位类型"""
    return get_enabled_job_types(db)


# ============== 系统配置接口 ==============
@app.get("/api/settings/job-types", response_model=JobTypeConfigListResponse)
def list_job_type_configs_endpoint(
    keyword: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    return list_job_type_configs(db, keyword=keyword, enabled=enabled)


@app.post("/api/settings/job-types", response_model=JobTypeConfigResponse)
def create_job_type_config_endpoint(data: JobTypeConfigCreate, db: Session = Depends(get_db)):
    try:
        return create_job_type_config(db, data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/settings/job-types/{config_id}", response_model=JobTypeConfigResponse)
def update_job_type_config_endpoint(config_id: int, data: JobTypeConfigUpdate, db: Session = Depends(get_db)):
    try:
        config = update_job_type_config(db, config_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not config:
        raise HTTPException(status_code=404, detail="岗位类型不存在")
    return config


@app.patch("/api/settings/job-types/{config_id}/archive", response_model=JobTypeConfigResponse)
def archive_job_type_config_endpoint(config_id: int, db: Session = Depends(get_db)):
    config = archive_job_type_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="岗位类型不存在")
    return config


@app.get("/api/settings/ai-prompts", response_model=AiPromptTemplateListResponse)
def list_ai_prompt_templates_endpoint(
    keyword: Optional[str] = Query(None),
    prompt_key: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return list_ai_prompt_templates(db, keyword=keyword, prompt_key=prompt_key, status=status)


@app.post("/api/settings/ai-prompts", response_model=AiPromptTemplateResponse)
def create_ai_prompt_template_endpoint(data: AiPromptTemplateCreate, db: Session = Depends(get_db)):
    try:
        return create_ai_prompt_template(db, data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/settings/ai-prompts/{prompt_id}", response_model=AiPromptTemplateResponse)
def update_ai_prompt_template_endpoint(prompt_id: int, data: AiPromptTemplateUpdate, db: Session = Depends(get_db)):
    prompt = update_ai_prompt_template(db, prompt_id, data.model_dump(exclude_unset=True))
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    return prompt


@app.post("/api/settings/ai-prompts/{prompt_id}/copy", response_model=AiPromptTemplateResponse)
def copy_ai_prompt_template_endpoint(prompt_id: int, db: Session = Depends(get_db)):
    prompt = copy_ai_prompt_template(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    return prompt


@app.post("/api/settings/ai-prompts/{prompt_id}/activate", response_model=AiPromptTemplateResponse)
def activate_ai_prompt_template_endpoint(prompt_id: int, db: Session = Depends(get_db)):
    prompt = activate_ai_prompt_template(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    return prompt


@app.patch("/api/settings/ai-prompts/{prompt_id}/archive", response_model=AiPromptTemplateResponse)
def archive_ai_prompt_template_endpoint(prompt_id: int, db: Session = Depends(get_db)):
    prompt = archive_ai_prompt_template(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    return prompt


@app.post("/api/settings/ai-prompts/{prompt_key}/reset", response_model=AiPromptTemplateResponse)
def reset_ai_prompt_template_endpoint(prompt_key: str, db: Session = Depends(get_db)):
    try:
        return reset_ai_prompt_template(db, prompt_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/jobs/parse-jd")
async def parse_jd_endpoint(data: ParseJDRequest, db: Session = Depends(get_db)):
    """AI 解析 JD 文本，返回结构化岗位信息（不直接保存）"""
    try:
        job_type_payload = get_enabled_job_types(db)
        parsed_jd = await parse_job_description(
            data.jd_text,
            prompt_config=get_active_prompt_pair(db, constants.PROMPT_KEY_JD_PARSE),
            job_type_options=job_type_payload["job_types"],
        )
        return {
            "success": True,
            "parsed_jd": parsed_jd,
            "job_update": build_job_update_from_parsed(parsed_jd),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD 解析失败，请稍后重试: {str(e)}")


@app.get("/api/job-positions", response_model=JobPositionListResponse)
def list_job_positions_endpoint(
    keyword: Optional[str] = Query(None),
    positionType: Optional[str] = Query(None),
    position_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """岗位库列表，服务于岗位初筛工作台的历史岗位选择。"""
    return list_job_positions(
        db,
        keyword=keyword,
        position_type=position_type or positionType,
        status=status,
        page=page,
        page_size=page_size or pageSize,
    )


@app.post("/api/job-positions", response_model=JobPositionDetailResponse)
def create_job_position_endpoint(data: JobPositionCreate, db: Session = Depends(get_db)):
    return create_job_position(db, data.model_dump())


@app.post("/api/job-positions/parse-jd", response_model=JobPositionParseJDResponse)
async def parse_job_position_jd_endpoint(data: JobPositionParseJDRequest, db: Session = Depends(get_db)):
    jd_text = data.jd_text or data.jdText or ""
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="请先粘贴岗位 JD 原文")
    try:
        job_type_payload = get_enabled_job_types(db)
        parsed_jd = await parse_job_description(
            jd_text,
            prompt_config=get_active_prompt_pair(db, constants.PROMPT_KEY_JD_PARSE),
            job_type_options=job_type_payload["job_types"],
        )
        return {
            "success": True,
            "jd_text": jd_text,
            "parsed_jd": parsed_jd,
            "position": build_job_position_draft_from_parsed(jd_text, parsed_jd),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"岗位信息生成失败，请检查 JD 内容后重试: {str(e)}")


@app.get("/api/job-positions/{job_id}", response_model=JobPositionDetailResponse)
def get_job_position_endpoint(job_id: int, db: Session = Depends(get_db)):
    job_position = get_job_position(db, job_id)
    if not job_position:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return job_position


@app.put("/api/job-positions/{job_id}", response_model=JobPositionDetailResponse)
def update_job_position_endpoint(job_id: int, data: JobPositionUpdate, db: Session = Depends(get_db)):
    job_position = update_job_position(db, job_id, data.model_dump(exclude_unset=True))
    if not job_position:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return job_position


@app.patch("/api/job-positions/{job_id}/archive", response_model=JobPositionDetailResponse)
def archive_job_position_endpoint(job_id: int, db: Session = Depends(get_db)):
    job_position = archive_job_position(db, job_id)
    if not job_position:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return job_position


@app.post("/api/job-positions/{job_id}/copy", response_model=JobPositionDetailResponse)
def copy_job_position_endpoint(job_id: int, db: Session = Depends(get_db)):
    job_position = copy_job_position(db, job_id)
    if not job_position:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return job_position


@app.post("/api/candidates/parse-resume")
async def parse_resume_endpoint(data: ParseResumeRequest, db: Session = Depends(get_db)):
    """AI 解析简历文本，返回结构化候选人信息（不直接保存）"""
    try:
        parsed_resume = await parse_resume(
            data.resume_text,
            prompt_config=get_active_prompt_pair(db, constants.PROMPT_KEY_RESUME_PARSE),
        )
        return {
            "success": True,
            "parsed_resume": parsed_resume,
            "candidate_update": build_candidate_update_from_parsed(parsed_resume),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"简历解析失败，请稍后重试: {str(e)}")


# ============== 岗位初筛任务接口 ==============
@app.post("/api/screening/jd/parse", response_model=ScreeningJDParseResponse)
async def screening_parse_jd_endpoint(data: ScreeningJDParseRequest, db: Session = Depends(get_db)):
    """解析 JD 文本，服务于岗位初筛工作台。"""
    try:
        job_type_payload = get_enabled_job_types(db)
        parsed_jd = await parse_job_description(
            data.jd_text,
            prompt_config=get_active_prompt_pair(db, constants.PROMPT_KEY_JD_PARSE),
            job_type_options=job_type_payload["job_types"],
        )
        return {"success": True, "jd_text": data.jd_text, "parsed_jd": parsed_jd}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD 解析失败，请稍后重试: {str(e)}")


@app.post("/api/screening/jd/parse-file", response_model=ScreeningJDParseResponse)
async def screening_parse_jd_file_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """抽取并解析 JD 文件，支持 PDF / Word / TXT。"""
    try:
        content = await file.read()
        jd_text = extract_text_from_bytes(file.filename or "jd.txt", content)
        job_type_payload = get_enabled_job_types(db)
        parsed_jd = await parse_job_description(
            jd_text,
            prompt_config=get_active_prompt_pair(db, constants.PROMPT_KEY_JD_PARSE),
            job_type_options=job_type_payload["job_types"],
        )
        return {"success": True, "jd_text": jd_text, "parsed_jd": parsed_jd}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD 文件解析失败，请稍后重试: {str(e)}")


@app.post("/api/screening/tasks", response_model=ScreeningTaskResponse)
def create_screening_task_endpoint(data: ScreeningTaskCreate, db: Session = Depends(get_db)):
    try:
        db_task = create_screening_task(db, data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return db_task


@app.get("/api/screening/tasks", response_model=ScreeningTaskListResponse)
def list_screening_tasks_endpoint(
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    job_position_id: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_screening_tasks(
        db,
        keyword=keyword,
        status=status,
        job_position_id=job_position_id,
        page=page,
        page_size=page_size or pageSize,
    )


@app.post("/api/screening/tasks/{task_id}/resumes", response_model=list[ResumeFileResponse])
async def upload_screening_resumes_endpoint(
    task_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    task = get_screening_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="岗位初筛任务不存在")

    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一份简历")
    settings = get_settings()
    if len(files) > settings.max_resume_upload_files:
        raise HTTPException(status_code=400, detail=f"单次最多上传 {settings.max_resume_upload_files} 份简历")

    created_files = []
    for upload_file in files:
        filename = upload_file.filename or "resume"
        content = await upload_file.read(settings.max_resume_upload_bytes + 1)
        if len(content) > settings.max_resume_upload_bytes:
            max_mb = max(settings.max_resume_upload_bytes // 1024 // 1024, 1)
            raise HTTPException(status_code=413, detail=f"单个简历文件不能超过 {max_mb}MB")
        file_hash = hashlib.sha256(content).hexdigest()
        try:
            file_type = get_file_type(filename)
            raw_text = extract_text_from_bytes(filename, content)
            text_hash = compute_resume_text_hash(raw_text)
            db_file = create_resume_file_record(
                db=db,
                task_id=task_id,
                file_name=filename,
                file_type=file_type,
                file_hash=file_hash,
                text_hash=text_hash,
                raw_text=raw_text,
                parse_status=constants.RESUME_FILE_PENDING,
            )
        except ValueError as e:
            suffix = filename.rsplit(".", 1)[-1].upper() if "." in filename else ""
            db_file = create_resume_file_record(
                db=db,
                task_id=task_id,
                file_name=filename,
                file_type=suffix,
                file_hash=file_hash,
                raw_text=None,
                parse_status=constants.RESUME_FILE_FAILED,
                parse_error_message=str(e),
            )
        created_files.append(db_file)

    refresh_screening_task_counts(db, task_id)
    task = get_screening_task(db, task_id)
    if task and task.status == constants.SCREENING_TASK_DRAFT:
        update_task_status(db, task, constants.SCREENING_TASK_READY)
    return created_files


@app.post("/api/screening/tasks/{task_id}/start")
async def start_screening_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    task = get_screening_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="岗位初筛任务不存在")

    resume_files = get_resume_files(db, task_id)
    if not resume_files:
        raise HTTPException(status_code=400, detail="请先上传简历")

    update_task_status(db, task, constants.SCREENING_TASK_SCREENING)

    try:
        if task.jd_structured_json:
            parsed_jd = json.loads(task.jd_structured_json)
        else:
            job_type_payload = get_enabled_job_types(db)
            parsed_jd = await parse_job_description(
                task.jd_text,
                prompt_config=get_active_prompt_pair(db, constants.PROMPT_KEY_JD_PARSE),
                job_type_options=job_type_payload["job_types"],
            )
            task = update_task_from_parsed_jd(db, task, parsed_jd)
    except Exception as e:
        update_task_status(db, task, constants.SCREENING_TASK_FAILED)
        raise HTTPException(status_code=500, detail=f"JD 解析失败: {str(e)}")

    for resume_file in resume_files:
        if resume_file.parse_status == constants.RESUME_FILE_COMPLETED:
            continue
        if resume_file.parse_status == constants.RESUME_FILE_FAILED and not resume_file.raw_text:
            continue
        await _process_screening_resume_file(db, task, resume_file, parsed_jd)

    task = refresh_screening_task_counts(db, task_id)
    if task:
        update_task_status(db, task, constants.SCREENING_TASK_COMPLETED)
        task = refresh_screening_task_counts(db, task_id)

    return {
        "success": True,
        "task": task,
        "progress": _build_screening_progress(task),
    }


@app.post("/api/screening/tasks/{task_id}/process-next")
async def process_next_screening_resume_endpoint(
    task_id: int,
    force_parse: bool = Query(False),
    force_screen: bool = Query(False),
    db: Session = Depends(get_db),
):
    """处理下一份待初筛简历，避免多份简历挤在一个长请求里导致前端超时。"""
    task = get_screening_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="岗位初筛任务不存在")

    resume_files = get_resume_files(db, task_id)
    if not resume_files:
        raise HTTPException(status_code=400, detail="请先上传简历")

    if task.status != constants.SCREENING_TASK_SCREENING:
        task = update_task_status(db, task, constants.SCREENING_TASK_SCREENING)

    try:
        parsed_jd, task = await _ensure_screening_task_jd(db, task)
    except Exception as e:
        update_task_status(db, task, constants.SCREENING_TASK_FAILED)
        raise HTTPException(status_code=500, detail=f"JD 解析失败: {str(e)}")

    resume_file = _get_next_screening_resume_file(resume_files)
    if not resume_file:
        task = refresh_screening_task_counts(db, task_id)
        if task:
            task = update_task_status(db, task, constants.SCREENING_TASK_COMPLETED)
            task = refresh_screening_task_counts(db, task_id)
        return {
            "success": True,
            "done": True,
            "resume_file": None,
            "progress": _build_screening_progress(task),
        }

    processed_file = await _process_screening_resume_file(
        db,
        task,
        resume_file,
        parsed_jd,
        force_parse=force_parse,
        force_screen=force_screen,
    )

    task = refresh_screening_task_counts(db, task_id)
    remaining_files = get_resume_files(db, task_id)
    done = _get_next_screening_resume_file(remaining_files) is None
    if done and task:
        task = update_task_status(db, task, constants.SCREENING_TASK_COMPLETED)
        task = refresh_screening_task_counts(db, task_id)

    return {
        "success": True,
        "done": done,
        "resume_file": _serialize_resume_file_for_step(processed_file),
        "progress": _build_screening_progress(task),
    }


@app.post("/api/screening/tasks/{task_id}/resume-files/{resume_file_id}/reprocess")
async def reprocess_screening_resume_endpoint(
    task_id: int,
    resume_file_id: int,
    force_parse: bool = Query(False),
    force_screen: bool = Query(True),
    db: Session = Depends(get_db),
):
    """手动重新解析或重新筛选单份简历。默认复用解析，仅重新做岗位匹配。"""
    task = get_screening_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="岗位初筛任务不存在")

    resume_file = get_resume_file(db, resume_file_id)
    if not resume_file or resume_file.task_id != task_id:
        raise HTTPException(status_code=404, detail="简历文件不存在")
    if not resume_file.raw_text:
        raise HTTPException(status_code=400, detail="简历文本为空，无法重新处理")

    try:
        parsed_jd, task = await _ensure_screening_task_jd(db, task)
    except Exception as e:
        update_task_status(db, task, constants.SCREENING_TASK_FAILED)
        raise HTTPException(status_code=500, detail=f"JD 解析失败: {str(e)}")

    if task.status != constants.SCREENING_TASK_SCREENING:
        task = update_task_status(db, task, constants.SCREENING_TASK_SCREENING)

    processed_file = await _process_screening_resume_file(
        db,
        task,
        resume_file,
        parsed_jd,
        force_parse=force_parse,
        force_screen=force_screen,
    )
    task = refresh_screening_task_counts(db, task_id)
    remaining_files = get_resume_files(db, task_id)
    if _get_next_screening_resume_file(remaining_files) is None and task:
        task = update_task_status(db, task, constants.SCREENING_TASK_COMPLETED)
        task = refresh_screening_task_counts(db, task_id)

    return {
        "success": True,
        "resume_file": _serialize_resume_file_for_step(processed_file),
        "progress": _build_screening_progress(task),
    }


@app.get("/api/resume-files", response_model=ResumeParseRecordListResponse)
def list_resume_parse_records_endpoint(
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    parse_status: Optional[str] = Query(None),
    reuse_source: Optional[str] = Query(None),
    task_id: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """简历解析记录列表，用于查看上传、解析、复用和初筛状态。"""
    return list_resume_parse_records(
        db,
        keyword=keyword,
        parse_status=parse_status or status,
        reuse_source=reuse_source,
        task_id=task_id,
        page=page,
        page_size=page_size or pageSize,
    )


@app.get("/api/resume-files/{resume_file_id}", response_model=ResumeParseRecordDetailResponse)
def get_resume_parse_record_detail_endpoint(resume_file_id: int, db: Session = Depends(get_db)):
    detail = get_resume_parse_record_detail(db, resume_file_id)
    if not detail:
        raise HTTPException(status_code=404, detail="简历解析记录不存在")
    return detail


@app.post("/api/resume-files/{resume_file_id}/reparse")
async def reparse_resume_file_record_endpoint(
    resume_file_id: int,
    force_screen: bool = Query(True),
    db: Session = Depends(get_db),
):
    """手动重新解析单份简历；默认同步重新筛选当前任务。"""
    resume_file = get_resume_file(db, resume_file_id)
    if not resume_file:
        raise HTTPException(status_code=404, detail="简历文件不存在")
    return await reprocess_screening_resume_endpoint(
        task_id=resume_file.task_id,
        resume_file_id=resume_file.id,
        force_parse=True,
        force_screen=force_screen,
        db=db,
    )


@app.get("/api/screening/tasks/{task_id}/progress", response_model=ScreeningTaskProgressResponse)
def get_screening_task_progress_endpoint(task_id: int, db: Session = Depends(get_db)):
    task = get_screening_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="岗位初筛任务不存在")
    refresh_screening_task_counts(db, task_id)
    task = get_screening_task(db, task_id)
    return _build_screening_progress(task)


@app.get("/api/screening/tasks/{task_id}/results", response_model=ScreeningResultListResponse)
def list_screening_results_endpoint(
    task_id: int,
    conclusion: Optional[str] = Query(None),
    parse_status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None, ge=0, le=100),
    score_max: Optional[int] = Query(None, ge=0, le=100),
    work_years_min: Optional[float] = Query(None, ge=0),
    education: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    task = get_screening_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="岗位初筛任务不存在")

    return list_screening_result_items(
        db,
        task_id,
        filters={
            "conclusion": conclusion,
            "parse_status": parse_status,
            "job_type": job_type,
            "score_min": score_min,
            "score_max": score_max,
            "work_years_min": work_years_min,
            "education": education,
        },
    )


@app.get("/api/screening/results/{result_id}", response_model=ScreeningResultDetailResponse)
def get_screening_result_detail_endpoint(result_id: int, db: Session = Depends(get_db)):
    detail = build_screening_result_detail(db, result_id)
    if not detail:
        raise HTTPException(status_code=404, detail="初筛结果不存在")
    return detail


@app.put("/api/screening/results/{result_id}/status", response_model=ScreeningResultDetailResponse)
def update_screening_result_status_endpoint(
    result_id: int,
    data: ScreeningResultStatusUpdate,
    db: Session = Depends(get_db),
):
    result = update_screening_result_status(db, result_id, data.status)
    if not result:
        raise HTTPException(status_code=400, detail="初筛结果不存在或状态值无效")
    detail = build_screening_result_detail(db, result_id)
    if not detail:
        raise HTTPException(status_code=404, detail="初筛结果不存在")
    return detail


def _build_screening_progress(task) -> dict:
    screened = (task.recommended_count or 0) + (task.pending_count or 0) + (task.rejected_count or 0)
    return {
        "status": task.status,
        "total": task.total_resume_count or 0,
        "parsed_success": task.parsed_success_count or 0,
        "parsed_failed": task.parsed_failed_count or 0,
        "screened": screened,
        "recommended": task.recommended_count or 0,
        "pending": task.pending_count or 0,
        "rejected": task.rejected_count or 0,
    }


async def _ensure_screening_task_jd(db: Session, task):
    if task.jd_structured_json:
        return json.loads(task.jd_structured_json), task

    job_type_payload = get_enabled_job_types(db)
    parsed_jd = await parse_job_description(
        task.jd_text,
        prompt_config=get_active_prompt_pair(db, constants.PROMPT_KEY_JD_PARSE),
        job_type_options=job_type_payload["job_types"],
    )
    task = update_task_from_parsed_jd(db, task, parsed_jd)
    return parsed_jd, task


def _get_next_screening_resume_file(resume_files):
    finished_statuses = {
        constants.RESUME_FILE_COMPLETED,
        constants.RESUME_FILE_FAILED,
    }
    for resume_file in resume_files:
        if resume_file.parse_status in finished_statuses:
            continue
        return resume_file
    return None


async def _process_screening_resume_file(
    db: Session,
    task,
    resume_file,
    parsed_jd: dict,
    force_parse: bool = False,
    force_screen: bool = False,
):
    try:
        if not resume_file.raw_text:
            raise ValueError("简历文本为空，无法解析")

        if not resume_file.text_hash:
            resume_file = update_resume_file(
                db,
                resume_file,
                text_hash=compute_resume_text_hash(resume_file.raw_text),
            )

        profile = None
        parsed_resume = None
        if not force_parse:
            reusable_profile = find_reusable_resume_profile(db, resume_file)
            if reusable_profile:
                source_file, source_profile, reuse_source = reusable_profile
                profile, parsed_resume = reuse_candidate_profile_from_history(
                    db,
                    resume_file=resume_file,
                    source_file=source_file,
                    source_profile=source_profile,
                    reuse_source=reuse_source,
                )

        if not profile or parsed_resume is None:
            update_resume_file(db, resume_file, parse_status=constants.RESUME_FILE_PARSING, parse_error_message=None)
            parsed_resume = await parse_resume(
                resume_file.raw_text,
                prompt_config=get_active_prompt_pair(db, constants.PROMPT_KEY_RESUME_PARSE),
            )
            profile = upsert_candidate_profile(db, resume_file.id, parsed_resume)

        if not force_screen:
            reusable_result = find_reusable_screening_result(db, task, resume_file)
            if reusable_result:
                copy_screening_result_from_history(
                    db,
                    task_id=task.id,
                    candidate_id=profile.id,
                    resume_file_id=resume_file.id,
                    source_result=reusable_result,
                )
                return update_resume_file(
                    db,
                    resume_file,
                    parse_status=constants.RESUME_FILE_COMPLETED,
                    parse_error_message="复用历史岗位匹配结果，未重复调用 AI 初筛",
                )

        update_resume_file(db, resume_file, parse_status=constants.RESUME_FILE_SCREENING, parse_error_message=None)
        screening_result = await analyze_task_screening(
            jd_text=task.jd_text,
            jd_structured=parsed_jd,
            resume_text=resume_file.raw_text,
            candidate_profile=parsed_resume,
            prompt_config=get_active_prompt_pair(db, constants.PROMPT_KEY_SCREENING_MATCH),
        )
        upsert_screening_result(db, task.id, profile.id, resume_file.id, screening_result)
        return update_resume_file(db, resume_file, parse_status=constants.RESUME_FILE_COMPLETED, parse_error_message=None)
    except Exception as e:
        return update_resume_file(
            db,
            resume_file,
            parse_status=constants.RESUME_FILE_FAILED,
            parse_error_message=str(e),
        )


def _serialize_resume_file_for_step(resume_file) -> dict:
    return {
        "id": resume_file.id,
        "task_id": resume_file.task_id,
        "file_name": resume_file.file_name,
        "file_type": resume_file.file_type,
        "file_hash": resume_file.file_hash,
        "text_hash": resume_file.text_hash,
        "reuse_source": resume_file.reuse_source,
        "reused_resume_file_id": resume_file.reused_resume_file_id,
        "reused_profile_id": resume_file.reused_profile_id,
        "parse_status": resume_file.parse_status,
        "parse_error_message": resume_file.parse_error_message,
        "created_at": resume_file.created_at,
        "updated_at": resume_file.updated_at,
    }


def _serialize_interview_round(db_round) -> dict:
    try:
        question_json = json.loads(db_round.question_json) if db_round.question_json else []
        if not isinstance(question_json, list):
            question_json = []
    except Exception:
        question_json = []

    return {
        "id": db_round.id,
        "candidate_id": db_round.candidate_id,
        "task_id": db_round.task_id,
        "round_no": db_round.round_no,
        "round_name": db_round.round_name,
        "round_type": db_round.round_type,
        "round_focus": db_round.round_focus,
        "status": db_round.status,
        "scheduled_time": db_round.scheduled_time,
        "interviewer": db_round.interviewer,
        "interview_method": db_round.interview_method,
        "question_json": question_json,
        "record_text": db_round.record_text,
        "score": db_round.score,
        "conclusion": db_round.conclusion,
        "decision": db_round.decision,
        "created_at": db_round.created_at,
        "updated_at": db_round.updated_at,
    }


def _safe_json_load(value: Optional[str], default):
    if not value:
        return default
    try:
        parsed = json.loads(value)
        return parsed if parsed is not None else default
    except Exception:
        return default


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _mask_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    cleaned = str(phone).strip()
    if len(cleaned) <= 4:
        return "****"
    prefix = cleaned[:3] if len(cleaned) >= 7 else cleaned[0]
    return f"{prefix}****{cleaned[-4:]}"


def _mask_email(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    cleaned = str(email).strip()
    if "@" not in cleaned:
        return "***"
    name, domain = cleaned.split("@", 1)
    if not name:
        masked_name = "***"
    elif len(name) == 1:
        masked_name = f"{name}***"
    else:
        masked_name = f"{name[0]}***{name[-1]}"
    return f"{masked_name}@{domain}"


def _candidate_status_label(status: Optional[str]) -> str:
    if not status:
        return "未知"
    return constants.CANDIDATE_STATUS_LABELS.get(status, status)


def _latest_interview_time(db: Session, candidate_id: int) -> Optional[datetime]:
    round_item = (
        db.query(CandidateInterviewRound)
        .filter(CandidateInterviewRound.candidate_id == candidate_id, CandidateInterviewRound.deleted == 0)
        .order_by(
            CandidateInterviewRound.scheduled_time.desc().nullslast(),
            CandidateInterviewRound.updated_at.desc(),
            CandidateInterviewRound.created_at.desc(),
        )
        .first()
    )
    legacy_item = (
        db.query(InterviewRecord)
        .filter(InterviewRecord.candidate_id == candidate_id, InterviewRecord.deleted == 0)
        .order_by(InterviewRecord.interview_time.desc().nullslast(), InterviewRecord.created_at.desc())
        .first()
    )
    times = [
        round_item.scheduled_time or round_item.updated_at if round_item else None,
        legacy_item.interview_time or legacy_item.created_at if legacy_item else None,
    ]
    times = [item for item in times if item]
    return max(times) if times else None


def _latest_candidate_report(db: Session, candidate_id: int) -> Optional[StageReport]:
    return (
        db.query(StageReport)
        .filter(
            StageReport.candidate_id == candidate_id,
            StageReport.stage_type == constants.STAGE_CANDIDATE_EVALUATION,
            StageReport.status == constants.REPORT_STATUS_SUCCESS,
            StageReport.is_current == 1,
            StageReport.deleted == 0,
        )
        .order_by(StageReport.created_at.desc(), StageReport.report_version.desc())
        .first()
    )


def _build_report_candidate_item(db: Session, db_candidate: Candidate) -> dict:
    job = get_job(db, db_candidate.job_id)
    latest_report = _latest_candidate_report(db, db_candidate.id)
    return {
        "id": db_candidate.id,
        "candidate_name": db_candidate.candidate_name,
        "phone_masked": _mask_phone(db_candidate.phone),
        "email_masked": _mask_email(db_candidate.email),
        "job_id": db_candidate.job_id,
        "job_name": job.job_name if job else None,
        "job_type": job.job_type if job else None,
        "current_status": db_candidate.current_status,
        "current_status_label": _candidate_status_label(db_candidate.current_status),
        "latest_resume_time": db_candidate.updated_at or db_candidate.created_at,
        "latest_interview_time": _latest_interview_time(db, db_candidate.id),
        "has_report": latest_report is not None,
        "latest_report_id": latest_report.id if latest_report else None,
        "resume_match_score": db_candidate.resume_match_score,
        "updated_at": db_candidate.updated_at,
    }


def _build_report_candidate_item_from_row(
    db_candidate: Candidate,
    job: Optional[Job],
    latest_interview_time: Optional[datetime],
    latest_report_id: Optional[int],
) -> dict:
    return {
        "id": db_candidate.id,
        "candidate_name": db_candidate.candidate_name,
        "phone_masked": _mask_phone(db_candidate.phone),
        "email_masked": _mask_email(db_candidate.email),
        "job_id": db_candidate.job_id,
        "job_name": job.job_name if job else None,
        "job_type": job.job_type if job else None,
        "current_status": db_candidate.current_status,
        "current_status_label": _candidate_status_label(db_candidate.current_status),
        "latest_resume_time": db_candidate.updated_at or db_candidate.created_at,
        "latest_interview_time": latest_interview_time,
        "has_report": latest_report_id is not None,
        "latest_report_id": latest_report_id,
        "resume_match_score": db_candidate.resume_match_score,
        "updated_at": db_candidate.updated_at,
    }


def _resume_summary_from_candidate(db_candidate: Candidate) -> dict:
    parsed = _safe_json_load(db_candidate.parsed_resume_json, {})
    return {
        "name": db_candidate.candidate_name or parsed.get("name"),
        "work_years": db_candidate.work_years or parsed.get("work_years"),
        "education": db_candidate.education_level or parsed.get("education") or parsed.get("education_level"),
        "latest_company": parsed.get("latest_company") or parsed.get("current_company"),
        "latest_position": parsed.get("latest_position") or parsed.get("current_position"),
        "core_experience": parsed.get("core_experience") or parsed.get("summary") or parsed.get("self_summary"),
        "skills": parsed.get("skills") or parsed.get("skill_tags") or [],
    }


def _build_candidate_snapshot(db_candidate: Candidate) -> dict:
    return {
        "candidate_id": db_candidate.id,
        "candidate_name": db_candidate.candidate_name,
        "phone": db_candidate.phone,
        "email": db_candidate.email,
        "source": db_candidate.source,
        "current_status": db_candidate.current_status,
        "current_status_label": _candidate_status_label(db_candidate.current_status),
        "education_level": db_candidate.education_level,
        "work_years": db_candidate.work_years,
        "expected_salary": db_candidate.expected_salary,
        "available_date": db_candidate.available_date,
        "parsed_resume_json": _safe_json_load(db_candidate.parsed_resume_json, {}),
        "snapshot_time": datetime.now().isoformat(),
    }


def _build_jd_snapshot(job) -> dict:
    return {
        "job_position_id": job.id,
        "job_position_version": job.version or 1,
        "position_name": job.job_name,
        "position_type": job.job_type,
        "department_name": job.department,
        "jd_original_text": job.jd_text,
        "jd_structured_json": _safe_json_load(job.parsed_jd_json, {}),
        "screening_rules": _safe_json_load(job.screening_rules_json, []),
        "must_have": _safe_json_load(job.must_have_json, []),
        "nice_to_have": _safe_json_load(job.nice_to_have_json, []),
        "risk_points": _safe_json_load(job.risk_points_json, []),
        "interview_questions": _safe_json_load(job.interview_questions_json, []),
        "snapshot_time": datetime.now().isoformat(),
    }


def _build_resume_snapshot(db_candidate: Candidate, resume_version: int = 1) -> dict:
    return {
        "resume_id": db_candidate.id,
        "resume_version": resume_version or 1,
        "resume_text": db_candidate.resume_text,
        "resume_text_hash": _stable_hash(db_candidate.resume_text or ""),
        "summary": _resume_summary_from_candidate(db_candidate),
        "uploaded_at": db_candidate.created_at,
        "updated_at": db_candidate.updated_at,
        "snapshot_time": datetime.now().isoformat(),
    }


def _build_screening_snapshot(db: Session, candidate_id: int, job_id: int) -> Optional[dict]:
    report = get_latest_stage_report(db, candidate_id, constants.STAGE_RESUME_SCREENING)
    if not report or report.job_id != job_id:
        return None
    return {
        "report_id": report.id,
        "report_version": report.report_version,
        "score": report.score,
        "suggestion": report.suggestion,
        "risk_level": report.risk_level,
        "report_json": _safe_json_load(report.report_json, {}),
        "created_at": report.created_at,
    }


def _serialize_context_interview_round(db_round) -> dict:
    return {
        "record_key": f"round:{db_round.id}",
        "id": db_round.id,
        "source": "INTERVIEW_ROUND",
        "source_label": "面试管理",
        "round_no": db_round.round_no,
        "round_name": db_round.round_name,
        "round_type": db_round.round_type or db_round.round_name,
        "interview_time": db_round.scheduled_time or db_round.updated_at,
        "interviewer": db_round.interviewer,
        "interview_method": db_round.interview_method,
        "record_source": "文字录入",
        "record_text": db_round.record_text,
        "record_version": 1,
        "record_hash": _stable_hash(db_round.record_text or ""),
        "has_report": False,
        "score": db_round.score,
        "conclusion": db_round.conclusion,
        "decision": db_round.decision,
        "created_at": db_round.created_at,
        "updated_at": db_round.updated_at,
    }


def _serialize_context_legacy_record(db_record) -> dict:
    round_name = "初试" if db_record.round_type == constants.ROUND_TYPE_FIRST else "复试"
    return {
        "record_key": f"legacy:{db_record.id}",
        "id": db_record.id,
        "source": "INTERVIEW_RECORD",
        "source_label": "历史面试记录",
        "round_no": 1 if db_record.round_type == constants.ROUND_TYPE_FIRST else 2,
        "round_name": round_name,
        "round_type": round_name,
        "interview_time": db_record.interview_time or db_record.created_at,
        "interviewer": db_record.interviewer_name,
        "interview_method": None,
        "record_source": "文字录入",
        "record_text": db_record.record_text,
        "record_version": 1,
        "record_hash": _stable_hash(db_record.record_text or ""),
        "has_report": False,
        "score": None,
        "conclusion": None,
        "decision": None,
        "created_at": db_record.created_at,
        "updated_at": db_record.updated_at,
    }


def _list_context_interview_records(db: Session, candidate_id: int) -> list[dict]:
    rounds = [
        _serialize_context_interview_round(item)
        for item in get_candidate_interview_rounds(db, candidate_id)
        if item.record_text and item.record_text.strip()
    ]
    legacy = [
        _serialize_context_legacy_record(item)
        for item in get_interview_records(db, candidate_id, page=1, page_size=100)["items"]
        if item.record_text and item.record_text.strip()
    ]
    records = rounds + legacy
    records.sort(key=lambda item: item.get("interview_time") or item.get("updated_at") or datetime.min, reverse=True)
    return records


def _serialize_candidate_evaluation_report(report: StageReport, db: Session, reused: bool = False) -> dict:
    candidate = get_candidate(db, report.candidate_id)
    job = get_job(db, report.job_id)
    parsed = _safe_json_load(report.report_json, {})
    overview = parsed.get("candidate_overview", {}) if isinstance(parsed, dict) else {}
    return {
        "id": report.id,
        "candidate_id": report.candidate_id,
        "job_id": report.job_id,
        "stage_type": report.stage_type,
        "report_version": report.report_version,
        "score": report.score,
        "suggestion": report.suggestion,
        "risk_level": report.risk_level,
        "report_json": report.report_json,
        "input_snapshot_json": report.input_snapshot_json,
        "status": report.status,
        "error_message": report.error_message,
        "content_hash": report.content_hash,
        "report_key": report.report_key,
        "is_current": report.is_current,
        "generate_type": report.generate_type,
        "ai_provider": report.ai_provider,
        "ai_model": report.ai_model,
        "candidate_snapshot_json": report.candidate_snapshot_json,
        "jd_snapshot_json": report.jd_snapshot_json,
        "resume_snapshot_json": report.resume_snapshot_json,
        "interview_record_snapshot_json": report.interview_record_snapshot_json,
        "screening_result_snapshot_json": report.screening_result_snapshot_json,
        "candidate_name": candidate.candidate_name if candidate else overview.get("candidate_name"),
        "job_name": job.job_name if job else overview.get("job_title"),
        "reused": reused,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }


def _build_report_context(db: Session, db_candidate: Candidate) -> dict:
    job = get_job(db, db_candidate.job_id)
    reports = list_candidate_evaluation_reports(db, candidate_id=db_candidate.id, page=1, page_size=100)["items"]
    job_ids = {db_candidate.job_id}
    job_ids.update(report.job_id for report in reports if report.job_id)

    job_positions = []
    for job_id in job_ids:
        item = get_job(db, job_id)
        if not item:
            continue
        screening = _build_screening_snapshot(db, db_candidate.id, item.id)
        job_positions.append({
            "id": item.id,
            "job_name": item.job_name,
            "job_type": item.job_type,
            "department": item.department,
            "version": item.version or 1,
            "jd_text": item.jd_text,
            "screening_score": screening.get("score") if screening else None,
            "screening_suggestion": screening.get("suggestion") if screening else None,
            "is_current": item.id == db_candidate.job_id,
            "updated_at": item.updated_at,
        })

    resumes = [{
        "id": db_candidate.id,
        "version": 1,
        "label": "简历 v1",
        "uploaded_at": db_candidate.created_at,
        "updated_at": db_candidate.updated_at,
        "resume_text_hash": _stable_hash(db_candidate.resume_text or ""),
        "summary": _resume_summary_from_candidate(db_candidate),
        "has_resume_text": bool((db_candidate.resume_text or "").strip()),
    }] if (db_candidate.resume_text or "").strip() else []

    interview_records = _list_context_interview_records(db, db_candidate.id)
    screening_snapshot = _build_screening_snapshot(db, db_candidate.id, db_candidate.job_id)
    report_items = [_serialize_candidate_evaluation_report(item, db) for item in reports]

    return {
        "candidate": {
            **_build_report_candidate_item(db, db_candidate),
            "phone": db_candidate.phone,
            "email": db_candidate.email,
            "source": db_candidate.source,
        },
        "job_positions": job_positions,
        "resumes": resumes,
        "interview_records": interview_records,
        "screening_results": [screening_snapshot] if screening_snapshot else [],
        "reports": report_items,
        "defaults": {
            "jobPositionId": job.id if job else None,
            "jobPositionVersion": job.version if job else 1,
            "resumeId": db_candidate.id if resumes else None,
            "resumeVersion": 1 if resumes else None,
            "interviewRecordIds": [interview_records[0]["record_key"]] if len(interview_records) == 1 else [],
        },
    }


def _resolve_report_interview_records(db: Session, candidate_id: int, record_ids: list[Any]) -> list[dict]:
    resolved = []
    seen = set()
    for raw_id in record_ids or []:
        key = str(raw_id)
        if not key:
            continue
        if ":" in key:
            source, raw_value = key.split(":", 1)
        else:
            source, raw_value = "round", key
        try:
            record_id = int(raw_value)
        except ValueError:
            continue

        record = None
        if source == "legacy":
            db_record = db.query(InterviewRecord).filter(
                InterviewRecord.id == record_id,
                InterviewRecord.candidate_id == candidate_id,
                InterviewRecord.deleted == 0,
            ).first()
            if db_record and db_record.record_text and db_record.record_text.strip():
                record = _serialize_context_legacy_record(db_record)
        else:
            db_round = db.query(CandidateInterviewRound).filter(
                CandidateInterviewRound.id == record_id,
                CandidateInterviewRound.candidate_id == candidate_id,
                CandidateInterviewRound.deleted == 0,
            ).first()
            if db_round and db_round.record_text and db_round.record_text.strip():
                record = _serialize_context_interview_round(db_round)

        if record and record["record_key"] not in seen:
            seen.add(record["record_key"])
            resolved.append(record)
    resolved.sort(key=lambda item: item.get("interview_time") or item.get("updated_at") or datetime.min)
    return resolved


def _build_interview_text(records: list[dict]) -> str:
    chunks = []
    for item in records:
        title = item.get("round_name") or item.get("round_type") or "面试记录"
        time_text = item.get("interview_time") or ""
        interviewer = item.get("interviewer") or "未记录面试官"
        chunks.append(f"【{title}｜{time_text}｜{interviewer}】\n{item.get('record_text') or ''}")
    return "\n\n".join(chunks)


async def _generate_candidate_evaluation_report(db: Session, data: ReportGenerateRequest, force_regenerate: bool = False) -> dict:
    db_candidate = get_candidate(db, data.candidateId)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    if data.resumeId != db_candidate.id:
        raise HTTPException(status_code=400, detail="当前候选人暂无所选简历版本")

    db_job = get_job(db, data.jobPositionId)
    if not db_job or db_job.deleted:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if not (db_candidate.resume_text or "").strip():
        raise HTTPException(status_code=400, detail="该候选人暂无简历，请先上传简历")

    records = _resolve_report_interview_records(db, db_candidate.id, data.interviewRecordIds)
    if not records:
        raise HTTPException(status_code=400, detail="请先选择至少一条面试记录")

    candidate_snapshot = _build_candidate_snapshot(db_candidate)
    jd_snapshot = _build_jd_snapshot(db_job)
    resume_snapshot = _build_resume_snapshot(db_candidate, data.resumeVersion or 1)
    interview_snapshot = {"records": records, "snapshot_time": datetime.now().isoformat()}
    screening_snapshot = _build_screening_snapshot(db, db_candidate.id, db_job.id)

    report_key_source = {
        "candidate_id": db_candidate.id,
        "job_position_id": db_job.id,
        "job_position_version": data.jobPositionVersion or db_job.version or 1,
        "resume_id": data.resumeId,
        "resume_version": data.resumeVersion or 1,
        "resume_text_hash": resume_snapshot["resume_text_hash"],
        "interview_records": [
            {
                "record_key": item["record_key"],
                "record_version": item.get("record_version") or 1,
                "record_hash": item.get("record_hash"),
            }
            for item in records
        ],
    }
    report_key = _stable_hash(report_key_source)
    content_hash = _stable_hash({
        "report_key_source": report_key_source,
        "candidate_snapshot": candidate_snapshot,
        "jd_snapshot": jd_snapshot,
        "resume_snapshot": resume_snapshot,
        "interview_record_snapshot": interview_snapshot,
        "screening_result_snapshot": screening_snapshot,
    })

    force = force_regenerate or data.forceRegenerate
    existing_report = get_existing_current_report_by_key(db, db_candidate.id, report_key)
    if existing_report and not force:
        return _serialize_candidate_evaluation_report(existing_report, db, reused=True)

    report_version = get_next_report_version_for_key(db, report_key)
    settings = get_settings()
    input_snapshot = {
        "candidate_snapshot": candidate_snapshot,
        "jd_snapshot": jd_snapshot,
        "resume_snapshot": resume_snapshot,
        "interview_record_snapshot": interview_snapshot,
        "screening_result_snapshot": screening_snapshot,
        "report_key_source": report_key_source,
    }

    try:
        result = await analyze_candidate(
            candidate_name=db_candidate.candidate_name,
            job_title=db_job.job_name,
            jd_text=db_job.jd_text,
            resume_text=db_candidate.resume_text,
            interview_text=_build_interview_text(records),
        )
        overview = result.get("candidate_overview", {})
        report_json = json.dumps(result, ensure_ascii=False)

        db_report = create_stage_report(
            db=db,
            candidate_id=db_candidate.id,
            job_id=db_job.id,
            stage_type=constants.STAGE_CANDIDATE_EVALUATION,
            report_version=report_version,
            report_json=report_json,
            input_snapshot_json=json.dumps(input_snapshot, ensure_ascii=False, default=str),
            score=overview.get("match_score"),
            suggestion=overview.get("recommendation"),
            risk_level=overview.get("risk_level"),
            content_hash=content_hash,
            request_id=data.requestId,
            status=constants.REPORT_STATUS_SUCCESS,
            report_key=report_key,
            is_current=1,
            generate_type=constants.REPORT_GENERATE_MANUAL_RERUN if force else constants.REPORT_GENERATE_AUTO,
            ai_provider="deepseek",
            ai_model=settings.deepseek_model,
            candidate_snapshot_json=json.dumps(candidate_snapshot, ensure_ascii=False, default=str),
            jd_snapshot_json=json.dumps(jd_snapshot, ensure_ascii=False, default=str),
            resume_snapshot_json=json.dumps(resume_snapshot, ensure_ascii=False, default=str),
            interview_record_snapshot_json=json.dumps(interview_snapshot, ensure_ascii=False, default=str),
            screening_result_snapshot_json=json.dumps(screening_snapshot, ensure_ascii=False, default=str) if screening_snapshot else None,
        )
        if force:
            mark_report_versions_not_current(db, report_key, exclude_report_id=db_report.id)
            db.refresh(db_report)
        return _serialize_candidate_evaluation_report(db_report, db, reused=False)
    except HTTPException:
        raise
    except Exception as e:
        create_stage_report(
            db=db,
            candidate_id=db_candidate.id,
            job_id=db_job.id,
            stage_type=constants.STAGE_CANDIDATE_EVALUATION,
            report_version=report_version,
            report_json="{}",
            input_snapshot_json=json.dumps(input_snapshot, ensure_ascii=False, default=str),
            content_hash=content_hash,
            request_id=data.requestId,
            status=constants.REPORT_STATUS_FAILED,
            error_message=str(e),
            report_key=report_key,
            is_current=0,
            generate_type=constants.REPORT_GENERATE_MANUAL_RERUN if force else constants.REPORT_GENERATE_AUTO,
            ai_provider="deepseek",
            ai_model=settings.deepseek_model,
            candidate_snapshot_json=json.dumps(candidate_snapshot, ensure_ascii=False, default=str),
            jd_snapshot_json=json.dumps(jd_snapshot, ensure_ascii=False, default=str),
            resume_snapshot_json=json.dumps(resume_snapshot, ensure_ascii=False, default=str),
            interview_record_snapshot_json=json.dumps(interview_snapshot, ensure_ascii=False, default=str),
            screening_result_snapshot_json=json.dumps(screening_snapshot, ensure_ascii=False, default=str) if screening_snapshot else None,
        )
        raise HTTPException(status_code=500, detail=f"AI 评估报告生成失败: {str(e)}")


def _build_candidate_response(db, db_candidate) -> dict:
    job = get_job(db, db_candidate.job_id)
    candidate_dict = CandidateDetailResponse.model_validate(db_candidate).model_dump()
    candidate_dict["job_name"] = job.job_name if job else None
    candidate_dict["department"] = job.department if job else None
    candidate_dict["job_type"] = job.job_type if job else None
    return candidate_dict


def _build_candidate_list_item_response(db: Session, db_candidate) -> dict:
    job = get_job(db, db_candidate.job_id)
    candidate_dict = CandidateResponse.model_validate(db_candidate).model_dump()
    candidate_dict["job_name"] = job.job_name if job else None
    candidate_dict["department"] = job.department if job else None
    candidate_dict["job_type"] = job.job_type if job else None
    return candidate_dict


def _build_interview_flow_response(db: Session, db_candidate) -> dict:
    return {
        "candidate": CandidateResponse.model_validate(db_candidate).model_dump(),
        "rounds": [_serialize_interview_round(item) for item in get_candidate_interview_rounds(db, db_candidate.id)],
    }


def _build_round_questions(db: Session, db_candidate, round_no: int, based_on_previous: bool) -> list[dict]:
    db_job = get_job(db, db_candidate.job_id)
    screening_report = get_latest_stage_report(db, db_candidate.id, constants.STAGE_RESUME_SCREENING)
    previous_round = get_latest_completed_interview_round(db, db_candidate.id, before_round_no=round_no)
    return generate_round_questions(
        job_name=db_job.job_name if db_job else "",
        jd_text=db_job.jd_text if db_job else "",
        resume_text=db_candidate.resume_text,
        screening_report_json=screening_report.report_json if screening_report else None,
        round_no=round_no,
        previous_record_text=previous_round.record_text if previous_round else None,
        previous_conclusion=previous_round.conclusion if previous_round else None,
        based_on_previous=based_on_previous,
    )


def _normalize_question_round_type(round_type: Optional[str]) -> str:
    if not round_type:
        return constants.QUESTION_ROUND_TYPE_FIRST
    value = str(round_type).strip()
    alias_map = {
        "初试": constants.QUESTION_ROUND_TYPE_FIRST,
        "初面": constants.QUESTION_ROUND_TYPE_FIRST,
        "FIRST": constants.QUESTION_ROUND_TYPE_FIRST,
        "复试": constants.QUESTION_ROUND_TYPE_SECOND,
        "复面": constants.QUESTION_ROUND_TYPE_SECOND,
        "SECOND": constants.QUESTION_ROUND_TYPE_SECOND,
        "终面": constants.QUESTION_ROUND_TYPE_FINAL,
        "FINAL": constants.QUESTION_ROUND_TYPE_FINAL,
        "HR面": constants.QUESTION_ROUND_TYPE_HR,
        "HR 面": constants.QUESTION_ROUND_TYPE_HR,
        "HR": constants.QUESTION_ROUND_TYPE_HR,
    }
    return alias_map.get(value, value)


def _question_round_type_label(round_type: Optional[str]) -> str:
    if not round_type:
        return "未标记轮次"
    return constants.INTERVIEW_QUESTION_ROUND_TYPE_LABELS.get(round_type, round_type)


def _resolve_question_request(data: Optional[CandidateInterviewQuestionsGenerateRequest]) -> tuple[str, Optional[int], Optional[str]]:
    if not data:
        return constants.QUESTION_ROUND_TYPE_FIRST, None, None
    round_type = _normalize_question_round_type(data.roundType or data.round_type)
    if round_type not in constants.VALID_INTERVIEW_QUESTION_ROUND_TYPES:
        raise HTTPException(status_code=400, detail="无效的问题类型")
    round_no = data.roundNo or data.round_no
    request_id = data.requestId or data.request_id
    return round_type, round_no, request_id


def _serialize_interview_questions_report(report: StageReport, db: Session) -> dict:
    candidate = get_candidate(db, report.candidate_id)
    job = get_job(db, report.job_id)
    parsed = _safe_json_load(report.report_json, {})
    questions = parsed.get("questions") if isinstance(parsed, dict) else []
    if not isinstance(questions, list):
        questions = []
    round_type = report.round_type or (parsed.get("round_type") if isinstance(parsed, dict) else None)
    round_no = report.round_no or (parsed.get("round_no") if isinstance(parsed, dict) else None)

    return {
        "id": report.id,
        "candidate_id": report.candidate_id,
        "job_id": report.job_id,
        "stage_type": report.stage_type,
        "report_version": report.report_version,
        "round_type": round_type,
        "round_type_label": _question_round_type_label(round_type),
        "round_no": round_no,
        "questions": questions,
        "question_count": len(questions),
        "report_json": report.report_json,
        "input_snapshot_json": report.input_snapshot_json,
        "content_hash": report.content_hash,
        "report_key": report.report_key,
        "is_current": report.is_current,
        "generate_type": report.generate_type,
        "ai_provider": report.ai_provider,
        "ai_model": report.ai_model,
        "candidate_snapshot_json": report.candidate_snapshot_json,
        "jd_snapshot_json": report.jd_snapshot_json,
        "resume_snapshot_json": report.resume_snapshot_json,
        "screening_result_snapshot_json": report.screening_result_snapshot_json,
        "candidate_name": candidate.candidate_name if candidate else None,
        "job_name": job.job_name if job else None,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }


async def _build_candidate_interview_questions(
    db: Session,
    db_candidate: Candidate,
    request_id: Optional[str] = None,
    round_type: str = constants.QUESTION_ROUND_TYPE_FIRST,
    round_no: Optional[int] = None,
) -> dict:
    db_job = get_job(db, db_candidate.job_id)
    if not db_job or db_job.deleted:
        raise HTTPException(status_code=404, detail="关联岗位不存在")
    if not (db_job.jd_text or "").strip():
        raise HTTPException(status_code=400, detail="当前岗位暂无 JD，不能生成面试问题")
    if not (db_candidate.resume_text or "").strip():
        raise HTTPException(status_code=400, detail="该候选人暂无简历，请先上传简历")

    screening_report = get_latest_stage_report(db, db_candidate.id, constants.STAGE_RESUME_SCREENING)
    questions = await generate_candidate_questions(
        job_name=db_job.job_name,
        jd_text=db_job.jd_text,
        resume_text=db_candidate.resume_text,
        screening_report_json=screening_report.report_json if screening_report else None,
        round_type=round_type,
    )

    candidate_snapshot = _build_candidate_snapshot(db_candidate)
    jd_snapshot = _build_jd_snapshot(db_job)
    resume_snapshot = _build_resume_snapshot(db_candidate, 1)
    screening_snapshot = _build_screening_snapshot(db, db_candidate.id, db_job.id)
    report_key_source = {
        "candidate_id": db_candidate.id,
        "job_position_id": db_job.id,
        "job_position_version": db_job.version or 1,
        "resume_id": db_candidate.id,
        "resume_version": 1,
        "resume_text_hash": resume_snapshot["resume_text_hash"],
        "jd_text_hash": _stable_hash(db_job.jd_text or ""),
        "basis": "JOB_AND_RESUME",
        "round_type": round_type,
        "round_no": round_no,
    }
    report_key = _stable_hash(report_key_source)
    content_hash = _stable_hash(report_key_source)
    input_snapshot = {
        "candidate_snapshot": candidate_snapshot,
        "jd_snapshot": jd_snapshot,
        "resume_snapshot": resume_snapshot,
        "screening_result_snapshot": screening_snapshot,
        "report_key_source": report_key_source,
        "round_type": round_type,
        "round_type_label": _question_round_type_label(round_type),
        "round_no": round_no,
    }
    report_body = {
        "questions": questions,
        "question_count": len(questions),
        "basis": "JOB_AND_RESUME",
        "round_type": round_type,
        "round_type_label": _question_round_type_label(round_type),
        "round_no": round_no,
        "candidate_name": db_candidate.candidate_name,
        "job_name": db_job.job_name,
        "generated_at": datetime.now().isoformat(),
    }
    settings = get_settings()
    ai_provider = "deepseek_with_local_fallback" if settings.deepseek_api_key else "local_rule"
    ai_model = settings.deepseek_model if settings.deepseek_api_key else "interview_question_service"

    db_report = create_stage_report(
        db=db,
        candidate_id=db_candidate.id,
        job_id=db_job.id,
        stage_type=constants.STAGE_INTERVIEW_QUESTIONS,
        report_version=get_next_report_version(db, db_candidate.id, constants.STAGE_INTERVIEW_QUESTIONS),
        report_json=json.dumps(report_body, ensure_ascii=False, default=str),
        input_snapshot_json=json.dumps(input_snapshot, ensure_ascii=False, default=str),
        suggestion=f"已生成 {len(questions)} 道面试问题",
        content_hash=content_hash,
        request_id=request_id,
        status=constants.REPORT_STATUS_SUCCESS,
        report_key=report_key,
        is_current=1,
        round_type=round_type,
        round_no=round_no,
        generate_type=constants.REPORT_GENERATE_MANUAL_RERUN,
        ai_provider=ai_provider,
        ai_model=ai_model,
        candidate_snapshot_json=json.dumps(candidate_snapshot, ensure_ascii=False, default=str),
        jd_snapshot_json=json.dumps(jd_snapshot, ensure_ascii=False, default=str),
        resume_snapshot_json=json.dumps(resume_snapshot, ensure_ascii=False, default=str),
        screening_result_snapshot_json=json.dumps(screening_snapshot, ensure_ascii=False, default=str) if screening_snapshot else None,
    )
    create_interview_question_items(db, db_report, questions, resume_id=db_candidate.id)
    mark_stage_reports_not_current(
        db,
        db_candidate.id,
        constants.STAGE_INTERVIEW_QUESTIONS,
        report_key=report_key,
        exclude_report_id=db_report.id,
    )
    return _serialize_interview_questions_report(db_report, db)


def _validate_interview_round_creation(db: Session, db_candidate, requested_round_no: Optional[int] = None) -> int:
    allowed_statuses = {
        constants.STATUS_INTERVIEW_WAITING,
        constants.STATUS_RESUME_SCREENING_DONE,
        constants.STATUS_RESUME_PASSED,
        constants.STATUS_RESUME_TBD,
    }
    if db_candidate.current_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="候选人未处于待安排面试状态，请先完成简历筛选或重新打开流程")

    next_round_no = get_next_interview_round_no(db, db_candidate.id)
    if requested_round_no is not None and requested_round_no != next_round_no:
        raise HTTPException(status_code=400, detail=f"面试轮次必须按顺序创建，下一轮应为第 {next_round_no} 轮")
    return next_round_no


def _has_later_interview_round(db: Session, candidate_id: int, round_no: int) -> bool:
    return any(item.round_no > round_no for item in get_candidate_interview_rounds(db, candidate_id))


# ============== 候选人接口 ==============
@app.post("/api/candidates", response_model=CandidateResponse)
def create_candidate_endpoint(candidate_data: CandidateCreate, db: Session = Depends(get_db)):
    if not get_job(db, candidate_data.job_id):
        raise HTTPException(status_code=404, detail="岗位不存在")
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
    result = get_candidate_list(db, job_id=job_id, candidate_name=candidate_name, source=source, current_status=current_status, page=page, page_size=page_size)
    result["items"] = [_build_candidate_list_item_response(db, item) for item in result["items"]]
    return result


@app.get("/api/candidates/{candidate_id}", response_model=CandidateDetailResponse)
def get_candidate_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")

    job = get_job(db, db_candidate.job_id)
    candidate_dict = CandidateDetailResponse.model_validate(db_candidate).model_dump()
    candidate_dict["job_name"] = job.job_name if job else None
    candidate_dict["department"] = job.department if job else None
    candidate_dict["job_type"] = job.job_type if job else None  # 新增
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


# ============== 候选人评估报告接口 ==============
@app.get("/api/report/candidates", response_model=ReportCandidateListResponse)
def list_report_candidates_endpoint(
    keyword: Optional[str] = Query(None),
    jobPositionId: Optional[int] = Query(None, ge=1),
    job_position_id: Optional[int] = Query(None, ge=1),
    status: Optional[str] = Query(None),
    hasInterviewRecord: Optional[bool] = Query(None),
    hasReport: Optional[bool] = Query(None),
    sortBy: Optional[str] = Query("recentInterview"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    latest_round = (
        db.query(
            CandidateInterviewRound.candidate_id.label("candidate_id"),
            func.max(
                func.coalesce(
                    CandidateInterviewRound.scheduled_time,
                    CandidateInterviewRound.updated_at,
                    CandidateInterviewRound.created_at,
                )
            ).label("latest_round_time"),
        )
        .filter(CandidateInterviewRound.deleted == 0)
        .group_by(CandidateInterviewRound.candidate_id)
        .subquery()
    )
    latest_legacy = (
        db.query(
            InterviewRecord.candidate_id.label("candidate_id"),
            func.max(func.coalesce(InterviewRecord.interview_time, InterviewRecord.created_at)).label("latest_legacy_time"),
        )
        .filter(InterviewRecord.deleted == 0)
        .group_by(InterviewRecord.candidate_id)
        .subquery()
    )
    latest_report = (
        db.query(
            StageReport.candidate_id.label("candidate_id"),
            func.max(StageReport.id).label("latest_report_id"),
        )
        .filter(
            StageReport.stage_type == constants.STAGE_CANDIDATE_EVALUATION,
            StageReport.status == constants.REPORT_STATUS_SUCCESS,
            StageReport.is_current == 1,
            StageReport.deleted == 0,
        )
        .group_by(StageReport.candidate_id)
        .subquery()
    )
    latest_interview_time = case(
        (latest_round.c.latest_round_time.is_(None), latest_legacy.c.latest_legacy_time),
        (latest_legacy.c.latest_legacy_time.is_(None), latest_round.c.latest_round_time),
        (latest_round.c.latest_round_time >= latest_legacy.c.latest_legacy_time, latest_round.c.latest_round_time),
        else_=latest_legacy.c.latest_legacy_time,
    ).label("latest_interview_time")

    query = (
        db.query(
            Candidate,
            Job,
            latest_interview_time,
            latest_report.c.latest_report_id,
        )
        .outerjoin(Job, and_(Job.id == Candidate.job_id, Job.deleted == 0))
        .outerjoin(latest_round, latest_round.c.candidate_id == Candidate.id)
        .outerjoin(latest_legacy, latest_legacy.c.candidate_id == Candidate.id)
        .outerjoin(latest_report, latest_report.c.candidate_id == Candidate.id)
        .filter(Candidate.deleted == 0)
    )
    job_id = job_position_id or jobPositionId
    if job_id:
        query = query.filter(Candidate.job_id == job_id)
    if status:
        query = query.filter(Candidate.current_status == status)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Candidate.candidate_name.ilike(pattern),
                Candidate.phone.ilike(pattern),
                Candidate.email.ilike(pattern),
            )
        )

    if hasInterviewRecord is not None:
        if hasInterviewRecord:
            query = query.filter(latest_interview_time.is_not(None))
        else:
            query = query.filter(latest_interview_time.is_(None))
    if hasReport is not None:
        if hasReport:
            query = query.filter(latest_report.c.latest_report_id.is_not(None))
        else:
            query = query.filter(latest_report.c.latest_report_id.is_(None))

    final_page_size = page_size or pageSize
    total = query.count()
    if sortBy == "recentResume":
        query = query.order_by(Candidate.updated_at.desc(), Candidate.created_at.desc())
    else:
        query = query.order_by(
            latest_interview_time.is_(None).asc(),
            latest_interview_time.desc(),
            Candidate.updated_at.desc(),
        )

    offset = (page - 1) * final_page_size
    rows = query.offset(offset).limit(final_page_size).all()
    items = [
        _build_report_candidate_item_from_row(candidate, job, latest_time, latest_report_id)
        for candidate, job, latest_time, latest_report_id in rows
    ]
    return {
        "total": total,
        "page": page,
        "page_size": final_page_size,
        "items": items,
    }


@app.get("/api/report/candidates/{candidate_id}/context", response_model=ReportCandidateContextResponse)
def get_report_candidate_context_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    return _build_report_context(db, db_candidate)


@app.post("/api/reports/generate", response_model=CandidateEvaluationReportResponse)
async def generate_candidate_report_endpoint(data: ReportGenerateRequest, db: Session = Depends(get_db)):
    return await _generate_candidate_evaluation_report(db, data, force_regenerate=False)


@app.get("/api/reports", response_model=CandidateEvaluationReportListResponse)
def list_candidate_reports_endpoint(
    candidateId: Optional[int] = Query(None, ge=1),
    candidate_id: Optional[int] = Query(None, ge=1),
    jobPositionId: Optional[int] = Query(None, ge=1),
    job_position_id: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = list_candidate_evaluation_reports(
        db=db,
        candidate_id=candidate_id or candidateId,
        job_id=job_position_id or jobPositionId,
        page=page,
        page_size=page_size or pageSize,
    )
    result["items"] = [_serialize_candidate_evaluation_report(item, db) for item in result["items"]]
    return result


@app.get("/api/reports/{report_id}", response_model=CandidateEvaluationReportResponse)
def get_candidate_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    db_report = get_stage_report(db, report_id)
    if not db_report or db_report.stage_type != constants.STAGE_CANDIDATE_EVALUATION:
        raise HTTPException(status_code=404, detail="评估报告不存在")
    return _serialize_candidate_evaluation_report(db_report, db)


@app.post("/api/reports/{report_id}/regenerate", response_model=CandidateEvaluationReportResponse)
async def regenerate_candidate_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    db_report = get_stage_report(db, report_id)
    if not db_report or db_report.stage_type != constants.STAGE_CANDIDATE_EVALUATION:
        raise HTTPException(status_code=404, detail="评估报告不存在")

    input_snapshot = _safe_json_load(db_report.input_snapshot_json, {})
    key_source = input_snapshot.get("report_key_source") or {}
    interview_records = key_source.get("interview_records") or []
    data = ReportGenerateRequest(
        candidateId=db_report.candidate_id,
        jobPositionId=db_report.job_id,
        jobPositionVersion=key_source.get("job_position_version") or 1,
        resumeId=key_source.get("resume_id") or db_report.candidate_id,
        resumeVersion=key_source.get("resume_version") or 1,
        interviewRecordIds=[item.get("record_key") for item in interview_records if item.get("record_key")],
        forceRegenerate=True,
    )
    return await _generate_candidate_evaluation_report(db, data, force_regenerate=True)


@app.get("/api/candidates/{candidate_id}/interview-questions", response_model=CandidateInterviewQuestionsListResponse)
def list_candidate_interview_questions_endpoint(
    candidate_id: int,
    roundType: Optional[str] = Query(None),
    round_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    resolved_round_type = None
    requested_round_type = round_type or roundType
    if requested_round_type:
        resolved_round_type = _normalize_question_round_type(requested_round_type)
        if resolved_round_type not in constants.VALID_INTERVIEW_QUESTION_ROUND_TYPES:
            raise HTTPException(status_code=400, detail="无效的问题类型")
    result = list_interview_question_reports(
        db=db,
        candidate_id=candidate_id,
        round_type=resolved_round_type,
        page=page,
        page_size=page_size or pageSize,
    )
    result["items"] = [_serialize_interview_questions_report(item, db) for item in result["items"]]
    return result


@app.get("/api/candidates/{candidate_id}/interview-questions/latest", response_model=CandidateInterviewQuestionsResponse)
def get_latest_candidate_interview_questions_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    db_report = get_latest_stage_report(db, candidate_id, constants.STAGE_INTERVIEW_QUESTIONS)
    if not db_report:
        raise HTTPException(status_code=404, detail="暂无面试问题")
    return _serialize_interview_questions_report(db_report, db)


@app.post("/api/candidates/{candidate_id}/interview-questions/generate", response_model=CandidateInterviewQuestionsResponse)
async def generate_candidate_interview_questions_endpoint(
    candidate_id: int,
    data: Optional[CandidateInterviewQuestionsGenerateRequest] = None,
    db: Session = Depends(get_db),
):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    round_type, round_no, request_id = _resolve_question_request(data)
    return await _build_candidate_interview_questions(
        db,
        db_candidate,
        request_id=request_id,
        round_type=round_type,
        round_no=round_no,
    )


@app.get("/api/interview-questions/stats", response_model=InterviewQuestionStatsResponse)
def get_interview_question_stats_endpoint(
    candidateId: Optional[int] = Query(None, ge=1),
    candidate_id: Optional[int] = Query(None, ge=1),
    jobPositionId: Optional[int] = Query(None, ge=1),
    job_id: Optional[int] = Query(None, ge=1),
    roundType: Optional[str] = Query(None),
    round_type: Optional[str] = Query(None),
    dimension: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    resolved_round_type = None
    requested_round_type = round_type or roundType
    if requested_round_type:
        resolved_round_type = _normalize_question_round_type(requested_round_type)
        if resolved_round_type not in constants.VALID_INTERVIEW_QUESTION_ROUND_TYPES:
            raise HTTPException(status_code=400, detail="无效的问题类型")
    items = list_interview_question_stats(
        db=db,
        candidate_id=candidate_id or candidateId,
        job_id=job_id or jobPositionId,
        round_type=resolved_round_type,
        dimension=dimension,
        limit=limit,
    )
    for item in items:
        item["round_type_label"] = _question_round_type_label(item.get("round_type"))
    return {"total": len(items), "items": items}


@app.get("/api/interview-questions/{report_id}", response_model=CandidateInterviewQuestionsResponse)
def get_interview_questions_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    db_report = get_stage_report(db, report_id)
    if not db_report or db_report.stage_type != constants.STAGE_INTERVIEW_QUESTIONS:
        raise HTTPException(status_code=404, detail="面试问题记录不存在")
    return _serialize_interview_questions_report(db_report, db)


# ============== 开放式面试轮次接口 ==============
@app.post("/api/interview-rounds/batch-query", response_model=CandidateInterviewRoundsBatchResponse)
def batch_list_candidate_interview_rounds_endpoint(
    data: CandidateInterviewRoundsBatchRequest,
    db: Session = Depends(get_db),
):
    raw_ids = data.candidate_ids if data.candidate_ids is not None else data.candidateIds
    candidate_ids = [candidate_id for candidate_id in (raw_ids or []) if candidate_id and candidate_id > 0]
    candidate_ids = list(dict.fromkeys(candidate_ids))
    if len(candidate_ids) > 500:
        raise HTTPException(status_code=400, detail="单次最多查询 500 个候选人的面试轮次")

    rounds_by_candidate_id = get_candidate_interview_rounds_by_candidate_ids(db, candidate_ids)
    return {
        "items": [
            {
                "candidate_id": candidate_id,
                "rounds": [_serialize_interview_round(item) for item in rounds_by_candidate_id.get(candidate_id, [])],
            }
            for candidate_id in candidate_ids
        ]
    }


@app.get("/api/candidates/{candidate_id}/interview-rounds", response_model=list[CandidateInterviewRoundResponse])
def list_candidate_interview_rounds_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    return [_serialize_interview_round(item) for item in get_candidate_interview_rounds(db, candidate_id)]


@app.post("/api/candidates/{candidate_id}/interview-rounds", response_model=CandidateInterviewRoundResponse)
def create_candidate_interview_round_endpoint(
    candidate_id: int,
    data: CandidateInterviewRoundCreate,
    db: Session = Depends(get_db),
):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    if has_active_interview_round(db, candidate_id):
        raise HTTPException(status_code=400, detail="当前已有待进行面试，请先完成或取消后再创建新轮次")
    round_no = _validate_interview_round_creation(db, db_candidate, data.round_no)

    data_dict = data.model_dump()
    data_dict["round_no"] = round_no
    data_dict["round_name"] = data.round_name or f"第 {round_no} 轮面试"

    questions = data.question_json or []
    if data.generate_questions and not questions:
        questions = _build_round_questions(db, db_candidate, round_no, data.based_on_previous)

    db_round = create_candidate_interview_round(
        db=db,
        db_candidate=db_candidate,
        data=data_dict,
        question_json=json.dumps(questions, ensure_ascii=False),
    )
    return _serialize_interview_round(db_round)


@app.put("/api/candidates/{candidate_id}/interview-rounds/{round_id}", response_model=CandidateInterviewRoundResponse)
def update_candidate_interview_round_endpoint(
    candidate_id: int,
    round_id: int,
    data: CandidateInterviewRoundUpdate,
    db: Session = Depends(get_db),
):
    db_round = get_candidate_interview_round(db, candidate_id, round_id)
    if not db_round:
        raise HTTPException(status_code=404, detail="面试轮次不存在")
    if db_round.status == constants.INTERVIEW_ROUND_STATUS_CANCELED:
        raise HTTPException(status_code=400, detail="已取消的面试轮次不能修改")

    db_round = update_candidate_interview_round(db, db_round, data.model_dump(exclude_unset=True))
    return _serialize_interview_round(db_round)


@app.post("/api/candidates/{candidate_id}/interview-rounds/{round_id}/record", response_model=CandidateInterviewRoundResponse)
def submit_candidate_interview_record_endpoint(
    candidate_id: int,
    round_id: int,
    data: CandidateInterviewRecordSubmit,
    db: Session = Depends(get_db),
):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    db_round = get_candidate_interview_round(db, candidate_id, round_id)
    if not db_round:
        raise HTTPException(status_code=404, detail="面试轮次不存在")
    if db_round.status == constants.INTERVIEW_ROUND_STATUS_CANCELED:
        raise HTTPException(status_code=400, detail="已取消的面试轮次不能填写记录")

    db_round = submit_candidate_interview_record(db, db_candidate, db_round, data.model_dump())
    return _serialize_interview_round(db_round)


@app.post("/api/candidates/{candidate_id}/interview-rounds/{round_id}/decision", response_model=CandidateInterviewFlowResponse)
def decide_candidate_interview_round_endpoint(
    candidate_id: int,
    round_id: int,
    data: CandidateInterviewDecisionSubmit,
    db: Session = Depends(get_db),
):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    db_round = get_candidate_interview_round(db, candidate_id, round_id)
    if not db_round:
        raise HTTPException(status_code=404, detail="面试轮次不存在")
    if db_round.status != constants.INTERVIEW_ROUND_STATUS_COMPLETED:
        raise HTTPException(status_code=400, detail="面试完成后才能做决策")
    if data.decision not in constants.VALID_INTERVIEW_DECISIONS:
        raise HTTPException(status_code=400, detail="无效的面试决策")
    if db_round.decision:
        raise HTTPException(status_code=400, detail="该轮面试已完成决策，不能重复决策")

    if data.decision == constants.INTERVIEW_DECISION_NEXT:
        if _has_later_interview_round(db, candidate_id, db_round.round_no):
            raise HTTPException(status_code=400, detail="该轮面试已有后续轮次，请在最新流程节点继续处理")
        if has_active_interview_round(db, candidate_id):
            raise HTTPException(status_code=400, detail="当前已有待进行面试，不能重复创建下一轮")
        next_round_data = data.next_round or CandidateInterviewRoundCreate()
        next_dict = next_round_data.model_dump()
        next_round_no = get_next_interview_round_no(db, candidate_id)
        if next_round_data.round_no is not None and next_round_data.round_no != next_round_no:
            raise HTTPException(status_code=400, detail=f"面试轮次必须按顺序创建，下一轮应为第 {next_round_no} 轮")
        next_dict["round_no"] = next_round_no
        next_dict["round_name"] = next_round_data.round_name or f"第 {next_round_no} 轮面试"

        questions = next_round_data.question_json or []
        if next_round_data.generate_questions and not questions:
            questions = _build_round_questions(db, db_candidate, next_round_no, next_round_data.based_on_previous)

        try:
            apply_candidate_interview_decision(db, db_candidate, db_round, data.decision, commit=False)
            db_candidate = get_candidate(db, candidate_id)
            create_candidate_interview_round(
                db=db,
                db_candidate=db_candidate,
                data=next_dict,
                question_json=json.dumps(questions, ensure_ascii=False),
                commit=False,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
    else:
        apply_candidate_interview_decision(db, db_candidate, db_round, data.decision)

    db_candidate = get_candidate(db, candidate_id)
    return _build_interview_flow_response(db, db_candidate)


@app.post("/api/candidates/{candidate_id}/interview-rounds/{round_id}/cancel", response_model=CandidateInterviewRoundResponse)
def cancel_candidate_interview_round_endpoint(candidate_id: int, round_id: int, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    db_round = get_candidate_interview_round(db, candidate_id, round_id)
    if not db_round:
        raise HTTPException(status_code=404, detail="面试轮次不存在")
    if db_round.status != constants.INTERVIEW_ROUND_STATUS_SCHEDULED:
        raise HTTPException(status_code=400, detail="只有待进行面试可以取消")

    db_round = cancel_candidate_interview_round(db, db_candidate, db_round)
    return _serialize_interview_round(db_round)


@app.post("/api/candidates/{candidate_id}/interview-rounds/{round_id}/questions", response_model=CandidateInterviewRoundResponse)
def regenerate_candidate_interview_questions_endpoint(
    candidate_id: int,
    round_id: int,
    based_on_previous: bool = True,
    db: Session = Depends(get_db),
):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    db_round = get_candidate_interview_round(db, candidate_id, round_id)
    if not db_round:
        raise HTTPException(status_code=404, detail="面试轮次不存在")

    questions = _build_round_questions(db, db_candidate, db_round.round_no, based_on_previous)
    db_round = update_candidate_interview_questions(db, db_round, json.dumps(questions, ensure_ascii=False))
    return _serialize_interview_round(db_round)


@app.post("/api/candidates/{candidate_id}/interview-rounds/reopen", response_model=CandidateInterviewFlowResponse)
def reopen_candidate_interview_flow_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    db_candidate = reopen_candidate_interview_flow(db, db_candidate)
    return _build_interview_flow_response(db, db_candidate)


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
            mark_candidate_waiting_interview_after_screening(db, candidate_id)
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
        mark_candidate_waiting_interview_after_screening(db, candidate_id)

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


# ============== 复试记录接口 ==============
@app.post("/api/candidates/{candidate_id}/second-interview-record", response_model=InterviewRecordResponse)
def create_second_interview_record_endpoint(candidate_id: int, data: InterviewRecordCreate, db: Session = Depends(get_db)):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")

    try:
        db_record = create_interview_record(
            db=db,
            candidate_id=candidate_id,
            job_id=db_candidate.job_id,
            round_type=constants.ROUND_TYPE_SECOND,
            record_text=data.record_text,
            interviewer_name=data.interviewer_name,
            interview_time=data.interview_time,
        )
        return db_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/candidates/{candidate_id}/second-interview-record/latest", response_model=InterviewRecordResponse)
def get_latest_second_interview_record_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_record = get_latest_interview_record(db, candidate_id, constants.ROUND_TYPE_SECOND)
    if not db_record:
        raise HTTPException(status_code=404, detail="暂无复试记录")
    return db_record


@app.get("/api/candidates/{candidate_id}/second-interview-record", response_model=dict)
def list_second_interview_records_endpoint(
    candidate_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_interview_records(db, candidate_id, round_type=constants.ROUND_TYPE_SECOND, page=page, page_size=page_size)


# ============== 复试分析接口 ==============
@app.post("/api/candidates/{candidate_id}/second-interview-analysis", response_model=StageReportResponse)
async def trigger_second_interview_analysis_endpoint(candidate_id: int, data: FirstInterviewAnalysisRequest, db: Session = Depends(get_db)):
    """触发复试分析"""
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")

    db_job = get_job(db, db_candidate.job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="关联岗位不存在")

    from app.crud_new import get_interview_record
    db_record = get_interview_record(db, data.interview_record_id)
    if not db_record or db_record.candidate_id != candidate_id:
        raise HTTPException(status_code=404, detail="复试记录不存在")

    # 获取初试分析报告
    first_interview_report = get_latest_stage_report(db, candidate_id, constants.STAGE_FIRST_INTERVIEW)
    first_interview_report_json = first_interview_report.report_json if first_interview_report else "{}"

    content_hash = compute_content_hash(
        db_job.jd_text,
        db_candidate.resume_text,
        first_interview_report_json,
        db_record.record_text,
    )

    if not data.force:
        existing_report = get_latest_stage_report(db, candidate_id, constants.STAGE_SECOND_INTERVIEW)
        if existing_report and existing_report.content_hash == content_hash:
            return existing_report

    from app.crud_new import get_next_report_version
    report_version = get_next_report_version(db, candidate_id, constants.STAGE_SECOND_INTERVIEW)

    input_snapshot = {
        "jd_text": db_job.jd_text,
        "resume_text": db_candidate.resume_text,
        "first_interview_report": first_interview_report_json,
        "record_text": db_record.record_text,
        "interviewer_name": db_record.interviewer_name,
        "interview_time": str(db_record.interview_time) if db_record.interview_time else None,
    }

    try:
        result = await analyze_second_interview(
            db_job.jd_text,
            db_candidate.resume_text,
            first_interview_report_json,
            db_record.record_text,
        )
        report_json = json.dumps(result, ensure_ascii=False)

        db_report = create_stage_report(
            db=db,
            candidate_id=candidate_id,
            job_id=db_candidate.job_id,
            stage_type=constants.STAGE_SECOND_INTERVIEW,
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
            stage_type=constants.STAGE_SECOND_INTERVIEW,
            score=result.get("score"),
            suggestion=result.get("suggestion"),
        )

        return db_report
    except Exception as e:
        create_stage_report(
            db=db,
            candidate_id=candidate_id,
            job_id=db_candidate.job_id,
            stage_type=constants.STAGE_SECOND_INTERVIEW,
            report_version=report_version,
            report_json="{}",
            input_snapshot_json=json.dumps(input_snapshot, ensure_ascii=False),
            content_hash=content_hash,
            request_id=data.request_id,
            status=constants.REPORT_STATUS_FAILED,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=f"复试分析失败: {str(e)}")


@app.get("/api/candidates/{candidate_id}/second-interview-analysis/latest", response_model=StageReportResponse)
def get_latest_second_interview_analysis_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    db_report = get_latest_stage_report(db, candidate_id, constants.STAGE_SECOND_INTERVIEW)
    if not db_report:
        raise HTTPException(status_code=404, detail="暂无复试分析报告")
    return db_report


# ============== 状态日志接口 ==============
@app.get("/api/candidates/{candidate_id}/status-logs", response_model=list[CandidateStatusLogResponse])
def get_candidate_status_logs_endpoint(candidate_id: int, db: Session = Depends(get_db)):
    from app.models import CandidateStatusLog
    logs = db.query(CandidateStatusLog).filter(CandidateStatusLog.candidate_id == candidate_id).all()
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
