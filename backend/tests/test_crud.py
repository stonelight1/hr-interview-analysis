"""
单元测试：CRUD 操作（模拟数据库）
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from app.crud_new import (
    create_job,
    get_job,
    update_job,
    update_job_status,
    delete_job,
    create_candidate,
    get_candidate,
    update_candidate,
    update_candidate_status,
    delete_candidate,
    create_stage_report,
    get_stage_report,
    get_latest_stage_report,
    create_interview_record,
    get_interview_record,
    get_latest_interview_record,
)
from app import constants


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = MagicMock()
    return db


class TestJobCRUD:
    """测试岗位 CRUD"""

    def test_create_job(self, mock_db):
        """测试创建岗位"""
        data = {
            "job_name": "电商客服",
            "department": "客服部",
            "headcount": 3,
            "jd_text": "负责售前售后沟通...",
            "remark": "备注",
        }
        result = create_job(mock_db, data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result.job_name == "电商客服"
        assert result.department == "客服部"
        assert result.headcount == 3
        assert result.status == constants.JOB_STATUS_OPEN

    def test_update_job(self, mock_db):
        """测试更新岗位"""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        data = {
            "job_name": "更新后的岗位",
            "department": "更新后的部门",
            "headcount": 5,
            "jd_text": "更新后的 JD",
            "remark": None,
        }
        result = update_job(mock_db, 1, data)

        assert mock_job.job_name == "更新后的岗位"
        assert mock_job.department == "更新后的部门"
        assert mock_job.headcount == 5
        mock_db.commit.assert_called_once()

    def test_update_job_status(self, mock_db):
        """测试更新岗位状态"""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        result = update_job_status(mock_db, 1, constants.JOB_STATUS_PAUSED)

        assert mock_job.status == constants.JOB_STATUS_PAUSED
        mock_db.commit.assert_called_once()

    def test_update_job_status_invalid(self, mock_db):
        """测试更新岗位状态无效值"""
        result = update_job_status(mock_db, 1, "INVALID")

        assert result is None
        mock_db.commit.assert_not_called()

    def test_delete_job(self, mock_db):
        """测试删除岗位"""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        result = delete_job(mock_db, 1)

        assert result is True
        assert mock_job.deleted == 1
        mock_db.commit.assert_called_once()

    def test_delete_job_not_found(self, mock_db):
        """测试删除不存在的岗位"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = delete_job(mock_db, 999)

        assert result is False


class TestCandidateCRUD:
    """测试候选人 CRUD"""

    def test_create_candidate(self, mock_db):
        """测试创建候选人"""
        data = {
            "job_id": 1,
            "candidate_name": "张三",
            "resume_text": "简历内容...",
            "phone": "13800138000",
            "email": "test@example.com",
            "source": "Boss直聘",
            "remark": "备注",
        }
        result = create_candidate(mock_db, data)

        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        assert result.candidate_name == "张三"
        assert result.current_status == constants.STATUS_RESUME_PENDING
        assert result.resume_match_score is None

    def test_update_candidate(self, mock_db):
        """测试更新候选人"""
        mock_candidate = MagicMock()
        mock_candidate.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_candidate

        data = {
            "candidate_name": "更新后的姓名",
            "phone": "13900139000",
            "email": None,
            "source": "智联招聘",
            "resume_text": "更新后的简历",
            "remark": None,
        }
        result = update_candidate(mock_db, 1, data)

        assert mock_candidate.candidate_name == "更新后的姓名"
        assert mock_candidate.phone == "13900139000"
        assert mock_candidate.source == "智联招聘"
        mock_db.commit.assert_called_once()

    def test_update_candidate_status_valid(self, mock_db):
        """测试更新候选人状态"""
        mock_candidate = MagicMock()
        mock_candidate.id = 1
        mock_candidate.current_status = constants.STATUS_RESUME_PENDING
        mock_db.query.return_value.filter.return_value.first.return_value = mock_candidate

        result = update_candidate_status(
            mock_db,
            1,
            constants.STATUS_RESUME_PASSED,
            "简历通过",
            "HR张三",
        )

        assert mock_candidate.current_status == constants.STATUS_RESUME_PASSED
        mock_db.commit.assert_called()

    def test_update_candidate_status_invalid_transition(self, mock_db):
        """测试更新候选人状态非法流转"""
        mock_candidate = MagicMock()
        mock_candidate.id = 1
        mock_candidate.current_status = constants.STATUS_RESUME_REJECTED  # 终态
        mock_db.query.return_value.filter.return_value.first.return_value = mock_candidate

        result = update_candidate_status(
            mock_db,
            1,
            constants.STATUS_FIRST_INTERVIEW_PENDING,
            "非法流转",
        )

        assert result is None
        mock_db.commit.assert_not_called()

    def test_delete_candidate(self, mock_db):
        """测试删除候选人"""
        mock_candidate = MagicMock()
        mock_candidate.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_candidate

        result = delete_candidate(mock_db, 1)

        assert result is True
        assert mock_candidate.deleted == 1
        mock_db.commit.assert_called_once()


class TestStageReportCRUD:
    """测试阶段报告 CRUD"""

    def test_create_stage_report(self, mock_db):
        """测试创建阶段报告"""
        report_json = '{"score": 80}'
        input_snapshot_json = '{"jd_text": "JD内容"}'

        result = create_stage_report(
            mock_db,
            candidate_id=1,
            job_id=1,
            stage_type=constants.STAGE_RESUME_SCREENING,
            report_version=1,
            report_json=report_json,
            input_snapshot_json=input_snapshot_json,
            score=80,
            suggestion="建议约初试",
            risk_level="低",
            content_hash="abc123",
            request_id="req-001",
            status=constants.REPORT_STATUS_SUCCESS,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_latest_stage_report(self, mock_db):
        """测试获取最新阶段报告"""
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.candidate_id = 1
        mock_report.stage_type = constants.STAGE_RESUME_SCREENING
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_report

        result = get_latest_stage_report(
            mock_db,
            1,
            constants.STAGE_RESUME_SCREENING,
        )

        assert result == mock_report


class TestInterviewRecordCRUD:
    """测试面试记录 CRUD"""

    def test_create_interview_record(self, mock_db):
        """测试创建面试记录"""
        result = create_interview_record(
            mock_db,
            candidate_id=1,
            job_id=1,
            round_type=constants.ROUND_TYPE_FIRST,
            record_text="面试记录内容...",
            interviewer_name="面试官",
            interview_time=datetime.now(),
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_interview_record_invalid_round_type(self, mock_db):
        """测试创建面试记录无效轮次"""
        with pytest.raises(ValueError) as excinfo:
            create_interview_record(
                mock_db,
                candidate_id=1,
                job_id=1,
                round_type="INVALID",
                record_text="面试记录内容...",
            )
        assert "无效的面试轮次类型" in str(excinfo.value)

    def test_get_interview_record(self, mock_db):
        """测试获取面试记录"""
        mock_record = MagicMock()
        mock_record.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_record

        result = get_interview_record(mock_db, 1)

        assert result == mock_record
