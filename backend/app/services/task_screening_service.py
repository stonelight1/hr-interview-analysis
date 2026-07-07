"""
岗位初筛任务 AI 服务。

输入结构化 JD、原始简历和候选人画像，输出严格的岗位匹配初筛 JSON。
"""
import json
from typing import Any, Dict, List, Optional

from app import constants
from app.services.deepseek_client import call_deepseek
from app.services.prompt_templates import get_default_prompt_template, render_prompt_template
from app.utils.json_utils import clean_json_text


SYSTEM_PROMPT_SCREENING_MATCH = """你是一名专业 HR 简历初筛助手。你的任务是根据岗位 JD 和候选人简历，生成可解释的岗位匹配初筛结果。

重要要求：
1. 只能基于 JD 和简历内容分析，不允许编造候选人信息。
2. 简历未体现的内容必须写“简历未体现，建议面试确认”，不能直接当作不符合。
3. 不要基于性别、年龄、婚育、疾病、民族等敏感因素做歧视性判断。
4. 当前阶段尚未面试，沟通表达如果简历无法判断，必须返回“简历无法判断”。
5. 必须返回严格 JSON，不要 Markdown，不要代码块，不要解释文字。
6. 所有字段必须存在，数组无内容时返回空数组。
7. conclusion 只能是 RECOMMENDED、PENDING、REJECTED。
8. confidence 只能是 HIGH、MEDIUM、LOW。
9. score 必须是 0 到 100 的整数。
10. 硬性条件明显不满足时，应降低 score 和 conclusion；信息缺失时优先标记为风险或待确认。
"""


USER_PROMPT_SCREENING_MATCH = """请根据以下岗位 JD 和候选人简历生成岗位初筛结果。

【结构化 JD】
{jd_structured_json}

【JD 原文】
{jd_text}

【候选人画像】
{candidate_profile_json}

【简历原文】
{resume_text}

请严格返回以下 JSON：
{{
  "score": 82,
  "conclusion": "RECOMMENDED",
  "confidence": "HIGH",
  "dimension_scores": {{
    "experience_match": 85,
    "skill_match": 80,
    "industry_match": 75,
    "education_match": 90,
    "stability": 70,
    "communication_expression": "简历无法判断",
    "overall_risk": 30
  }},
  "match_highlights": [
    "具备电商行业工作经验",
    "有客户沟通和订单处理经验"
  ],
  "risk_points": [
    "简历未体现家电或净水器行业经验，建议面试确认",
    "最近一段工作时间较短，需要面试确认稳定性"
  ],
  "interview_questions": [
    "你之前主要负责哪些客户沟通场景？",
    "是否接触过家电、净水器或类似产品？",
    "上一份工作离职原因是什么？"
  ],
  "ai_reason": "该候选人与岗位职责有较高重合度，建议进入初面。"
}}"""


async def analyze_task_screening(
    jd_text: str,
    jd_structured: Dict[str, Any],
    resume_text: str,
    candidate_profile: Dict[str, Any],
    prompt_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    default_template = get_default_prompt_template(constants.PROMPT_KEY_SCREENING_MATCH)
    template = prompt_config or default_template
    context = {
        "jd_structured_json": json.dumps(jd_structured or {}, ensure_ascii=False),
        "jd_text": jd_text,
        "candidate_profile_json": json.dumps(candidate_profile or {}, ensure_ascii=False),
        "resume_text": resume_text,
    }
    system_prompt = render_prompt_template(template.get("system_prompt") or default_template["system_prompt"], context)
    user_prompt = render_prompt_template(template.get("user_prompt") or default_template["user_prompt"], context)

    raw_response = await call_deepseek(user_prompt, system_prompt)
    cleaned_text = clean_json_text(raw_response)

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI 返回格式异常，无法解析 JSON: {str(exc)}") from exc

    return normalize_screening_result(result)


def normalize_screening_result(result: Dict[str, Any]) -> Dict[str, Any]:
    result["score"] = _clamp_int(result.get("score"), 0, 100)

    if result.get("conclusion") not in constants.VALID_SCREENING_CONCLUSIONS:
        result["conclusion"] = _infer_conclusion(result["score"])

    if result.get("confidence") not in {"HIGH", "MEDIUM", "LOW"}:
        result["confidence"] = "MEDIUM"

    dimensions = result.get("dimension_scores")
    if not isinstance(dimensions, dict):
        dimensions = {}

    normalized_dimensions: Dict[str, Any] = {
        "experience_match": _clamp_int(dimensions.get("experience_match"), 0, 100),
        "skill_match": _clamp_int(dimensions.get("skill_match"), 0, 100),
        "industry_match": _clamp_int(dimensions.get("industry_match"), 0, 100),
        "education_match": _clamp_int(dimensions.get("education_match"), 0, 100),
        "stability": _clamp_int(dimensions.get("stability"), 0, 100),
        "communication_expression": dimensions.get("communication_expression") or "简历无法判断",
        "overall_risk": _clamp_int(dimensions.get("overall_risk"), 0, 100),
    }
    result["dimension_scores"] = normalized_dimensions

    result["match_highlights"] = _normalize_string_list(result.get("match_highlights"))
    result["risk_points"] = _normalize_string_list(result.get("risk_points"))
    result["interview_questions"] = _normalize_string_list(result.get("interview_questions"))
    result["ai_reason"] = str(result.get("ai_reason") or "")

    return result


def _infer_conclusion(score: int) -> str:
    if score >= 75:
        return constants.SCREENING_CONCLUSION_RECOMMENDED
    if score >= 55:
        return constants.SCREENING_CONCLUSION_PENDING
    return constants.SCREENING_CONCLUSION_REJECTED


def _clamp_int(value: Any, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = minimum
    return max(minimum, min(maximum, number))


def _normalize_string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    normalized = []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = item.get("detail") or item.get("title") or item.get("risk") or item.get("question") or ""
            text = str(text).strip()
        else:
            text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized
