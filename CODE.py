"""
Greedy Job Sequencing with Deadlines & Single-Slot Resilience Analysis.
DAA Hackathon Solution - Standalone Implementation.
"""

import sys


def schedule_jobs(n, H, unavailable, jobs):
    """
    Schedules jobs using Greedy Job Sequencing with Deadlines.

    Parameters:
        n (int): Total number of jobs.
        H (int): Horizon / number of time slots (1 to H).
        unavailable (iterable): Initially unavailable time slots.
        jobs (list of tuples): Each job is (job_id, deadline, profit).

    Returns:
        total_profit (int/float): Total profit achieved.
        schedule (list): 1-based slot allocations represented as a list of length H
                         (0 for unavailable or unused slots).
        rejected (list): Sorted list of rejected job IDs in increasing numeric order.
    """
    unavailable_set = set(unavailable)

    # 1-indexed array for slots 0..H; 0 means free, -1 means unavailable
    slots = [0] * (H + 1)
    for s in unavailable_set:
        if 1 <= s <= H:
            slots[s] = -1

    # Sort jobs: decreasing profit, tie-breaking by increasing job ID
    def job_sort_key(job):
        jid = job[0]
        numeric_id = int(jid) if str(jid).lstrip("-").isdigit() else str(jid)
        return (-job[2], numeric_id)

    jobs_sorted = sorted(jobs, key=job_sort_key)

    total_profit = 0
    rejected = []

    # Greedy backward allocation to latest feasible available slot
    for job_id, deadline, profit in jobs_sorted:
        assigned = False
        latest_slot = min(deadline, H)
        for s in range(latest_slot, 0, -1):
            if slots[s] == 0:
                slots[s] = job_id
                total_profit += profit
                assigned = True
                break
        if not assigned:
            rejected.append(job_id)

    # Sort rejected jobs by increasing numeric order
    rejected.sort(key=lambda x: int(x) if str(x).lstrip("-").isdigit() else str(x))

    # Format schedule slots (0 for unavailable or unused slots)
    schedule = [0 if slots[s] == -1 else slots[s] for s in range(1, H + 1)]

    return total_profit, schedule, rejected


def analyze_resilience(n, H, unavailable, jobs, baseline_profit):
    """
    Counterfactual Resilience Analysis:
    Independently rebuilds the schedule for every originally available slot.
    Identifies the critical slot causing maximum profit loss.
    Ties are broken in favor of the smallest slot number.
    Handles the edge case where all slots are initially unavailable.

    Parameters:
        n (int): Total number of jobs.
        H (int): Scheduling horizon (1 to H).
        unavailable (iterable): Initially unavailable slots.
        jobs (list): List of job tuples (job_id, deadline, profit).
        baseline_profit (int/float): Profit from baseline schedule.

    Returns:
        critical_slot (int): Most critical slot (0 if all slots unavailable).
        max_loss (int/float): Maximum profit reduction.
        after_profit (int/float): Achieved profit after losing critical slot.
        after_slots (list): Resulting schedule slots after losing critical slot.
    """
    unavailable_set = set(unavailable)
    available_slots = [s for s in range(1, H + 1) if s not in unavailable_set]

    # Edge case: All slots initially unavailable (or H == 0)
    if not available_slots:
        return 0, 0, 0, [0] * H

    max_loss = -1
    critical_slot = 0
    after_profit = baseline_profit
    _, after_slots, _ = schedule_jobs(n, H, unavailable, jobs)

    # Rebuild schedule independently from scratch for each available slot
    for slot in available_slots:
        simulated_unavailable = unavailable_set | {slot}
        profit, schedule, _ = schedule_jobs(n, H, simulated_unavailable, jobs)
        loss = baseline_profit - profit

        # Strictly greater preserves the smallest slot number on ties
        if loss > max_loss:
            max_loss = loss
            critical_slot = slot
            after_profit = profit
            after_slots = schedule

    if max_loss == -1:
        max_loss = 0
        critical_slot = 0

    return critical_slot, max_loss, after_profit, after_slots


def main():
    tokens = sys.stdin.read().split()
    if not tokens:
        return

    it = iter(tokens)
    n = int(next(it))
    H = int(next(it))
    b = int(next(it))

    unavailable = [int(next(it)) for _ in range(b)]

    jobs = []
    for _ in range(n):
        jid_str = next(it)
        job_id = int(jid_str) if jid_str.lstrip("-").isdigit() else jid_str
        deadline = int(next(it))
        profit_str = next(it)
        try:
            profit = int(profit_str)
        except ValueError:
            profit = float(profit_str)
        jobs.append((job_id, deadline, profit))

    # 1. Baseline greedy scheduling
    baseline_profit, baseline_slots, rejected = schedule_jobs(n, H, unavailable, jobs)

    # 2. Resilience analysis
    critical_slot, loss, after_profit, after_slots = analyze_resilience(
        n, H, unavailable, jobs, baseline_profit
    )

    # 3. Print exactly the seven required output lines
    print(f"BASE_PROFIT {baseline_profit}")
    print("BASE_SLOTS", *baseline_slots)
    if len(rejected) == 0:
        print("REJECTED 0")
    else:
        print(f"REJECTED {len(rejected)}", *rejected)
    print(f"CRITICAL_SLOT {critical_slot}")
    print(f"LOSS {loss}")
    print(f"AFTER_PROFIT {after_profit}")
    print("AFTER_SLOTS", *after_slots)


if __name__ == "__main__":
    main()
