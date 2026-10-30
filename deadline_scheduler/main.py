"""Application Integration for Job Scheduling and Resilience Analysis.

This module reads input from standard input according to the hackathon
specification, executes baseline greedy job sequencing, performs resilience
analysis, and outputs the exact required 7-line report.
"""

import sys
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from deadline_scheduler.scheduler import schedule_jobs
    from deadline_scheduler.resilience import analyze_resilience
except ImportError:
    from scheduler import schedule_jobs
    from resilience import analyze_resilience


def parse_input(
    stream: Optional[Any] = None,
) -> Tuple[int, int, List[int], List[Tuple[Any, int, Union[int, float]]]]:
    """Parses problem input from standard input according to specification.

    Input Format:
        Line 1: n H b
        Line 2: b distinct initially unavailable slot numbers (blank when b = 0)
        Next n lines: job_ID deadline profit

    Returns:
        Tuple of (n, H, unavailable_slots, jobs).
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
        # When b = 0, line 2 is blank. If the immediate next line is blank, advance past it.
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

        # Parse numeric job ID as integer if possible
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
    """Formats an integer or float without trailing decimal zeros."""
    if isinstance(val, (int, float)) and val == int(val):
        return str(int(val))
    return str(val)


def build_output_lines(
    base_profit: Union[int, float],
    base_schedule: Dict[int, Optional[Any]],
    rejected: List[Any],
    critical_slot: Optional[int],
    max_loss: Union[int, float],
    after_profit: Union[int, float],
    after_schedule: Dict[int, Optional[Any]],
    H: int,
) -> List[str]:
    """Formats the seven required output lines according to problem specifications."""
    # Line 1: BASE_PROFIT P
    line1 = f"BASE_PROFIT {format_num(base_profit)}"

    # Line 2: BASE_SLOTS followed by H job IDs in slot order (0 for unused/unavailable)
    base_slots = [
        str(base_schedule.get(slot) if base_schedule.get(slot) is not None else 0)
        for slot in range(1, H + 1)
    ]
    line2 = f"BASE_SLOTS {' '.join(base_slots)}"

    # Line 3: REJECTED K followed by K rejected job IDs in increasing numeric order
    # If K = 0, print only REJECTED 0
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

    # Line 4: CRITICAL_SLOT T (Use 0 if all slots are initially unavailable)
    crit_slot = critical_slot if critical_slot is not None else 0
    line4 = f"CRITICAL_SLOT {crit_slot}"

    # Line 5: LOSS L
    line5 = f"LOSS {format_num(max_loss)}"

    # Line 6: AFTER_PROFIT P_after
    line6 = f"AFTER_PROFIT {format_num(after_profit)}"

    # Line 7: AFTER_SLOTS followed by H slot entries using the same 0 convention
    after_slots = [
        str(after_schedule.get(slot) if after_schedule.get(slot) is not None else 0)
        for slot in range(1, H + 1)
    ]
    line7 = f"AFTER_SLOTS {' '.join(after_slots)}"

    return [line1, line2, line3, line4, line5, line6, line7]


def main() -> None:
    """Main execution flow: parse stdin, schedule, analyze, print output."""
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

    # 3. Format and display exact 7 output lines
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
