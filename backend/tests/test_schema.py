"""
单元测试：Pydantic Schema 校验
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas import (
    JobCreate, JobUpdate, JobStatusUpdate,
    CandidateCreate, CandidateUpdate, CandidateStatusUpdate,
    ResumeScreeningRequest, FirstInterviewAnalysisRequest,
    InterviewRecordCreate,
)


class TestJobSchema:
    """测试岗位 Schema"""

    def test_job_create_valid(self):
        """测试岗位创建 Schema 有效数据"""
        job = JobCreate(
            job_name="电商客服",
            department="客服部",
            headcount=3,
            jd_text="负责售前售后沟通处理...",
        )
        assert job.job_name == "电商客服"
        assert job.department == "客服部"
        assert job.headcount == 3
        assert job.remark is None

    def test_job_create_with_remark(self):
        """测试岗位创建 Schema 带备注"""
        job = JobCreate(
            job_name="售后客服",
            department="客服部",
            headcount=1,
            jd_text="负责售后处理...",
            remark="优先有经验",
        )
        assert job.remark == "优先有经验"

    def test_job_create_empty_name_fails(self):
        """测试岗位名称不能为空"""
        with pytest.raises(ValidationError):
            JobCreate(
                job_name="",
                department="客服部",
                headcount=1,
                jd_text="岗位 JD",
            )

    def test_job_create_headcount_min(self):
        """测试招聘人数最小值"""
        with pytest.raises(ValidationError):
            JobCreate(
                job_name="测试岗位",
                department="测试部门",
                headcount=0,
                jd_text="岗位 JD",
            )

    def test_job_create_headcount_max(self):
        """测试招聘人数最大值"""
        with pytest.raises(ValidationError):
            JobCreate(
                job_name="测试岗位",
                department="测试部门",
                headcount=1000,
                jd_text="岗位 JD",
            )

    def test_job_status_update_valid(self):
        """测试岗位状态更新"""
        status = JobStatusUpdate(status="OPEN")
        assert status.status == "OPEN"

    def test_job_status_update_paused(self):
        """测试岗位状态暂停"""
        status = JobStatusUpdate(status="PAUSED")
        assert status.status == "PAUSED"

    def test_job_status_update_closed(self):
        """测试岗位状态关闭"""
        status = JobStatusUpdate(status="CLOSED")
        assert status.status == "CLOSED"


class TestCandidateSchema:
    """测试候选人 Schema"""

    def test_candidate_create_valid(self):
        """测试候选人创建 Schema 有效数据"""
        candidate = CandidateCreate(
            job_id=1,
            candidate_name="张三",
            resume_text="简历内容...",
        )
        assert candidate.job_id == 1
        assert candidate.candidate_name == "张三"
        assert candidate.phone is None
        assert candidate.email is None
        assert candidate.source is None

    def test_candidate_create_with_all_fields(self):
        """测试候选人创建 Schema 带所有可选字段"""
        candidate = CandidateCreate(
            job_id=1,
            candidate_name="李四",
            phone="13800138000",
            email="test@example.com",
            source="Boss直聘",
            resume_text="简历内容...",
            remark="备注信息",
        )
        assert candidate.phone == "13800138000"
        assert candidate.email == "test@example.com"
        assert candidate.source == "Boss直聘"

    def test_candidate_create_empty_name_fails(self):
        """测试候选人姓名不能为空"""
        with pytest.raises(ValidationError):
            CandidateCreate(
                job_id=1,
                candidate_name="",
                resume_text="简历内容",
            )

    def test_candidate_create_empty_resume_fails(self):
        """测试简历内容不能为空"""
        with pytest.raises(ValidationError):
            CandidateCreate(
                job_id=1,
                candidate_name="测试",
                resume_text="",
            )

    def test_candidate_create_invalid_job_id(self):
        """测试岗位 ID 无效"""
        with pytest.raises(ValidationError):
            CandidateCreate(
                job_id=0,
                candidate_name="测试",
                resume_text="简历内容",
            )

    def test_candidate_status_update_valid(self):
        """测试候选人状态更新"""
        status = CandidateStatusUpdate(
            to_status="RESUME_PASSED",
            reason="简历筛选通过",
            operator_name="HR张三",
        )
        assert status.to_status == "RESUME_PASSED"
        assert status.reason == "简历筛选通过"
        assert status.operator_name == "HR张三"

    def test_candidate_status_update_minimal(self):
        """测试候选人状态更新最小字段"""
        status = CandidateStatusUpdate(to_status="RESUME_PASSED")
        assert status.to_status == "RESUME_PASSED"
        assert status.reason is None
        assert status.operator_name is None


class TestAIRequestSchemas:
    """测试 AI 请求 Schema"""

    def test_resume_screening_request_default(self):
        """测试简历筛选请求默认值"""
        request = ResumeScreeningRequest()
        assert request.force is False
        assert request.request_id is None

    def test_resume_screening_request_force(self):
        """测试简历筛选请求强制模式"""
        request = ResumeScreeningRequest(force=True, request_id="req-001")
        assert request.force is True
        assert request.request_id == "req-001"

    def test_first_interview_analysis_request_valid(self):
        """测试初试分析请求"""
        request = FirstInterviewAnalysisRequest(
            interview_record_id=1,
            force=False,
        )
        assert request.interview_record_id == 1
        assert request.force is False

    def test_first_interview_analysis_request_invalid_record_id(self):
        """测试初试分析请求无效记录 ID"""
        with pytest.raises(ValidationError):
            FirstInterviewAnalysisRequest(
                interview_record_id=0,
                force=False,
            )


class TestInterviewRecordSchema:
    """测试面试记录 Schema"""

    def test_interview_record_create_valid(self):
        """测试面试记录创建"""
        record = InterviewRecordCreate(
            record_text="面试记录内容...",
        )
        assert record.record_text == "面试记录内容..."
        assert record.interviewer_name is None
        assert record.interview_time is None

    def test_interview_record_create_with_all_fields(self):
        """测试面试记录创建带所有字段"""
        record = InterviewRecordCreate(
            interviewer_name="面试官张三",
            interview_time=datetime(2026, 7, 6, 10, 0, 0),
            record_text="面试记录内容...",
        )
        assert record.interviewer_name == "面试官张三"
        assert record.interview_time.year == 2026

    def test_interview_record_create_empty_text_fails(self):
        """测试面试记录不能为空"""
        with pytest.raises(ValidationError):
            InterviewRecordCreate(
                record_text="",
            )
