# File: src/utils/score_calculator.py

# This module contains a shared score calculation function using the formula from FlagScanner._initialize_dataframe

def calculate_score(row):
    """Calculate the final score for a user based on their activity and flags."""
    score = 0
    # Base score: each message contributes increasing amount
    num_messages = int(row.get("messages_past_month", 0))
    for i in range(num_messages):
        score += 5 + (i * 0.2)

    # Flag contributions
    flag_weights = {
        "sent_messages_after_joining": 50,
        "messaged_within_30_days": 100,
        "above_100_messages": 150,
        "below_10_messages": -50,
        "never_messaged": -200,
        "no_role_assigned": -100,
        "low_interaction_high_activity": -150
    }
    for flag, weight in flag_weights.items():
        if row.get(flag):
            score += weight

    # Time adjustment based on recency
    days = int(row.get("days_since_last_message", 0))
    if days <= 7:
        for _ in range(7 - days):
            score += 10
    elif days > 30:
        for _ in range(days - 30):
            score -= 5

    return score
