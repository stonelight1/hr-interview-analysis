import json
import hashlib
from typing import Optional

from app.services.deepseek_client import call_deepseek
from app import constants


SYSTEM_PROMPT_RESUME_SCREENING = """你是一名专业招聘筛选助手，擅长根据岗位 JD 和候选人简历进行初步筛选。

业务背景：
- 公司是电商公司。
- 业务是美的净水器经销商。
- 常见岗位包括电商客服、售后客服、销售、运营助理、仓库、文员、财务、人事行政等。
- 电商客服岗位重点看：平台经验（淘宝/京东/拼多多）、售后处理经验、抗压能力、打字速度。
- 售后客服岗位重点看：投诉处理经验、情绪管理、沟通技巧、退款流程经验。
- 销售岗位重点看：销售业绩、客户开发经验、沟通能力、行业经验。

你的任务：
1. 评估候选人与岗位的匹配度（重点关注相关经验、技能、稳定性）。
2. 列出匹配优势（基于简历和 JD 的对应证据，越具体越好）。
3. 列出不匹配点（基于 JD 要求但简历中缺少的部分）。
4. 列出风险点（稳定性、经验断层、频繁跳槽、薪资期望等）。
5. 判断是否建议约初试。
6. 给出初试建议追问问题（要针对简历中不明确或需要深挖的点）。

评分标准：
- 90-100：高度匹配，有直接相关经验，稳定性好
- 70-89：较好匹配，有部分相关经验，基本符合要求
- 50-69：一般匹配，有可迁移技能，但经验不足
- 30-49：匹配度低，经验差异大，需要大量培训
- 0-29：完全不匹配，不符合基本要求

重要要求：
- 必须基于输入内容分析，不要凭空编造。
- 如果信息不足，要明确写"信息不足"，并说明具体缺少什么。
- 不要基于性别、年龄、婚育、疾病、地域、民族等敏感因素做判断。
- 不要输出 Markdown、代码块、解释文字，只能输出 JSON。
- 所有字段必须存在，数组字段无内容时返回空数组。
- score 必须是 0 到 100 的整数，分数要合理，不能都给高分或都给低分。
- suggestion 只能是：建议约初试、建议淘汰、人才库储备。
- risk_level 只能是：低、中、高。
- 本阶段不能评价面试表现、沟通能力等，因为候选人尚未面试。
- 经验断层超过 3 个月、频繁跳槽（1年内换2次以上工作）要明确指出。
- 简历中的错别字、逻辑矛盾也要指出。

示例岗位类型：
1. 电商客服：看重平台操作经验、售后处理、抗压能力
2. 售后客服：看重投诉处理、情绪管理、退款流程
3. 销售：看重销售业绩、客户开发、行业资源
4. 仓库：看重体力、加班接受度、库存管理经验
5. 文员/财务：看重细心程度、软件操作、证书资质"""

USER_PROMPT_RESUME_SCREENING = """请根据以下岗位 JD 和候选人简历生成简历筛选报告。

【岗位 JD / 岗位要求】
{jd_text}

【候选人简历文本】
{resume_text}

请严格返回以下 JSON 结构，字段必须完整：

{{
  "stage": "RESUME_SCREENING",
  "score": 0,
  "suggestion": "",
  "risk_level": "",
  "summary": "",
  "strengths": [
    {{
      "title": "优势标题（简短）",
      "detail": "详细说明",
      "evidence": "简历中的具体证据（引用原文）"
    }}
  ],
  "mismatches": [
    {{
      "title": "不匹配点标题（简短）",
      "detail": "详细说明",
      "evidence": "缺少什么或简历中哪里体现不匹配"
    }}
  ],
  "risk_points": [
    {{
      "risk": "风险点标题（简短）",
      "level": "低/中/高",
      "detail": "详细说明风险原因和可能影响"
    }}
  ],
  "follow_up_questions": [
    {{
      "question": "具体的追问问题（不要问简历中已明确的内容）",
      "purpose": "追问的目的（验证什么能力或确认什么信息）"
    }}
  ],
  "summary": "一句话总结筛选结论（不超过30字）"
}}"""


def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def compute_content_hash(*parts: str) -> str:
    combined = "|".join(part or "" for part in parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def validate_resume_screening_report(result: dict) -> dict:
    if "score" not in result or not isinstance(result["score"], int):
        result["score"] = 0
    result["score"] = max(0, min(100, result["score"]))

    if result.get("suggestion") not in constants.RESUME_SUGGESTIONS:
        result["suggestion"] = "建议淘汰"

    if result.get("risk_level") not in constants.VALID_RISK_LEVELS:
        result["risk_level"] = "中"

    for key in ("strengths", "mismatches", "risk_points", "follow_up_questions"):
        if key not in result or not isinstance(result[key], list):
            result[key] = []

    if "summary" not in result or not result["summary"]:
        result["summary"] = ""

    return result


async def analyze_resume_screening(jd_text: str, resume_text: str) -> dict:
    user_prompt = USER_PROMPT_RESUME_SCREENING.format(
        jd_text=jd_text,
        resume_text=resume_text,
    )

    raw_response = await call_deepseek(user_prompt)
    cleaned_text = clean_json_text(raw_response)

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI 返回格式异常，无法解析 JSON: {str(e)}")

    result = validate_resume_screening_report(result)
    return result
