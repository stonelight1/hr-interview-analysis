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

SCORING_MODEL_VERSION = "interview_verification_v1"

DIMENSION_MAX_SCORES = {
    "job_experience_match": 35,
    "industry_product_match": 20,
    "communication_ability": 20,
    "stability_motivation": 10,
    "salary_arrival_match": 10,
    "risk_control": 5,
}

DIMENSION_NAMES = {
    "job_experience_match": "岗位核心能力验证",
    "industry_product_match": "简历真实性/经历一致性",
    "communication_ability": "问题解决与案例深度",
    "stability_motivation": "沟通表达与稳定性",
    "salary_arrival_match": "薪资/到岗匹配",
    "risk_control": "风险控制",
}

VALID_VERIFICATION_STATUSES = {"VERIFIED", "PARTIAL", "MISSING", "CONTRADICTED", "UNVERIFIED"}
WEAK_ANSWER_TEXTS = {"1", "11", "111", "无", "没有", "没做过", "不会", "不知道", "不清楚", "不了解", "不确定", "忘了"}
QUESTION_PREFIX_RE = re.compile(r"^(HR|面试官|问|Q|question)\s*[:：]", flags=re.IGNORECASE)
CANDIDATE_PREFIX_RE = re.compile(
    r"^(候选人|应聘者|求职者|面试者|candidate|answer|答|A)\s*[:：]\s*(.+)$",
    flags=re.IGNORECASE,
)


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_answer_text(text: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text or "", flags=re.UNICODE).strip()


def _extract_candidate_answers(interview_text: str) -> list[str]:
    answers = []
    for line in (interview_text or "").splitlines():
        text = line.strip()
        if not text:
            continue
        match = CANDIDATE_PREFIX_RE.match(text)
        if match:
            answers.append(match.group(2).strip())

    if answers:
        return answers

    chunks = re.split(r"[\n。！？!?]+", interview_text or "")
    return [
        chunk.strip()
        for chunk in chunks
        if chunk.strip()
        and not chunk.strip().startswith("【")
        and not QUESTION_PREFIX_RE.match(chunk.strip())
    ]


def evaluate_interview_quality(interview_text: str) -> dict:
    text = (interview_text or "").strip()
    if not text:
        return {
            "answer_count": 0,
            "valid_answer_count": 0,
            "meaningful_char_count": 0,
            "score_cap": 35,
            "flags": ["EMPTY_INTERVIEW"],
            "reason": "面试记录为空，无法验证简历和岗位能力。",
        }

    answers = _extract_candidate_answers(text)
    valid_answers = []
    meaningful_char_count = 0

    for answer in answers:
        normalized = _normalize_answer_text(answer)
        meaningful_char_count += len(normalized)
        is_weak = (
            len(normalized) <= 2
            or normalized.isdigit()
            or len(set(normalized)) == 1
            or normalized in WEAK_ANSWER_TEXTS
        )
        if not is_weak:
            valid_answers.append(answer)

    digit_only_text = _normalize_answer_text(text)
    if digit_only_text and digit_only_text.isdigit():
        return {
            "answer_count": len(answers),
            "valid_answer_count": 0,
            "meaningful_char_count": meaningful_char_count,
            "score_cap": 35,
            "flags": ["MEANINGLESS_INTERVIEW"],
            "reason": "面试记录几乎全是数字，无法验证候选人能力。",
        }

    if not valid_answers:
        return {
            "answer_count": len(answers),
            "valid_answer_count": 0,
            "meaningful_char_count": meaningful_char_count,
            "score_cap": 35,
            "flags": ["NO_VALID_ANSWER"],
            "reason": "候选人没有提供有效回答，无法验证简历真实性和岗位能力。",
        }

    if len(valid_answers) < 2 or meaningful_char_count < 40:
        return {
            "answer_count": len(answers),
            "valid_answer_count": len(valid_answers),
            "meaningful_char_count": meaningful_char_count,
            "score_cap": 45,
            "flags": ["VERY_THIN_INTERVIEW"],
            "reason": "有效回答过少，核心经历和能力验证不足。",
        }

    if len(valid_answers) < 4 or meaningful_char_count < 100:
        return {
            "answer_count": len(answers),
            "valid_answer_count": len(valid_answers),
            "meaningful_char_count": meaningful_char_count,
            "score_cap": 60,
            "flags": ["INSUFFICIENT_INTERVIEW_EVIDENCE"],
            "reason": "面试证据偏少，不能支撑高分或强推进建议。",
        }

    return {
        "answer_count": len(answers),
        "valid_answer_count": len(valid_answers),
        "meaningful_char_count": meaningful_char_count,
        "score_cap": None,
        "flags": [],
        "reason": "",
    }


def _normalize_score_detail(result: dict) -> dict:
    score_detail = result.get("score_detail", {})
    if not isinstance(score_detail, dict):
        score_detail = {}

    for dim in SCORE_DIMENSIONS:
        dim_data = score_detail.get(dim)
        if not isinstance(dim_data, dict):
            dim_data = {}
        max_score = DIMENSION_MAX_SCORES[dim]
        dim_data["score"] = max(0, min(max_score, _safe_int(dim_data.get("score"))))
        dim_data["max_score"] = max_score
        if "reason" not in dim_data or not isinstance(dim_data["reason"], str):
            dim_data["reason"] = ""
        score_detail[dim] = dim_data

    result["score_detail"] = score_detail
    return score_detail


def _normalize_interview_verification(result: dict) -> list[dict]:
    items = result.get("interview_verification")
    if not isinstance(items, list):
        items = []

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "UNVERIFIED").upper()
        if status not in VALID_VERIFICATION_STATUSES:
            status = "UNVERIFIED"
        normalized.append({
            "claim": str(item.get("claim") or ""),
            "interview_evidence": str(item.get("interview_evidence") or ""),
            "status": status,
            "is_core": bool(item.get("is_core", True)),
            "score_impact": str(item.get("score_impact") or ""),
        })

    result["interview_verification"] = normalized
    return normalized


def _ensure_candidate_analysis(result: dict) -> dict:
    analysis = result.get("candidate_analysis")
    if not isinstance(analysis, dict):
        analysis = {}
    for key in ("advantages", "weaknesses", "risk_points"):
        if not isinstance(analysis.get(key), list):
            analysis[key] = []
    result["candidate_analysis"] = analysis
    return analysis


def _add_system_risk(result: dict, risk: str, level: str, detail: str) -> None:
    analysis = _ensure_candidate_analysis(result)
    existing = analysis["risk_points"]
    if not any(isinstance(item, dict) and item.get("risk") == risk for item in existing):
        existing.insert(0, {"risk": risk, "level": level, "detail": detail})


def _build_caps(interview_quality: dict, verification_items: list[dict]) -> list[dict]:
    caps = []
    if interview_quality.get("score_cap") is not None:
        caps.append({
            "code": interview_quality["flags"][0] if interview_quality.get("flags") else "INTERVIEW_QUALITY_CAP",
            "cap": interview_quality["score_cap"],
            "reason": interview_quality.get("reason") or "面试证据不足，触发封顶。",
        })

    core_items = [item for item in verification_items if item.get("is_core")]
    if any(item["status"] == "CONTRADICTED" for item in core_items):
        caps.append({
            "code": "CORE_CLAIM_CONTRADICTED",
            "cap": 45,
            "reason": "核心简历经历与面试回答矛盾，疑似简历不实。",
        })
    elif any(item["status"] == "MISSING" for item in core_items):
        caps.append({
            "code": "CORE_EVIDENCE_MISSING",
            "cap": 50,
            "reason": "核心岗位能力缺少面试证据。",
        })
    elif any(item["status"] == "UNVERIFIED" for item in core_items):
        caps.append({
            "code": "CORE_CLAIM_UNVERIFIED",
            "cap": 60,
            "reason": "核心简历声称尚未被面试验证。",
        })

    return caps


def _infer_recommendation(score: int, applied_caps: list[dict]) -> str:
    lowest_cap = min((cap["cap"] for cap in applied_caps), default=None)
    if score < 45 or (lowest_cap is not None and lowest_cap <= 45):
        return "不建议"
    if score < 60 or (lowest_cap is not None and lowest_cap <= 60):
        return "暂缓"
    if score >= 85:
        return "强烈建议进入下一轮"
    return "建议进入下一轮"


def _infer_risk_level(score: int, applied_caps: list[dict]) -> str:
    lowest_cap = min((cap["cap"] for cap in applied_caps), default=None)
    if score < 45 or (lowest_cap is not None and lowest_cap <= 45):
        return "高"
    if score < 70 or (lowest_cap is not None and lowest_cap <= 60):
        return "中"
    return "低"


def _infer_confidence(applied_caps: list[dict]) -> str:
    low_confidence_caps = {
        "EMPTY_INTERVIEW",
        "MEANINGLESS_INTERVIEW",
        "NO_VALID_ANSWER",
        "VERY_THIN_INTERVIEW",
    }
    if any(cap["code"] in low_confidence_caps for cap in applied_caps):
        return "低"
    if applied_caps:
        return "中"
    return "高"


def _infer_leader_decision(score: int, recommendation: str) -> str:
    if recommendation == "不建议" or score < 55:
        return "不推荐"
    if recommendation == "暂缓" or score < 75:
        return "待观察"
    return "可复试"


def apply_interview_verification_scoring(result: dict, interview_text: str) -> dict:
    score_detail = _normalize_score_detail(result)
    verification_items = _normalize_interview_verification(result)
    interview_quality = evaluate_interview_quality(interview_text)
    base_score = sum(score_detail[dim]["score"] for dim in SCORE_DIMENSIONS)
    applied_caps = _build_caps(interview_quality, verification_items)
    final_score = min([base_score] + [cap["cap"] for cap in applied_caps]) if applied_caps else base_score

    if applied_caps:
        _add_system_risk(
            result,
            "面试验证不足",
            _infer_risk_level(final_score, applied_caps),
            "；".join(cap["reason"] for cap in applied_caps),
        )

    overview = result.setdefault("candidate_overview", {})
    overview["match_score"] = final_score
    overview["recommendation"] = _infer_recommendation(final_score, applied_caps)
    overview["risk_level"] = _infer_risk_level(final_score, applied_caps)
    overview["confidence"] = _infer_confidence(applied_caps)

    leader_summary = result.setdefault("leader_summary", {})
    leader_summary["decision"] = _infer_leader_decision(final_score, overview["recommendation"])

    result["scoring_model"] = {
        "version": SCORING_MODEL_VERSION,
        "formula": "sum(weighted_dimensions), capped by interview quality and verification risk",
        "dimension_weights": [
            {"key": dim, "name": DIMENSION_NAMES[dim], "max_score": DIMENSION_MAX_SCORES[dim]}
            for dim in SCORE_DIMENSIONS
        ],
    }
    result["scoring_adjustment"] = {
        "base_score": base_score,
        "final_score": final_score,
        "applied_caps": applied_caps,
        "interview_quality": interview_quality,
    }

    return result


def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def validate_and_fix_analysis(result: dict, interview_text: str = "") -> dict:
    overview = result.get("candidate_overview", {})
    result["candidate_overview"] = overview
    result = apply_interview_verification_scoring(result, interview_text)
    overview = result.get("candidate_overview", {})

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

    result = validate_and_fix_analysis(result, interview_text)

    return result
