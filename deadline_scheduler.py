
def schedule_jobs(n, H, unavailable, jobs):

    slots = [0] * (H + 1)

    # Mark unavailable slots
    for slot in unavailable:
        slots[slot] = -1

    # Sort jobs by profit (highest first)
    jobs_sorted = sorted(jobs, key=lambda x: (-x[2], x[0]))

    total_profit = 0
    rejected = []

    # Schedule each job
    for job_id, deadline, profit in jobs_sorted:

        assigned = False

        for slot in range(min(deadline, H), 0, -1):

            if slots[slot] == 0:
                slots[slot] = job_id
                total_profit += profit
                assigned = True
                break

        if not assigned:
            rejected.append(job_id)

    rejected.sort()

    return total_profit, slots[1:], rejected


# Test input
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

profit, schedule, rejected = schedule_jobs(
    n, H, unavailable, jobs
)

print("BASE_PROFIT", profit)
print("BASE_SLOTS", *schedule)
print("REJECTED", *rejected)