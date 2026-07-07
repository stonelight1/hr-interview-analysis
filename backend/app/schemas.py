from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


# ============== 旧系统兼容 Schema ==============
class AnalysisCreate(BaseModel):
    candidate_name: str = Field(..., min_length=1, max_length=100)
    job_title: str = Field(..., min_length=1, max_length=100)
    jd_text: str = Field(..., min_length=1)
    resume_text: str = Field(..., min_length=1)
    interview_text: str = Field(..., min_length=1)


class AnalysisResponse(BaseModel):
    id: int
    candidate_name: str
    job_title: str
    match_score: Optional[int] = None
    recommendation: Optional[str] = None
    risk_level: Optional[str] = None
    confidence: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisDetailResponse(AnalysisResponse):
    jd_text: str
    resume_text: str
    interview_text: str
    analysis_result: str
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[AnalysisResponse]


class AnalysisFilter(BaseModel):
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    recommendation: Optional[str] = None
    risk_level: Optional[str] = None
    page: int = 1
    page_size: int = 10


# ============== 通用分页 Schema ==============
class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int


# ============== Job Schema ==============
class JobCreate(BaseModel):
    job_name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=1, max_length=100)
    headcount: int = Field(..., ge=1, le=999)
    jd_text: str = Field(..., min_length=1)
    remark: Optional[str] = None

    # 新增：岗位类型和扩展字段
    job_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    salary_range: Optional[str] = Field(None, max_length=50)
    education_req: Optional[str] = Field(None, max_length=50)
    experience_req: Optional[str] = Field(None, max_length=50)
    parsed_jd_json: Optional[str] = None  # AI 解析后的结构化 JD


class JobUpdate(BaseModel):
    job_name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=1, max_length=100)
    headcount: int = Field(..., ge=1, le=999)
    jd_text: str = Field(..., min_length=1)
    remark: Optional[str] = None

    # 新增：岗位类型和扩展字段
    job_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    salary_range: Optional[str] = Field(None, max_length=50)
    education_req: Optional[str] = Field(None, max_length=50)
    experience_req: Optional[str] = Field(None, max_length=50)
    parsed_jd_json: Optional[str] = None


class JobStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


class JobResponse(BaseModel):
    id: int
    job_name: str
    department: str
    headcount: int
    status: str
    job_type: Optional[str] = None  # 新增
    location: Optional[str] = None  # 新增
    salary_range: Optional[str] = None  # 新增
    version: int = 1
    last_used_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    jd_text: str
    remark: Optional[str] = None
    education_req: Optional[str] = None  # 新增
    experience_req: Optional[str] = None  # 新增
    parsed_jd_json: Optional[str] = None  # 新增
    screening_rules_json: Optional[str] = None
    must_have_json: Optional[str] = None
    nice_to_have_json: Optional[str] = None
    risk_points_json: Optional[str] = None
    interview_questions_json: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[JobResponse]


class JobDetailWrapperResponse(JobDetailResponse):
    candidate_count: int = 0
    resume_passed_count: int = 0
    first_interview_passed_count: int = 0
    second_interview_passed_count: int = 0

    class Config:
        from_attributes = True


class JobPositionCreate(BaseModel):
    position_name: str = Field(..., min_length=1, max_length=100)
    position_type: Optional[str] = Field(None, max_length=50)
    department_name: Optional[str] = Field(None, max_length=100)
    education_requirement: Optional[str] = Field(None, max_length=50)
    experience_requirement: Optional[str] = Field(None, max_length=50)
    jd_original_text: str = Field(..., min_length=1)
    jd_structured_json: Optional[Dict[str, Any]] = None
    screening_rules: Optional[List[str]] = None
    must_have: Optional[List[str]] = None
    nice_to_have: Optional[List[str]] = None
    risk_points: Optional[List[str]] = None
    interview_questions: Optional[List[Any]] = None
    created_by: Optional[str] = Field(None, max_length=100)
    updated_by: Optional[str] = Field(None, max_length=100)


class JobPositionUpdate(BaseModel):
    position_name: Optional[str] = Field(None, min_length=1, max_length=100)
    position_type: Optional[str] = Field(None, max_length=50)
    department_name: Optional[str] = Field(None, max_length=100)
    education_requirement: Optional[str] = Field(None, max_length=50)
    experience_requirement: Optional[str] = Field(None, max_length=50)
    jd_original_text: Optional[str] = Field(None, min_length=1)
    jd_structured_json: Optional[Dict[str, Any]] = None
    screening_rules: Optional[List[str]] = None
    must_have: Optional[List[str]] = None
    nice_to_have: Optional[List[str]] = None
    risk_points: Optional[List[str]] = None
    interview_questions: Optional[List[Any]] = None
    save_mode: Optional[str] = Field(None, max_length=30)
    updated_by: Optional[str] = Field(None, max_length=100)


class JobPositionResponse(BaseModel):
    id: int
    position_name: str
    position_type: Optional[str] = None
    department_name: Optional[str] = None
    education_requirement: Optional[str] = None
    experience_requirement: Optional[str] = None
    version: int = 1
    status: str
    candidate_count: int = 0
    last_used_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class JobPositionDetailResponse(JobPositionResponse):
    jd_original_text: str
    jd_structured_json: Dict[str, Any] = Field(default_factory=dict)
    screening_rules: List[str] = Field(default_factory=list)
    must_have: List[str] = Field(default_factory=list)
    nice_to_have: List[str] = Field(default_factory=list)
    risk_points: List[str] = Field(default_factory=list)
    interview_questions: List[Any] = Field(default_factory=list)


class JobPositionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[JobPositionResponse]


class JobPositionParseJDRequest(BaseModel):
    jd_text: Optional[str] = None
    jdText: Optional[str] = None
    file_id: Optional[int] = None


class JobPositionParseJDResponse(BaseModel):
    success: bool
    jd_text: str
    parsed_jd: Dict[str, Any]
    position: Dict[str, Any]


# ============== Settings Schema ==============
class JobTypeConfigCreate(BaseModel):
    type_name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    evaluation_focus: List[str] = Field(default_factory=list)
    enabled: bool = True
    sort_order: int = 0


class JobTypeConfigUpdate(BaseModel):
    type_name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    evaluation_focus: Optional[List[str]] = None
    enabled: Optional[bool] = None
    sort_order: Optional[int] = None


class JobTypeConfigResponse(BaseModel):
    id: int
    type_name: str
    description: Optional[str] = None
    evaluation_focus: List[str] = Field(default_factory=list)
    enabled: bool = True
    sort_order: int = 0
    builtin: bool = False
    created_at: datetime
    updated_at: datetime


class JobTypeConfigListResponse(BaseModel):
    total: int
    items: List[JobTypeConfigResponse]


class AiPromptTemplateCreate(BaseModel):
    prompt_key: str = Field(..., min_length=1, max_length=80)
    prompt_name: str = Field(..., min_length=1, max_length=100)
    scene: Optional[str] = Field(None, max_length=80)
    system_prompt: Optional[str] = None
    user_prompt: str = Field(..., min_length=1)
    remark: Optional[str] = None


class AiPromptTemplateUpdate(BaseModel):
    prompt_name: Optional[str] = Field(None, min_length=1, max_length=100)
    scene: Optional[str] = Field(None, max_length=80)
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = Field(None, min_length=1)
    remark: Optional[str] = None


class AiPromptTemplateResponse(BaseModel):
    id: int
    prompt_key: str
    prompt_name: str
    scene: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: str
    version: int = 1
    status: str
    builtin: bool = False
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AiPromptTemplateListResponse(BaseModel):
    total: int
    items: List[AiPromptTemplateResponse]


# ============== Candidate Schema ==============
class CandidateCreate(BaseModel):
    job_id: int = Field(..., ge=1)
    candidate_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=50)
    resume_text: str = Field(..., min_length=1)
    remark: Optional[str] = None

    # 新增：结构化简历字段（AI 解析后填充）
    gender: Optional[str] = Field(None, max_length=10)
    age: Optional[int] = Field(None, ge=18, le=100)
    current_city: Optional[str] = Field(None, max_length=50)
    expected_city: Optional[str] = Field(None, max_length=50)
    job_search_status: Optional[str] = Field(None, max_length=50)
    available_date: Optional[str] = Field(None, max_length=50)
    expected_salary: Optional[str] = Field(None, max_length=50)
    education_level: Optional[str] = Field(None, max_length=50)
    graduation_school: Optional[str] = Field(None, max_length=100)
    major: Optional[str] = Field(None, max_length=100)
    work_years: Optional[int] = Field(None, ge=0, le=50)
    parsed_resume_json: Optional[str] = None


class CandidateUpdate(BaseModel):
    candidate_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=50)
    resume_text: str = Field(..., min_length=1)
    remark: Optional[str] = None

    # 新增：结构化简历字段
    gender: Optional[str] = Field(None, max_length=10)
    age: Optional[int] = Field(None, ge=18, le=100)
    current_city: Optional[str] = Field(None, max_length=50)
    expected_city: Optional[str] = Field(None, max_length=50)
    job_search_status: Optional[str] = Field(None, max_length=50)
    available_date: Optional[str] = Field(None, max_length=50)
    expected_salary: Optional[str] = Field(None, max_length=50)
    education_level: Optional[str] = Field(None, max_length=50)
    graduation_school: Optional[str] = Field(None, max_length=100)
    major: Optional[str] = Field(None, max_length=100)
    work_years: Optional[int] = Field(None, ge=0, le=50)
    parsed_resume_json: Optional[str] = None


class CandidateStatusUpdate(BaseModel):
    to_status: str = Field(..., min_length=1, max_length=50)
    reason: Optional[str] = None
    operator_name: Optional[str] = Field(None, max_length=100)


class CandidateResponse(BaseModel):
    id: int
    job_id: int
    candidate_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    current_status: str
    current_round_no: Optional[int] = None
    final_conclusion: Optional[str] = None
    resume_match_score: Optional[int] = None
    first_interview_score: Optional[int] = None
    second_interview_score: Optional[int] = None
    latest_ai_suggestion: Optional[str] = None
    job_name: Optional[str] = None
    department: Optional[str] = None
    job_type: Optional[str] = None
    # 新增：结构化简历字段
    gender: Optional[str] = None
    age: Optional[int] = None
    current_city: Optional[str] = None
    expected_city: Optional[str] = None
    education_level: Optional[str] = None
    graduation_school: Optional[str] = None
    major: Optional[str] = None
    work_years: Optional[int] = None
    expected_salary: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class CandidateDetailResponse(CandidateResponse):
    resume_text: str
    remark: Optional[str] = None
    created_at: datetime
    parsed_resume_json: Optional[str] = None  # 新增：AI 解析后的结构化简历 JSON
    available_date: Optional[str] = None  # 新增
    job_search_status: Optional[str] = None  # 新增

    class Config:
        from_attributes = True


class CandidateListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CandidateResponse]


# ============== Stage Report Schema ==============
class StageReportResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    stage_type: str
    report_version: int
    score: Optional[int] = None
    suggestion: Optional[str] = None
    risk_level: Optional[str] = None
    report_json: str
    input_snapshot_json: str
    status: str
    error_message: Optional[str] = None
    content_hash: Optional[str] = None
    report_key: Optional[str] = None
    is_current: Optional[int] = 1
    generate_type: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    candidate_snapshot_json: Optional[str] = None
    jd_snapshot_json: Optional[str] = None
    resume_snapshot_json: Optional[str] = None
    interview_record_snapshot_json: Optional[str] = None
    screening_result_snapshot_json: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportCandidateListItem(BaseModel):
    id: int
    candidate_name: str
    phone_masked: Optional[str] = None
    email_masked: Optional[str] = None
    job_id: Optional[int] = None
    job_name: Optional[str] = None
    job_type: Optional[str] = None
    current_status: str
    current_status_label: str
    latest_resume_time: Optional[datetime] = None
    latest_interview_time: Optional[datetime] = None
    has_report: bool = False
    latest_report_id: Optional[int] = None
    resume_match_score: Optional[int] = None
    updated_at: datetime


class ReportCandidateListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ReportCandidateListItem]


class ReportCandidateContextResponse(BaseModel):
    candidate: Dict[str, Any]
    job_positions: List[Dict[str, Any]] = Field(default_factory=list)
    resumes: List[Dict[str, Any]] = Field(default_factory=list)
    interview_records: List[Dict[str, Any]] = Field(default_factory=list)
    screening_results: List[Dict[str, Any]] = Field(default_factory=list)
    reports: List[Dict[str, Any]] = Field(default_factory=list)
    defaults: Dict[str, Any] = Field(default_factory=dict)


class ReportGenerateRequest(BaseModel):
    candidateId: int = Field(..., ge=1)
    jobPositionId: int = Field(..., ge=1)
    jobPositionVersion: Optional[int] = Field(None, ge=1)
    resumeId: int = Field(..., ge=1)
    resumeVersion: Optional[int] = Field(1, ge=1)
    interviewRecordIds: List[Any] = Field(default_factory=list)
    forceRegenerate: bool = False
    requestId: Optional[str] = Field(None, max_length=100)


class CandidateEvaluationReportResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    stage_type: str
    report_version: int
    score: Optional[int] = None
    suggestion: Optional[str] = None
    risk_level: Optional[str] = None
    report_json: str
    input_snapshot_json: str
    status: str
    error_message: Optional[str] = None
    content_hash: Optional[str] = None
    report_key: Optional[str] = None
    is_current: Optional[int] = 1
    generate_type: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    candidate_snapshot_json: Optional[str] = None
    jd_snapshot_json: Optional[str] = None
    resume_snapshot_json: Optional[str] = None
    interview_record_snapshot_json: Optional[str] = None
    screening_result_snapshot_json: Optional[str] = None
    candidate_name: Optional[str] = None
    job_name: Optional[str] = None
    reused: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class CandidateEvaluationReportListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CandidateEvaluationReportResponse]


class ParseJDRequest(BaseModel):
    """JD 解析请求"""
    jd_text: str = Field(..., min_length=1)


class ParseResumeRequest(BaseModel):
    """简历解析请求"""
    resume_text: str = Field(..., min_length=1)


class ResumeScreeningRequest(BaseModel):
    force: bool = False
    request_id: Optional[str] = Field(None, max_length=100)


class FirstInterviewAnalysisRequest(BaseModel):
    interview_record_id: int = Field(..., ge=1)
    force: bool = False
    request_id: Optional[str] = Field(None, max_length=100)


# ============== Interview Record Schema ==============
class InterviewRecordCreate(BaseModel):
    interviewer_name: Optional[str] = Field(None, max_length=100)
    interview_time: Optional[datetime] = None
    record_text: str = Field(..., min_length=1)


class InterviewRecordResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    round_type: str
    interviewer_name: Optional[str] = None
    interview_time: Optional[datetime] = None
    record_text: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Candidate Status Log Schema ==============
class CandidateStatusLogResponse(BaseModel):
    id: int
    candidate_id: int
    from_status: Optional[str] = None
    to_status: str
    reason: Optional[str] = None
    operator_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Open Interview Round Schema ==============
class CandidateInterviewRoundCreate(BaseModel):
    task_id: Optional[int] = None
    round_no: Optional[int] = Field(None, ge=1)
    round_name: Optional[str] = Field(None, max_length=100)
    round_type: Optional[str] = Field(None, max_length=50)
    round_focus: Optional[str] = Field(None, max_length=100)
    scheduled_time: Optional[datetime] = None
    interviewer: Optional[str] = Field(None, max_length=100)
    interview_method: Optional[str] = Field(None, max_length=30)
    generate_questions: bool = False
    based_on_previous: bool = True
    question_json: Optional[List[Dict[str, Any]]] = None


class CandidateInterviewRoundUpdate(BaseModel):
    round_name: Optional[str] = Field(None, max_length=100)
    round_type: Optional[str] = Field(None, max_length=50)
    round_focus: Optional[str] = Field(None, max_length=100)
    scheduled_time: Optional[datetime] = None
    interviewer: Optional[str] = Field(None, max_length=100)
    interview_method: Optional[str] = Field(None, max_length=30)


class CandidateInterviewRecordSubmit(BaseModel):
    record_text: str = Field(..., min_length=1)
    score: Optional[int] = Field(None, ge=0, le=100)
    conclusion: Optional[str] = None


class CandidateInterviewDecisionSubmit(BaseModel):
    decision: str = Field(..., min_length=1, max_length=50)
    next_round: Optional[CandidateInterviewRoundCreate] = None


class CandidateInterviewRoundResponse(BaseModel):
    id: int
    candidate_id: int
    task_id: Optional[int] = None
    round_no: int
    round_name: str
    round_type: Optional[str] = None
    round_focus: Optional[str] = None
    status: str
    scheduled_time: Optional[datetime] = None
    interviewer: Optional[str] = None
    interview_method: Optional[str] = None
    question_json: List[Dict[str, Any]] = Field(default_factory=list)
    record_text: Optional[str] = None
    score: Optional[int] = None
    conclusion: Optional[str] = None
    decision: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CandidateInterviewFlowResponse(BaseModel):
    candidate: CandidateResponse
    rounds: List[CandidateInterviewRoundResponse]


class CandidateInterviewRoundsBatchRequest(BaseModel):
    candidate_ids: Optional[List[int]] = None
    candidateIds: Optional[List[int]] = None


class CandidateInterviewRoundsBatchItem(BaseModel):
    candidate_id: int
    rounds: List[CandidateInterviewRoundResponse] = Field(default_factory=list)


class CandidateInterviewRoundsBatchResponse(BaseModel):
    items: List[CandidateInterviewRoundsBatchItem] = Field(default_factory=list)


class CandidateInterviewQuestionsGenerateRequest(BaseModel):
    requestId: Optional[str] = Field(None, max_length=100)
    request_id: Optional[str] = Field(None, max_length=100)
    roundType: Optional[str] = Field(None, max_length=30)
    round_type: Optional[str] = Field(None, max_length=30)
    roundNo: Optional[int] = Field(None, ge=1)
    round_no: Optional[int] = Field(None, ge=1)
    forceRegenerate: bool = True
    force_regenerate: Optional[bool] = None


class CandidateInterviewQuestionsResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    stage_type: str
    report_version: int
    round_type: Optional[str] = None
    round_type_label: Optional[str] = None
    round_no: Optional[int] = None
    questions: List[Dict[str, Any]] = Field(default_factory=list)
    question_count: int = 0
    report_json: str
    input_snapshot_json: str
    content_hash: Optional[str] = None
    report_key: Optional[str] = None
    is_current: Optional[int] = 1
    generate_type: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    candidate_snapshot_json: Optional[str] = None
    jd_snapshot_json: Optional[str] = None
    resume_snapshot_json: Optional[str] = None
    screening_result_snapshot_json: Optional[str] = None
    candidate_name: Optional[str] = None
    job_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class CandidateInterviewQuestionsListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CandidateInterviewQuestionsResponse]


class InterviewQuestionStatsItem(BaseModel):
    question: str
    count: int
    round_type: Optional[str] = None
    round_type_label: Optional[str] = None
    dimension: Optional[str] = None
    source: Optional[str] = None
    latest_generated_at: Optional[datetime] = None


class InterviewQuestionStatsResponse(BaseModel):
    total: int
    items: List[InterviewQuestionStatsItem]


# ============== Screening Task Schema ==============
class ScreeningTaskCreate(BaseModel):
    jd_text: Optional[str] = Field(None, min_length=1)
    job_type: Optional[str] = Field(None, max_length=50)
    task_name: Optional[str] = Field(None, max_length=200)
    jd_structured_json: Optional[Dict[str, Any]] = None
    job_position_id: Optional[int] = Field(None, ge=1)
    job_position_version: Optional[int] = Field(None, ge=1)
    jd_snapshot_json: Optional[Dict[str, Any]] = None


class ScreeningTaskResponse(BaseModel):
    id: int
    task_name: Optional[str] = None
    job_title: Optional[str] = None
    job_type: Optional[str] = None
    work_location: Optional[str] = None
    experience_requirement: Optional[str] = None
    education_requirement: Optional[str] = None
    job_position_id: Optional[int] = None
    job_position_version: Optional[int] = None
    jd_text: str
    jd_structured_json: Optional[str] = None
    jd_snapshot_json: Optional[str] = None
    status: str
    total_resume_count: int = 0
    parsed_success_count: int = 0
    parsed_failed_count: int = 0
    recommended_count: int = 0
    pending_count: int = 0
    rejected_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScreeningTaskListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ScreeningTaskResponse]


class ScreeningJDParseRequest(BaseModel):
    jd_text: str = Field(..., min_length=1)


class ScreeningJDParseResponse(BaseModel):
    success: bool
    jd_text: str
    parsed_jd: Dict[str, Any]


class ResumeFileResponse(BaseModel):
    id: int
    task_id: int
    file_name: str
    file_type: Optional[str] = None
    file_hash: Optional[str] = None
    text_hash: Optional[str] = None
    reuse_source: Optional[str] = None
    reused_resume_file_id: Optional[int] = None
    reused_profile_id: Optional[int] = None
    parse_status: str
    parse_error_message: Optional[str] = None
    raw_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeParseRecordListItem(BaseModel):
    id: int
    task_id: int
    task_name: Optional[str] = None
    job_title: Optional[str] = None
    job_position_id: Optional[int] = None
    job_position_version: Optional[int] = None
    file_name: str
    file_type: Optional[str] = None
    file_hash: Optional[str] = None
    text_hash: Optional[str] = None
    parse_status: str
    parse_error_message: Optional[str] = None
    reuse_source: Optional[str] = None
    reused_resume_file_id: Optional[int] = None
    reused_profile_id: Optional[int] = None
    candidate_profile_id: Optional[int] = None
    candidate_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    education: Optional[str] = None
    work_years: Optional[str] = None
    latest_company: Optional[str] = None
    latest_position: Optional[str] = None
    screening_result_id: Optional[int] = None
    screening_score: Optional[int] = None
    screening_conclusion: Optional[str] = None
    screening_status: Optional[str] = None
    result_source: Optional[str] = None
    reused_from_result_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ResumeParseRecordListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ResumeParseRecordListItem]


class ScreeningTaskProgressResponse(BaseModel):
    status: str
    total: int
    parsed_success: int
    parsed_failed: int
    screened: int
    recommended: int
    pending: int
    rejected: int


class ScreeningResultStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=30)


class ScreeningResultListItem(BaseModel):
    row_type: str
    rank: Optional[int] = None
    task_id: int
    resume_file_id: int
    result_id: Optional[int] = None
    candidate_id: Optional[int] = None
    file_name: str
    parse_status: str
    parse_error_message: Optional[str] = None
    candidate_name: Optional[str] = None
    latest_position: Optional[str] = None
    work_years: Optional[str] = None
    education: Optional[str] = None
    city: Optional[str] = None
    score: Optional[int] = None
    conclusion: Optional[str] = None
    conclusion_label: Optional[str] = None
    status: Optional[str] = None
    match_highlights: List[str] = Field(default_factory=list)
    risk_points: List[str] = Field(default_factory=list)
    result_source: Optional[str] = None
    reused_from_result_id: Optional[int] = None
    job_type: Optional[str] = None
    updated_at: datetime


class ScreeningResultListResponse(BaseModel):
    total: int
    items: List[ScreeningResultListItem]


class CandidateProfileResponse(BaseModel):
    id: int
    resume_file_id: int
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    city: Optional[str] = None
    expected_city: Optional[str] = None
    education: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[str] = None
    work_years: Optional[str] = None
    latest_company: Optional[str] = None
    latest_position: Optional[str] = None
    past_companies: Optional[str] = None
    skills_json: Optional[str] = None
    work_experience_json: Optional[str] = None
    project_experience_json: Optional[str] = None
    industry_experience: Optional[str] = None
    salary_expectation: Optional[str] = None
    available_time: Optional[str] = None
    profile_json: Optional[str] = None
    data_source: str
    manual_modified_flag: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScreeningResultDetailResponse(BaseModel):
    task: ScreeningTaskResponse
    resume_file: ResumeFileResponse
    candidate_profile: CandidateProfileResponse
    result: Dict[str, Any]


class ResumeParseRecordDetailResponse(BaseModel):
    resume_file: ResumeFileResponse
    task: Optional[ScreeningTaskResponse] = None
    job_position: Optional[Dict[str, Any]] = None
    candidate_profile: Optional[CandidateProfileResponse] = None
    screening_result: Optional[Dict[str, Any]] = None


# ============== 通用 Response ==============
class SuccessResponse(BaseModel):
    success: bool
