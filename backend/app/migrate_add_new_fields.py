"""
数据库迁移脚本：添加新字段到 jobs 和 candidates 表

运行方式：
cd backend
python -m app.migrate_add_new_fields
"""
import sqlite3
import os
import hashlib
import json
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hr_interview_analysis.db')


def add_column_if_missing(cursor, table_name, columns, column_name, definition):
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
        columns.add(column_name)
        print(f"{table_name}.{column_name} 字段添加完成")


def normalize_question_text(text):
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^\s*\d+[\.\、\)]\s*", "", cleaned)
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = re.sub(r"[？?。！!，,；;：:\.、]+$", "", cleaned)
    return cleaned


def question_hash(text):
    normalized = normalize_question_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""


def backfill_interview_question_items(cursor):
    cursor.execute("""
        SELECT r.id, r.candidate_id, r.job_id, r.round_type, r.round_no, r.report_json, r.created_at
        FROM stage_reports r
        WHERE r.stage_type = 'INTERVIEW_QUESTIONS'
          AND r.status = 'SUCCESS'
          AND r.deleted = 0
    """)
    reports = cursor.fetchall()
    inserted = 0
    for report_id, candidate_id, job_id, round_type, round_no, report_json, created_at in reports:
        cursor.execute("SELECT COUNT(1) FROM interview_question_items WHERE report_id = ?", (report_id,))
        if cursor.fetchone()[0]:
            continue
        try:
            body = json.loads(report_json or "{}")
        except Exception:
            body = {}
        body_round_type = body.get("round_type") if isinstance(body, dict) else None
        body_round_no = body.get("round_no") if isinstance(body, dict) else None
        questions = body.get("questions") if isinstance(body, dict) else []
        if not isinstance(questions, list):
            continue
        for item in questions:
            if isinstance(item, str):
                question_text = item.strip()
                dimension = None
                source = None
                is_required = 1
            elif isinstance(item, dict):
                question_text = str(item.get("question") or item.get("title") or item.get("detail") or "").strip()
                dimension = item.get("dimension") or item.get("category")
                source = item.get("source")
                is_required = 0 if item.get("required") is False else 1
            else:
                continue
            q_hash = question_hash(question_text)
            if not question_text or not q_hash:
                continue
            cursor.execute("""
                INSERT INTO interview_question_items (
                    report_id, candidate_id, job_id, resume_id, round_type, round_no,
                    question_text, question_hash, dimension, source, is_required, deleted, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (
                report_id,
                candidate_id,
                job_id,
                candidate_id,
                round_type or body_round_type,
                round_no or body_round_no,
                question_text,
                q_hash,
                dimension,
                source,
                is_required,
                created_at,
            ))
            inserted += 1
    if inserted:
        print(f"面试问题统计明细回填完成：{inserted} 条")


def migrate():
    """执行数据库迁移"""
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在: {DB_PATH}")
        print("跳过迁移，将在首次启动时创建表")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查 jobs 表是否已有 job_type 字段
        cursor.execute("PRAGMA table_info(jobs)")
        job_columns = {col[1] for col in cursor.fetchall()}

        if 'job_type' not in job_columns:
            print("正在给 jobs 表添加新字段...")
            cursor.execute("ALTER TABLE jobs ADD COLUMN job_type VARCHAR(50)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN location VARCHAR(100)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN salary_range VARCHAR(50)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN education_req VARCHAR(50)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN experience_req VARCHAR(50)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN parsed_jd_json TEXT")
            job_columns.update({
                "job_type", "location", "salary_range", "education_req",
                "experience_req", "parsed_jd_json",
            })
            print("jobs 表新字段添加完成")
        else:
            print("jobs 表已有新字段，跳过迁移")

        add_column_if_missing(cursor, "jobs", job_columns, "version", "INTEGER NOT NULL DEFAULT 1")
        add_column_if_missing(cursor, "jobs", job_columns, "screening_rules_json", "TEXT")
        add_column_if_missing(cursor, "jobs", job_columns, "must_have_json", "TEXT")
        add_column_if_missing(cursor, "jobs", job_columns, "nice_to_have_json", "TEXT")
        add_column_if_missing(cursor, "jobs", job_columns, "risk_points_json", "TEXT")
        add_column_if_missing(cursor, "jobs", job_columns, "interview_questions_json", "TEXT")
        add_column_if_missing(cursor, "jobs", job_columns, "last_used_time", "DATETIME")
        add_column_if_missing(cursor, "jobs", job_columns, "created_by", "VARCHAR(100)")
        add_column_if_missing(cursor, "jobs", job_columns, "updated_by", "VARCHAR(100)")

        # 检查 candidates 表是否已有 gender 字段
        cursor.execute("PRAGMA table_info(candidates)")
        candidate_columns = {col[1] for col in cursor.fetchall()}

        if 'gender' not in candidate_columns:
            print("正在给 candidates 表添加新字段...")
            cursor.execute("ALTER TABLE candidates ADD COLUMN gender VARCHAR(10)")
            cursor.execute("ALTER TABLE candidates ADD COLUMN age INTEGER")
            cursor.execute("ALTER TABLE candidates ADD COLUMN current_city VARCHAR(50)")
            cursor.execute("ALTER TABLE candidates ADD COLUMN expected_city VARCHAR(50)")
            cursor.execute("ALTER TABLE candidates ADD COLUMN job_search_status VARCHAR(50)")
            cursor.execute("ALTER TABLE candidates ADD COLUMN available_date VARCHAR(50)")
            cursor.execute("ALTER TABLE candidates ADD COLUMN expected_salary VARCHAR(50)")
            cursor.execute("ALTER TABLE candidates ADD COLUMN education_level VARCHAR(50)")
            cursor.execute("ALTER TABLE candidates ADD COLUMN graduation_school VARCHAR(100)")
            cursor.execute("ALTER TABLE candidates ADD COLUMN major VARCHAR(100)")
            cursor.execute("ALTER TABLE candidates ADD COLUMN work_years INTEGER")
            cursor.execute("ALTER TABLE candidates ADD COLUMN parsed_resume_json TEXT")
            candidate_columns.update({
                "gender", "age", "current_city", "expected_city", "job_search_status",
                "available_date", "expected_salary", "education_level",
                "graduation_school", "major", "work_years", "parsed_resume_json",
            })
            print("candidates 表新字段添加完成")
        else:
            print("candidates 表已有新字段，跳过迁移")

        cursor.execute("PRAGMA table_info(candidates)")
        candidate_columns = {col[1] for col in cursor.fetchall()}
        if 'current_round_no' not in candidate_columns:
            cursor.execute("ALTER TABLE candidates ADD COLUMN current_round_no INTEGER")
            print("candidates.current_round_no 字段添加完成")
        if 'final_conclusion' not in candidate_columns:
            cursor.execute("ALTER TABLE candidates ADD COLUMN final_conclusion VARCHAR(50)")
            print("candidates.final_conclusion 字段添加完成")

        print("正在确保岗位初筛任务表存在...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name VARCHAR(200),
                job_title VARCHAR(100),
                job_type VARCHAR(50),
                work_location VARCHAR(100),
                experience_requirement VARCHAR(100),
                education_requirement VARCHAR(100),
                job_position_id INTEGER,
                job_position_version INTEGER,
                jd_text TEXT NOT NULL,
                jd_structured_json TEXT,
                jd_snapshot_json TEXT,
                status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
                total_resume_count INTEGER NOT NULL DEFAULT 0,
                parsed_success_count INTEGER NOT NULL DEFAULT 0,
                parsed_failed_count INTEGER NOT NULL DEFAULT 0,
                recommended_count INTEGER NOT NULL DEFAULT 0,
                pending_count INTEGER NOT NULL DEFAULT 0,
                rejected_count INTEGER NOT NULL DEFAULT 0,
                deleted INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(job_position_id) REFERENCES jobs(id)
            )
        """)
        cursor.execute("PRAGMA table_info(screening_tasks)")
        screening_task_columns = {col[1] for col in cursor.fetchall()}
        add_column_if_missing(cursor, "screening_tasks", screening_task_columns, "job_position_id", "INTEGER")
        add_column_if_missing(cursor, "screening_tasks", screening_task_columns, "job_position_version", "INTEGER")
        add_column_if_missing(cursor, "screening_tasks", screening_task_columns, "jd_snapshot_json", "TEXT")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                file_type VARCHAR(20),
                file_url VARCHAR(500),
                file_hash VARCHAR(64),
                text_hash VARCHAR(64),
                reuse_source VARCHAR(50),
                reused_resume_file_id INTEGER,
                reused_profile_id INTEGER,
                parse_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
                parse_error_message TEXT,
                raw_text TEXT,
                deleted INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(task_id) REFERENCES screening_tasks(id)
            )
        """)
        cursor.execute("PRAGMA table_info(resume_files)")
        resume_file_columns = {col[1] for col in cursor.fetchall()}
        add_column_if_missing(cursor, "resume_files", resume_file_columns, "text_hash", "VARCHAR(64)")
        add_column_if_missing(cursor, "resume_files", resume_file_columns, "reuse_source", "VARCHAR(50)")
        add_column_if_missing(cursor, "resume_files", resume_file_columns, "reused_resume_file_id", "INTEGER")
        add_column_if_missing(cursor, "resume_files", resume_file_columns, "reused_profile_id", "INTEGER")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_file_id INTEGER NOT NULL,
                name VARCHAR(100),
                phone VARCHAR(30),
                email VARCHAR(100),
                gender VARCHAR(20),
                age VARCHAR(20),
                city VARCHAR(100),
                expected_city VARCHAR(100),
                education VARCHAR(100),
                school VARCHAR(150),
                major VARCHAR(150),
                graduation_year VARCHAR(50),
                work_years VARCHAR(50),
                latest_company VARCHAR(150),
                latest_position VARCHAR(150),
                past_companies TEXT,
                skills_json TEXT,
                work_experience_json TEXT,
                project_experience_json TEXT,
                industry_experience TEXT,
                salary_expectation VARCHAR(100),
                available_time VARCHAR(100),
                profile_json TEXT,
                data_source VARCHAR(50) NOT NULL DEFAULT 'resume_parse',
                manual_modified_flag INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(resume_file_id) REFERENCES resume_files(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                resume_file_id INTEGER NOT NULL,
                score INTEGER,
                conclusion VARCHAR(30) NOT NULL,
                match_highlights_json TEXT,
                risk_points_json TEXT,
                interview_questions_json TEXT,
                dimension_scores_json TEXT,
                confidence VARCHAR(20),
                ai_reason TEXT,
                status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
                result_source VARCHAR(50),
                reused_from_result_id INTEGER,
                deleted INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(task_id) REFERENCES screening_tasks(id),
                FOREIGN KEY(candidate_id) REFERENCES candidate_profiles(id),
                FOREIGN KEY(resume_file_id) REFERENCES resume_files(id)
            )
        """)
        cursor.execute("PRAGMA table_info(screening_results)")
        screening_result_columns = {col[1] for col in cursor.fetchall()}
        add_column_if_missing(cursor, "screening_results", screening_result_columns, "result_source", "VARCHAR(50)")
        add_column_if_missing(cursor, "screening_results", screening_result_columns, "reused_from_result_id", "INTEGER")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_interview_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                task_id INTEGER,
                round_no INTEGER NOT NULL,
                round_name VARCHAR(100) NOT NULL,
                round_type VARCHAR(50),
                round_focus VARCHAR(100),
                status VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED',
                scheduled_time DATETIME,
                interviewer VARCHAR(100),
                interview_method VARCHAR(30),
                question_json TEXT,
                record_text TEXT,
                score INTEGER,
                conclusion TEXT,
                decision VARCHAR(50),
                deleted INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(candidate_id) REFERENCES candidates(id)
            )
        """)
        cursor.execute("PRAGMA table_info(stage_reports)")
        stage_report_columns = {col[1] for col in cursor.fetchall()}
        if stage_report_columns:
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "report_key", "VARCHAR(255)")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "is_current", "INTEGER NOT NULL DEFAULT 1")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "round_type", "VARCHAR(30)")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "round_no", "INTEGER")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "generate_type", "VARCHAR(30)")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "ai_provider", "VARCHAR(50)")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "ai_model", "VARCHAR(100)")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "candidate_snapshot_json", "TEXT")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "jd_snapshot_json", "TEXT")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "resume_snapshot_json", "TEXT")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "interview_record_snapshot_json", "TEXT")
            add_column_if_missing(cursor, "stage_reports", stage_report_columns, "screening_result_snapshot_json", "TEXT")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interview_question_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                resume_id INTEGER,
                round_type VARCHAR(30),
                round_no INTEGER,
                question_text TEXT NOT NULL,
                question_hash VARCHAR(64) NOT NULL,
                dimension VARCHAR(100),
                source VARCHAR(100),
                is_required INTEGER NOT NULL DEFAULT 1,
                deleted INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(report_id) REFERENCES stage_reports(id),
                FOREIGN KEY(candidate_id) REFERENCES candidates(id),
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_question_items_report ON interview_question_items(report_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_question_items_stats ON interview_question_items(job_id, round_type, question_hash)")
        backfill_interview_question_items(cursor)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_type_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name VARCHAR(50) NOT NULL,
                description TEXT,
                evaluation_focus_json TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                sort_order INTEGER NOT NULL DEFAULT 0,
                builtin INTEGER NOT NULL DEFAULT 0,
                deleted INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_prompt_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_key VARCHAR(80) NOT NULL,
                prompt_name VARCHAR(100) NOT NULL,
                scene VARCHAR(80),
                system_prompt TEXT,
                user_prompt TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
                builtin INTEGER NOT NULL DEFAULT 0,
                remark TEXT,
                deleted INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        print("岗位初筛任务表检查完成")

        conn.commit()
        print("数据库迁移完成！")

    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
