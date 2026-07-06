"""
单元测试：AI 服务的 JSON 解析和校验
"""
import json
import pytest
from app.services.resume_screening_service import (
    clean_json_text,
    validate_resume_screening_report,
    compute_content_hash,
)
from app.services.first_interview_service import (
    validate_first_interview_report,
)


class TestCleanJsonText:
    """测试 JSON 文本清理"""

    def test_clean_json_with_markdown(self):
        """测试清理 Markdown 代码块"""
        text = '```json\n{"key": "value"}\n```'
        result = clean_json_text(text)
        assert result == '{"key": "value"}'

    def test_clean_json_with_only_backticks(self):
        """测试清理只有反引号的情况"""
        text = '```\n{"key": "value"}\n```'
        result = clean_json_text(text)
        assert result == '{"key": "value"}'

    def test_clean_json_with_whitespace(self):
        """测试清理空白"""
        text = '  \n  {"key": "value"}  \n  '
        result = clean_json_text(text)
        assert result == '{"key": "value"}'

    def test_clean_json_no_markdown(self):
        """测试无 Markdown 的 JSON"""
        text = '{"key": "value"}'
        result = clean_json_text(text)
        assert result == '{"key": "value"}'


class TestComputeContentHash:
    """测试内容哈希计算"""

    def test_same_content_same_hash(self):
        """测试相同内容生成相同哈希"""
        hash1 = compute_content_hash("content1", "content2")
        hash2 = compute_content_hash("content1", "content2")
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """测试不同内容生成不同哈希"""
        hash1 = compute_content_hash("content1")
        hash2 = compute_content_hash("content2")
        assert hash1 != hash2

    def test_hash_is_string(self):
        """测试哈希是字符串"""
        hash_value = compute_content_hash("test")
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 hex digest

    def test_hash_with_empty_content(self):
        """测试空内容哈希"""
        hash_value = compute_content_hash()
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64


class TestValidateResumeScreeningReport:
    """测试简历筛选报告校验"""

    def test_valid_report(self):
        """测试有效报告"""
        report = {
            "score": 80,
            "suggestion": "建议约初试",
            "risk_level": "低",
            "summary": "匹配度较高",
            "strengths": [{"title": "经验匹配", "detail": "有相关经验", "evidence": "简历中提到"}],
            "mismatches": [],
            "risk_points": [],
            "follow_up_questions": [],
        }
        result = validate_resume_screening_report(report)
        assert result["score"] == 80
        assert result["suggestion"] == "建议约初试"

    def test_invalid_suggestion(self):
        """测试无效建议"""
        report = {
            "score": 80,
            "suggestion": "无效建议",
            "risk_level": "低",
        }
        result = validate_resume_screening_report(report)
        assert result["suggestion"] == "建议淘汰"  # 默认值

    def test_invalid_risk_level(self):
        """测试无效风险等级"""
        report = {
            "score": 80,
            "suggestion": "建议约初试",
            "risk_level": "无效",
        }
        result = validate_resume_screening_report(report)
        assert result["risk_level"] == "中"  # 默认值

    def test_score_out_of_range(self):
        """测试分数超出范围"""
        report = {
            "score": 150,
            "suggestion": "建议约初试",
        }
        result = validate_resume_screening_report(report)
        assert result["score"] == 100  # 限制在 0-100

    def test_score_negative(self):
        """测试负分"""
        report = {
            "score": -10,
            "suggestion": "建议约初试",
        }
        result = validate_resume_screening_report(report)
        assert result["score"] == 0  # 限制在 0-100

    def test_missing_score(self):
        """测试缺少分数"""
        report = {
            "suggestion": "建议约初试",
        }
        result = validate_resume_screening_report(report)
        assert result["score"] == 0

    def test_missing_optional_fields(self):
        """测试缺少可选字段"""
        report = {
            "score": 80,
            "suggestion": "建议约初试",
        }
        result = validate_resume_screening_report(report)
        assert "strengths" in result
        assert "mismatches" in result
        assert "risk_points" in result
        assert "follow_up_questions" in result
        assert result["strengths"] == []
        assert result["mismatches"] == []
        assert result["risk_points"] == []
        assert result["follow_up_questions"] == []


class TestValidateFirstInterviewReport:
    """测试初试分析报告校验"""

    def test_valid_report(self):
        """测试有效报告"""
        report = {
            "score": 75,
            "suggestion": "建议进入复试",
            "risk_level": "中",
            "summary": "表现较好",
            "dimensions": {
                "communication_ability": {"score": 20, "max_score": 25, "comment": "表达清晰"},
                "job_understanding": {"score": 18, "max_score": 25, "comment": "理解较好"},
                "stability": {"score": 17, "max_score": 25, "comment": "稳定性一般"},
                "salary_match": {"score": 15, "max_score": 25, "comment": "基本匹配"},
            },
            "risk_points": [],
            "next_round_focus": [],
        }
        result = validate_first_interview_report(report)
        assert result["score"] == 75
        assert result["suggestion"] == "建议进入复试"

    def test_invalid_suggestion(self):
        """测试无效建议"""
        report = {
            "score": 75,
            "suggestion": "无效建议",
            "dimensions": {
                "communication_ability": {"score": 20, "max_score": 25, "comment": "清晰"},
                "job_understanding": {"score": 18, "max_score": 25, "comment": "较好"},
                "stability": {"score": 17, "max_score": 25, "comment": "一般"},
                "salary_match": {"score": 15, "max_score": 25, "comment": "匹配"},
            },
        }
        result = validate_first_interview_report(report)
        assert result["suggestion"] == "建议淘汰"  # 默认值

    def test_missing_dimensions(self):
        """测试缺少评估维度"""
        report = {
            "score": 75,
            "suggestion": "建议进入复试",
            "dimensions": {},
        }
        result = validate_first_interview_report(report)
        assert "communication_ability" in result["dimensions"]
        assert "job_understanding" in result["dimensions"]
        assert "stability" in result["dimensions"]
        assert "salary_match" in result["dimensions"]

    def test_partial_dimensions(self):
        """测试部分评估维度"""
        report = {
            "score": 75,
            "suggestion": "建议进入复试",
            "dimensions": {
                "communication_ability": {"score": 20, "max_score": 25, "comment": "表达清晰"},
            },
        }
        result = validate_first_interview_report(report)
        assert "job_understanding" in result["dimensions"]
        assert "stability" in result["dimensions"]
        assert "salary_match" in result["dimensions"]

    def test_score_out_of_range(self):
        """测试分数超出范围"""
        report = {
            "score": 150,
            "suggestion": "建议进入复试",
            "dimensions": {
                "communication_ability": {"score": 20, "max_score": 25, "comment": "清晰"},
                "job_understanding": {"score": 18, "max_score": 25, "comment": "较好"},
                "stability": {"score": 17, "max_score": 25, "comment": "一般"},
                "salary_match": {"score": 15, "max_score": 25, "comment": "匹配"},
            },
        }
        result = validate_first_interview_report(report)
        assert result["score"] == 100

    def test_missing_risk_points(self):
        """测试缺少风险点"""
        report = {
            "score": 75,
            "suggestion": "建议进入复试",
            "dimensions": {
                "communication_ability": {"score": 20, "max_score": 25, "comment": "清晰"},
                "job_understanding": {"score": 18, "max_score": 25, "comment": "较好"},
                "stability": {"score": 17, "max_score": 25, "comment": "一般"},
                "salary_match": {"score": 15, "max_score": 25, "comment": "匹配"},
            },
        }
        result = validate_first_interview_report(report)
        assert "risk_points" in result
        assert "next_round_focus" in result
        assert result["risk_points"] == []
        assert result["next_round_focus"] == []
