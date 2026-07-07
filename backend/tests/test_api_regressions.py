import asyncio
import importlib
import os

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import constants
from app.config import get_settings
from app.database import Base
from app.models import Candidate, CandidateInterviewRound, StageReport


@pytest.fixture
def main_module(monkeypatch):
    monkeypatch.setenv("HR_API_KEY", "test-secret")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
    get_settings.cache_clear()

    import app.main as main

    main = importlib.reload(main)
    try:
        yield main
    finally:
        main.app.dependency_overrides.clear()
        get_settings.cache_clear()


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(main_module, db_session):
    def override_get_db():
        yield db_session

    main_module.app.dependency_overrides[main_module.get_db] = override_get_db
    return TestClient(main_module.app)


def test_api_requires_configured_api_key(client):
    assert client.get("/api/dashboard/stats").status_code == 401
    assert client.get("/api/dashboard/stats", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/api/dashboard/stats", headers={"X-API-Key": "test-secret"}).status_code == 200


def test_create_candidate_rejects_missing_job(client):
    response = client.post(
        "/api/candidates",
        headers={"X-API-Key": "test-secret"},
        json={
            "job_id": 999,
            "candidate_name": "张三",
            "resume_text": "3 年客服经验。",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "岗位不存在"


def test_report_candidate_list_filters_with_database_pagination(client, main_module, db_session):
    job = main_module.create_job(
        db_session,
        {
            "job_name": "客服专员",
            "department": "客服部",
            "headcount": 1,
            "jd_text": "负责客户沟通。",
        },
    )
    matched_candidate = main_module.create_candidate(
        db_session,
        {
            "job_id": job.id,
            "candidate_name": "李四",
            "resume_text": "有客服经验。",
        },
    )
    main_module.create_candidate(
        db_session,
        {
            "job_id": job.id,
            "candidate_name": "王五",
            "resume_text": "应届生。",
        },
    )
    db_session.add(
        CandidateInterviewRound(
            candidate_id=matched_candidate.id,
            round_no=1,
            round_name="第 1 轮面试",
            status=constants.INTERVIEW_ROUND_STATUS_COMPLETED,
            record_text="表达清楚。",
        )
    )
    main_module.create_stage_report(
        db_session,
        candidate_id=matched_candidate.id,
        job_id=job.id,
        stage_type=constants.STAGE_CANDIDATE_EVALUATION,
        report_version=1,
        report_json="{}",
        input_snapshot_json="{}",
        status=constants.REPORT_STATUS_SUCCESS,
        is_current=1,
    )

    response = client.get(
        "/api/report/candidates",
        headers={"X-API-Key": "test-secret"},
        params={"hasReport": True, "hasInterviewRecord": True, "page": 1, "pageSize": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == matched_candidate.id
    assert payload["items"][0]["has_report"] is True
    assert payload["items"][0]["latest_interview_time"] is not None


def test_sqlite_foreign_keys_reject_orphan_candidate(db_session):
    db_session.add(
        Candidate(
            job_id=999,
            candidate_name="张三",
            resume_text="3 年客服经验。",
            current_status=constants.STATUS_RESUME_PENDING,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_force_regenerate_failure_keeps_existing_current_report(main_module, db_session, monkeypatch):
    job = main_module.create_job(
        db_session,
        {
            "job_name": "客服专员",
            "department": "客服部",
            "headcount": 1,
            "jd_text": "负责客户沟通。",
        },
    )
    candidate = main_module.create_candidate(
        db_session,
        {
            "job_id": job.id,
            "candidate_name": "李四",
            "resume_text": "有客服经验。",
        },
    )
    interview_round = CandidateInterviewRound(
        candidate_id=candidate.id,
        round_no=1,
        round_name="第 1 轮面试",
        status=constants.INTERVIEW_ROUND_STATUS_COMPLETED,
        record_text="表达清楚，服务意识较好。",
    )
    db_session.add(interview_round)
    db_session.commit()
    db_session.refresh(interview_round)

    async def successful_analyze_candidate(**kwargs):
        return {
            "candidate_overview": {
                "match_score": 80,
                "recommendation": "建议进入下一轮",
                "risk_level": "低",
            }
        }

    request = main_module.ReportGenerateRequest(
        candidateId=candidate.id,
        jobPositionId=job.id,
        resumeId=candidate.id,
        interviewRecordIds=[f"round:{interview_round.id}"],
    )
    monkeypatch.setattr(main_module, "analyze_candidate", successful_analyze_candidate)
    first_response = asyncio.run(main_module._generate_candidate_evaluation_report(db_session, request))
    first_report = db_session.get(StageReport, first_response["id"])
    assert first_report.is_current == 1

    async def failed_analyze_candidate(**kwargs):
        raise RuntimeError("AI unavailable")

    monkeypatch.setattr(main_module, "analyze_candidate", failed_analyze_candidate)
    with pytest.raises(HTTPException):
        asyncio.run(main_module._generate_candidate_evaluation_report(db_session, request, force_regenerate=True))

    db_session.refresh(first_report)
    failed_report = (
        db_session.query(StageReport)
        .filter(StageReport.status == constants.REPORT_STATUS_FAILED)
        .one()
    )
    assert first_report.is_current == 1
    assert failed_report.is_current == 0


def test_next_round_decision_rolls_back_when_round_creation_fails(main_module, db_session, monkeypatch):
    job = main_module.create_job(
        db_session,
        {
            "job_name": "客服专员",
            "department": "客服部",
            "headcount": 1,
            "jd_text": "负责客户沟通。",
        },
    )
    candidate = main_module.create_candidate(
        db_session,
        {
            "job_id": job.id,
            "candidate_name": "王五",
            "resume_text": "有客服经验。",
        },
    )
    interview_round = CandidateInterviewRound(
        candidate_id=candidate.id,
        round_no=1,
        round_name="第 1 轮面试",
        status=constants.INTERVIEW_ROUND_STATUS_COMPLETED,
        record_text="需要业务复核。",
    )
    db_session.add(interview_round)
    db_session.commit()
    db_session.refresh(interview_round)

    def fail_create_candidate_interview_round(**kwargs):
        raise RuntimeError("create next round failed")

    monkeypatch.setattr(main_module, "create_candidate_interview_round", fail_create_candidate_interview_round)

    with pytest.raises(RuntimeError):
        main_module.decide_candidate_interview_round_endpoint(
            candidate.id,
            interview_round.id,
            main_module.CandidateInterviewDecisionSubmit(decision=constants.INTERVIEW_DECISION_NEXT),
            db_session,
        )

    db_session.refresh(interview_round)
    assert interview_round.decision is None
    assert db_session.query(CandidateInterviewRound).filter(CandidateInterviewRound.candidate_id == candidate.id).count() == 1
