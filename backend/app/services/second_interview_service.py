"""
复试分析服务

根据岗位 JD、候选人简历、初试分析报告和复试记录，生成复试评估报告。
重点判断岗位胜任力、业务能力、团队匹配度、录用风险等。
"""
import json

from app.services.deepseek_client import call_deepseek
from app import constants
from app.services.first_interview_service import clean_json_text


SYSTEM_PROMPT_SECOND_INTERVIEW = """你是一名专业招聘面试评估助手，擅长根据岗位 JD、候选人简历、初试报告和复试记录评估候选人是否适合录用。

业务背景：
- 公司是电商公司。
- 业务是美的净水器经销商。
- 常见岗位包括电商客服、售后客服、销售、运营助理、仓库、文员、财务、人事行政等。
- 当前阶段是复试评估，候选人已经通过初试，需要判断其是否适合录用。

你的任务：
1. 给出复试综合评分（0-100分）。
2. 评估岗位胜任力（0-25分）。
3. 评估业务能力（0-25分）。
4. 评估团队匹配度（0-25分）。
5. 评估录用风险（0-25分）。
6. 列出候选人优势和不足。
7. 给出最终建议。

评估维度详细标准：

【岗位胜任力】（满分25分）
- 20-25分：具备岗位所需的全部核心技能，有成功案例，能快速上手
- 15-19分：具备大部分核心技能，但某些方面需要培训
- 10-14分：具备部分技能，需要较长时间培训
- 0-9分：缺乏核心技能，无法胜任岗位

【业务能力】（满分25分）
- 20-25分：业务经验丰富，解决问题能力强，有创新思维
- 15-19分：业务能力较好，能独立处理常规问题
- 10-14分：业务能力一般，需要指导
- 0-9分：业务能力弱，无法独立工作

【团队匹配度】（满分25分）
- 20-25分：价值观与团队高度契合，沟通协作能力强，能快速融入
- 15-19分：价值观基本契合，沟通协作能力较好
- 10-14分：价值观有些差异，沟通协作能力一般
- 0-9分：价值观不契合，难以融入团队

【录用风险】（满分25分，分数越高风险越低）
- 20-25分：录用风险很低，稳定性高，预期留存时间长
- 15-19分：录用风险较低，稳定性较好
- 10-14分：录用风险中等，存在一定不确定性
- 0-9分：录用风险很高，可能很快离职

重要要求：
- 必须基于输入内容分析，不要凭空编造。
- 如果信息不足，要明确写"信息不足"，并说明具体缺少什么。
- 不要基于性别、年龄、婚育、疾病、地域、民族等敏感因素做判断。
- 不要输出 Markdown、代码块、解释文字，只能输出 JSON。
- 所有字段必须存在，数组字段无内容时返回空数组。
- score 必须是 0 到 100 的整数，要合理分配，不能都给高分或都给低分。
- suggestion 只能是：录用、人才库储备、淘汰。
- risk_level 只能是：低、中、高。
- 本阶段重点评价岗位胜任力和业务能力，不要重复初试已经得出的结论。
- 要结合初试报告中的信息，看候选人在复试中的表现是否有提升或变化。
- 录用风险要看：职业规划、薪资预期、稳定性、岗位匹配度。

岗位特定评估重点：
- 电商客服：看压力承受、客户投诉处理、平台操作熟练度
- 售后客服：看问题解决能力、沟通技巧、服务意识
- 销售：看业绩潜力、客户开发策略、谈判能力
- 仓库：看体力、细心程度、加班接受度
- 文员/财务：看专业能力、细心程度、办公软件操作"""

USER_PROMPT_SECOND_INTERVIEW = """请根据以下岗位 JD、候选人简历、初试报告和复试记录生成复试分析报告。

【岗位 JD / 岗位要求】
{jd_text}

【候选人简历文本】
{resume_text}

【初试分析报告】
{first_interview_report}

【复试记录文本】
{interview_text}

请严格返回以下 JSON 结构，字段必须完整：

{{
  "stage": "SECOND_INTERVIEW",
  "score": 0,
  "suggestion": "",
  "risk_level": "",
  "summary": "一句话总结复试结论（不超过30字）",
  "dimensions": {{
    "job_competency": {{
      "score": 0,
      "max_score": 25,
      "comment": "具体评估依据（引用复试中的例子）"
    }},
    "business_ability": {{
      "score": 0,
      "max_score": 25,
      "comment": "具体评估依据（引用复试中的例子）"
    }},
    "team_fit": {{
      "score": 0,
      "max_score": 25,
      "comment": "具体评估依据（沟通风格、价值观等）"
    }},
    "hire_risk": {{
      "score": 0,
      "max_score": 25,
      "comment": "具体评估依据（稳定性、职业规划等）"
    }}
  }},
  "strengths": [
    "候选人优势1",
    "候选人优势2"
  ],
  "weaknesses": [
    "候选人不足1",
    "候选人不足2"
  ],
  "risk_points": [
    {{
      "risk": "风险点标题（简短）",
      "level": "低/中/高",
      "detail": "详细说明风险原因和可能影响"
    }}
  ],
  "final_recommendation": "最终建议的详细说明（50-100字）"
}}"""


def validate_second_interview_report(result: dict) -> dict:
    """校验和规范化复试分析报告"""
    if "score" not in result or not isinstance(result["score"], int):
        result["score"] = 0
    result["score"] = max(0, min(100, result["score"]))

    if result.get("suggestion") not in constants.SECOND_INTERVIEW_SUGGESTIONS:
        result["suggestion"] = "淘汰"

    if result.get("risk_level") not in constants.VALID_RISK_LEVELS:
        result["risk_level"] = "中"

    dimensions = result.get("dimensions", {})
    required_dimensions = ["job_competency", "business_ability", "team_fit", "hire_risk"]
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

    if "strengths" not in result or not isinstance(result["strengths"], list):
        result["strengths"] = []
    if "weaknesses" not in result or not isinstance(result["weaknesses"], list):
        result["weaknesses"] = []
    if "risk_points" not in result or not isinstance(result["risk_points"], list):
        result["risk_points"] = []
    if "summary" not in result or not result["summary"]:
        result["summary"] = ""
    if "final_recommendation" not in result or not result["final_recommendation"]:
        result["final_recommendation"] = ""

    return result


async def analyze_second_interview(
    jd_text: str,
    resume_text: str,
    first_interview_report: str,
    interview_text: str,
) -> dict:
    """
    分析复试表现，生成复试评估报告

    Args:
        jd_text: 岗位 JD 文本
        resume_text: 候选人简历文本
        first_interview_report: 初试分析报告（JSON 字符串）
        interview_text: 复试记录文本

    Returns:
        复试评估报告
    """
    user_prompt = USER_PROMPT_SECOND_INTERVIEW.format(
        jd_text=jd_text,
        resume_text=resume_text,
        first_interview_report=first_interview_report,
        interview_text=interview_text,
    )

    raw_response = await call_deepseek(user_prompt)
    cleaned_text = clean_json_text(raw_response)

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI 返回格式异常，无法解析 JSON: {str(e)}")

    result = validate_second_interview_report(result)
    return result
