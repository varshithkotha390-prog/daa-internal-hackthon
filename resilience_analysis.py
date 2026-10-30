
from deadline_scheduler import schedule_jobs


def analyze_resilience(n, H, unavailable, jobs, baseline_profit):

    unavailable_set = set(unavailable)

    max_loss = -1
    critical_slot = 0
    after_profit = baseline_profit

    # Get the original schedule
    _, after_slots, _ = schedule_jobs(
        n, H, unavailable, jobs
    )

    # Simulate losing each originally available slot
    for slot in range(1, H + 1):

        if slot in unavailable_set:
            continue

        # Temporarily block this slot
        simulated_unavailable = unavailable_set | {slot}

        # Rebuild the schedule
        profit, schedule, rejected = schedule_jobs(
            n, H, simulated_unavailable, jobs
        )

        # Calculate profit loss
        loss = baseline_profit - profit

        # Find maximum loss
        # If tied, choose the smaller slot number
        if (loss > max_loss or
            (loss == max_loss and
             (critical_slot == 0 or slot < critical_slot))):

            max_loss = loss
            critical_slot = slot
            after_profit = profit
            after_slots = schedule

    # Handle the case where all slots are unavailable
    if max_loss == -1:
        max_loss = 0
        critical_slot = 0

    return critical_slot, max_loss, after_profit, after_slots


# Test the resilience algorithm
if __name__ == "__main__":

    n = 5
    H = 5
    unavailable = [3]

    jobs = [
        (101, 2, 100),
        (102, 1, 50),
        (103, 3, 80),
        (104, 2, 120),
        (105, 4, 60)
    ]

    baseline_profit, _, _ = schedule_jobs(
        n, H, unavailable, jobs
    )

    critical_slot, max_loss, after_profit, after_slots = analyze_resilience(
        n, H, unavailable, jobs, baseline_profit
    )

    print("CRITICAL_SLOT", critical_slot)
    print("MAX_LOSS", max_loss)
    print("AFTER_PROFIT", after_profit)
    print("AFTER_SLOTS", *after_slots)
