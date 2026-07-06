"""
单元测试：常量定义和枚举值校验
"""
import pytest
from app import constants


class TestConstants:
    """测试常量定义"""

    def test_valid_job_statuses(self):
        """测试岗位状态枚举值"""
        assert "OPEN" in constants.VALID_JOB_STATUSES
        assert "PAUSED" in constants.VALID_JOB_STATUSES
        assert "CLOSED" in constants.VALID_JOB_STATUSES
        assert len(constants.VALID_JOB_STATUSES) == 3

    def test_valid_candidate_statuses(self):
        """测试候选人状态枚举值"""
        required_statuses = {
            "IMPORTED",
            "RESUME_PENDING",
            "RESUME_PASSED",
            "RESUME_REJECTED",
            "FIRST_INTERVIEW_PENDING",
            "FIRST_INTERVIEW_PASSED",
            "FIRST_INTERVIEW_REJECTED",
            "SECOND_INTERVIEW_PENDING",
            "SECOND_INTERVIEW_PASSED",
            "SECOND_INTERVIEW_REJECTED",
            "HIRED",
            "ABANDONED",
            "TALENT_POOL",
        }
        assert required_statuses.issubset(constants.VALID_CANDIDATE_STATUSES)
        assert len(constants.VALID_CANDIDATE_STATUSES) == 13

    def test_valid_stage_types(self):
        """测试阶段类型枚举值"""
        assert "RESUME_SCREENING" in constants.VALID_STAGE_TYPES
        assert "FIRST_INTERVIEW" in constants.VALID_STAGE_TYPES
        assert "SECOND_INTERVIEW" in constants.VALID_STAGE_TYPES
        assert len(constants.VALID_STAGE_TYPES) == 3

    def test_valid_round_types(self):
        """测试面试轮次枚举值"""
        assert "FIRST" in constants.VALID_ROUND_TYPES
        assert "SECOND" in constants.VALID_ROUND_TYPES
        assert len(constants.VALID_ROUND_TYPES) == 2

    def test_valid_report_statuses(self):
        """测试报告状态枚举值"""
        assert "PROCESSING" in constants.VALID_REPORT_STATUSES
        assert "SUCCESS" in constants.VALID_REPORT_STATUSES
        assert "FAILED" in constants.VALID_REPORT_STATUSES
        assert len(constants.VALID_REPORT_STATUSES) == 3

    def test_valid_risk_levels(self):
        """测试风险等级枚举值"""
        assert "低" in constants.VALID_RISK_LEVELS
        assert "中" in constants.VALID_RISK_LEVELS
        assert "高" in constants.VALID_RISK_LEVELS
        assert len(constants.VALID_RISK_LEVELS) == 3


class TestStatusTransitions:
    """测试状态机流转"""

    def test_resume_pending_can_transition_to_passed(self):
        """简历待筛选状态可以流转到简历通过"""
        allowed = constants.ALLOWED_STATUS_TRANSITIONS.get("RESUME_PENDING", set())
        assert "RESUME_PASSED" in allowed

    def test_resume_pending_can_transition_to_rejected(self):
        """简历待筛选状态可以流转到简历淘汰"""
        allowed = constants.ALLOWED_STATUS_TRANSITIONS.get("RESUME_PENDING", set())
        assert "RESUME_REJECTED" in allowed

    def test_resume_passed_can_transition_to_first_interview(self):
        """简历通过状态可以流转到待初试"""
        allowed = constants.ALLOWED_STATUS_TRANSITIONS.get("RESUME_PASSED", set())
        assert "FIRST_INTERVIEW_PENDING" in allowed

    def test_first_interview_pending_can_transition_to_passed(self):
        """待初试状态可以流转到初试通过"""
        allowed = constants.ALLOWED_STATUS_TRANSITIONS.get("FIRST_INTERVIEW_PENDING", set())
        assert "FIRST_INTERVIEW_PASSED" in allowed

    def test_first_interview_pending_can_transition_to_rejected(self):
        """待初试状态可以流转到初试淘汰"""
        allowed = constants.ALLOWED_STATUS_TRANSITIONS.get("FIRST_INTERVIEW_PENDING", set())
        assert "FIRST_INTERVIEW_REJECTED" in allowed

    def test_first_interview_passed_can_transition_to_second_interview(self):
        """初试通过状态可以流转到待复试"""
        allowed = constants.ALLOWED_STATUS_TRANSITIONS.get("FIRST_INTERVIEW_PASSED", set())
        assert "SECOND_INTERVIEW_PENDING" in allowed

    def test_second_interview_passed_can_transition_to_hired(self):
        """复试通过状态可以流转到已录用"""
        allowed = constants.ALLOWED_STATUS_TRANSITIONS.get("SECOND_INTERVIEW_PASSED", set())
        assert "HIRED" in allowed

    def test_any_status_can_transition_to_abandoned(self):
        """所有中间状态都可以流转到已放弃"""
        intermediate_statuses = [
            "IMPORTED",
            "RESUME_PENDING",
            "RESUME_PASSED",
            "FIRST_INTERVIEW_PENDING",
            "FIRST_INTERVIEW_PASSED",
            "SECOND_INTERVIEW_PENDING",
        ]
        for status in intermediate_statuses:
            allowed = constants.ALLOWED_STATUS_TRANSITIONS.get(status, set())
            assert "ABANDONED" in allowed, f"{status} should allow ABANDONED"

    def test_any_status_can_transition_to_talent_pool(self):
        """所有中间状态都可以流转到人才库储备"""
        intermediate_statuses = [
            "RESUME_PENDING",
            "RESUME_PASSED",
            "FIRST_INTERVIEW_PENDING",
            "FIRST_INTERVIEW_PASSED",
            "SECOND_INTERVIEW_PENDING",
            "SECOND_INTERVIEW_PASSED",
        ]
        for status in intermediate_statuses:
            allowed = constants.ALLOWED_STATUS_TRANSITIONS.get(status, set())
            assert "TALENT_POOL" in allowed, f"{status} should allow TALENT_POOL"

    def test_hired_cannot_transition(self):
        """已录用状态是终态，不能流转"""
        allowed = constants.ALLOWED_STATUS_TRANSITIONS.get("HIRED", set())
        assert len(allowed) == 0

    def test_rejected_cannot_transition(self):
        """淘汰状态是终态，不能流转"""
        rejected_statuses = ["RESUME_REJECTED", "FIRST_INTERVIEW_REJECTED", "SECOND_INTERVIEW_REJECTED"]
        for status in rejected_statuses:
            allowed = constants.ALLOWED_STATUS_TRANSITIONS.get(status, set())
            assert len(allowed) == 0, f"{status} should be a terminal state"

    def test_resume_rejected_cannot_go_to_interview(self):
        """简历淘汰不能直接进入面试"""
        allowed = constants.ALLOWED_STATUS_TRANSITIONS.get("RESUME_REJECTED", set())
        assert "FIRST_INTERVIEW_PENDING" not in allowed
        assert "SECOND_INTERVIEW_PENDING" not in allowed


class TestStageSuggestions:
    """测试阶段建议枚举值"""

    def test_resume_screening_suggestions(self):
        """测试简历筛选阶段的建议"""
        assert "建议约初试" in constants.RESUME_SUGGESTIONS
        assert "建议淘汰" in constants.RESUME_SUGGESTIONS
        assert "人才库储备" in constants.RESUME_SUGGESTIONS

    def test_first_interview_suggestions(self):
        """测试初试阶段的建议"""
        assert "建议进入复试" in constants.FIRST_INTERVIEW_SUGGESTIONS
        assert "建议淘汰" in constants.FIRST_INTERVIEW_SUGGESTIONS
        assert "人才库储备" in constants.FIRST_INTERVIEW_SUGGESTIONS

    def test_second_interview_suggestions(self):
        """测试复试阶段的建议"""
        assert "录用" in constants.SECOND_INTERVIEW_SUGGESTIONS
        assert "人才库储备" in constants.SECOND_INTERVIEW_SUGGESTIONS
        assert "淘汰" in constants.SECOND_INTERVIEW_SUGGESTIONS
