from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from app.database import Base
from datetime import datetime


class InterviewAnalysis(Base):
    __tablename__ = "hr_interview_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_name = Column(String(100), nullable=False)
    job_title = Column(String(100), nullable=False)
    jd_text = Column(Text, nullable=False)
    resume_text = Column(Text, nullable=False)
    interview_text = Column(Text, nullable=False)
    analysis_result = Column(Text, nullable=False)
    match_score = Column(Integer, nullable=True)
    recommendation = Column(String(50), nullable=True)
    risk_level = Column(String(20), nullable=True)
    confidence = Column(String(20), nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    headcount = Column(Integer, nullable=False, default=1)
    jd_text = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")

    # 新增：岗位类型和扩展字段
    job_type = Column(String(50), nullable=True)  # 岗位类型
    location = Column(String(100), nullable=True)  # 工作地点
    salary_range = Column(String(50), nullable=True)  # 薪资范围
    education_req = Column(String(50), nullable=True)  # 学历要求
    experience_req = Column(String(50), nullable=True)  # 经验要求
    parsed_jd_json = Column(Text, nullable=True)  # AI 解析后的结构化 JD
    version = Column(Integer, nullable=False, default=1)  # JD 版本号
    screening_rules_json = Column(Text, nullable=True)  # 筛选规则
    must_have_json = Column(Text, nullable=True)  # 必备条件
    nice_to_have_json = Column(Text, nullable=True)  # 加分项
    risk_points_json = Column(Text, nullable=True)  # 淘汰风险
    interview_questions_json = Column(Text, nullable=True)  # 面试建议问题
    last_used_time = Column(DateTime, nullable=True)  # 最近使用时间
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)

    remark = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=True)
    email = Column(String(100), nullable=True)
    source = Column(String(50), nullable=True)
    resume_text = Column(Text, nullable=False)
    current_status = Column(String(50), nullable=False, default="IMPORTED")
    current_round_no = Column(Integer, nullable=True)
    final_conclusion = Column(String(50), nullable=True)
    resume_match_score = Column(Integer, nullable=True)
    first_interview_score = Column(Integer, nullable=True)
    second_interview_score = Column(Integer, nullable=True)
    latest_ai_suggestion = Column(String(50), nullable=True)
    remark = Column(Text, nullable=True)

    # 新增：结构化简历字段
    gender = Column(String(10), nullable=True)  # 性别
    age = Column(Integer, nullable=True)  # 年龄
    current_city = Column(String(50), nullable=True)  # 当前城市
    expected_city = Column(String(50), nullable=True)  # 期望城市
    job_search_status = Column(String(50), nullable=True)  # 求职状态
    available_date = Column(String(50), nullable=True)  # 到岗时间
    expected_salary = Column(String(50), nullable=True)  # 期望薪资
    education_level = Column(String(50), nullable=True)  # 最高学历
    graduation_school = Column(String(100), nullable=True)  # 毕业学校
    major = Column(String(100), nullable=True)  # 专业
    work_years = Column(Integer, nullable=True)  # 工作年限
    parsed_resume_json = Column(Text, nullable=True)  # AI 解析后的结构化简历 JSON

    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class StageReport(Base):
    __tablename__ = "stage_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    stage_type = Column(String(30), nullable=False)
    report_version = Column(Integer, nullable=False, default=1)
    score = Column(Integer, nullable=True)
    suggestion = Column(String(50), nullable=True)
    risk_level = Column(String(20), nullable=True)
    report_json = Column(Text, nullable=False)
    input_snapshot_json = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True)
    report_key = Column(String(255), nullable=True)
    is_current = Column(Integer, nullable=False, default=1)
    round_type = Column(String(30), nullable=True)
    round_no = Column(Integer, nullable=True)
    generate_type = Column(String(30), nullable=True)
    ai_provider = Column(String(50), nullable=True)
    ai_model = Column(String(100), nullable=True)
    candidate_snapshot_json = Column(Text, nullable=True)
    jd_snapshot_json = Column(Text, nullable=True)
    resume_snapshot_json = Column(Text, nullable=True)
    interview_record_snapshot_json = Column(Text, nullable=True)
    screening_result_snapshot_json = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="SUCCESS")
    error_message = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class InterviewQuestionItem(Base):
    __tablename__ = "interview_question_items"
    __table_args__ = (
        Index("idx_interview_question_items_report", "report_id"),
        Index("idx_interview_question_items_stats", "job_id", "round_type", "question_hash"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("stage_reports.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(Integer, nullable=True)
    round_type = Column(String(30), nullable=True)
    round_no = Column(Integer, nullable=True)
    question_text = Column(Text, nullable=False)
    question_hash = Column(String(64), nullable=False)
    dimension = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    is_required = Column(Integer, nullable=False, default=1)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class InterviewRecord(Base):
    __tablename__ = "interview_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    round_type = Column(String(20), nullable=False)
    interviewer_name = Column(String(100), nullable=True)
    interview_time = Column(DateTime, nullable=True)
    record_text = Column(Text, nullable=False)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class CandidateStatusLog(Base):
    __tablename__ = "candidate_status_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    operator_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class ScreeningTask(Base):
    __tablename__ = "screening_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_name = Column(String(200), nullable=True)
    job_title = Column(String(100), nullable=True)
    job_type = Column(String(50), nullable=True)
    work_location = Column(String(100), nullable=True)
    experience_requirement = Column(String(100), nullable=True)
    education_requirement = Column(String(100), nullable=True)
    job_position_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    job_position_version = Column(Integer, nullable=True)
    jd_text = Column(Text, nullable=False)
    jd_structured_json = Column(Text, nullable=True)
    jd_snapshot_json = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="DRAFT")
    total_resume_count = Column(Integer, nullable=False, default=0)
    parsed_success_count = Column(Integer, nullable=False, default=0)
    parsed_failed_count = Column(Integer, nullable=False, default=0)
    recommended_count = Column(Integer, nullable=False, default=0)
    pending_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class CandidateInterviewRound(Base):
    __tablename__ = "candidate_interview_rounds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    task_id = Column(Integer, nullable=True)
    round_no = Column(Integer, nullable=False)
    round_name = Column(String(100), nullable=False)
    round_type = Column(String(50), nullable=True)
    round_focus = Column(String(100), nullable=True)
    status = Column(String(30), nullable=False, default="SCHEDULED")
    scheduled_time = Column(DateTime, nullable=True)
    interviewer = Column(String(100), nullable=True)
    interview_method = Column(String(30), nullable=True)
    question_json = Column(Text, nullable=True)
    record_text = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    conclusion = Column(Text, nullable=True)
    decision = Column(String(50), nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class ResumeFile(Base):
    __tablename__ = "resume_files"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("screening_tasks.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=True)
    file_url = Column(String(500), nullable=True)
    file_hash = Column(String(64), nullable=True)
    text_hash = Column(String(64), nullable=True)
    reuse_source = Column(String(50), nullable=True)
    reused_resume_file_id = Column(Integer, nullable=True)
    reused_profile_id = Column(Integer, nullable=True)
    parse_status = Column(String(30), nullable=False, default="PENDING")
    parse_error_message = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resume_file_id = Column(Integer, ForeignKey("resume_files.id"), nullable=False)
    name = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(100), nullable=True)
    gender = Column(String(20), nullable=True)
    age = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    expected_city = Column(String(100), nullable=True)
    education = Column(String(100), nullable=True)
    school = Column(String(150), nullable=True)
    major = Column(String(150), nullable=True)
    graduation_year = Column(String(50), nullable=True)
    work_years = Column(String(50), nullable=True)
    latest_company = Column(String(150), nullable=True)
    latest_position = Column(String(150), nullable=True)
    past_companies = Column(Text, nullable=True)
    skills_json = Column(Text, nullable=True)
    work_experience_json = Column(Text, nullable=True)
    project_experience_json = Column(Text, nullable=True)
    industry_experience = Column(Text, nullable=True)
    salary_expectation = Column(String(100), nullable=True)
    available_time = Column(String(100), nullable=True)
    profile_json = Column(Text, nullable=True)
    data_source = Column(String(50), nullable=False, default="resume_parse")
    manual_modified_flag = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("screening_tasks.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    resume_file_id = Column(Integer, ForeignKey("resume_files.id"), nullable=False)
    score = Column(Integer, nullable=True)
    conclusion = Column(String(30), nullable=False)
    match_highlights_json = Column(Text, nullable=True)
    risk_points_json = Column(Text, nullable=True)
    interview_questions_json = Column(Text, nullable=True)
    dimension_scores_json = Column(Text, nullable=True)
    confidence = Column(String(20), nullable=True)
    ai_reason = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="PENDING")
    result_source = Column(String(50), nullable=True)
    reused_from_result_id = Column(Integer, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class JobTypeConfig(Base):
    __tablename__ = "job_type_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type_name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    evaluation_focus_json = Column(Text, nullable=True)
    enabled = Column(Integer, nullable=False, default=1)
    sort_order = Column(Integer, nullable=False, default=0)
    builtin = Column(Integer, nullable=False, default=0)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class AiPromptTemplate(Base):
    __tablename__ = "ai_prompt_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prompt_key = Column(String(80), nullable=False)
    prompt_name = Column(String(100), nullable=False)
    scene = Column(String(80), nullable=True)
    system_prompt = Column(Text, nullable=True)
    user_prompt = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="DRAFT")
    builtin = Column(Integer, nullable=False, default=0)
    remark = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
