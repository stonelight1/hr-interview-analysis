import json
import re
from app.services.deepseek_client import build_user_prompt, call_deepseek

VALID_RECOMMENDATIONS = ["强烈建议进入下一轮", "建议进入下一轮", "暂缓", "不建议"]
VALID_RISK_LEVELS = ["低", "中", "高"]
VALID_CONFIDENCES = ["低", "中", "高"]
VALID_DECISIONS = ["可复试", "待观察", "不推荐"]

SCORE_DIMENSIONS = [
    "job_experience_match",
    "industry_product_match",
    "communication_ability",
    "stability_motivation",
    "salary_arrival_match",
    "risk_control"
]


def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def validate_and_fix_analysis(result: dict) -> dict:
    overview = result.get("candidate_overview", {})
    score_detail = result.get("score_detail", {})

    # 校验并修正 match_score
    total_score = 0
    for dim in SCORE_DIMENSIONS:
        dim_data = score_detail.get(dim, {})
        score = dim_data.get("score", 0)
        if not isinstance(score, int):
            score = 0
        total_score += score

    match_score = overview.get("match_score", 0)
    if not isinstance(match_score, int) or match_score < 0 or match_score > 100:
        match_score = total_score
    elif match_score != total_score:
        match_score = total_score

    overview["match_score"] = match_score

    # 校验枚举值
    recommendation = overview.get("recommendation", "")
    if recommendation not in VALID_RECOMMENDATIONS:
        overview["recommendation"] = "暂缓"

    risk_level = overview.get("risk_level", "")
    if risk_level not in VALID_RISK_LEVELS:
        overview["risk_level"] = "中"

    confidence = overview.get("confidence", "")
    if confidence not in VALID_CONFIDENCES:
        overview["confidence"] = "中"

    # 校验 leader_summary.decision
    leader_summary = result.get("leader_summary", {})
    decision = leader_summary.get("decision", "")
    if decision not in VALID_DECISIONS:
        leader_summary["decision"] = "待观察"

    return result


def validate_json_structure(result: dict) -> bool:
    required_sections = [
        "candidate_overview",
        "score_detail",
        "candidate_analysis",
        "follow_up_questions",
        "hr_interview_feedback",
        "leader_summary"
    ]

    for section in required_sections:
        if section not in result:
            return False

    overview = result.get("candidate_overview", {})
    required_overview_fields = ["candidate_name", "job_title", "summary", "match_score",
                                 "recommendation", "risk_level", "confidence"]
    for field in required_overview_fields:
        if field not in overview:
            return False

    score_detail = result.get("score_detail", {})
    for dim in SCORE_DIMENSIONS:
        if dim not in score_detail:
            return False
        dim_data = score_detail[dim]
        if "score" not in dim_data or "max_score" not in dim_data or "reason" not in dim_data:
            return False

    return True


async def analyze_candidate(candidate_name: str, job_title: str, jd_text: str,
                            resume_text: str, interview_text: str) -> dict:
    user_prompt = build_user_prompt(candidate_name, job_title, jd_text, resume_text, interview_text)

    raw_response = await call_deepseek(user_prompt)

    cleaned_text = clean_json_text(raw_response)

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI 返回格式异常，无法解析 JSON: {str(e)}")

    if not validate_json_structure(result):
        raise ValueError("AI 返回 JSON 结构不完整，缺少必要字段")

    result = validate_and_fix_analysis(result)

    return result
