import json

from app.services.deepseek_client import call_deepseek
from app import constants


SYSTEM_PROMPT_FIRST_INTERVIEW = """你是一名专业招聘面试评估助手，擅长根据岗位 JD、候选人简历和初试记录评估候选人表现。

业务背景：
- 公司是电商公司。
- 业务是美的净水器经销商。
- 常见岗位包括电商客服、售后客服、销售、运营助理、仓库、文员、财务、人事行政等。
- 当前阶段是初试评估，候选人已经完成初试，需要判断其是否适合进入复试。

你的任务：
1. 给出初试综合评分（0-100分）。
2. 评估沟通表达能力（0-25分）。
3. 评估岗位理解能力（0-25分）。
4. 评估工作稳定性判断（0-25分）。
5. 评估薪资期望匹配度（0-25分）。
6. 列出风险点。
7. 判断是否建议进入复试。

评估维度详细标准：

【沟通表达能力】（满分25分）
- 20-25分：表达清晰有条理，逻辑性强，能准确回答问题，沟通高效
- 15-19分：表达较清晰，基本能回答问题，但有时不够简洁
- 10-14分：表达一般，需要多次追问才能理解意思
- 0-9分：表达混乱，难以理解，沟通效率很低

【岗位理解能力】（满分25分）
- 20-25分：对岗位职责、工作内容有清晰认识，有相关经验案例
- 15-19分：对岗位有基本理解，但经验略显不足
- 10-14分：对岗位理解模糊，经验相关性低
- 0-9分：对岗位完全不了解，无相关经验

【工作稳定性】（满分25分）
- 20-25分：离职原因合理，职业规划清晰，稳定性高
- 15-19分：离职原因基本合理，稳定性一般
- 10-14分：离职原因模糊，稳定性存疑
- 0-9分：频繁跳槽，离职原因不合理，稳定性很差

【薪资期望匹配度】（满分25分）
- 20-25分：期望与岗位预算匹配，有弹性空间
- 15-19分：期望略高或略低，但可协商
- 10-14分：期望差距较大，协商空间小
- 0-9分：期望完全不匹配，无法协商

重要要求：
- 必须基于输入内容分析，不要凭空编造。
- 如果信息不足，要明确写"信息不足"，并说明具体缺少什么。
- 不要基于性别、年龄、婚育、疾病、地域、民族等敏感因素做判断。
- 不要输出 Markdown、代码块、解释文字，只能输出 JSON。
- 所有字段必须存在，数组字段无内容时返回空数组。
- score 必须是 0 到 100 的整数，要合理分配，不能都给高分或都给低分。
- suggestion 只能是：建议进入复试、建议淘汰、人才库储备。
- risk_level 只能是：低、中、高。
- 本阶段重点评价面试表现，不要重复简历筛选已经得出的结论。
- 离职原因模糊（如"个人原因"）要明确指出。
- 回答问题时有矛盾、犹豫、不确定要指出。
- 薪资期望与岗位预算差距超过20%要明确指出。
- 稳定性判断要看：最近2份工作的时长、离职原因合理性、职业规划。

岗位特定评估重点：
- 电商客服：看抗压能力、打字速度、平台经验、情绪管理
- 售后客服：看投诉处理经验、沟通技巧、退款流程熟悉度
- 销售：看销售业绩、客户开发能力、沟通说服力
- 仓库：看体力、加班接受度、细心程度
- 文员/财务：看细心程度、软件操作、专业证书"""

USER_PROMPT_FIRST_INTERVIEW = """请根据以下岗位 JD、候选人简历和初试记录生成初试分析报告。

【岗位 JD / 岗位要求】
{jd_text}

【候选人简历文本】
{resume_text}

【初试记录文本】
{interview_text}

请严格返回以下 JSON 结构，字段必须完整：

{{
  "stage": "FIRST_INTERVIEW",
  "score": 0,
  "suggestion": "",
  "risk_level": "",
  "summary": "一句话总结初试结论（不超过30字）",
  "dimensions": {{
    "communication_ability": {{
      "score": 0,
      "max_score": 25,
      "comment": "具体评估依据（引用面试中的例子）"
    }},
    "job_understanding": {{
      "score": 0,
      "max_score": 25,
      "comment": "具体评估依据（引用面试中的例子）"
    }},
    "stability": {{
      "score": 0,
      "max_score": 25,
      "comment": "具体评估依据（离职原因、职业规划等）"
    }},
    "salary_match": {{
      "score": 0,
      "max_score": 25,
      "comment": "具体评估依据（期望薪资、谈判情况等）"
    }}
  }},
  "risk_points": [
    {{
      "risk": "风险点标题（简短）",
      "level": "低/中/高",
      "detail": "详细说明风险原因和可能影响"
    }}
  ],
  "next_round_focus": [
    "复试需要重点追问的问题1",
    "复试需要重点追问的问题2"
  ]
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


def validate_first_interview_report(result: dict) -> dict:
    if "score" not in result or not isinstance(result["score"], int):
        result["score"] = 0
    result["score"] = max(0, min(100, result["score"]))

    if result.get("suggestion") not in constants.FIRST_INTERVIEW_SUGGESTIONS:
        result["suggestion"] = "建议淘汰"

    if result.get("risk_level") not in constants.VALID_RISK_LEVELS:
        result["risk_level"] = "中"

    dimensions = result.get("dimensions", {})
    required_dimensions = ["communication_ability", "job_understanding", "stability", "salary_match"]
    for dim in required_dimensions:
        if dim not in dimensions:
            dimensions[dim] = {"score": 0, "max_score": 25, "comment": ""}
        else:
            dim_data = dimensions[dim]
            if "score" not in dim_data or not isinstance(dim_data["score"], int):
                dim_data["score"] = 0
            if "max_score" not in dim_data:
                dim_data["max_score"] = 25
            if "comment" not in dim_data:
                dim_data["comment"] = ""
    result["dimensions"] = dimensions

    if "risk_points" not in result or not isinstance(result["risk_points"], list):
        result["risk_points"] = []
    if "next_round_focus" not in result or not isinstance(result["next_round_focus"], list):
        result["next_round_focus"] = []
    if "summary" not in result or not result["summary"]:
        result["summary"] = ""

    return result


async def analyze_first_interview(jd_text: str, resume_text: str, interview_text: str) -> dict:
    user_prompt = USER_PROMPT_FIRST_INTERVIEW.format(
        jd_text=jd_text,
        resume_text=resume_text,
        interview_text=interview_text,
    )

    raw_response = await call_deepseek(user_prompt)
    cleaned_text = clean_json_text(raw_response)

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI 返回格式异常，无法解析 JSON: {str(e)}")

    result = validate_first_interview_report(result)
    return result
