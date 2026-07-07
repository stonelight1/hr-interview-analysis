import asyncio
import json
from typing import Any, Optional

from app.config import get_settings
from app.services.deepseek_client import call_deepseek


SYSTEM_PROMPT_INTERVIEW_QUESTIONS = """你是一名专业招聘面试官，擅长根据岗位 JD 和候选人简历生成面试问题。

要求：
- 必须基于 JD 和简历，不要凭空编造。
- 问题要用于真实面试，避免空泛提问。
- 重点覆盖岗位理解、经验真实性、能力匹配、风险确认、动机稳定性和基础条件。
- 不要询问婚育、疾病、民族、宗教、家庭隐私等敏感或不合规问题。
- 只返回严格 JSON，不要 Markdown，不要解释文字。
- 字段必须完整，数组无内容时返回空数组。"""

USER_PROMPT_INTERVIEW_QUESTIONS = """请根据以下岗位 JD 和候选人简历生成面试问题。

【问题类型】
{round_label}

【生成策略】
{round_guidance}

【岗位名称】
{job_name}

【岗位 JD】
{jd_text}

【候选人简历】
{resume_text}

【可选初筛报告】
{screening_report_json}

请返回严格 JSON：
{{
  "questions": [
    {{
      "question": "具体面试问题",
      "purpose": "提问目的",
      "dimension": "考察维度",
      "required": true,
      "reference": "判断回答是否合格的依据",
      "source": "JD/简历/风险点"
    }}
  ]
}}

生成要求：
- 总数 8 到 12 题。
- 必问题不少于 6 题，备选题不少于 2 题。
- 至少 3 题必须直接追问简历中的具体经历。
- 至少 3 题必须验证 JD 中的关键要求。
- 如果初筛报告存在，可以针对风险点生成追问，但不要让问题只依赖初筛报告。"""


def parse_report_json(report_json: Optional[str]) -> dict[str, Any]:
    if not report_json:
        return {}
    try:
        data = json.loads(report_json)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


async def generate_candidate_questions(
    *,
    job_name: str,
    jd_text: str,
    resume_text: str,
    screening_report_json: Optional[str],
    round_type: Optional[str] = None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.deepseek_api_key:
        return _fallback_candidate_questions(job_name, jd_text, resume_text, screening_report_json, round_type)

    user_prompt = USER_PROMPT_INTERVIEW_QUESTIONS.format(
        round_label=_question_round_label(round_type),
        round_guidance=_question_round_guidance(round_type),
        job_name=job_name or "当前岗位",
        jd_text=jd_text or "",
        resume_text=resume_text or "",
        screening_report_json=screening_report_json or "{}",
    )
    try:
        raw_response = await asyncio.wait_for(
            call_deepseek(user_prompt, system_prompt=SYSTEM_PROMPT_INTERVIEW_QUESTIONS),
            timeout=25,
        )
        parsed = _parse_question_response(raw_response)
        questions = parsed.get("questions") if isinstance(parsed, dict) else []
        normalized = [_normalize_question_item(item) for item in questions if item]
        normalized = [item for item in normalized if item.get("question")]
        if normalized:
            return normalized[:12]
    except Exception:
        pass
    return _fallback_candidate_questions(job_name, jd_text, resume_text, screening_report_json, round_type)


def _fallback_candidate_questions(
    job_name: str,
    jd_text: str,
    resume_text: str,
    screening_report_json: Optional[str],
    round_type: Optional[str] = None,
) -> list[dict[str, Any]]:
    questions = generate_round_questions(
        job_name=job_name,
        jd_text=jd_text,
        resume_text=resume_text,
        screening_report_json=screening_report_json,
        round_no=_fallback_round_no(round_type),
        based_on_previous=round_type not in {"FIRST_INTERVIEW", "HR_INTERVIEW"},
    )
    guidance = _question_round_guidance(round_type)
    if round_type in {"HR_INTERVIEW", "FINAL_INTERVIEW"}:
        questions = [
            _question("请说明你当前求职最看重的三项因素，并按优先级排序。", "确认候选人核心诉求和岗位供给是否匹配。", "动机匹配", True, "回答应具体，不只停留在泛泛表态。", "简历/JD"),
            _question("请说明你的期望薪资、可接受薪资范围和到岗时间。", "确认基础录用条件是否存在阻断。", "基础条件", True, "薪资、到岗时间与招聘条件基本匹配或可协商。", "JD"),
            _question("你离开上一份工作的主要原因是什么？这次选择机会时会避免什么问题？", "核实稳定性和离职风险。", "稳定性", True, "原因与简历时间线一致，能说明真实诉求。", "简历"),
            _question("如果业务节奏和预期不一致，你通常如何调整并保持交付？", "评估适应能力和抗压方式。", "适应能力", True, "能给出具体做法和过往例子。", "JD"),
        ] + questions[:8]
    for item in questions:
        item.setdefault("round_guidance", guidance)
    return questions[:12]


def _question_round_label(round_type: Optional[str]) -> str:
    return {
        "FIRST_INTERVIEW": "初试问题",
        "SECOND_INTERVIEW": "复试问题",
        "FINAL_INTERVIEW": "终面问题",
        "HR_INTERVIEW": "HR 面问题",
        "OTHER": "其他问题",
    }.get(round_type or "", "初试问题")


def _question_round_guidance(round_type: Optional[str]) -> str:
    return {
        "FIRST_INTERVIEW": "重点验证简历真实性、基础匹配、岗位动机、稳定性、基础条件和明显风险点。",
        "SECOND_INTERVIEW": "重点深挖岗位关键能力、项目/经历细节、业务场景处理、复杂问题解决和团队协作。",
        "FINAL_INTERVIEW": "重点判断综合胜任、价值观匹配、长期稳定性、入职风险和最终录用决策疑点。",
        "HR_INTERVIEW": "重点确认薪资期望、到岗时间、离职原因、稳定性、沟通表达和合规基础条件。",
        "OTHER": "围绕岗位 JD、简历证据和 HR 指定关注点生成可追问的问题。",
    }.get(round_type or "", "重点验证简历真实性、基础匹配、岗位动机、稳定性、基础条件和明显风险点。")


def _fallback_round_no(round_type: Optional[str]) -> int:
    if round_type in {"SECOND_INTERVIEW", "FINAL_INTERVIEW"}:
        return 2
    return 1


def generate_round_questions(
    *,
    job_name: str,
    jd_text: str,
    resume_text: str,
    screening_report_json: Optional[str],
    round_no: int,
    previous_record_text: Optional[str] = None,
    previous_conclusion: Optional[str] = None,
    based_on_previous: bool = True,
) -> list[dict[str, Any]]:
    report = parse_report_json(screening_report_json)
    risks = report.get("risk_points") if isinstance(report.get("risk_points"), list) else []
    follow_ups = report.get("follow_up_questions") if isinstance(report.get("follow_up_questions"), list) else []
    primary_risk = _risk_text(risks[0] if risks else None)

    if round_no <= 1:
        required = [
            _question(f"请用 2 分钟说明你对{job_name or '当前岗位'}核心工作的理解。", "确认候选人是否理解岗位职责和业务场景。", "岗位理解", True, "能准确说出岗位关键任务，并能结合自身经历回应。", "JD"),
            _question("请介绍一段和本岗位最相关的工作经历，重点说明你的具体职责和结果。", "验证简历经历真实性和相关度。", "经验匹配", True, "回答应包含时间、职责、动作和可验证结果。", "简历"),
            _question(f"针对初筛报告中提到的风险点：{primary_risk}，请你补充说明背景和现状。", "核实关键风险是否可接受。", "风险确认", True, "能解释原因、影响和改进情况，不回避关键事实。", "风险点"),
            _question(_follow_up_text(follow_ups, 0, "你过往处理过最接近本岗位要求的问题是什么？请说明过程。"), "围绕 AI 初筛建议继续深挖。", "能力验证", True, "能给出具体案例和可复盘过程。", "AI 初筛报告"),
            _question("请说明你最近一份工作的离职原因，以及当前求职最看重的因素。", "确认稳定性、动机和期望匹配。", "稳定性", True, "回答与简历经历一致，诉求与岗位条件基本匹配。", "简历"),
            _question("如果入职后发现实际工作节奏高于预期，你通常如何调整？", "评估抗压和适应能力。", "适应能力", True, "能给出具体方法，不只停留在态度表态。", "JD"),
            _question("请举例说明你在工作中和他人协作解决问题的一次经历。", "了解沟通协作方式。", "协作沟通", True, "能说明角色、沟通对象、冲突点和结果。", "简历"),
            _question("你对薪资、到岗时间、工作地点或排班有什么明确限制？", "确认基础条件是否存在阻断。", "基础确认", True, "关键条件与岗位供给不冲突，若有差异需可协商。", "JD"),
        ]
        optional = [
            _question(_follow_up_text(follow_ups, 1, "简历中有一段经历描述较简略，请补充你实际负责的范围和产出。"), "补齐简历信息缺口。", "信息完整性", False, "补充内容应和简历时间线一致。", "简历"),
            _question("如果让上一任主管评价你，他可能会提到哪一个优点和哪一个需要改进的点？", "了解自我认知和改进意愿。", "自我认知", False, "能具体说明，不做空泛包装。", "风险点"),
            _question(_follow_up_text(follow_ups, 2, "你希望下一份工作提供哪些成长或资源支持？"), "判断候选人诉求与团队环境匹配度。", "动机匹配", False, "诉求与岗位阶段、团队资源基本一致。", "AI 初筛报告"),
        ]
        return required + optional

    previous_text = previous_conclusion or previous_record_text or "上一轮面试记录"
    previous_source = "上轮面试" if based_on_previous else "AI 初筛报告"
    required = [
        _question(f"上一轮记录中提到“{previous_text[:40]}”，请你进一步补充具体案例。", "基于上一轮记录继续验证关键点。", "追问验证", True, "回答能补充事实细节，而不是重复上一轮表述。", previous_source),
        _question(f"请结合{job_name or '当前岗位'}，说明你会如何在入职前 30 天开展工作。", "验证岗位落地能力。", "岗位胜任力", True, "计划应有优先级、关键动作和衡量标准。", "JD"),
        _question(f"针对风险点：{primary_risk}，如果业务负责人追问，你会如何证明风险可控？", "复核风险是否已被充分解释。", "风险复核", True, "能提供事实证据或可验证承诺。", "风险点"),
        _question("请讲一个你独立推动复杂问题解决的案例。", "验证更高要求下的主动性和解决问题能力。", "问题解决", True, "能说明问题规模、约束、决策和结果。", "简历"),
        _question("如果团队对你的方案提出不同意见，你通常如何推进共识？", "考察跨角色沟通和协同。", "沟通协作", True, "能体现倾听、权衡和推进方式。", previous_source),
        _question("你认为自己入职后最大的风险点是什么？准备如何弥补？", "确认自我认知和风险应对。", "风险确认", True, "能客观承认短板，并提出可执行动作。", "风险点"),
    ]
    optional = [
        _question("如果本轮面试官只保留一个疑问，你希望他继续追问你什么？", "发现候选人最希望补充证明的能力点。", "补充验证", False, "能主动暴露需要进一步验证的信息。", previous_source),
        _question("请补充一个能代表你工作风格的具体场景。", "帮助主管判断团队适配度。", "团队适配", False, "案例能反映协作、执行或复盘习惯。", "简历"),
    ]
    return required + optional


def _parse_question_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    try:
        data = json.loads(cleaned.strip())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _normalize_question_item(item: Any) -> dict[str, Any]:
    if isinstance(item, str):
        return _question(item, "", "综合判断", True, "", "JD/简历")
    if not isinstance(item, dict):
        return {}
    return {
        "question": str(item.get("question") or item.get("title") or item.get("detail") or "").strip(),
        "purpose": str(item.get("purpose") or "").strip(),
        "dimension": str(item.get("dimension") or item.get("category") or "综合判断").strip(),
        "required": item.get("required") is not False,
        "reference": str(item.get("reference") or item.get("evaluation_reference") or "").strip(),
        "source": str(item.get("source") or "JD/简历").strip(),
    }


def _question(
    question: str,
    purpose: str,
    dimension: str,
    required: bool,
    reference: str,
    source: str,
) -> dict[str, Any]:
    return {
        "question": question,
        "purpose": purpose,
        "dimension": dimension,
        "required": required,
        "reference": reference,
        "source": source,
    }


def _risk_text(item: Any) -> str:
    if not item:
        return "简历中的稳定性、经验断层、薪资期望或信息缺口"
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("risk") or item.get("title") or item.get("detail") or "简历风险点"
    return "简历风险点"


def _follow_up_text(items: list[Any], index: int, fallback: str) -> str:
    if index >= len(items):
        return fallback
    item = items[index]
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("question") or fallback
    return fallback
