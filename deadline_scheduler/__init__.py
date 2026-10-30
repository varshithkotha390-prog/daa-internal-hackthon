"""Deadline Scheduler - Greedy Job Sequencing and Resilience Analysis Package."""

try:
    from deadline_scheduler.scheduler import schedule_jobs
    from deadline_scheduler.resilience import analyze_resilience, ResilienceReport
except ImportError:
    from scheduler import schedule_jobs
    from resilience import analyze_resilience, ResilienceReport

__all__ = [
    "schedule_jobs",
    "analyze_resilience",
    "ResilienceReport",
]
