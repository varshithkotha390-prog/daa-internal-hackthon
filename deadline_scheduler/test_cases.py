"""Comprehensive Automated Test Suite for Deadline Scheduler Application.

Covers all 14 required testing scenarios, invariant checks, unit tests for
scheduler, resilience, and main modules, as well as end-to-end integration tests.
"""

import io
import random
import sys
import time
import unittest
from contextlib import redirect_stdout
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from deadline_scheduler.scheduler import schedule_jobs
    from deadline_scheduler.resilience import analyze_resilience, ResilienceReport
    from deadline_scheduler.main import parse_input, build_output_lines, main
except ImportError:
    from scheduler import schedule_jobs
    from resilience import analyze_resilience, ResilienceReport
    from main import parse_input, build_output_lines, main


def verify_schedule_invariants(
    test_case: unittest.TestCase,
    n: int,
    H: int,
    unavailable: Any,
    jobs: List[Tuple[Any, int, Union[int, float]]],
    profit: Union[int, float],
    schedule: Dict[int, Optional[Any]],
    rejected: List[Any],
) -> None:
    """Helper method to rigorously verify all fundamental scheduling invariants.

    Invariants checked:
      1. Schedule contains exactly slots 1 to H.
      2. No job is assigned to an unavailable slot.
      3. No two slots contain the same job (no duplicate assignments).
      4. Every scheduled job is assigned to a slot <= its deadline.
      5. The union of scheduled jobs and rejected jobs equals the total job set.
      6. The intersection of scheduled jobs and rejected jobs is empty.
      7. The sum of profits of scheduled jobs equals the reported total profit.
      8. Rejected job IDs are sorted in ascending order.
    """
    # 1. Schedule bounds
    test_case.assertEqual(set(schedule.keys()), set(range(1, H + 1)))

    # Normalize unavailable slots
    if unavailable is None:
        unavail_set: Set[int] = set()
    elif isinstance(unavailable, (int, str)):
        unavail_set = {int(unavailable)}
    else:
        unavail_set = {int(s) for s in unavailable}

    # Map job_id to (deadline, profit)
    job_map: Dict[Any, Tuple[int, Union[int, float]]] = {}
    for j in jobs:
        j_id = j.get("job_id", j.get("id")) if isinstance(j, dict) else j[0]
        deadline = int(j["deadline"]) if isinstance(j, dict) else int(j[1])
        prof = j["profit"] if isinstance(j, dict) else j[2]
        job_map[j_id] = (deadline, prof)

    # 2. Unavailable slots must be None
    for slot in unavail_set:
        if 1 <= slot <= H:
            test_case.assertIsNone(
                schedule[slot],
                f"Invariant violation: Unavailable slot {slot} has assigned job {schedule[slot]}",
            )

    # Collect scheduled jobs
    scheduled_jobs = [j_id for s, j_id in schedule.items() if j_id is not None]

    # 3. No duplicate assignments
    test_case.assertEqual(
        len(scheduled_jobs),
        len(set(scheduled_jobs)),
        "Invariant violation: Duplicate job scheduled across multiple slots",
    )

    # 4. Deadline compliance
    for slot, j_id in schedule.items():
        if j_id is not None:
            deadline, _ = job_map[j_id]
            test_case.assertLessEqual(
                slot,
                deadline,
                f"Invariant violation: Job {j_id} scheduled at slot {slot} after deadline {deadline}",
            )

    # 5 & 6. Partitioning of jobs into scheduled and rejected
    all_job_ids = list(job_map.keys())
    test_case.assertEqual(
        set(scheduled_jobs) | set(rejected),
        set(all_job_ids),
        "Invariant violation: Union of scheduled and rejected jobs does not match input jobs",
    )
    test_case.assertEqual(
        set(scheduled_jobs) & set(rejected),
        set(),
        "Invariant violation: Job exists in both scheduled and rejected lists",
    )

    # 7. Total profit matches sum of scheduled job profits
    expected_profit = sum(job_map[j_id][1] for j_id in scheduled_jobs)
    test_case.assertEqual(
        profit,
        expected_profit,
        f"Invariant violation: Reported profit {profit} != calculated profit {expected_profit}",
    )

    # 8. Rejected job IDs are sorted in ascending order
    expected_sorted_rejected = sorted(
        rejected,
        key=lambda x: (
            int(x) if str(x).lstrip("-").isdigit() else float("inf"),
            str(x),
        ),
    )
    test_case.assertEqual(
        rejected,
        expected_sorted_rejected,
        f"Invariant violation: Rejected list {rejected} is not sorted ascending",
    )


class TestSchedulerUnit(unittest.TestCase):
    """Unit tests for schedule_jobs() in scheduler.py."""

    def test_scenario_01_normal_scheduling_with_unavailable_slots(self) -> None:
        """Scenario 1: Normal scheduling with initially unavailable slot."""
        H = 5
        n = 5
        unavailable = [3]
        jobs = [
            (101, 2, 100),
            (102, 1, 50),
            (103, 3, 80),
            (104, 2, 120),
            (105, 4, 60),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        self.assertEqual(profit, 280)
        self.assertEqual(schedule[1], 101)
        self.assertEqual(schedule[2], 104)
        self.assertIsNone(schedule[3])
        self.assertEqual(schedule[4], 105)
        self.assertIsNone(schedule[5])
        self.assertEqual(rejected, [102, 103])

    def test_scenario_02_no_unavailable_slots(self) -> None:
        """Scenario 2: No initially unavailable slots (b = 0)."""
        H = 3
        n = 3
        unavailable: List[int] = []
        jobs = [
            (1, 2, 100),
            (2, 1, 50),
            (3, 3, 70),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        self.assertEqual(profit, 220)
        self.assertEqual(schedule[1], 2)
        self.assertEqual(schedule[2], 1)
        self.assertEqual(schedule[3], 3)
        self.assertEqual(rejected, [])

    def test_scenario_03_all_slots_unavailable(self) -> None:
        """Scenario 3: All slots initially unavailable (b = H)."""
        H = 4
        n = 3
        unavailable = [1, 2, 3, 4]
        jobs = [
            (10, 2, 100),
            (20, 3, 200),
            (30, 1, 50),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        self.assertEqual(profit, 0)
        for s in range(1, H + 1):
            self.assertIsNone(schedule[s])
        self.assertEqual(rejected, [10, 20, 30])

    def test_scenario_04_no_rejected_jobs(self) -> None:
        """Scenario 4: All jobs successfully scheduled, no rejected jobs."""
        H = 4
        n = 3
        unavailable: List[int] = []
        jobs = [
            (1, 4, 30),
            (2, 2, 50),
            (3, 3, 40),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        self.assertEqual(profit, 120)
        self.assertEqual(rejected, [])
        self.assertEqual(len([j for j in schedule.values() if j is not None]), 3)

    def test_scenario_05_all_jobs_rejected(self) -> None:
        """Scenario 5: All jobs rejected due to blocked slots before deadline."""
        H = 4
        n = 3
        unavailable = [1, 2]
        # All jobs have deadline <= 2, but slots 1 and 2 are unavailable
        jobs = [
            (501, 1, 100),
            (502, 2, 200),
            (503, 2, 150),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        self.assertEqual(profit, 0)
        self.assertEqual(rejected, [501, 502, 503])
        self.assertTrue(all(val is None for val in schedule.values()))

    def test_scenario_06_equal_profit_tie_breaking(self) -> None:
        """Scenario 6: Equal-profit jobs broken by smaller Job ID."""
        H = 1
        n = 2
        unavailable: List[int] = []
        # Both jobs have same deadline (1) and same profit (100)
        # Job 5 has smaller ID than Job 10, so Job 5 must be scheduled
        jobs = [
            (10, 1, 100),
            (5, 1, 100),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        self.assertEqual(profit, 100)
        self.assertEqual(schedule[1], 5)
        self.assertEqual(rejected, [10])

    def test_scenario_07_multiple_jobs_same_deadline(self) -> None:
        """Scenario 7: Multiple jobs sharing the same deadline, cascading backward."""
        H = 4
        n = 4
        unavailable: List[int] = []
        # All 4 jobs have deadline 3
        jobs = [
            (1, 3, 10),
            (2, 3, 40),
            (3, 3, 30),
            (4, 3, 20),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        # Slots 1, 2, 3 should hold jobs 4 (profit 20), 3 (profit 30), 2 (profit 40)
        # Job 1 (profit 10) should be rejected
        self.assertEqual(profit, 90)
        self.assertEqual(schedule[3], 2)
        self.assertEqual(schedule[2], 3)
        self.assertEqual(schedule[1], 4)
        self.assertIsNone(schedule[4])
        self.assertEqual(rejected, [1])

    def test_scenario_08_jobs_with_deadline_one(self) -> None:
        """Scenario 8: Multiple jobs with deadline 1 competing for slot 1."""
        H = 3
        n = 3
        unavailable: List[int] = []
        jobs = [
            (10, 1, 50),
            (20, 1, 100),
            (30, 1, 75),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        self.assertEqual(profit, 100)
        self.assertEqual(schedule[1], 20)
        self.assertIsNone(schedule[2])
        self.assertIsNone(schedule[3])
        self.assertEqual(rejected, [10, 30])

    def test_scenario_09_jobs_with_deadline_H(self) -> None:
        """Scenario 9: Jobs with deadline H can be placed in any earlier available slot."""
        H = 3
        n = 3
        unavailable = [2]
        # All have deadline H = 3
        jobs = [
            (101, 3, 50),
            (102, 3, 70),
            (103, 3, 90),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        # Slots available: 1 and 3 (slot 2 is unavailable)
        # 103 takes slot 3, 102 takes slot 1, 101 rejected
        self.assertEqual(profit, 160)
        self.assertEqual(schedule[3], 103)
        self.assertIsNone(schedule[2])
        self.assertEqual(schedule[1], 102)
        self.assertEqual(rejected, [101])

    def test_scenario_10_unused_time_slots(self) -> None:
        """Scenario 10: Unused time slots remain None when fewer jobs or deadlines restrict placement."""
        H = 5
        n = 2
        unavailable = [2]
        jobs = [
            (1, 1, 100),
            (2, 3, 80),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        self.assertEqual(profit, 180)
        self.assertEqual(schedule[1], 1)
        self.assertIsNone(schedule[2])  # unavailable
        self.assertEqual(schedule[3], 2)
        self.assertIsNone(schedule[4])  # unused
        self.assertIsNone(schedule[5])  # unused
        self.assertEqual(rejected, [])

    def test_scenario_13_single_job_scheduling(self) -> None:
        """Scenario 13: Single job scheduling (fits vs rejected)."""
        # Subcase A: Single job fits
        H = 3
        n = 1
        jobs = [(42, 2, 99)]
        profit, schedule, rejected = schedule_jobs(n, H, [], jobs)
        verify_schedule_invariants(self, n, H, [], jobs, profit, schedule, rejected)
        self.assertEqual(profit, 99)
        self.assertEqual(schedule[2], 42)
        self.assertEqual(rejected, [])

        # Subcase B: Single job rejected because slot is unavailable
        profit2, schedule2, rejected2 = schedule_jobs(n, H, [1], [(42, 1, 99)])
        verify_schedule_invariants(self, n, H, [1], [(42, 1, 99)], profit2, schedule2, rejected2)
        self.assertEqual(profit2, 0)
        self.assertIsNone(schedule2[1])
        self.assertEqual(rejected2, [42])

    def test_job_dict_input_compatibility(self) -> None:
        """Verify scheduler accepts dictionary format for jobs."""
        H = 2
        n = 2
        jobs = [
            {"job_id": "J1", "deadline": 2, "profit": 50},
            {"id": "J2", "deadline": 1, "profit": 80},
        ]
        profit, schedule, rejected = schedule_jobs(n, H, [], jobs)
        self.assertEqual(profit, 130)
        self.assertEqual(schedule[1], "J2")
        self.assertEqual(schedule[2], "J1")
        self.assertEqual(rejected, [])


class TestResilienceUnit(unittest.TestCase):
    """Unit tests for analyze_resilience() in resilience.py."""

    def test_scenario_01_and_11_sample_resilience_and_tie_breaking(self) -> None:
        """Scenario 1 & 11: Sample case with multiple slots producing equal max loss tie-break."""
        H = 5
        n = 5
        unavailable = [3]
        jobs = [
            (101, 2, 100),
            (102, 1, 50),
            (103, 3, 80),
            (104, 2, 120),
            (105, 4, 60),
        ]
        base_profit, _, _ = schedule_jobs(n, H, unavailable, jobs)
        self.assertEqual(base_profit, 280)

        report = analyze_resilience(n, H, unavailable, jobs, base_profit)

        # Both slot 1 and slot 2 yield loss = 100. Smallest slot number (1) must be selected.
        self.assertEqual(report.critical_slot, 1)
        self.assertEqual(report.max_loss, 100)
        self.assertEqual(report.profit_after_loss, 180)

        # Verify schedule invariants for the resilience schedule
        verify_schedule_invariants(
            self,
            n,
            H,
            [3, 1],
            jobs,
            report.profit_after_loss,
            report.schedule,
            [101, 102, 103],
        )

    def test_scenario_03_resilience_all_slots_unavailable(self) -> None:
        """Scenario 3: Resilience analysis when all slots are initially unavailable."""
        H = 3
        n = 2
        unavailable = [1, 2, 3]
        jobs = [(1, 1, 100), (2, 2, 200)]

        report = analyze_resilience(n, H, unavailable, jobs, baseline_profit=0)

        self.assertIsNone(report.critical_slot)
        self.assertEqual(report.max_loss, 0)
        self.assertEqual(report.profit_after_loss, 0)
        self.assertTrue(all(v is None for v in report.schedule.values()))

    def test_scenario_11_explicit_equal_loss_tie_break(self) -> None:
        """Scenario 11: Multiple slots (3 and 4) produce equal max loss; smallest slot 3 chosen."""
        H = 4
        n = 3
        unavailable: List[int] = []
        # Jobs:
        # Job 1: deadline 4, profit 100
        # Job 2: deadline 4, profit 100
        # Job 3: deadline 2, profit 10
        # Baseline: profit 210.
        # Losing slot 4: job 1 and 2 take slots 3 and 2 (job 3 takes slot 1). Profit 210, loss 0.
        # Losing slot 1: job 3 rejected, profit 200, loss 10.
        # Losing slot 2: job 3 can go to slot 1, profit 210, loss 0.
        # Let's create an unambiguous symmetric tie:
        jobs = [
            (10, 2, 100),
            (20, 4, 100),
        ]
        # Baseline: slot 2 = 10, slot 4 = 20. Total = 200.
        # Losing slot 1: slot 2 = 10, slot 4 = 20 -> profit 200, loss 0.
        # Losing slot 2: slot 1 = 10, slot 4 = 20 -> profit 200, loss 0.
        # Losing slot 3: profit 200, loss 0.
        # Losing slot 4: slot 2 = 10, slot 3 = 20 -> profit 200, loss 0.
        # All losses are 0. Ties across slots 1, 2, 3, 4!
        # Smallest slot 1 must be critical slot!
        report = analyze_resilience(n=2, H=4, unavailable=[], jobs=jobs, baseline_profit=200)
        self.assertEqual(report.critical_slot, 1)
        self.assertEqual(report.max_loss, 0)
        self.assertEqual(report.profit_after_loss, 200)

    def test_scenario_12_loss_of_unused_slot(self) -> None:
        """Scenario 12: Additional loss of a slot that is unused in baseline schedule."""
        H = 4
        n = 1
        unavailable: List[int] = []
        jobs = [(1, 1, 100)]
        # Baseline schedule: slot 1 = 1, slots 2, 3, 4 are unused. Profit = 100.
        # Losing slot 2: profit 100, loss 0.
        # Losing slot 3: profit 100, loss 0.
        # Losing slot 4: profit 100, loss 0.
        # Losing slot 1: profit 0, loss 100.
        # Critical slot must be slot 1 with loss 100.
        report = analyze_resilience(n, H, unavailable, jobs, baseline_profit=100)
        self.assertEqual(report.critical_slot, 1)
        self.assertEqual(report.max_loss, 100)
        self.assertEqual(report.profit_after_loss, 0)

    def test_resilience_independent_scratch_rebuild(self) -> None:
        """Verify each slot failure is simulated completely independently from scratch."""
        H = 4
        n = 4
        unavailable = [2]
        jobs = [
            (1, 4, 100),
            (2, 3, 80),
            (3, 1, 50),
            (4, 2, 40),
        ]
        base_profit, _, _ = schedule_jobs(n, H, unavailable, jobs)
        report = analyze_resilience(n, H, unavailable, jobs, base_profit)

        # Independently calculate for critical slot
        crit = report.critical_slot
        expected_profit, expected_sched, _ = schedule_jobs(
            n, H, unavailable=[2, crit], jobs=jobs
        )
        self.assertEqual(report.profit_after_loss, expected_profit)
        self.assertEqual(report.schedule, expected_sched)
        self.assertEqual(report.max_loss, base_profit - expected_profit)

    def test_resilience_report_accessors(self) -> None:
        """Verify ResilienceReport dictionary and property accessors."""
        sched = {1: 101, 2: None}
        report = ResilienceReport(
            critical_slot=1,
            max_loss=50,
            profit_after_loss=100,
            schedule=sched,
        )
        # Property access
        self.assertEqual(report.critical_slot, 1)
        self.assertEqual(report.max_loss, 50)
        self.assertEqual(report.profit_after_loss, 100)
        self.assertEqual(report.new_profit, 100)
        self.assertEqual(report.schedule, sched)
        self.assertEqual(report.schedule_after_loss, sched)

        # Dict key access
        self.assertEqual(report["critical_slot"], 1)
        self.assertEqual(report["max_loss"], 50)
        self.assertEqual(report["profit_after_loss"], 100)
        self.assertEqual(report["new_profit"], 100)
        self.assertEqual(report["schedule"], sched)
        self.assertEqual(report["schedule_after_loss"], sched)

        # to_tuple()
        self.assertEqual(report.to_tuple(), (1, 50, 100, sched))


class TestMainIntegration(unittest.TestCase):
    """Integration and End-to-End tests for main.py."""

    def test_parse_input_standard(self) -> None:
        """Test input parsing with standard valid input."""
        input_data = (
            "5 5 1\n"
            "3\n"
            "101 2 100\n"
            "102 1 50\n"
            "103 3 80\n"
            "104 2 120\n"
            "105 4 60\n"
        )
        stream = io.StringIO(input_data)
        n, H, unavailable, jobs = parse_input(stream)

        self.assertEqual(n, 5)
        self.assertEqual(H, 5)
        self.assertEqual(unavailable, [3])
        self.assertEqual(len(jobs), 5)
        self.assertEqual(jobs[0], (101, 2, 100))
        self.assertEqual(jobs[3], (104, 2, 120))

    def test_parse_input_b_zero_with_blank_line(self) -> None:
        """Test input parsing when b = 0 with a blank second line."""
        input_data = (
            "3 3 0\n"
            "\n"
            "1 1 10\n"
            "2 2 20\n"
            "3 3 30\n"
        )
        stream = io.StringIO(input_data)
        n, H, unavailable, jobs = parse_input(stream)

        self.assertEqual(n, 3)
        self.assertEqual(H, 3)
        self.assertEqual(unavailable, [])
        self.assertEqual(len(jobs), 3)

    def test_parse_input_validation_errors(self) -> None:
        """Test input validation error handling."""
        # Empty input
        with self.assertRaises(ValueError):
            parse_input(io.StringIO(""))

        # b > H
        with self.assertRaises(ValueError):
            parse_input(io.StringIO("2 2 3\n1 2 3\n1 1 10\n2 2 20\n"))

        # Unavailable slot outside horizon
        with self.assertRaises(ValueError):
            parse_input(io.StringIO("1 3 1\n5\n1 1 10\n"))

        # Job deadline < 1
        with self.assertRaises(ValueError):
            parse_input(io.StringIO("1 3 0\n\n1 0 10\n"))

    def test_build_output_lines_sample_case(self) -> None:
        """Verify exact 7-line output format matching hackathon specification."""
        base_profit = 280
        base_schedule = {1: 101, 2: 104, 3: None, 4: 105, 5: None}
        rejected = [102, 103]
        critical_slot = 1
        max_loss = 100
        after_profit = 180
        after_schedule = {1: None, 2: 104, 3: None, 4: 105, 5: None}

        lines = build_output_lines(
            base_profit=base_profit,
            base_schedule=base_schedule,
            rejected=rejected,
            critical_slot=critical_slot,
            max_loss=max_loss,
            after_profit=after_profit,
            after_schedule=after_schedule,
            H=5,
        )

        expected = [
            "BASE_PROFIT 280",
            "BASE_SLOTS 101 104 0 105 0",
            "REJECTED 2 102 103",
            "CRITICAL_SLOT 1",
            "LOSS 100",
            "AFTER_PROFIT 180",
            "AFTER_SLOTS 0 104 0 105 0",
        ]
        self.assertEqual(lines, expected)

    def test_build_output_lines_zero_rejected(self) -> None:
        """Verify REJECTED 0 output format when no jobs are rejected."""
        lines = build_output_lines(
            base_profit=100,
            base_schedule={1: 1, 2: 2},
            rejected=[],
            critical_slot=1,
            max_loss=50,
            after_profit=50,
            after_schedule={1: 0, 2: 2},
            H=2,
        )
        self.assertEqual(lines[2], "REJECTED 0")

    def test_build_output_lines_all_unavailable_convention(self) -> None:
        """Verify CRITICAL_SLOT 0 convention when all slots are unavailable."""
        lines = build_output_lines(
            base_profit=0,
            base_schedule={1: None, 2: None},
            rejected=[10, 20],
            critical_slot=None,
            max_loss=0,
            after_profit=0,
            after_schedule={1: None, 2: None},
            H=2,
        )
        self.assertEqual(lines[0], "BASE_PROFIT 0")
        self.assertEqual(lines[1], "BASE_SLOTS 0 0")
        self.assertEqual(lines[2], "REJECTED 2 10 20")
        self.assertEqual(lines[3], "CRITICAL_SLOT 0")
        self.assertEqual(lines[4], "LOSS 0")
        self.assertEqual(lines[5], "AFTER_PROFIT 0")
        self.assertEqual(lines[6], "AFTER_SLOTS 0 0")

    def test_e2e_full_application_sample(self) -> None:
        """End-to-End test running main() with redirected stdin and stdout."""
        sample_input = (
            "5 5 1\n"
            "3\n"
            "101 2 100\n"
            "102 1 50\n"
            "103 3 80\n"
            "104 2 120\n"
            "105 4 60\n"
        )
        expected_output = (
            "BASE_PROFIT 280\n"
            "BASE_SLOTS 101 104 0 105 0\n"
            "REJECTED 2 102 103\n"
            "CRITICAL_SLOT 1\n"
            "LOSS 100\n"
            "AFTER_PROFIT 180\n"
            "AFTER_SLOTS 0 104 0 105 0\n"
        )

        orig_stdin = sys.stdin
        try:
            sys.stdin = io.StringIO(sample_input)
            captured_stdout = io.StringIO()
            with redirect_stdout(captured_stdout):
                main()
            actual_output = captured_stdout.getvalue()
            self.assertEqual(actual_output, expected_output)
        finally:
            sys.stdin = orig_stdin

    def test_e2e_full_application_b_zero(self) -> None:
        """End-to-End test with b = 0 and blank line."""
        sample_input = (
            "2 2 0\n"
            "\n"
            "1 1 50\n"
            "2 2 70\n"
        )
        orig_stdin = sys.stdin
        try:
            sys.stdin = io.StringIO(sample_input)
            captured_stdout = io.StringIO()
            with redirect_stdout(captured_stdout):
                main()
            actual_lines = captured_stdout.getvalue().strip().splitlines()
            self.assertEqual(len(actual_lines), 7)
            self.assertEqual(actual_lines[0], "BASE_PROFIT 120")
            self.assertEqual(actual_lines[1], "BASE_SLOTS 1 2")
            self.assertEqual(actual_lines[2], "REJECTED 0")
            self.assertEqual(actual_lines[3], "CRITICAL_SLOT 1")
            self.assertEqual(actual_lines[4], "LOSS 50")
            self.assertEqual(actual_lines[5], "AFTER_PROFIT 70")
            self.assertEqual(actual_lines[6], "AFTER_SLOTS 0 2")
        finally:
            sys.stdin = orig_stdin


class TestStressAndConstraints(unittest.TestCase):
    """Scenario 14: Maximum constraints stress testing and boundary conditions."""

    def test_scenario_14_maximum_constraints_stress(self) -> None:
        """Scenario 14: Stress test with n = 200 jobs, H = 60 time slots."""
        n = 200
        H = 60
        # Block 10 slots
        unavailable = [5, 12, 19, 26, 33, 40, 47, 54, 58, 60]

        # Deterministically generate 200 jobs with varying deadlines and profits
        jobs = []
        for i in range(1, n + 1):
            deadline = ((i * 7) % H) + 1
            profit = ((i * 37) % 500) + 10
            jobs.append((i, deadline, profit))

        start_time = time.perf_counter()

        # 1. Baseline schedule
        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)

        # Verify baseline invariants
        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)

        # 2. Resilience analysis
        report = analyze_resilience(n, H, unavailable, jobs, profit)

        elapsed = time.perf_counter() - start_time

        # Assert correct calculation
        self.assertIsNotNone(report.critical_slot)
        self.assertGreaterEqual(report.max_loss, 0)
        self.assertEqual(report.profit_after_loss, profit - report.max_loss)
        self.assertNotIn(report.critical_slot, unavailable)

        # Verify resilience schedule invariants
        sim_unavail = set(unavailable) | {report.critical_slot}
        verify_schedule_invariants(
            self,
            n,
            H,
            sim_unavail,
            jobs,
            report.profit_after_loss,
            report.schedule,
            [j[0] for j in jobs if j[0] not in report.schedule.values()],
        )

        # Performance constraint: execution time must be under 1.0 second
        self.assertLess(
            elapsed,
            1.0,
            f"Stress test took {elapsed:.4f}s, exceeding 1.0 second requirement",
        )

    def test_boundary_zero_jobs(self) -> None:
        """Boundary test with n = 0 jobs and H = 5."""
        H = 5
        n = 0
        unavailable = [1]
        jobs: List[Tuple[Any, int, Union[int, float]]] = []

        profit, schedule, rejected = schedule_jobs(n, H, unavailable, jobs)
        verify_schedule_invariants(self, n, H, unavailable, jobs, profit, schedule, rejected)
        self.assertEqual(profit, 0)
        self.assertEqual(rejected, [])

        report = analyze_resilience(n, H, unavailable, jobs, baseline_profit=0)
        self.assertEqual(report.critical_slot, 2)  # Smallest available slot
        self.assertEqual(report.max_loss, 0)
        self.assertEqual(report.profit_after_loss, 0)

    def test_large_profit_values(self) -> None:
        """Test handling of large profit values without overflow or formatting distortion."""
        H = 2
        n = 2
        jobs = [
            (1, 2, 10**9),
            (2, 1, 10**8),
        ]
        profit, schedule, rejected = schedule_jobs(n, H, [], jobs)
        self.assertEqual(profit, 1_100_000_000)
        self.assertEqual(rejected, [])

        lines = build_output_lines(
            base_profit=profit,
            base_schedule=schedule,
            rejected=rejected,
            critical_slot=1,
            max_loss=10**8,
            after_profit=10**9,
            after_schedule={1: None, 2: 1},
            H=H,
        )
        self.assertEqual(lines[0], "BASE_PROFIT 1100000000")
        self.assertEqual(lines[4], "LOSS 100000000")
        self.assertEqual(lines[5], "AFTER_PROFIT 1000000000")


# =====================================================================
# Phase 5: Independent Brute Force Algorithm Validation & Benchmarking
# =====================================================================

def brute_force_schedule_max_profit(
    n: int,
    H: int,
    unavailable: Optional[Union[int, List[int], Set[int], Tuple[int, ...]]],
    jobs: List[Tuple[Any, int, Union[int, float]]],
) -> Union[int, float]:
    """Exhaustively searches all feasible job assignments to find the global maximum profit.

    For small problem instances (n <= 7, H <= 6), this independently explores all valid
    one-to-one assignments from available slots to jobs such that for every assigned
    job, slot <= deadline and slot not in unavailable.

    Args:
        n: Number of jobs.
        H: Scheduling horizon [1, H].
        unavailable: Blocked time slots.
        jobs: List of job tuples (job_id, deadline, profit).

    Returns:
        The exact maximum profit achievable across all feasible schedules.
    """
    if unavailable is None:
        unavail_set: Set[int] = set()
    elif isinstance(unavailable, (int, str)):
        unavail_set = {int(unavailable)}
    else:
        unavail_set = {int(s) for s in unavailable}

    available_slots = [s for s in range(1, H + 1) if s not in unavail_set]
    job_list: List[Tuple[Any, int, Union[int, float]]] = [
        (j.get("job_id", j.get("id")), int(j["deadline"]), j["profit"])
        if isinstance(j, dict)
        else (j[0], int(j[1]), j[2])
        for j in jobs
    ]

    if not available_slots or not job_list:
        return 0

    max_profit: Union[int, float] = 0
    used_jobs = [False] * len(job_list)

    def backtrack(slot_idx: int, current_profit: Union[int, float]) -> None:
        nonlocal max_profit
        if current_profit > max_profit:
            max_profit = current_profit

        if slot_idx == len(available_slots):
            return

        slot = available_slots[slot_idx]

        # Branch 1: Leave current slot unassigned
        backtrack(slot_idx + 1, current_profit)

        # Branch 2: Assign each eligible unused job to current slot
        for j_idx in range(len(job_list)):
            if not used_jobs[j_idx]:
                _, deadline, profit = job_list[j_idx]
                if slot <= deadline:
                    used_jobs[j_idx] = True
                    backtrack(slot_idx + 1, current_profit + profit)
                    used_jobs[j_idx] = False

    backtrack(0, 0)
    return max_profit


def brute_force_analyze_resilience(
    n: int,
    H: int,
    unavailable: Optional[Union[int, List[int], Set[int], Tuple[int, ...]]],
    jobs: List[Tuple[Any, int, Union[int, float]]],
    baseline_profit: Optional[Union[int, float]] = None,
) -> Tuple[Optional[int], Union[int, float], Union[int, float]]:
    """Independently calculates resilience metrics using exhaustive brute-force search.

    Simulates the loss of each originally available slot one by one. For each slot,
    re-runs brute-force optimization to determine the optimal profit and profit loss.
    Identifies the critical slot causing maximum profit loss, breaking ties in favor
    of the smallest slot number.

    Returns:
        (critical_slot, max_loss, profit_after_loss)
    """
    if unavailable is None:
        unavail_set: Set[int] = set()
    elif isinstance(unavailable, (int, str)):
        unavail_set = {int(unavailable)}
    else:
        unavail_set = {int(s) for s in unavailable}

    if baseline_profit is None:
        baseline_profit = brute_force_schedule_max_profit(n, H, unavail_set, jobs)

    available_slots = [s for s in range(1, H + 1) if s not in unavail_set]
    if not available_slots:
        return None, 0, baseline_profit

    critical_slot: Optional[int] = None
    max_loss: Union[int, float] = float("-inf")
    profit_after_loss: Union[int, float] = 0

    for slot in available_slots:
        simulated_unavail = unavail_set | {slot}
        p_after = brute_force_schedule_max_profit(n, H, simulated_unavail, jobs)
        loss = baseline_profit - p_after

        if loss > max_loss:
            max_loss = loss
            critical_slot = slot
            profit_after_loss = p_after

    return critical_slot, max_loss, profit_after_loss


class TestBruteForceValidation(unittest.TestCase):
    """Phase 5: Independent Brute Force Algorithm Validation and Benchmarking."""

    def test_brute_force_sample_case_matches_greedy(self) -> None:
        """Verify brute-force matches greedy on the sample problem instance."""
        H = 5
        n = 5
        unavailable = [3]
        jobs = [
            (101, 2, 100),
            (102, 1, 50),
            (103, 3, 80),
            (104, 2, 120),
            (105, 4, 60),
        ]
        g_profit, _, _ = schedule_jobs(n, H, unavailable, jobs)
        bf_profit = brute_force_schedule_max_profit(n, H, unavailable, jobs)
        self.assertEqual(g_profit, bf_profit)
        self.assertEqual(bf_profit, 280)

        g_report = analyze_resilience(n, H, unavailable, jobs, g_profit)
        bf_crit, bf_loss, bf_after = brute_force_analyze_resilience(
            n, H, unavailable, jobs, bf_profit
        )
        self.assertEqual(g_report.critical_slot, bf_crit)
        self.assertEqual(g_report.max_loss, bf_loss)
        self.assertEqual(g_report.profit_after_loss, bf_after)
        self.assertEqual(bf_crit, 1)
        self.assertEqual(bf_loss, 100)
        self.assertEqual(bf_after, 180)

    def test_200_deterministic_random_cases_greedy_vs_brute_force(self) -> None:
        """Generate 200 deterministic random cases (seed=42) and verify 100% agreement."""
        random.seed(42)

        total_cases = 200
        baseline_comparisons = 0
        resilience_comparisons = 0
        baseline_mismatches = 0
        resilience_mismatches = 0

        for case_idx in range(1, total_cases + 1):
            n = random.randint(1, 7)
            H = random.randint(1, 6)
            b = random.randint(0, H)
            unavailable = sorted(random.sample(range(1, H + 1), b)) if b > 0 else []

            jobs = []
            for j in range(1, n + 1):
                deadline = random.randint(1, H)
                profit = random.randint(10, 500)
                jobs.append((100 + j, deadline, profit))

            # 1. Baseline greedy vs brute force
            g_profit, _, _ = schedule_jobs(n, H, unavailable, jobs)
            bf_profit = brute_force_schedule_max_profit(n, H, unavailable, jobs)
            baseline_comparisons += 1
            if g_profit != bf_profit:
                baseline_mismatches += 1

            self.assertEqual(
                g_profit,
                bf_profit,
                f"Case {case_idx}: Baseline profit mismatch! Greedy={g_profit}, BF={bf_profit}. "
                f"n={n}, H={H}, unavail={unavailable}, jobs={jobs}",
            )

            # 2. Resilience greedy vs brute force
            g_report = analyze_resilience(n, H, unavailable, jobs, g_profit)
            bf_crit, bf_loss, bf_after = brute_force_analyze_resilience(
                n, H, unavailable, jobs, bf_profit
            )
            resilience_comparisons += 1

            if (
                g_report.critical_slot != bf_crit
                or g_report.max_loss != bf_loss
                or g_report.profit_after_loss != bf_after
            ):
                resilience_mismatches += 1

            self.assertEqual(
                g_report.critical_slot,
                bf_crit,
                f"Case {case_idx}: Critical slot mismatch! Greedy={g_report.critical_slot}, BF={bf_crit}",
            )
            self.assertEqual(
                g_report.max_loss,
                bf_loss,
                f"Case {case_idx}: Max loss mismatch! Greedy={g_report.max_loss}, BF={bf_loss}",
            )
            self.assertEqual(
                g_report.profit_after_loss,
                bf_after,
                f"Case {case_idx}: Profit after loss mismatch! Greedy={g_report.profit_after_loss}, BF={bf_after}",
            )

        self.assertEqual(baseline_mismatches, 0)
        self.assertEqual(resilience_mismatches, 0)
        self.assertEqual(baseline_comparisons, 200)
        self.assertEqual(resilience_comparisons, 200)

    def test_performance_benchmarks(self) -> None:
        """Benchmark baseline scheduling and resilience analysis with n = 200, H = 60."""
        n = 200
        H = 60
        unavailable = [5, 12, 19, 26, 33, 40, 47, 54, 58, 60]
        jobs = [
            (i, ((i * 7) % H) + 1, ((i * 37) % 500) + 10)
            for i in range(1, n + 1)
        ]

        # Warm-up run
        schedule_jobs(n, H, unavailable, jobs)

        # 1. Baseline scheduling benchmark
        start_base = time.perf_counter()
        base_profit, base_schedule, _ = schedule_jobs(n, H, unavailable, jobs)
        base_time = time.perf_counter() - start_base

        # 2. Complete resilience analysis benchmark
        start_res = time.perf_counter()
        report = analyze_resilience(n, H, unavailable, jobs, base_profit)
        res_time = time.perf_counter() - start_res

        # Performance assertions (must be well under 100ms and 500ms respectively)
        self.assertLess(
            base_time,
            0.05,
            f"Baseline scheduling took {base_time*1000:.2f}ms (threshold 50ms)",
        )
        self.assertLess(
            res_time,
            0.5,
            f"Resilience analysis took {res_time*1000:.2f}ms (threshold 500ms)",
        )
        self.assertGreater(base_profit, 0)
        self.assertIsNotNone(report.critical_slot)


def run_all_tests() -> unittest.TestResult:
    """Executes the complete test suite including Phase 5 validation."""
    suite = unittest.TestLoader().loadTestsFromNames([
        "deadline_scheduler.test_cases.TestSchedulerUnit",
        "deadline_scheduler.test_cases.TestResilienceUnit",
        "deadline_scheduler.test_cases.TestMainIntegration",
        "deadline_scheduler.test_cases.TestStressAndConstraints",
        "deadline_scheduler.test_cases.TestBruteForceValidation",
    ])
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    unittest.main()
