import sys
from deadline_scheduler import schedule_jobs
from resilience_analysis import analyze_resilience


def token_generator():
    for line in sys.stdin:
        stripped = line.strip()
        if not stripped:
            continue
        for token in stripped.split():
            yield token


def main():
    tokens = token_generator()

    first_token = next(tokens, None)
    if first_token is None:
        return

    n = int(first_token)
    H = int(next(tokens))
    b = int(next(tokens))

    unavailable = [int(next(tokens)) for _ in range(b)]

    jobs = []
    for _ in range(n):
        job_id = int(next(tokens))
        deadline = int(next(tokens))
        profit = int(next(tokens))
        jobs.append((job_id, deadline, profit))

    # Baseline scheduling
    baseline_profit, baseline_slots, rejected = schedule_jobs(
        n, H, unavailable, jobs
    )

    # Resilience analysis
    critical_slot, loss, after_profit, after_slots = analyze_resilience(
        n, H, unavailable, jobs, baseline_profit
    )

    # Ensure 0 for every unavailable or unused slot
    base_slots_formatted = [0 if slot == -1 else slot for slot in baseline_slots]
    after_slots_formatted = [0 if slot == -1 else slot for slot in after_slots]

    # Exact output format (all seven lines in required order)
    print(f"BASE_PROFIT {baseline_profit}")
    print("BASE_SLOTS", *base_slots_formatted)
    if len(rejected) == 0:
        print("REJECTED 0")
    else:
        print(f"REJECTED {len(rejected)}", *sorted(rejected))
    print(f"CRITICAL_SLOT {critical_slot}")
    print(f"LOSS {loss}")
    print(f"AFTER_PROFIT {after_profit}")
    print("AFTER_SLOTS", *after_slots_formatted)


if __name__ == "__main__":
    main()