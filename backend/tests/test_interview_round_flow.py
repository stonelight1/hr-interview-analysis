"""
单元测试：开放式面试轮次流程
"""
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import constants
from app import models  # noqa: F401
from app.crud_new import (
    apply_candidate_interview_decision,
    create_candidate,
    create_candidate_interview_round,
    get_candidate_interview_rounds_by_candidate_ids,
    create_job,
    get_next_interview_round_no,
    mark_candidate_waiting_interview_after_screening,
    submit_candidate_interview_record,
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


def create_candidate_for_flow(db):
    job = create_job(
        db,
        {
            "job_name": "客服专员",
            "department": "客服部",
            "headcount": 2,
            "jd_text": "负责客户沟通、问题处理和服务质量跟进。",
        },
    )
    candidate = create_candidate(
        db,
        {
            "job_id": job.id,
            "candidate_name": "张三",
            "resume_text": "3 年客服经验，熟悉售后沟通和投诉处理。",
        },
    )
    return job, candidate


def test_resume_screening_moves_candidate_to_waiting_interview(db_session):
    _, candidate = create_candidate_for_flow(db_session)

    candidate = mark_candidate_waiting_interview_after_screening(db_session, candidate.id)

    assert candidate.current_status == constants.STATUS_INTERVIEW_WAITING
    assert candidate.current_round_no is None
    assert candidate.final_conclusion is None


def test_create_round_and_pass_end_flow(db_session):
    _, candidate = create_candidate_for_flow(db_session)
    candidate = mark_candidate_waiting_interview_after_screening(db_session, candidate.id)

    interview_round = create_candidate_interview_round(
        db_session,
        candidate,
        {
            "round_no": 1,
            "round_name": "第 1 轮面试",
            "round_type": "HR 面",
            "round_focus": "基础确认",
            "interview_method": "线上",
        },
        question_json=json.dumps([{"question": "请介绍你的客服经验", "required": True}], ensure_ascii=False),
    )

    assert interview_round.status == constants.INTERVIEW_ROUND_STATUS_SCHEDULED
    assert candidate.current_status == constants.STATUS_INTERVIEW_SCHEDULED
    assert candidate.current_round_no == 1

    interview_round = submit_candidate_interview_record(
        db_session,
        candidate,
        interview_round,
        {
            "record_text": "沟通表达清晰，服务意识较好。",
            "score": 82,
            "conclusion": "建议通过并结束",
        },
    )

    assert interview_round.status == constants.INTERVIEW_ROUND_STATUS_COMPLETED
    assert candidate.current_status == constants.STATUS_INTERVIEW_DECISION_PENDING

    candidate = apply_candidate_interview_decision(
        db_session,
        candidate,
        interview_round,
        constants.INTERVIEW_DECISION_PASS_END,
    )

    assert interview_round.decision == constants.INTERVIEW_DECISION_PASS_END
    assert candidate.current_status == constants.STATUS_FINAL_PASSED
    assert candidate.final_conclusion == constants.INTERVIEW_DECISION_PASS_END


def test_next_round_is_created_on_hr_decision(db_session):
    _, candidate = create_candidate_for_flow(db_session)
    candidate = mark_candidate_waiting_interview_after_screening(db_session, candidate.id)
    first_round = create_candidate_interview_round(
        db_session,
        candidate,
        {"round_no": 1, "round_name": "第 1 轮面试"},
        question_json="[]",
    )
    first_round = submit_candidate_interview_record(
        db_session,
        candidate,
        first_round,
        {
            "record_text": "基础条件符合，但需要业务进一步复核。",
            "score": 76,
            "conclusion": "建议进入下一轮",
        },
    )

    apply_candidate_interview_decision(
        db_session,
        candidate,
        first_round,
        constants.INTERVIEW_DECISION_NEXT,
    )
    assert first_round.decision == constants.INTERVIEW_DECISION_NEXT
    assert get_next_interview_round_no(db_session, candidate.id) == 2

    second_round = create_candidate_interview_round(
        db_session,
        candidate,
        {
            "round_no": 2,
            "round_name": "第 2 轮面试",
            "round_type": "业务面",
            "round_focus": "能力复核",
        },
        question_json="[]",
    )

    assert second_round.round_no == 2
    assert second_round.status == constants.INTERVIEW_ROUND_STATUS_SCHEDULED
    assert candidate.current_status == constants.STATUS_INTERVIEW_SCHEDULED
    assert candidate.current_round_no == 2


def test_batch_get_interview_rounds_by_candidate_ids(db_session):
    _, first_candidate = create_candidate_for_flow(db_session)
    _, second_candidate = create_candidate_for_flow(db_session)
    first_candidate = mark_candidate_waiting_interview_after_screening(db_session, first_candidate.id)
    second_candidate = mark_candidate_waiting_interview_after_screening(db_session, second_candidate.id)

    create_candidate_interview_round(
        db_session,
        first_candidate,
        {"round_no": 1, "round_name": "第 1 轮面试"},
        question_json="[]",
    )
    create_candidate_interview_round(
        db_session,
        second_candidate,
        {"round_no": 1, "round_name": "第 1 轮面试"},
        question_json="[]",
    )

    rounds_by_candidate = get_candidate_interview_rounds_by_candidate_ids(
        db_session,
        [first_candidate.id, second_candidate.id],
    )

    assert set(rounds_by_candidate.keys()) == {first_candidate.id, second_candidate.id}
    assert [item.round_no for item in rounds_by_candidate[first_candidate.id]] == [1]
    assert [item.round_no for item in rounds_by_candidate[second_candidate.id]] == [1]
