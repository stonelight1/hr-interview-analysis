from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
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
    request_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="SUCCESS")
    error_message = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


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
