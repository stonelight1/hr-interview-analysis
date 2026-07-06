#!/usr/bin/env python3
"""
旧数据迁移脚本
将 hr_interview_analysis 表中的数据转换为新的候选人 + 阶段报告格式。

使用方法：
1. 确保数据库文件路径正确
2. 运行脚本：python migrate_old_data.py
3. 检查迁移结果
"""

import json
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 数据库配置 - 根据实际情况调整
DATABASE_URL = "sqlite:///./hr_interview.db"  # 默认当前目录
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def migrate_old_data():
    """执行数据迁移"""
    db = SessionLocal()
    try:
        # 1. 查询旧表的所有记录
        result = db.execute(text("SELECT * FROM hr_interview_analysis WHERE deleted = 0"))
        old_records = result.fetchall()

        print(f"找到 {len(old_records)} 条旧数据需要迁移")

        # 2. 统计信息
        success_count = 0
        failed_count = 0
        failed_ids = []

        for old_record in old_records:
            try:
                migrate_single_record(db, old_record)
                success_count += 1
                print(f"✓ 迁移成功：ID={old_record.id} - {old_record.candidate_name}")
            except Exception as e:
                failed_count += 1
                failed_ids.append(old_record.id)
                print(f"✗ 迁移失败：ID={old_record.id} - {str(e)}")
                db.rollback()

        # 3. 打印迁移结果
        print("\n" + "=" * 60)
        print("迁移完成")
        print(f"成功：{success_count} 条")
        print(f"失败：{failed_count} 条")
        if failed_ids:
            print(f"失败 ID：{failed_ids}")
        print("=" * 60)

        return success_count, failed_count, failed_ids

    finally:
        db.close()


def migrate_single_record(db, old_record):
    """迁移单条旧记录"""
    # 1. 创建岗位记录（使用统一默认岗位）
    job_id = get_or_create_default_job(db)

    # 2. 创建候选人记录
    candidate_id = create_candidate_from_old_record(db, old_record, job_id)

    # 3. 创建阶段报告记录
    create_stage_report_from_old_record(db, old_record, candidate_id, job_id)

    # 4. 创建状态流转日志
    create_status_log(db, candidate_id, old_record)

    # 5. 更新候选人的状态
    update_candidate_status_from_analysis(db, candidate_id, old_record)


def get_or_create_default_job(db):
    """获取或创建默认岗位"""
    # 检查是否已存在默认岗位
    result = db.execute(text(
        "SELECT id FROM jobs WHERE job_name = '默认岗位' AND deleted = 0"
    ))
    existing_job = result.fetchone()

    if existing_job:
        return existing_job[0]

    # 创建新岗位
    now = datetime.now()
    result = db.execute(text(
        """INSERT INTO jobs (job_name, department, headcount, jd_text, status, remark, deleted, created_at, updated_at)
           VALUES (:job_name, :department, :headcount, :jd_text, :status, :remark, :deleted, :created_at, :updated_at)""",
        {
            "job_name": "默认岗位",
            "department": "待分配",
            "headcount": 1,
            "jd_text": "岗位 JD 由旧数据迁移生成，请手动更新。",
            "status": "OPEN",
            "remark": "由旧数据迁移脚本自动创建",
            "deleted": 0,
            "created_at": now,
            "updated_at": now,
        }
    ))
    db.flush()  # 获取新插入的 ID
    return result.lastrowid


def create_candidate_from_old_record(db, old_record, job_id):
    """从旧记录创建候选人"""
    now = datetime.now()

    # 根据旧记录的 recommendation 推断初始状态
    if old_record.recommendation in ("强烈建议进入下一轮", "建议进入下一轮"):
        initial_status = "RESUME_PASSED"
    elif old_record.recommendation == "暂缓":
        initial_status = "RESUME_PASSED"  # 暂缓的先设为简历通过
    else:
        initial_status = "RESUME_REJECTED"

    result = db.execute(text(
        """INSERT INTO candidates
           (job_id, candidate_name, phone, email, source, resume_text, current_status,
            resume_match_score, first_interview_score, second_interview_score, latest_ai_suggestion,
            remark, deleted, created_at, updated_at)
           VALUES
           (:job_id, :candidate_name, :phone, :email, :source, :resume_text, :current_status,
            :resume_match_score, :first_interview_score, :second_interview_score, :latest_ai_suggestion,
            :remark, :deleted, :created_at, :updated_at)""",
        {
            "job_id": job_id,
            "candidate_name": old_record.candidate_name,
            "phone": None,
            "email": None,
            "source": "旧数据迁移",
            "resume_text": old_record.resume_text,
            "current_status": initial_status,
            "resume_match_score": old_record.match_score,
            "first_interview_score": None,
            "second_interview_score": None,
            "latest_ai_suggestion": old_record.recommendation,
            "remark": f"由旧数据迁移生成，原始 ID: {old_record.id}",
            "deleted": 0,
            "created_at": now,
            "updated_at": now,
        }
    ))
    db.flush()
    return result.lastrowid


def create_stage_report_from_old_record(db, old_record, candidate_id, job_id):
    """从旧记录创建阶段报告"""
    now = datetime.now()

    # 构建 report_json
    report_data = {
        "stage": "FIRST_INTERVIEW",
        "source": "旧数据迁移",
        "original_analysis_result": old_record.analysis_result,
    }

    # 尝试解析原有的 analysis_result
    try:
        analysis_result = json.loads(old_record.analysis_result) if old_record.analysis_result else {}
        report_data["analysis_result"] = analysis_result
    except json.JSONDecodeError:
        report_data["analysis_result"] = {}

    report_json = json.dumps(report_data, ensure_ascii=False)

    # 构建 input_snapshot
    input_snapshot = {
        "job_title": old_record.job_title,
        "jd_text": old_record.jd_text,
        "resume_text": old_record.resume_text,
        "interview_text": old_record.interview_text,
        "migrated_from": f"旧数据 ID: {old_record.id}",
    }
    input_snapshot_json = json.dumps(input_snapshot, ensure_ascii=False)

    db.execute(text(
        """INSERT INTO stage_reports
           (candidate_id, job_id, stage_type, report_version, score, suggestion, risk_level,
            report_json, input_snapshot_json, content_hash, request_id, status, error_message,
            deleted, created_at, updated_at)
           VALUES
           (:candidate_id, :job_id, :stage_type, :report_version, :score, :suggestion, :risk_level,
            :report_json, :input_snapshot_json, :content_hash, :request_id, :status, :error_message,
            :deleted, :created_at, :updated_at)""",
        {
            "candidate_id": candidate_id,
            "job_id": job_id,
            "stage_type": "FIRST_INTERVIEW",
            "report_version": 1,
            "score": old_record.match_score,
            "suggestion": old_record.recommendation,
            "risk_level": old_record.risk_level,
            "report_json": report_json,
            "input_snapshot_json": input_snapshot_json,
            "content_hash": None,
            "request_id": f"migrated_{old_record.id}_{now.timestamp()}",
            "status": "SUCCESS",
            "error_message": None,
            "deleted": 0,
            "created_at": now,
            "updated_at": now,
        }
    ))


def create_status_log(db, candidate_id, old_record):
    """创建状态流转日志"""
    now = datetime.now()

    # 创建初始状态日志
    db.execute(text(
        """INSERT INTO candidate_status_logs (candidate_id, from_status, to_status, reason, operator_name, created_at)
           VALUES (:candidate_id, :from_status, :to_status, :reason, :operator_name, :created_at)""",
        {
            "candidate_id": candidate_id,
            "from_status": None,
            "to_status": "RESUME_PENDING",
            "reason": "候选人导入（旧数据迁移）",
            "operator_name": "系统迁移",
            "created_at": now,
        }
    ))


def update_candidate_status_from_analysis(db, candidate_id, old_record):
    """根据旧数据分析结果更新候选人状态"""
    now = datetime.now()

    # 根据 recommendation 推断最终状态
    if old_record.recommendation in ("强烈建议进入下一轮", "建议进入下一轮"):
        to_status = "RESUME_PASSED"
        reason = "简历筛选通过（旧数据分析结果）"
    elif old_record.recommendation == "暂缓":
        to_status = "FIRST_INTERVIEW_PENDING"
        reason = "简历待筛选（旧数据分析结果）"
    else:
        to_status = "RESUME_REJECTED"
        reason = "简历淘汰（旧数据分析结果）"

    # 创建状态日志
    db.execute(text(
        """INSERT INTO candidate_status_logs (candidate_id, from_status, to_status, reason, operator_name, created_at)
           VALUES (:candidate_id, :from_status, :to_status, :reason, :operator_name, :created_at)""",
        {
            "candidate_id": candidate_id,
            "from_status": "RESUME_PENDING",
            "to_status": to_status,
            "reason": reason,
            "operator_name": "系统迁移",
            "created_at": now,
        }
    ))

    # 更新候选人当前状态
    db.execute(text(
        """UPDATE candidates SET current_status = :current_status, updated_at = :updated_at WHERE id = :id""",
        {
            "id": candidate_id,
            "current_status": to_status,
            "updated_at": now,
        }
    ))


def verify_migration():
    """验证迁移结果"""
    db = SessionLocal()
    try:
        # 统计新表数据
        result = db.execute(text("SELECT COUNT(*) FROM candidates WHERE deleted = 0"))
        candidate_count = result.fetchone()[0]

        result = db.execute(text("SELECT COUNT(*) FROM stage_reports WHERE deleted = 0"))
        report_count = result.fetchone()[0]

        result = db.execute(text("SELECT COUNT(*) FROM candidate_status_logs"))
        log_count = result.fetchone()[0]

        print("\n迁移验证：")
        print(f"候选人数量：{candidate_count}")
        print(f"阶段报告数量：{report_count}")
        print(f"状态日志数量：{log_count}")

        return candidate_count, report_count, log_count

    finally:
        db.close()


if __name__ == "__main__":
    print("开始迁移旧数据...")
    print("=" * 60)

    # 执行迁移
    success_count, failed_count, failed_ids = migrate_old_data()

    # 验证迁移
    verify_migration()

    print("\n迁移完成！")
    print("注意事项：")
    print("1. 旧数据已保留，新旧数据并存")
    print("2. 建议检查迁移后的数据是否正确")
    print("3. 旧接口仍然可用，新接口需要使用新数据")
    sys.exit(0 if failed_count == 0 else 1)
