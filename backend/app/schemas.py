from pydantic import BaseModel, Field
from typing import Optional, List
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
    created_at: datetime

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    jd_text: str
    remark: Optional[str] = None
    education_req: Optional[str] = None  # 新增
    experience_req: Optional[str] = None  # 新增
    parsed_jd_json: Optional[str] = None  # 新增
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
    resume_match_score: Optional[int] = None
    first_interview_score: Optional[int] = None
    second_interview_score: Optional[int] = None
    latest_ai_suggestion: Optional[str] = None
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
    job_name: Optional[str] = None
    department: Optional[str] = None
    job_type: Optional[str] = None  # 新增：关联岗位的类型
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
    created_at: datetime

    class Config:
        from_attributes = True


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


# ============== 通用 Response ==============
class SuccessResponse(BaseModel):
    success: bool
