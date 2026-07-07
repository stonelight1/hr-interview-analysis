"""
单元测试：候选人面试问题历史和高频统计
"""
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import constants
from app import models  # noqa: F401
from app.crud_new import (
    create_candidate,
    create_interview_question_items,
    create_job,
    create_stage_report,
    list_interview_question_reports,
    list_interview_question_stats,
)
from app.database import Base


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


def create_candidate_context(db):
    job = create_job(
        db,
        {
            "job_name": "销售代表",
            "department": "销售部",
            "headcount": 1,
            "jd_text": "负责客户开发、商机跟进和销售转化。",
        },
    )
    candidate = create_candidate(
        db,
        {
            "job_id": job.id,
            "candidate_name": "李四",
            "resume_text": "2 年销售经验，负责客户开发和续约。",
        },
    )
    return job, candidate


def create_question_report(db, job, candidate, version, round_type, questions):
    return create_stage_report(
        db=db,
        candidate_id=candidate.id,
        job_id=job.id,
        stage_type=constants.STAGE_INTERVIEW_QUESTIONS,
        report_version=version,
        report_json=json.dumps({"questions": questions, "round_type": round_type}, ensure_ascii=False),
        input_snapshot_json="{}",
        suggestion=f"已生成 {len(questions)} 道面试问题",
        status=constants.REPORT_STATUS_SUCCESS,
        report_key=f"{candidate.id}:{job.id}:{round_type}",
        round_type=round_type,
        round_no=1 if round_type == constants.QUESTION_ROUND_TYPE_FIRST else 2,
        generate_type=constants.REPORT_GENERATE_MANUAL_RERUN,
    )


def test_interview_question_reports_keep_history_by_round_type(db_session):
    job, candidate = create_candidate_context(db_session)
    first_questions = [{"question": "请介绍一个客户开发案例。", "dimension": "销售经验", "required": True}]
    second_questions = [{"question": "请复盘一个复杂客户推进过程。", "dimension": "项目复盘", "required": True}]

    first_report = create_question_report(
        db_session,
        job,
        candidate,
        1,
        constants.QUESTION_ROUND_TYPE_FIRST,
        first_questions,
    )
    second_report = create_question_report(
        db_session,
        job,
        candidate,
        2,
        constants.QUESTION_ROUND_TYPE_SECOND,
        second_questions,
    )
    create_interview_question_items(db_session, first_report, first_questions, resume_id=candidate.id)
    create_interview_question_items(db_session, second_report, second_questions, resume_id=candidate.id)

    all_history = list_interview_question_reports(db_session, candidate.id, page=1, page_size=10)
    first_history = list_interview_question_reports(
        db_session,
        candidate.id,
        round_type=constants.QUESTION_ROUND_TYPE_FIRST,
        page=1,
        page_size=10,
    )

    assert all_history["total"] == 2
    assert first_history["total"] == 1
    assert first_history["items"][0].round_type == constants.QUESTION_ROUND_TYPE_FIRST


def test_interview_question_stats_group_same_question(db_session):
    job, candidate = create_candidate_context(db_session)
    questions = [
        {"question": "请介绍一个客户开发案例。", "dimension": "销售经验", "source": "简历", "required": True},
        {"question": "请说明你的销售转化方法。", "dimension": "销售能力", "source": "JD", "required": True},
    ]
    rerun_questions = [
        {"question": "1. 请介绍一个客户开发案例？", "dimension": "销售经验", "source": "简历", "required": True},
    ]
    report_v1 = create_question_report(
        db_session,
        job,
        candidate,
        1,
        constants.QUESTION_ROUND_TYPE_FIRST,
        questions,
    )
    report_v2 = create_question_report(
        db_session,
        job,
        candidate,
        2,
        constants.QUESTION_ROUND_TYPE_FIRST,
        rerun_questions,
    )
    create_interview_question_items(db_session, report_v1, questions, resume_id=candidate.id)
    create_interview_question_items(db_session, report_v2, rerun_questions, resume_id=candidate.id)

    stats = list_interview_question_stats(
        db_session,
        job_id=job.id,
        round_type=constants.QUESTION_ROUND_TYPE_FIRST,
        limit=10,
    )

    assert stats[0]["question"] in {"请介绍一个客户开发案例。", "1. 请介绍一个客户开发案例？"}
    assert stats[0]["count"] == 2
    assert stats[0]["round_type"] == constants.QUESTION_ROUND_TYPE_FIRST
