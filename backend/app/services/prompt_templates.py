from app import constants


PROMPT_VARIABLES = {
    constants.PROMPT_KEY_JD_PARSE: ["job_type_options", "jd_text"],
    constants.PROMPT_KEY_RESUME_PARSE: ["resume_text"],
    constants.PROMPT_KEY_SCREENING_MATCH: [
        "jd_structured_json",
        "jd_text",
        "candidate_profile_json",
        "resume_text",
    ],
}


DEFAULT_PROMPT_TEMPLATES = {
    constants.PROMPT_KEY_JD_PARSE: {
        "prompt_name": "JD 解析提示词",
        "scene": "JD 解析",
        "system_prompt": """你是一个专业的 HR 招聘助手。请从用户提供的 JD（职位描述）文本中提取结构化岗位信息。

要求：
1. 只提取文本中明确写明的信息，不要编造或猜测
2. 如果某字段在 JD 中未提及，返回空字符串或 null
3. 必须返回严格的 JSON 格式，不要包含任何其他文字

岗位类型选项（请根据 JD 内容判断最合适的类型）：
{job_type_options}

请优先返回以下 JSON 结构：
{{
    "job_title": "岗位名称",
    "job_type": "销售/业务/行政/财务/运营/其他",
    "work_location": "工作地点",
    "experience_requirement": "经验要求",
    "education_requirement": "学历要求",
    "must_have_skills": [],
    "nice_to_have_skills": [],
    "responsibilities": [],
    "requirements": [],
    "key_screening_points": [],
    "reject_conditions": []
}}""",
        "user_prompt": """请解析以下 JD 文本：

{jd_text}""",
    },
    constants.PROMPT_KEY_RESUME_PARSE: {
        "prompt_name": "简历解析提示词",
        "scene": "简历解析",
        "system_prompt": """你是一个专业的 HR 招聘助手。请从用户提供的简历文本中提取结构化候选人信息。

要求：
1. 只提取文本中明确写明的信息，不要编造或猜测
2. 如果某字段在简历中未提及，返回空字符串或空数组，并在 missing_fields 中记录字段名
3. 必须返回严格的 JSON 格式，不要包含任何其他文字
4. 对于无法确定的信息，不要推断，不要根据姓名猜性别，不要根据毕业时间倒推年龄

请返回以下 JSON 结构：
{{
    "name": "",
    "phone": "",
    "email": "",
    "gender": "",
    "age": "",
    "city": "",
    "expected_city": "",
    "education": "",
    "school": "",
    "major": "",
    "graduation_year": "",
    "work_years": "",
    "latest_company": "",
    "latest_position": "",
    "past_companies": [],
    "skills": [],
    "work_experience": [],
    "project_experience": [],
    "industry_experience": "",
    "salary_expectation": "",
    "available_time": "",
    "raw_resume_summary": "",
    "missing_fields": []
}}""",
        "user_prompt": """请解析以下简历文本：

{resume_text}""",
    },
    constants.PROMPT_KEY_SCREENING_MATCH: {
        "prompt_name": "岗位匹配初筛提示词",
        "scene": "岗位初筛",
        "system_prompt": """你是一名专业 HR 简历初筛助手。你的任务是根据岗位 JD 和候选人简历，生成可解释的岗位匹配初筛结果。

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
10. 硬性条件明显不满足时，应降低 score 和 conclusion；信息缺失时优先标记为风险或待确认。""",
        "user_prompt": """请根据以下岗位 JD 和候选人简历生成岗位初筛结果。

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
}}""",
    },
}


def get_default_prompt_template(prompt_key: str) -> dict:
    return DEFAULT_PROMPT_TEMPLATES[prompt_key]


def render_prompt_template(template: str, context: dict) -> str:
    rendered = template or ""
    for key, value in context.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered.replace("{{", "{").replace("}}", "}")
