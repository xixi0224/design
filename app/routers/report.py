import json
from fastapi import APIRouter, HTTPException
from app.db import get_conn
from datetime import datetime, timedelta

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/summary")
async def get_report_summary():
    """
    获取学习报告全部数据，聚合自真实数据库
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # ========== 1. 四大核心统计 ==========
        # 总学习时长（分钟 -> 小时）
        cursor.execute("SELECT COALESCE(SUM(study_duration), 0) FROM zhinote_study_stats")
        total_study_minutes = cursor.fetchone()[0]
        total_study_hours = round(total_study_minutes / 60, 1) if total_study_minutes else 0

        # 笔记总数量
        cursor.execute("SELECT COUNT(*) FROM zhinote_notes")
        total_notes = cursor.fetchone()[0]

        # 累计复习打卡总次数
        cursor.execute("SELECT COALESCE(SUM(review_count), 0) FROM zhinote_study_stats")
        total_reviews = cursor.fetchone()[0]

        # 知识点掌握度（基于zhinote_analysis中is_exam_point=1的重要度均值）
        cursor.execute(
            """
            SELECT COALESCE(AVG(importance), 0) 
            FROM zhinote_analysis 
            WHERE is_exam_point = 1
            """
        )
        avg_importance = cursor.fetchone()[0]
        # importance范围1-5，映射到0-100%
        mastery_percent = round(avg_importance * 20) if avg_importance else 0

        # ========== 2. 考点热度分析（横向柱状图） ==========
        cursor.execute(
            """
            SELECT section, COUNT(*) as cnt
            FROM zhinote_analysis
            WHERE is_exam_point = 1
            GROUP BY section
            ORDER BY cnt DESC
            LIMIT 10
            """
        )
        heat_rows = cursor.fetchall()
        heat_data = [{"name": r[0] or "未分类", "value": r[1]} for r in heat_rows]

        # ========== 3. 学习曲线（近30天每日学习时长） ==========
        start_30 = (datetime.now() - timedelta(days=29)).strftime("%Y-%m-%d")
        cursor.execute(
            """
            SELECT study_date, study_duration
            FROM zhinote_study_stats
            WHERE study_date >= %s
            ORDER BY study_date ASC
            """,
            (start_30,)
        )
        trend_rows = cursor.fetchall()
        # 构建完整30天日期map
        trend_map = {}
        for i in range(30):
            d = (datetime.now() - timedelta(days=29 - i)).strftime("%Y-%m-%d")
            trend_map[d] = 0
        for r in trend_rows:
            date_str = r[0].strftime("%Y-%m-%d") if hasattr(r[0], 'strftime') else str(r[0])
            if date_str in trend_map:
                trend_map[date_str] = r[1]
        trend_dates = list(trend_map.keys())
        trend_values = list(trend_map.values())

        # ========== 4. 掌握度雷达图（按section分组计算平均importance） ==========
        cursor.execute(
            """
            SELECT section, COALESCE(AVG(importance), 0) as avg_imp
            FROM zhinote_analysis
            WHERE is_exam_point = 1 AND section IS NOT NULL AND section != ''
            GROUP BY section
            ORDER BY avg_imp DESC
            LIMIT 8
            """
        )
        radar_rows = cursor.fetchall()
        radar_indicators = [{"name": r[0], "max": 100} for r in radar_rows]
        radar_values = [round(r[1] * 20) for r in radar_rows]  # importance 1-5 -> 20-100

        # ========== 5. 章节学习时间分布柱状图 ==========
        cursor.execute(
            """
            SELECT section, COUNT(*) as cnt
            FROM zhinote_analysis
            WHERE section IS NOT NULL AND section != ''
            GROUP BY section
            ORDER BY cnt DESC
            LIMIT 8
            """
        )
        chapter_rows = cursor.fetchall()
        chapter_categories = [r[0] for r in chapter_rows]
        chapter_values = [r[1] for r in chapter_rows]

        # ========== 6. 笔记内容分类占比饼图 ==========
        cursor.execute(
            """
            SELECT 
                CASE 
                    WHEN content LIKE '%音频转文字%' THEN '音频'
                    WHEN content LIKE '%PDF导入%' THEN 'PDF'
                    WHEN content LIKE '%Word导入%' THEN 'Word'
                    WHEN content LIKE '%语音录入%' THEN '语音'
                    ELSE '文本'
                END as source_type,
                COUNT(*) as cnt
            FROM zhinote_notes
            GROUP BY source_type
            """
        )
        category_rows = cursor.fetchall()
        category_data = [{"name": r[0], "value": r[1]} for r in category_rows]

        # ========== 7. 每周平均专注度变化 ==========
        start_84 = (datetime.now() - timedelta(days=83)).strftime("%Y-%m-%d")
        cursor.execute(
            """
            SELECT study_date, study_duration, task_count
            FROM zhinote_study_stats
            WHERE study_date >= %s
            ORDER BY study_date ASC
            """,
            (start_84,)
        )
        focus_rows = cursor.fetchall()
        # 按周分组
        week_map = {}
        for r in focus_rows:
            date_str = r[0].strftime("%Y-%m-%d") if hasattr(r[0], 'strftime') else str(r[0])
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            week_start = (date_obj - timedelta(days=date_obj.weekday())).strftime("%Y-%m-%d")
            if week_start not in week_map:
                week_map[week_start] = {"total_duration": 0, "total_tasks": 0, "days": 0}
            week_map[week_start]["total_duration"] += r[1]
            week_map[week_start]["total_tasks"] += r[2]
            week_map[week_start]["days"] += 1

        focus_weeks = sorted(week_map.keys())[-12:]
        focus_values = []
        for w in focus_weeks:
            data = week_map[w]
            # 专注度 = 每天平均学习时长(分钟) / 120分钟 * 100，上限100
            avg_daily = data["total_duration"] / data["days"] if data["days"] > 0 else 0
            focus_pct = min(round(avg_daily / 120 * 100), 100)
            focus_values.append(focus_pct)

        # ========== 8. 高频关键词云 ==========
        cursor.execute("SELECT keywords FROM zhinote_analysis WHERE keywords IS NOT NULL")
        kw_rows = cursor.fetchall()
        keyword_count = {}
        for r in kw_rows:
            try:
                kws = json.loads(r[0]) if r[0] else []
                for k in kws:
                    keyword_count[k] = keyword_count.get(k, 0) + 1
            except:
                pass
        word_cloud_data = [{"name": k, "value": v} for k, v in sorted(keyword_count.items(), key=lambda x: -x[1])[:30]]

        cursor.close()
        conn.close()

        return {
            "code": 0,
            "data": {
                # 四大核心统计
                "totalStudyHours": total_study_hours,
                "totalNotes": total_notes,
                "totalReviews": total_reviews,
                "masteryPercent": mastery_percent,
                # 考点热度
                "heatData": heat_data,
                # 学习曲线
                "trendDates": trend_dates,
                "trendValues": trend_values,
                # 雷达图
                "radarIndicators": radar_indicators,
                "radarValues": radar_values,
                # 章节分布
                "chapterCategories": chapter_categories,
                "chapterValues": chapter_values,
                # 分类占比
                "categoryData": category_data,
                # 专注度
                "focusWeeks": [f"第{i+1}周" for i in range(len(focus_values))],
                "focusValues": focus_values,
                # 关键词云
                "wordCloudData": word_cloud_data
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习报告失败: {str(e)}")


@router.get("/export")
async def export_report():
    """
    导出学习报告（返回markdown格式文本）
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 收集基础统计
        cursor.execute("SELECT COALESCE(SUM(study_duration), 0) FROM zhinote_study_stats")
        total_minutes = cursor.fetchone()[0]
        total_hours = round(total_minutes / 60, 1)

        cursor.execute("SELECT COUNT(*) FROM zhinote_notes")
        total_notes = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(review_count), 0) FROM zhinote_study_stats")
        total_reviews = cursor.fetchone()[0]

        # 考点热度
        cursor.execute(
            """
            SELECT section, COUNT(*) as cnt
            FROM zhinote_analysis
            WHERE is_exam_point = 1
            GROUP BY section
            ORDER BY cnt DESC
            LIMIT 10
            """
        )
        heat_rows = cursor.fetchall()

        cursor.close()
        conn.close()

        # 生成markdown报告
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        report = f"""# ZhiNote 学习报告

生成时间：{now}

## 核心数据

| 指标 | 数值 |
|------|------|
| 总学习时长 | {total_hours} 小时 |
| 笔记总数 | {total_notes} 篇 |
| 复习打卡 | {total_reviews} 次 |

## 考点热度 TOP10

| 排名 | 考点 | 出现次数 |
|------|------|---------|
"""
        for i, r in enumerate(heat_rows):
            report += f"| {i+1} | {r[0] or '未分类'} | {r[1]} |\n"

        report += "\n---\n*由 ZhiNote 智能生成*\n"

        return {"code": 0, "data": {"report": report, "filename": f"学习报告_{datetime.now().strftime('%Y%m%d')}.md"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出报告失败: {str(e)}")
