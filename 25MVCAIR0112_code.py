"""
================================================================================
Design and Analysis of Algorithms (DAA) - Hackathon Project
Registration Number : 25MVCAIR0112
Project Title       : Deadline Scheduler – Survive a Lost Time Slot
Algorithm Technique : Greedy Job Sequencing with Deadlines &
                      Counterfactual Resilience Analysis
Complexity          : Baseline   : O(n log n + n * H) time, O(n + H) space
                      Resilience : O(H * (n log n + n * H)) time, O(n + H) space
Python Version      : Python 3.8+ (Standard Library Only - Zero External Dependencies)
================================================================================
"""

import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union


# ==============================================================================
# Phase 1: Greedy Job Sequencing with Deadlines
# ==============================================================================

def schedule_jobs(
    n: int,
    H: int,
    unavailable: Optional[Union[int, List[int], Set[int], Tuple[int, ...]]],
    jobs: List[Union[Tuple[Any, int, Union[int, float]], Dict[str, Any]]],
) -> Tuple[Union[int, float], Dict[int, Optional[Any]], List[Any]]:
    """
    Schedules jobs to maximize total profit within deadlines using a greedy strategy.

    Each job has unit processing time (duration = 1) and must be scheduled in a
    discrete time slot t in [1, H] such that 1 <= t <= deadline.

    Algorithmic Steps:
      1. Normalize initially unavailable slots into a fast lookup set.
      2. Normalize and sort jobs:
         - Primary Key   : Descending Profit (highest profit considered first).
         - Secondary Key : Ascending Job ID (deterministic tie-breaking).
      3. For each job in sorted order, find the latest feasible available slot:
         - Search backwards from min(deadline, H) down to slot 1.
         - Assigning to the latest slot preserves earlier slots for tighter deadlines.
      4. If a valid slot is found, assign the job; otherwise, add to rejected list.
      5. Sort rejected job IDs in increasing numeric order.

    Parameters:
        n           : Total number of candidate jobs.
        H           : Scheduling horizon (total time slots, 1 to H).
        unavailable : Set/list of time slots blocked and unavailable for jobs.
        jobs        : List of job tuples (job_id, deadline, profit) or job dictionaries.

    Returns:
        total_profit : Sum of profits of all successfully scheduled jobs.
        schedule     : Dict mapping slot (1 to H) -> Job ID (or None if empty/blocked).
        rejected     : List of rejected job IDs in ascending numerical order.
    """
    # 1. Normalize unavailable slots into a set of integers
    if unavailable is None:
        unavailable_slots: Set[int] = set()
    elif isinstance(unavailable, (int, str)):
        unavailable_slots = {int(unavailable)}
    else:
        unavailable_slots = {int(slot) for slot in unavailable}

    # 2. Initialize schedule mapping for all slots 1 to H as None
    schedule: Dict[int, Optional[Any]] = {slot: None for slot in range(1, H + 1)}

    # Helper function to extract (job_id, deadline, profit) from tuple or dict
    def parse_job(job: Any) -> Tuple[Any, int, Union[int, float]]:
        if isinstance(job, dict):
            j_id = job.get("job_id", job.get("id"))
            return (j_id, int(job["deadline"]), job["profit"])
        return (job[0], int(job[1]), job[2])

    parsed_jobs = [parse_job(j) for j in jobs]

    # Helper key for consistent tie-breaking by numeric Job ID
    def sort_key(j: Tuple[Any, int, Union[int, float]]):
        j_id, _, profit = j
        numeric_id = int(j_id) if str(j_id).lstrip("-").isdigit() else float("inf")
        return (-profit, numeric_id, str(j_id))

    parsed_jobs.sort(key=sort_key)

    total_profit: Union[int, float] = 0
    rejected_job_ids: List[Any] = []

    # 3. Greedy allocation: allocate each job to its latest feasible free slot
    for job_id, deadline, profit in parsed_jobs:
        allocated_slot: Optional[int] = None
        latest_possible_slot = min(deadline, H)

        # Backward search from min(deadline, H) down to 1
        for slot in range(latest_possible_slot, 0, -1):
            if slot not in unavailable_slots and schedule[slot] is None:
                allocated_slot = slot
                break

        if allocated_slot is not None:
            schedule[allocated_slot] = job_id
            total_profit += profit
        else:
            rejected_job_ids.append(job_id)

    # 4. Sort rejected job IDs in ascending numerical order
    rejected_job_ids.sort(
        key=lambda x: (int(x) if str(x).lstrip("-").isdigit() else float("inf"), str(x))
    )

    return total_profit, schedule, rejected_job_ids


# ==============================================================================
# Phase 2: Resilience Analysis & Critical Slot Simulation
# ==============================================================================

class ResilienceReport(dict):
    """
    Structured container holding resilience analysis results.
    Supports dictionary-key access, attribute access, and tuple conversion.
    """

    def __init__(
        self,
        critical_slot: Optional[int],
        max_loss: Union[int, float],
        profit_after_loss: Union[int, float],
        schedule: Dict[int, Optional[Any]],
    ) -> None:
        super().__init__(
            critical_slot=critical_slot,
            max_loss=max_loss,
            profit_after_loss=profit_after_loss,
            schedule=schedule,
        )

    def __getitem__(self, key: str) -> Any:
        if key == "new_profit":
            return super().__getitem__("profit_after_loss")
        if key == "schedule_after_loss":
            return super().__getitem__("schedule")
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        if key in ("new_profit", "schedule_after_loss"):
            return self[key]
        return super().get(key, default)

    @property
    def critical_slot(self) -> Optional[int]:
        return self["critical_slot"]

    @property
    def max_loss(self) -> Union[int, float]:
        return self["max_loss"]

    @property
    def profit_after_loss(self) -> Union[int, float]:
        return self["profit_after_loss"]

    @property
    def new_profit(self) -> Union[int, float]:
        return self["profit_after_loss"]

    @property
    def schedule(self) -> Dict[int, Optional[Any]]:
        return self["schedule"]

    @property
    def schedule_after_loss(self) -> Dict[int, Optional[Any]]:
        return self["schedule"]

    def to_tuple(
        self,
    ) -> Tuple[Optional[int], Union[int, float], Union[int, float], Dict[int, Optional[Any]]]:
        return (
            self["critical_slot"],
            self["max_loss"],
            self["profit_after_loss"],
            self["schedule"],
        )


def analyze_resilience(
    n: int,
    H: int,
    unavailable: Optional[Union[int, List[int], Set[int], Tuple[int, ...]]],
    jobs: List[Union[Tuple[Any, int, Union[int, float]], Dict[str, Any]]],
    baseline_profit: Optional[Union[int, float]] = None,
) -> ResilienceReport:
    """
    Simulates single-slot failures to find the most critical time slot.

    Algorithmic Steps:
      1. Identify all originally available slots in horizon [1, H].
      2. If all slots are initially unavailable (b = H), return critical_slot = 0,
         loss = 0, and profit_after_loss = baseline_profit (convention).
      3. For every originally available slot s in increasing order (1 to H):
         a. Temporarily mark slot s as unavailable: simulated = unavailable | {s}.
         b. Completely rebuild the schedule from scratch using schedule_jobs().
         c. Compute profit loss: loss = baseline_profit - new_profit.
         d. If loss > max_loss:
            - Update max_loss, critical_slot = s, profit_after_loss, and schedule.
            - Strictly greater (>) comparison preserves the smallest slot on ties.

    Returns:
        ResilienceReport with critical_slot, max_loss, profit_after_loss, schedule.
    """
    # 1. Normalize initially unavailable slots
    if unavailable is None:
        init_unavailable: Set[int] = set()
    elif isinstance(unavailable, (int, str)):
        init_unavailable = {int(unavailable)}
    else:
        init_unavailable = {int(slot) for slot in unavailable}

    # 2. Determine baseline profit if not provided
    if baseline_profit is None:
        baseline_profit, _, _ = schedule_jobs(n, H, init_unavailable, jobs)

    # 3. Identify all originally available time slots within [1, H]
    available_slots: List[int] = [
        slot for slot in range(1, H + 1) if slot not in init_unavailable
    ]

    # 4. Handle boundary condition: no available slots in horizon
    if not available_slots:
        empty_schedule: Dict[int, Optional[Any]] = {
            slot: None for slot in range(1, H + 1)
        }
        return ResilienceReport(
            critical_slot=None,
            max_loss=0,
            profit_after_loss=baseline_profit,
            schedule=empty_schedule,
        )

    # 5. Track the critical slot with maximum loss
    critical_slot: Optional[int] = None
    max_loss: Union[int, float] = float("-inf")
    profit_after_loss: Union[int, float] = 0
    critical_schedule: Dict[int, Optional[Any]] = {}

    # 6. Evaluate each candidate slot in strictly ascending order (1 to H)
    for slot in available_slots:
        simulated_unavailable: Set[int] = init_unavailable | {slot}

        # Independent scratch re-computation guarantees global optimality
        new_profit, new_schedule, _ = schedule_jobs(
            n=n,
            H=H,
            unavailable=simulated_unavailable,
            jobs=jobs,
        )

        loss = baseline_profit - new_profit

        # Strictly greater preserves the smallest slot number on ties
        if loss > max_loss:
            max_loss = loss
            critical_slot = slot
            profit_after_loss = new_profit
            critical_schedule = new_schedule

    return ResilienceReport(
        critical_slot=critical_slot,
        max_loss=max_loss,
        profit_after_loss=profit_after_loss,
        schedule=critical_schedule,
    )


# ==============================================================================
# Phase 3: Input Parsing, Output Formatting & CLI Main
# ==============================================================================

def parse_input(
    stream: Optional[Any] = None,
) -> Tuple[int, int, List[int], List[Tuple[Any, int, Union[int, float]]]]:
    """
    Parses problem input from standard input stream according to specification.

    Input Specification:
      Line 1: n H b
      Line 2: b distinct initially unavailable slot numbers (blank line when b = 0)
      Next n lines: job_ID deadline profit

    Returns:
        (n, H, unavailable_slots, jobs)
    """
    if stream is None:
        stream = sys.stdin

    content = stream.read()
    if not content or not content.strip():
        raise ValueError("Empty input received")

    lines = content.splitlines()
    non_empty_indices = [i for i, line in enumerate(lines) if line.strip()]
    if not non_empty_indices:
        raise ValueError("No valid input lines found")

    # Line 1: n H b
    first_line_idx = non_empty_indices[0]
    parts1 = lines[first_line_idx].strip().split()
    if len(parts1) < 3:
        raise ValueError(
            f"Line 1 must contain n, H, b; got '{lines[first_line_idx]}'"
        )

    n = int(parts1[0])
    H = int(parts1[1])
    b = int(parts1[2])

    if n < 0 or H < 0 or b < 0:
        raise ValueError("n, H, and b must be non-negative integers")
    if b > H:
        raise ValueError(f"Unavailable slots count b ({b}) cannot exceed H ({H})")

    # Line 2: b distinct initially unavailable slot numbers
    current_line_idx = first_line_idx + 1
    unavailable: List[int] = []

    if b > 0:
        while current_line_idx < len(lines) and not lines[current_line_idx].strip():
            current_line_idx += 1
        if current_line_idx >= len(lines):
            raise ValueError(f"Expected {b} unavailable slots, reached end of input")

        unavail_parts = lines[current_line_idx].strip().split()
        if len(unavail_parts) != b:
            raise ValueError(
                f"Expected {b} unavailable slots, got {len(unavail_parts)}"
            )
        unavailable = [int(x) for x in unavail_parts]
        for slot in unavailable:
            if slot < 1 or slot > H:
                raise ValueError(
                    f"Unavailable slot {slot} is outside valid horizon [1, {H}]"
                )
        current_line_idx += 1
    else:
        # When b = 0, line 2 is blank. Skip any blank line before job definitions.
        if current_line_idx < len(lines) and not lines[current_line_idx].strip():
            current_line_idx += 1

    # Next n lines: job_ID deadline profit
    jobs: List[Tuple[Any, int, Union[int, float]]] = []
    while current_line_idx < len(lines) and len(jobs) < n:
        line_str = lines[current_line_idx].strip()
        current_line_idx += 1
        if not line_str:
            continue

        job_parts = line_str.split()
        if len(job_parts) < 3:
            raise ValueError(
                f"Job line must contain ID, deadline, profit; got '{line_str}'"
            )

        j_id = (
            int(job_parts[0])
            if job_parts[0].lstrip("-").isdigit()
            else job_parts[0]
        )
        deadline = int(job_parts[1])
        try:
            profit: Union[int, float] = int(job_parts[2])
        except ValueError:
            profit = float(job_parts[2])

        if deadline < 1:
            raise ValueError(f"Job {j_id} deadline must be >= 1, got {deadline}")
        if profit < 0:
            raise ValueError(f"Job {j_id} profit must be non-negative, got {profit}")

        jobs.append((j_id, deadline, profit))

    if len(jobs) != n:
        raise ValueError(f"Expected {n} jobs, but parsed {len(jobs)} jobs")

    return n, H, unavailable, jobs


def format_num(val: Union[int, float]) -> str:
    """Formats numbers without trailing decimal zeros (e.g. 100 instead of 100.0)."""
    if isinstance(val, (int, float)) and val == int(val):
        return str(int(val))
    return str(val)


def build_output_lines(
    base_profit: Union[int, float],
    base_schedule: Union[Dict[int, Optional[Any]], List[Any]],
    rejected: List[Any],
    critical_slot: Optional[int],
    max_loss: Union[int, float],
    after_profit: Union[int, float],
    after_schedule: Union[Dict[int, Optional[Any]], List[Any]],
    H: int,
) -> List[str]:
    """Formats the seven required output lines according to specification."""
    # Line 1: BASE_PROFIT P
    line1 = f"BASE_PROFIT {format_num(base_profit)}"

    # Line 2: BASE_SLOTS followed by H slot values (0 for unused/unavailable)
    if isinstance(base_schedule, dict):
        base_slots = [
            str(base_schedule.get(slot) if base_schedule.get(slot) is not None else 0)
            for slot in range(1, H + 1)
        ]
    else:
        base_slots = [str(x) for x in base_schedule]
    line2 = f"BASE_SLOTS {' '.join(base_slots)}"

    # Line 3: REJECTED K followed by K rejected IDs in ascending order (or REJECTED 0)
    k = len(rejected)
    if k == 0:
        line3 = "REJECTED 0"
    else:
        sorted_rejected = sorted(
            rejected,
            key=lambda x: (
                int(x) if str(x).lstrip("-").isdigit() else float("inf"),
                str(x),
            ),
        )
        line3 = f"REJECTED {k} {' '.join(str(x) for x in sorted_rejected)}"

    # Line 4: CRITICAL_SLOT T (0 if all slots initially unavailable)
    crit_slot = critical_slot if critical_slot is not None else 0
    line4 = f"CRITICAL_SLOT {crit_slot}"

    # Line 5: LOSS L
    line5 = f"LOSS {format_num(max_loss)}"

    # Line 6: AFTER_PROFIT P_after
    line6 = f"AFTER_PROFIT {format_num(after_profit)}"

    # Line 7: AFTER_SLOTS followed by H slot values (0 convention)
    if isinstance(after_schedule, dict):
        after_slots = [
            str(after_schedule.get(slot) if after_schedule.get(slot) is not None else 0)
            for slot in range(1, H + 1)
        ]
    else:
        after_slots = [str(x) for x in after_schedule]
    line7 = f"AFTER_SLOTS {' '.join(after_slots)}"

    return [line1, line2, line3, line4, line5, line6, line7]


def main() -> None:
    """Main execution flow: parse stdin, schedule, analyze resilience, print output."""
    n, H, unavailable, jobs = parse_input(sys.stdin)

    # 1. Baseline greedy scheduling
    base_profit, base_schedule, base_rejected = schedule_jobs(
        n=n,
        H=H,
        unavailable=unavailable,
        jobs=jobs,
    )

    # 2. Resilience analysis
    resilience_report = analyze_resilience(
        n=n,
        H=H,
        unavailable=unavailable,
        jobs=jobs,
        baseline_profit=base_profit,
    )

    # 3. Format and print exact 7-line report
    output_lines = build_output_lines(
        base_profit=base_profit,
        base_schedule=base_schedule,
        rejected=base_rejected,
        critical_slot=resilience_report.critical_slot,
        max_loss=resilience_report.max_loss,
        after_profit=resilience_report.profit_after_loss,
        after_schedule=resilience_report.schedule,
        H=H,
    )

    for line in output_lines:
        print(line)


if __name__ == "__main__":
    main()
