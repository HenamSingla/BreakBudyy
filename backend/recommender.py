# backend/recommender.py
from datetime import date, timedelta

def suggest_windows(today: date,
                    horizon_days: int,
                    desired_len_days: int,
                    team_size: int,
                    team_out_dates: list,
                    max_coverage_ratio: float,
                    top_k: int = 5):
    # Return a few dummy windows
    results = []
    for i in range(top_k):
        start = today + timedelta(days=7 + i*desired_len_days)
        end = start + timedelta(days=desired_len_days - 1)
        cov = 0.1  # pretend coverage ratio
        results.append((start, end, cov))
    return results
