"""
单元测试：岗位库与初筛任务快照
"""
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import constants
from app import models  # noqa: F401
from app.crud_new import create_job_position, get_job_position, list_job_positions, update_job_position
from app.crud_screening import (
    copy_screening_result_from_history,
    create_resume_file_record,
    create_screening_task,
    find_reusable_resume_profile,
    find_reusable_screening_result,
    get_resume_parse_record_detail,
    list_resume_parse_records,
    list_screening_tasks,
    reuse_candidate_profile_from_history,
    upsert_candidate_profile,
    upsert_screening_result,
)
from app.crud_settings import (
    activate_ai_prompt_template,
    archive_job_type_config,
    create_ai_prompt_template,
    create_job_type_config,
    get_active_prompt_pair,
    get_enabled_job_types,
    list_ai_prompt_templates,
    list_job_type_configs,
    reset_ai_prompt_template,
    update_job_type_config,
)
from app.database import Base
from app.models import Candidate, CandidateStatusLog, ScreeningResult, StageReport
from app.services.file_text_extractor import compute_resume_text_hash


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def make_position_payload():
    return {
        "position_name": "销售代表",
        "position_type": "销售",
        "department_name": "销售部",
        "education_requirement": "大专及以上",
        "experience_requirement": "1-3年",
        "jd_original_text": "负责客户跟进、渠道维护和销售转化。",
        "jd_structured_json": {
            "job_title": "销售代表",
            "job_type": "销售",
            "department_name": "销售部",
            "education_requirement": "大专及以上",
            "experience_requirement": "1-3年",
            "key_screening_points": ["客户跟进经验", "渠道维护经验"],
            "must_have": ["销售相关经验"],
            "nice_to_have": ["家电行业经验"],
            "risk_points": ["频繁跳槽"],
        },
        "screening_rules": ["客户跟进经验", "渠道维护经验"],
        "must_have": ["销售相关经验"],
        "nice_to_have": ["家电行业经验"],
        "risk_points": ["频繁跳槽"],
        "interview_questions": ["请介绍一次客户跟进经历"],
    }


def test_create_and_search_job_position(db_session):
    created = create_job_position(db_session, make_position_payload())

    assert created["position_name"] == "销售代表"
    assert created["version"] == 1
    assert created["must_have"] == ["销售相关经验"]

    listed = list_job_positions(db_session, keyword="销售", position_type="销售", status="ACTIVE")
    assert listed["total"] == 1
    assert listed["items"][0]["position_name"] == "销售代表"

    detail = get_job_position(db_session, created["id"])
    assert detail["screening_rules"] == ["客户跟进经验", "渠道维护经验"]
    assert detail["risk_points"] == ["频繁跳槽"]


def test_screening_task_keeps_job_position_snapshot_when_position_changes(db_session):
    created = create_job_position(db_session, make_position_payload())

    task = create_screening_task(
        db_session,
        {
            "job_position_id": created["id"],
            "jd_structured_json": created["jd_structured_json"],
        },
    )

    assert task.job_position_id == created["id"]
    assert task.job_position_version == 1
    task_snapshot = json.loads(task.jd_snapshot_json)
    assert task_snapshot["position_name"] == "销售代表"
    assert task_snapshot["job_position_version"] == 1

    updated = update_job_position(
        db_session,
        created["id"],
        {
            "position_name": "高级销售代表",
            "jd_original_text": "负责重点客户开发和销售团队协同。",
            "jd_structured_json": {
                "job_title": "高级销售代表",
                "job_type": "销售",
                "education_requirement": "本科及以上",
                "experience_requirement": "3-5年",
                "key_screening_points": ["重点客户开发"],
            },
            "save_mode": "NEW_VERSION",
        },
    )

    assert updated["version"] == 2
    db_session.refresh(task)
    unchanged_snapshot = json.loads(task.jd_snapshot_json)
    assert task.job_position_version == 1
    assert unchanged_snapshot["position_name"] == "销售代表"
    assert unchanged_snapshot["experience_requirement"] == "1-3年"


def test_list_screening_tasks_returns_history(db_session):
    created = create_job_position(db_session, make_position_payload())
    task = create_screening_task(
        db_session,
        {
            "job_position_id": created["id"],
            "jd_structured_json": created["jd_structured_json"],
            "task_name": "销售代表 七月初筛",
        },
    )

    listed = list_screening_tasks(db_session, keyword="销售", page=1, page_size=10)

    assert listed["total"] == 1
    assert listed["page"] == 1
    assert listed["page_size"] == 10
    assert listed["items"][0].id == task.id
    assert listed["items"][0].task_name == "销售代表 七月初筛"


def test_screening_result_syncs_to_candidate_library(db_session):
    created = create_job_position(db_session, make_position_payload())
    task = create_screening_task(
        db_session,
        {
            "job_position_id": created["id"],
            "jd_structured_json": created["jd_structured_json"],
        },
    )
    resume_file = create_resume_file_record(
        db_session,
        task_id=task.id,
        file_name="张三.pdf",
        file_type="pdf",
        file_hash="resume-hash-1",
        raw_text="张三，电话 13800138000，有 3 年销售经验。",
        parse_status=constants.RESUME_FILE_SCREENING,
    )
    profile = upsert_candidate_profile(
        db_session,
        resume_file_id=resume_file.id,
        parsed_resume={
            "name": "张三",
            "phone": "13800138000",
            "education": "大专",
            "work_years": 3,
            "latest_position": "销售代表",
        },
    )

    upsert_screening_result(
        db_session,
        task_id=task.id,
        candidate_id=profile.id,
        resume_file_id=resume_file.id,
        result={
            "score": 82,
            "conclusion": constants.SCREENING_CONCLUSION_RECOMMENDED,
            "confidence": "HIGH",
            "dimension_scores": {"overall_risk": 20},
            "match_highlights": ["有销售经验"],
            "risk_points": ["离职原因需确认"],
            "interview_questions": ["请说明最近一段销售经历"],
            "ai_reason": "销售经验匹配，建议 HR 复核后约面。",
        },
    )

    candidate = db_session.query(Candidate).filter(Candidate.phone == "13800138000").first()
    assert candidate is not None
    assert candidate.job_id == created["id"]
    assert candidate.candidate_name == "张三"
    assert candidate.current_status == constants.STATUS_INTERVIEW_WAITING
    assert candidate.resume_match_score == 82
    assert candidate.latest_ai_suggestion == "建议约初试"

    report = db_session.query(StageReport).filter(StageReport.candidate_id == candidate.id).first()
    assert report is not None
    assert report.stage_type == constants.STAGE_RESUME_SCREENING
    assert report.score == 82
    assert report.suggestion == "建议约初试"

    status_log = db_session.query(CandidateStatusLog).filter(CandidateStatusLog.candidate_id == candidate.id).first()
    assert status_log is not None
    assert status_log.to_status == constants.STATUS_INTERVIEW_WAITING


def test_duplicate_resume_reuses_profile_and_same_job_screening_result(db_session):
    created = create_job_position(db_session, make_position_payload())
    task = create_screening_task(
        db_session,
        {
            "job_position_id": created["id"],
            "jd_structured_json": created["jd_structured_json"],
        },
    )
    resume_text = "张三，电话 13800138000，有 3 年销售经验，负责客户跟进。"
    text_hash = compute_resume_text_hash(resume_text)
    source_file = create_resume_file_record(
        db_session,
        task_id=task.id,
        file_name="张三.pdf",
        file_type="pdf",
        file_hash="file-hash-a",
        text_hash=text_hash,
        raw_text=resume_text,
        parse_status=constants.RESUME_FILE_COMPLETED,
    )
    source_profile = upsert_candidate_profile(
        db_session,
        resume_file_id=source_file.id,
        parsed_resume={
            "name": "张三",
            "phone": "13800138000",
            "education": "大专",
            "work_years": 3,
            "latest_position": "销售代表",
        },
    )
    source_result = upsert_screening_result(
        db_session,
        task_id=task.id,
        candidate_id=source_profile.id,
        resume_file_id=source_file.id,
        result={
            "score": 86,
            "conclusion": constants.SCREENING_CONCLUSION_RECOMMENDED,
            "confidence": "HIGH",
            "dimension_scores": {"overall_risk": 15},
            "match_highlights": ["销售经验匹配"],
            "risk_points": ["需确认稳定性"],
            "interview_questions": ["请说明客户跟进案例"],
            "ai_reason": "岗位匹配度较高。",
        },
    )

    duplicate_task = create_screening_task(
        db_session,
        {
            "job_position_id": created["id"],
            "jd_structured_json": created["jd_structured_json"],
        },
    )
    duplicate_file = create_resume_file_record(
        db_session,
        task_id=duplicate_task.id,
        file_name="张三-重新导出.pdf",
        file_type="pdf",
        file_hash="file-hash-b",
        text_hash=text_hash,
        raw_text=resume_text,
        parse_status=constants.RESUME_FILE_PENDING,
    )

    reusable_profile = find_reusable_resume_profile(db_session, duplicate_file)
    assert reusable_profile is not None
    matched_file, matched_profile, reuse_source = reusable_profile
    assert matched_file.id == source_file.id
    assert matched_profile.id == source_profile.id
    assert reuse_source == constants.RESUME_REUSE_SOURCE_TEXT_HASH

    copied_profile, parsed_resume = reuse_candidate_profile_from_history(
        db_session,
        resume_file=duplicate_file,
        source_file=matched_file,
        source_profile=matched_profile,
        reuse_source=reuse_source,
    )
    db_session.refresh(duplicate_file)
    assert copied_profile.id != source_profile.id
    assert copied_profile.name == "张三"
    assert parsed_resume["phone"] == "13800138000"
    assert duplicate_file.reuse_source == constants.RESUME_REUSE_SOURCE_TEXT_HASH

    reusable_result = find_reusable_screening_result(db_session, duplicate_task, duplicate_file)
    assert reusable_result is not None
    assert reusable_result.id == source_result.id

    copied_result = copy_screening_result_from_history(
        db_session,
        task_id=duplicate_task.id,
        candidate_id=copied_profile.id,
        resume_file_id=duplicate_file.id,
        source_result=reusable_result,
    )
    assert copied_result.result_source == constants.SCREENING_RESULT_SOURCE_REUSED
    assert copied_result.reused_from_result_id == source_result.id
    assert copied_result.score == 86

    results = db_session.query(ScreeningResult).filter(ScreeningResult.deleted == 0).all()
    assert len(results) == 2
    candidate = db_session.query(Candidate).filter(Candidate.phone == "13800138000").first()
    assert candidate is not None
    assert candidate.resume_match_score == 86


def test_screening_result_not_reused_after_job_version_changes(db_session):
    created = create_job_position(db_session, make_position_payload())
    task = create_screening_task(
        db_session,
        {
            "job_position_id": created["id"],
            "jd_structured_json": created["jd_structured_json"],
        },
    )
    resume_text = "李四，电话 13900139000，有 2 年销售经验。"
    text_hash = compute_resume_text_hash(resume_text)
    source_file = create_resume_file_record(
        db_session,
        task_id=task.id,
        file_name="李四.pdf",
        file_type="pdf",
        file_hash="lisi-file-a",
        text_hash=text_hash,
        raw_text=resume_text,
        parse_status=constants.RESUME_FILE_COMPLETED,
    )
    source_profile = upsert_candidate_profile(
        db_session,
        resume_file_id=source_file.id,
        parsed_resume={"name": "李四", "phone": "13900139000"},
    )
    upsert_screening_result(
        db_session,
        task_id=task.id,
        candidate_id=source_profile.id,
        resume_file_id=source_file.id,
        result={"score": 70, "conclusion": constants.SCREENING_CONCLUSION_PENDING},
    )

    updated = update_job_position(
        db_session,
        created["id"],
        {
            "position_name": "高级销售代表",
            "jd_original_text": "负责重点客户开发。",
            "jd_structured_json": {
                "job_title": "高级销售代表",
                "job_type": "销售",
                "key_screening_points": ["重点客户开发"],
            },
            "save_mode": "NEW_VERSION",
        },
    )
    new_version_task = create_screening_task(
        db_session,
        {
            "job_position_id": updated["id"],
            "jd_structured_json": updated["jd_structured_json"],
        },
    )
    duplicate_file = create_resume_file_record(
        db_session,
        task_id=new_version_task.id,
        file_name="李四-重复.pdf",
        file_type="pdf",
        file_hash="lisi-file-b",
        text_hash=text_hash,
        raw_text=resume_text,
        parse_status=constants.RESUME_FILE_PENDING,
    )

    assert find_reusable_resume_profile(db_session, duplicate_file) is not None
    assert find_reusable_screening_result(db_session, new_version_task, duplicate_file) is None


def test_resume_parse_records_list_and_detail(db_session):
    created = create_job_position(db_session, make_position_payload())
    task = create_screening_task(
        db_session,
        {
            "job_position_id": created["id"],
            "jd_structured_json": created["jd_structured_json"],
            "task_name": "销售代表 初筛任务",
        },
    )
    resume_file = create_resume_file_record(
        db_session,
        task_id=task.id,
        file_name="王五.pdf",
        file_type="pdf",
        file_hash="wangwu-file-hash",
        text_hash=compute_resume_text_hash("王五，电话 13700137000，有销售经验。"),
        raw_text="王五，电话 13700137000，有销售经验。",
        parse_status=constants.RESUME_FILE_COMPLETED,
        reuse_source=constants.RESUME_REUSE_SOURCE_TEXT_HASH,
        reused_resume_file_id=1,
        reused_profile_id=1,
    )
    profile = upsert_candidate_profile(
        db_session,
        resume_file_id=resume_file.id,
        parsed_resume={
            "name": "王五",
            "phone": "13700137000",
            "education": "本科",
            "work_years": 4,
            "latest_position": "渠道销售",
        },
        data_source=f"resume_reuse:{constants.RESUME_REUSE_SOURCE_TEXT_HASH}",
    )
    result = upsert_screening_result(
        db_session,
        task_id=task.id,
        candidate_id=profile.id,
        resume_file_id=resume_file.id,
        result={
            "score": 78,
            "conclusion": constants.SCREENING_CONCLUSION_PENDING,
            "confidence": "MEDIUM",
            "match_highlights": ["销售经验可复用"],
            "risk_points": ["稳定性待确认"],
        },
    )

    records = list_resume_parse_records(db_session, keyword="王五", page=1, page_size=10)
    assert records["total"] == 1
    row = records["items"][0]
    assert row["id"] == resume_file.id
    assert row["task_name"] == "销售代表 初筛任务"
    assert row["candidate_name"] == "王五"
    assert row["reuse_source"] == constants.RESUME_REUSE_SOURCE_TEXT_HASH
    assert row["screening_result_id"] == result.id
    assert row["screening_score"] == 78

    detail = get_resume_parse_record_detail(db_session, resume_file.id)
    assert detail is not None
    assert detail["resume_file"].id == resume_file.id
    assert detail["task"].id == task.id
    assert detail["candidate_profile"].id == profile.id
    assert detail["job_position"]["position_name"] == "销售代表"
    assert detail["screening_result"]["id"] == result.id


def test_job_type_config_crud_and_public_job_types(db_session):
    defaults = list_job_type_configs(db_session)
    assert defaults["total"] >= 1
    assert constants.JOB_TYPE_SALES in [item["type_name"] for item in defaults["items"]]

    created = create_job_type_config(
        db_session,
        {
            "type_name": "直播运营类",
            "description": "直播间运营与投放相关岗位",
            "evaluation_focus": ["直播经验", "数据复盘"],
            "enabled": True,
            "sort_order": 99,
        },
    )
    assert created["type_name"] == "直播运营类"
    assert created["evaluation_focus"] == ["直播经验", "数据复盘"]

    updated = update_job_type_config(
        db_session,
        created["id"],
        {"enabled": False, "evaluation_focus": ["直播经验"]},
    )
    assert updated["enabled"] is False
    assert updated["evaluation_focus"] == ["直播经验"]

    public_payload = get_enabled_job_types(db_session)
    assert "job_types" in public_payload
    assert "evaluation_focus" in public_payload
    assert "直播运营类" not in public_payload["job_types"]

    archived = archive_job_type_config(db_session, created["id"])
    assert archived["id"] == created["id"]
    assert list_job_type_configs(db_session, keyword="直播运营类")["total"] == 0


def test_ai_prompt_template_versions_and_active_pair(db_session):
    seeded = list_ai_prompt_templates(db_session)
    assert seeded["total"] >= 3

    custom = create_ai_prompt_template(
        db_session,
        {
            "prompt_key": constants.PROMPT_KEY_JD_PARSE,
            "prompt_name": "JD 解析自定义模板",
            "scene": "JD 解析",
            "system_prompt": "system {job_type_options}",
            "user_prompt": "user {jd_text}",
            "remark": "单元测试模板",
        },
    )
    assert custom["status"] == constants.PROMPT_STATUS_DRAFT

    active = activate_ai_prompt_template(db_session, custom["id"])
    assert active["status"] == constants.PROMPT_STATUS_ACTIVE

    pair = get_active_prompt_pair(db_session, constants.PROMPT_KEY_JD_PARSE)
    assert pair["system_prompt"] == "system {job_type_options}"
    assert pair["user_prompt"] == "user {jd_text}"

    reset = reset_ai_prompt_template(db_session, constants.PROMPT_KEY_JD_PARSE)
    assert reset["status"] == constants.PROMPT_STATUS_ACTIVE
    assert reset["version"] > active["version"]
