"""Greedy Job Sequencing with Deadlines.

This module implements the core Greedy Job Sequencing algorithm with support
for initially unavailable time slots and deadline constraints.

Complexity:
    Baseline scheduling:
        Time Complexity:  O(n log n + nH)
            - O(n log n) to sort n jobs by descending profit (tie-break by ID).
            - O(nH) to search backward from min(deadline, H) to slot 1 for each job.
        Space Complexity: O(n + H)
            - O(H) for schedule mapping across horizon slots [1, H].
            - O(n) for parsed jobs and rejected job ID storage.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union


def schedule_jobs(
    n: int,
    H: int,
    unavailable: Optional[Union[int, List[int], Set[int], Tuple[int, ...]]],
    jobs: List[Tuple[Any, int, Union[int, float]]],
) -> Tuple[Union[int, float], Dict[int, Optional[Any]], List[Any]]:
    """Schedules jobs to maximize total profit within deadlines using a greedy strategy.

    Each job has a duration of 1 time unit and must be scheduled in a discrete
    time slot t in the range [1, H] such that t <= deadline.

    Args:
        n: Total number of jobs (length of jobs list).
        H: Scheduling horizon / maximum number of time slots (1 to H).
        unavailable: Time slot(s) that are initially blocked and cannot host jobs.
                     Can be a single slot integer, an iterable of slots, or None.
        jobs: List of job tuples, each represented as (job_id, deadline, profit).

    Returns:
        A tuple of:
            - total_profit: Sum of profits of all successfully scheduled jobs.
            - schedule: Dictionary mapping each slot (1 to H) to the assigned job ID,
                        or None if the slot remains unassigned/unavailable.
            - rejected: Sorted list of job IDs that could not be scheduled.
    """
    # Normalize unavailable slots into a set of integers
    if unavailable is None:
        unavailable_slots: Set[int] = set()
    elif isinstance(unavailable, (int, str)):
        unavailable_slots = {int(unavailable)}
    else:
        unavailable_slots = {int(slot) for slot in unavailable}

    # Initialize schedule mapping for all slots from 1 to H as None
    schedule: Dict[int, Optional[Any]] = {slot: None for slot in range(1, H + 1)}

    # Helper function to extract (job_id, deadline, profit) whether tuple or dict
    def parse_job(job: Any) -> Tuple[Any, int, Union[int, float]]:
        if isinstance(job, dict):
            j_id = job.get("job_id", job.get("id"))
            return (j_id, int(job["deadline"]), job["profit"])
        return (job[0], int(job[1]), job[2])

    parsed_jobs = [parse_job(j) for j in jobs]

    # Sort jobs:
    # Primary key: Descending profit (-profit)
    # Secondary key: Ascending job ID to break ties consistently
    parsed_jobs.sort(key=lambda j: (-j[2], j[0]))

    total_profit: Union[int, float] = 0
    rejected_job_ids: List[Any] = []

    # Greedy allocation: assign each job to the latest available feasible slot
    for job_id, deadline, profit in parsed_jobs:
        allocated_slot: Optional[int] = None

        # A job with deadline d can only be placed in a slot t where 1 <= t <= min(deadline, H)
        latest_possible_slot = min(deadline, H)

        # Search backwards from the latest feasible slot to slot 1
        for slot in range(latest_possible_slot, 0, -1):
            if slot not in unavailable_slots and schedule[slot] is None:
                allocated_slot = slot
                break

        if allocated_slot is not None:
            schedule[allocated_slot] = job_id
            total_profit += profit
        else:
            rejected_job_ids.append(job_id)

    # Sort rejected job IDs in ascending order
    rejected_job_ids.sort()

    return total_profit, schedule, rejected_job_ids
