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
from app.services.analysis_service import (
    evaluate_interview_quality,
    validate_and_fix_analysis,
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


class TestCandidateEvaluationScoring:
    """测试综合评估报告的面试验证评分规则"""

    def _high_score_report(self):
        return {
            "candidate_overview": {
                "candidate_name": "张三",
                "job_title": "电商客服",
                "summary": "纸面条件较好",
                "match_score": 100,
                "recommendation": "强烈建议进入下一轮",
                "risk_level": "低",
                "confidence": "高",
            },
            "score_detail": {
                "job_experience_match": {"score": 35, "max_score": 35, "reason": "模型认为经验匹配"},
                "industry_product_match": {"score": 20, "max_score": 20, "reason": "模型认为经历一致"},
                "communication_ability": {"score": 20, "max_score": 20, "reason": "模型认为案例充分"},
                "stability_motivation": {"score": 10, "max_score": 10, "reason": "模型认为稳定"},
                "salary_arrival_match": {"score": 10, "max_score": 10, "reason": "模型认为匹配"},
                "risk_control": {"score": 5, "max_score": 5, "reason": "模型认为风险低"},
            },
            "interview_verification": [],
            "candidate_analysis": {
                "advantages": [],
                "weaknesses": [],
                "risk_points": [],
            },
            "follow_up_questions": [],
            "hr_interview_feedback": {
                "overall_comment": "",
                "strengths": [],
                "improvements": [],
                "missed_questions": [],
                "compliance_risks": [],
            },
            "leader_summary": {
                "short_conclusion": "",
                "decision": "可复试",
            },
        }

    def test_all_digit_interview_caps_score(self):
        report = self._high_score_report()
        interview_text = "HR：你介绍一下自己。\n候选人：1\nHR：你做过什么平台？\n候选人：1"

        result = validate_and_fix_analysis(report, interview_text)

        assert result["candidate_overview"]["match_score"] == 35
        assert result["candidate_overview"]["recommendation"] == "不建议"
        assert result["candidate_overview"]["risk_level"] == "高"
        assert result["candidate_overview"]["confidence"] == "低"
        assert result["leader_summary"]["decision"] == "不推荐"
        assert result["scoring_adjustment"]["applied_caps"][0]["cap"] == 35
        assert result["candidate_analysis"]["risk_points"][0]["risk"] == "面试验证不足"

    def test_core_claim_contradiction_caps_score(self):
        report = self._high_score_report()
        report["interview_verification"] = [
            {
                "claim": "简历声称熟悉京东、拼多多客服后台",
                "interview_evidence": "候选人表示没有实际操作过相关后台",
                "status": "CONTRADICTED",
                "is_core": True,
                "score_impact": "核心经历矛盾",
            }
        ]
        interview_text = "\n".join([
            "候选人：我之前主要处理淘宝售前咨询，每天会接待客户并记录问题。",
            "候选人：遇到投诉时我会先安抚情绪，再核对订单和售后政策。",
            "候选人：如果是物流问题，我会联系仓库和快递确认节点后回复客户。",
            "候选人：我对京东和拼多多后台没有实际操作经验，需要重新学习。",
        ])

        result = validate_and_fix_analysis(report, interview_text)

        assert result["candidate_overview"]["match_score"] == 45
        assert result["candidate_overview"]["recommendation"] == "不建议"
        cap_codes = {item["code"] for item in result["scoring_adjustment"]["applied_caps"]}
        assert "CORE_CLAIM_CONTRADICTED" in cap_codes

    def test_good_interview_keeps_dimension_score(self):
        report = self._high_score_report()
        report["interview_verification"] = [
            {
                "claim": "具备电商客服售后处理经验",
                "interview_evidence": "候选人能说明投诉处理、订单核对和售后协同流程",
                "status": "VERIFIED",
                "is_core": True,
                "score_impact": "支持高分",
            }
        ]
        interview_text = "\n".join([
            "候选人：我做过两年电商客服，主要负责售前咨询、订单跟进和售后投诉处理。",
            "候选人：遇到客户投诉时，我会先确认订单信息，再判断是物流、产品还是安装问题。",
            "候选人：如果涉及退款，我会按照平台规则提交凭证，并同步客户预计处理时间。",
            "候选人：我也会复盘高频问题，整理话术给新人使用，减少重复咨询。",
        ])

        result = validate_and_fix_analysis(report, interview_text)

        assert result["candidate_overview"]["match_score"] == 100
        assert result["candidate_overview"]["recommendation"] == "强烈建议进入下一轮"
        assert result["scoring_adjustment"]["applied_caps"] == []

    def test_interview_quality_detects_meaningless_answers(self):
        quality = evaluate_interview_quality("候选人：1\n候选人：1\n候选人：1")

        assert quality["score_cap"] == 35
        assert quality["valid_answer_count"] == 0

    def test_interview_quality_ignores_hr_only_questions(self):
        quality = evaluate_interview_quality("HR：你介绍一下自己。\n面试官：你做过哪些平台？")

        assert quality["score_cap"] == 35
        assert quality["valid_answer_count"] == 0
