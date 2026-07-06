"""
数据库迁移脚本：添加新字段到 jobs 和 candidates 表

运行方式：
cd backend
python -m app.migrate_add_new_fields
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hr_interview.db')


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
        job_columns = [col[1] for col in cursor.fetchall()]

        if 'job_type' not in job_columns:
            print("正在给 jobs 表添加新字段...")
            cursor.execute("ALTER TABLE jobs ADD COLUMN job_type VARCHAR(50)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN location VARCHAR(100)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN salary_range VARCHAR(50)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN education_req VARCHAR(50)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN experience_req VARCHAR(50)")
            cursor.execute("ALTER TABLE jobs ADD COLUMN parsed_jd_json TEXT")
            print("jobs 表新字段添加完成")
        else:
            print("jobs 表已有新字段，跳过迁移")

        # 检查 candidates 表是否已有 gender 字段
        cursor.execute("PRAGMA table_info(candidates)")
        candidate_columns = [col[1] for col in cursor.fetchall()]

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
            print("candidates 表新字段添加完成")
        else:
            print("candidates 表已有新字段，跳过迁移")

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
