"""Resilience Analysis for Job Scheduling under Slot Failures.

This module simulates single time-slot failures to identify the most critical
time slot whose loss results in the maximum reduction in total scheduling profit.

Complexity:
    Resilience analysis:
        Time Complexity:  O(H(n log n + nH))
            - Evaluates up to H originally available slots independently.
            - Re-executes schedule_jobs() from scratch for each candidate slot:
              O(H * (n log n + nH)).
        Space Complexity: O(n + H)
            - Reuses auxiliary storage of O(n + H) across iterations for the simulated
              schedule and unavailable slot set.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from deadline_scheduler.scheduler import schedule_jobs
except ImportError:
    from scheduler import schedule_jobs


class ResilienceReport(dict):
    """Structured dictionary holding resilience analysis results.

    Provides both dictionary-key and object-attribute access to:
      - critical_slot: The slot number whose loss causes maximum profit loss.
      - max_loss: The maximum profit loss observed.
      - profit_after_loss / new_profit: Profit achieved after losing the critical slot.
      - schedule / schedule_after_loss: Resulting schedule after losing the critical slot.
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
        """Returns the result as a standard 4-tuple."""
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
    jobs: List[Tuple[Any, int, Union[int, float]]],
    baseline_profit: Optional[Union[int, float]] = None,
) -> ResilienceReport:
    """Identifies the most critical time slot by simulating individual slot failures.

    For every originally available time slot in the range [1, H], the slot is
    temporarily marked as unavailable in addition to initially unavailable slots.
    A full rescheduling is executed via `schedule_jobs()`. The slot that causes the
    maximum loss in profit relative to `baseline_profit` is determined as the
    critical slot. If a tie occurs between multiple slots causing the same
    maximum loss, the smallest slot number is chosen.

    Args:
        n: Number of jobs.
        H: Total number of time slots in the horizon (1 to H).
        unavailable: Initially unavailable slot(s).
        jobs: List of job tuples (job_id, deadline, profit).
        baseline_profit: Maximum profit obtained before any slot failure.
                         If None, it is calculated automatically.

    Returns:
        A ResilienceReport (dict-like structure) containing:
            - critical_slot: Smallest slot number producing maximum profit loss.
            - max_loss: Value of the maximum profit loss.
            - profit_after_loss: Profit obtained when the critical slot is lost.
            - schedule: Complete schedule resulting from the loss of the critical slot.
    """
    # 1. Normalize initially unavailable slots into a set of integers
    if unavailable is None:
        init_unavailable: Set[int] = set()
    elif isinstance(unavailable, (int, str)):
        init_unavailable = {int(unavailable)}
    else:
        init_unavailable = {int(slot) for slot in unavailable}

    # 2. Determine baseline profit if not provided
    if baseline_profit is None:
        baseline_profit, _, _ = schedule_jobs(n, H, init_unavailable, jobs)

    # 3. Identify all originally available time slots within the horizon [1, H]
    available_slots: List[int] = [
        slot for slot in range(1, H + 1) if slot not in init_unavailable
    ]

    # 4. Handle edge case: all time slots are initially unavailable (or H <= 0)
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

    # 5. Track the critical slot with maximum profit loss
    critical_slot: Optional[int] = None
    max_loss: Union[int, float] = float("-inf")
    profit_after_loss: Union[int, float] = 0
    critical_schedule: Dict[int, Optional[Any]] = {}

    # 6. Iterate through each originally available slot in increasing order (1 to H)
    for slot in available_slots:
        # Combine the tested slot with initially unavailable slots
        simulated_unavailable: Set[int] = init_unavailable | {slot}

        # Rebuild schedule from scratch using greedy scheduling algorithm
        new_profit, new_schedule, _ = schedule_jobs(
            n=n,
            H=H,
            unavailable=simulated_unavailable,
            jobs=jobs,
        )

        # Calculate profit loss
        loss = baseline_profit - new_profit

        # Maintain maximum loss; strictly greater (>) preserves smallest slot on ties
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
