from gemini_helper import get_ai_insight

def generate_weekly_report(
    total_hours,
    total_problems,
    streak,
    leetcode_total
):

    prompt = f"""
    Analyze this student's weekly progress.

    Study Hours: {total_hours}
    Problems Solved: {total_problems}
    Current Streak: {streak}
    LeetCode Solved: {leetcode_total}

    Give:
    1. One positive observation
    2. One improvement suggestion
    3. One goal for next week

    Keep it under 120 words.
    """

    return get_ai_insight(prompt)