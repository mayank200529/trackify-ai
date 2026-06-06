from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_study_report(
    filename,
    user_name,
    total_entries,
    total_hours,
    latest_topic,
    streak,
    ai_insight,
    total_problems=0,
    leetcode_total=0,
    leetcode_easy=0,
    leetcode_medium=0,
    leetcode_hard=0
):
    c = canvas.Canvas(filename, pagesize=A4)

    width, height = A4
    y = height - 60

    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, y, "Trackify AI - Performance Report")

    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Student Summary")

    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Student Name: {user_name}")

    y -= 25
    c.drawString(50, y, f"Total Study Entries: {total_entries}")

    y -= 25
    c.drawString(50, y, f"Total Study Hours: {total_hours}")

    y -= 25
    c.drawString(50, y, f"Latest Topic Studied: {latest_topic}")

    y -= 25
    c.drawString(50, y, f"Current Study Streak: {streak} Days")

    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Coding Progress")

    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Trackify Coding Problems: {total_problems}")

    y -= 25
    c.drawString(50, y, f"LeetCode Total Solved: {leetcode_total}")

    y -= 25
    c.drawString(50, y, f"Easy: {leetcode_easy} | Medium: {leetcode_medium} | Hard: {leetcode_hard}")

    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "AI Study Insight")

    y -= 30
    c.setFont("Helvetica", 11)
    text = c.beginText(50, y)

    for line in ai_insight.split("\n"):
        text.textLine(line)

    c.drawText(text)

    c.save()