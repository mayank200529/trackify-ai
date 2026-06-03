from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_study_report(filename, user_name, total_entries, total_hours, latest_topic, streak, ai_insight):
    c = canvas.Canvas(filename, pagesize=A4)

    width, height = A4

    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 60, "Trackify AI - Study Progress Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Student Name: {user_name}")
    c.drawString(50, height - 130, f"Total Entries: {total_entries}")
    c.drawString(50, height - 160, f"Total Study Hours: {total_hours}")
    c.drawString(50, height - 190, f"Latest Topic: {latest_topic}")
    c.drawString(50, height - 220, f"Current Streak: {streak} Days")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 270, "AI Study Insight:")

    c.setFont("Helvetica", 11)
    text = c.beginText(50, height - 300)

    for line in ai_insight.split("\n"):
        text.textLine(line)

    c.drawText(text)

    c.save()