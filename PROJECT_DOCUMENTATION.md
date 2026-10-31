# Project Documentation: Deadline Scheduler – Survive a Lost Time Slot

**Course / Subject**: Design and Analysis of Algorithms (DAA)  
**Project Category**: Internal Hackathon / Algorithmic Optimization  
**Registration Number**: 25MVCAIR0112  
**Implementation**: Python 3.8+ (Zero External Dependencies)  

---

## 1. Project Title

**Deadline Scheduler – Survive a Lost Time Slot**  
*An Optimal Greedy Job Scheduling Engine with Counterfactual Single-Slot Failure Resilience Analysis.*

---

## 2. Project Overview

In computational scheduling, batch processing, and logistics, tasks frequently arrive with strict deadlines and financial rewards. If a job is executed on or before its deadline, a profit is earned; otherwise, the job expires and yields nothing. Modern computer systems, however, operate in unpredictable environments: server maintenance windows, hardware faults, spot-instance revocations, or network outages can suddenly make an operational time slot unavailable.

The **Deadline Scheduler** project addresses this challenge:
1. It produces an **optimal baseline schedule** using a Greedy Job Sequencing algorithm that maximizes total earned profit while respecting unit-time execution constraints, discrete deadlines, and pre-existing unavailable slots.
2. It proactively performs **Resilience Analysis** to evaluate system vulnerability before an outage strikes. By simulating the unexpected failure of every originally available time slot, the engine discovers the single **"Critical Slot"** whose loss causes the highest financial loss, computes the exact revenue loss, and produces an instant fallback schedule.

---

## 3. Problem Statement

### The Scheduling Challenge
We are given:
* A scheduling horizon $H$ representing discrete time slots $\{1, 2, \dots, H\}$.
* A set of $n$ independent unit-length jobs ($J_1, J_2, \dots, J_n$). Each job $i$ has:
  * A unique identifier $\text{job\_ID}_i$.
  * An integer deadline $\text{deadline}_i$ (the job must be placed in a slot $t \le \text{deadline}_i$).
  * A non-negative profit $\text{profit}_i$ awarded if completed on time.
* A list of $b$ initially unavailable slots ($0 \le b \le H$) that cannot host any job.

### The Failure & Resilience Problem
What happens if an operational time slot unexpectedly breaks down or is cancelled?
* If slot $t$ fails, any job assigned to slot $t$ must either move to an earlier free slot, displace lower-profit jobs, or be discarded.
* Simply shifting jobs locally often yields suboptimal schedules.
* The system must determine:
  1. Which available slot is the most dangerous to lose (**Critical Slot**)?
  2. What is the maximum revenue reduction (**Maximum Loss**)?
  3. If the critical slot is lost, what is the best possible recovery schedule (**Contingency Schedule**) and its resulting profit (**After Profit**)?
  4. If multiple slots tie for the worst profit loss, which one should be prioritized? (Resolved by choosing the **smallest slot number**).

---

## 4. Project Objectives

1. **Optimal Profit Maximization**: Implement a greedy algorithm that achieves the theoretical maximum total profit for any valid set of jobs, deadlines, and blocked slots.
2. **Deterministic Tie-Breaking**: Guarantee 100% reproducible schedules by resolving profit ties using the smallest Job ID.
3. **Comprehensive Rejection Tracking**: Accurately detect all rejected jobs and format their IDs in increasing numerical order.
4. **Counterfactual Resilience Simulation**: Simulate the loss of every available slot independently from scratch to identify the true global critical bottleneck.
5. **Smallest-Slot Tie-Breaking on Maximum Loss**: Resolve ties between multiple slots causing equal maximum loss by choosing the smallest slot index.
6. **Boundary & Edge Case Integrity**: Seamlessly handle extreme configurations such as all slots unavailable ($b = H$), no slots unavailable ($b = 0$), empty input, and large problem instances ($n = 200, H = 60$).
7. **Strict Specification Adherence**: Accept input from standard input (`sys.stdin`) and generate exactly the required seven-line output format without third-party dependencies.

---

## 5. Technologies Used

| Category | Technology / Tool | Purpose in Project |
|:---|:---|:---|
| **Programming Language** | Python 3 (Tested on 3.8, 3.10, 3.11) | Core algorithm implementation, CLI engine, and test validation suite |
| **Standard Libraries** | `sys` | Reading standard input (`stdin`) and printing to standard output (`stdout`) |
| | `typing` | Static type hinting (`List`, `Dict`, `Tuple`, `Optional`, `Union`, `Set`, `Any`) |
| | `unittest` | Formal automated test runner with 32 comprehensive test cases |
| | `itertools` & `random` | Exhaustive combinatorial permutations and deterministic brute-force validation |
| | `time` | Microsecond-precision benchmarking of baseline and resilience execution |
| **Version Control** | Git & GitHub | Distributed version control, branch management, and team collaboration |
| **Operating Systems** | Windows (PowerShell & CMD), Linux, macOS | Cross-platform compatibility verified across all platforms |
| **External Dependencies** | **None (Zero pip packages)** | Runs instantly on any standard Python interpreter |

---

## 6. Algorithm Explanation

The scheduling of unit-time jobs with deadlines on a single shared processor is a classic problem in combinatorial optimization known as the **Job Sequencing with Deadlines Problem**. It maps directly to an independent system over a **Transversal Matroid**, meaning a greedy strategy is mathematically guaranteed to find the globally optimal subset of jobs.

### 6.1 Job Sorting Strategy
1. Jobs are sorted in **descending order of profit** ($\text{profit} \downarrow$).
2. When two or more jobs offer the exact same profit, ties are broken deterministically by **ascending Job ID** ($\text{job\_ID} \uparrow$, numeric values compared numerically, string IDs lexicographically).
3. This guarantees that higher-value jobs always receive priority over lower-value jobs.

### 6.2 Greedy Backward Slot Allocation
For each job in sorted order:
1. Compute the latest feasible slot index:
   $$\text{latest\_slot} = \min(\text{deadline}, H)$$
2. Search backward from $\text{latest\_slot}$ down to slot $1$:
   * If slot $t$ is **not** in the unavailable set and is currently **free**, allocate the job to slot $t$ and immediately stop searching.
   * If slot $t$ is occupied or unavailable, check slot $t - 1$.
3. **Why search backward?**
   Placing a job as late as possible before its deadline leaves earlier time slots free for jobs that have tighter, earlier deadlines.

### 6.3 Rejection Identification
* If every slot from $\min(\text{deadline}, H)$ down to $1$ is either occupied or unavailable, the job cannot be accommodated.
* The job is marked as **rejected**.
* At the conclusion of scheduling, all rejected job IDs are sorted in ascending numerical order.

### 6.4 Scheduling Algorithm Pseudocode

```text
Algorithm SCHEDULE_JOBS(n, H, unavailable, jobs):
    Input:
        n           : number of jobs
        H           : scheduling horizon (slots 1 to H)
        unavailable : set of blocked slots
        jobs        : list of (job_id, deadline, profit)
    Output:
        total_profit : total earned profit
        schedule     : array of size H (schedule[t] = job_id or 0)
        rejected     : sorted list of unplaced job IDs

    1. Initialize schedule[1..H] = 0
    2. Sort jobs primarily by profit descending, secondarily by job_id ascending
    3. total_profit = 0
    4. rejected = empty list

    5. FOR EACH job (job_id, deadline, profit) IN sorted jobs DO:
         assigned = FALSE
         latest_slot = MIN(deadline, H)

         FOR slot = latest_slot DOWNTO 1 DO:
             IF slot NOT IN unavailable AND schedule[slot] == 0 THEN:
                 schedule[slot] = job_id
                 total_profit = total_profit + profit
                 assigned = TRUE
                 BREAK
             END IF
         END FOR

         IF assigned == FALSE THEN:
             APPEND job_id TO rejected
         END IF
       END FOR

    6. SORT rejected in ascending numeric order
    7. RETURN (total_profit, schedule, rejected)
```

---

## 7. System Workflow

The end-to-end execution follows a clean, deterministic, multi-stage pipeline:

```text
+-----------------------------------------------------------------------------+
|                                STANDARD INPUT                               |
|        Line 1: n H b  |  Line 2: unavailable slots  |  Lines 3..n+2: jobs   |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                           STAGE 1: INPUT PARSING                            |
|  - Validates positive integers, horizon boundaries, and slot numbers        |
|  - Extracts jobs and handles blank lines when b = 0                         |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                     STAGE 2: BASELINE GREEDY SCHEDULING                     |
|  - Sorts jobs by descending profit & ascending job ID                       |
|  - Allocates feasible jobs backward from min(deadline, H) down to 1         |
|  - Computes BASE_PROFIT, BASE_SLOTS, and REJECTED list                      |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                       STAGE 3: RESILIENCE ANALYSIS                          |
|  - Identifies all originally available slots in [1, H]                      |
|  - FOR EACH candidate slot s:                                               |
|      * Temporarily block slot s: simulated = unavailable U {s}             |
|      * Rebuild complete schedule from scratch via schedule_jobs()           |
|      * Compute Loss(s) = BASE_PROFIT - New_Profit                           |
|  - Find CRITICAL_SLOT = argmax Loss(s), breaking ties with smallest slot s  |
|  - Determine LOSS, AFTER_PROFIT, and AFTER_SLOTS                            |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                       STAGE 4: OUTPUT FORMATTING                            |
|  - Generates the exact required 7 lines (0 convention for empty/blocked)    |
|  - Prints report to standard output (stdout)                                |
+-----------------------------------------------------------------------------+
```

---

## 8. Resilience Analysis

Resilience analysis evaluates the structural stability of the scheduling system under single-slot resource failures.

### 8.1 Candidate Slot Identification
Only slots that were **originally available** ($s \in \{1, \dots, H\} \setminus \text{unavailable}$) can experience an unexpected failure. Slots that were already marked as unavailable ($b$) are skipped because they are already out of service.

### 8.2 Independent Scratch Re-Scheduling
When an operational slot $s$ is lost, the system does not simply attempt to shift the job that was in slot $s$. A localized heuristic can lead to suboptimal decisions because:
* A previously rejected high-profit job might now fit into an earlier slot vacated by a reassigned job.
* Cascading deadline shifts might unlock higher overall profit.

Therefore, for each available slot $s$, the system creates an augmented unavailable set:
$$\text{Unavailable}_{\text{simulated}} = \text{Unavailable}_{\text{initial}} \cup \{s\}$$
and re-computes the entire schedule **completely from scratch** using the greedy algorithm.

### 8.3 Profit Loss Calculation
The financial impact of losing slot $s$ is:
$$\text{Loss}(s) = \text{Baseline Profit} - \text{Profit}_{\text{simulated}}(s)$$

### 8.4 Critical Slot Identification & Tie-Breaking
The **Critical Slot** is the candidate slot that inflicts the greatest damage:
$$\text{Critical Slot} = \arg\max_{s} \text{Loss}(s)$$

**The Tie-Breaking Rule**:
If multiple slots produce the identical maximum loss:
$$\text{Loss}(s_1) = \text{Loss}(s_2) = \dots = \text{Max Loss}$$
The algorithm deterministically selects the **smallest slot number** ($\min(s_1, s_2, \dots)$). This is achieved cleanly in code by scanning slots in increasing order ($1 \dots H$) and updating the critical slot only when a candidate strictly exceeds the current maximum (`loss > max_loss`).

### 8.5 All-Unavailable Boundary ($b = H$)
If every slot from $1$ to $H$ was already unavailable at the start, no operational slot can be lost. In accordance with problem conventions:
* $\text{Critical Slot} = 0$
* $\text{Loss} = 0$
* $\text{After Profit} = \text{Baseline Profit} = 0$
* $\text{After Slots} = [0, 0, \dots, 0]$

### 8.6 Resilience Analysis Pseudocode

```text
Algorithm ANALYZE_RESILIENCE(n, H, unavailable, jobs, baseline_profit):
    Input:
        n               : number of jobs
        H               : scheduling horizon
        unavailable     : initially unavailable slots set
        jobs            : list of jobs
        baseline_profit : profit from baseline schedule
    Output:
        critical_slot   : slot causing highest loss (or 0)
        max_loss        : maximum profit reduction
        after_profit    : profit after losing critical slot
        after_schedule  : schedule after losing critical slot

    1. available_slots = [s for s in 1..H if s NOT IN unavailable]
    2. IF available_slots is EMPTY THEN:
           RETURN (critical_slot=0, max_loss=0, after_profit=0, after_schedule=[0]*H)
       END IF

    3. max_loss = -1
    4. critical_slot = 0
    5. after_profit = baseline_profit
    6. after_schedule = empty array of size H

    7. FOR EACH slot IN available_slots (in ascending order 1..H) DO:
           simulated_unavail = unavailable U {slot}
           (new_profit, new_sched, _) = SCHEDULE_JOBS(n, H, simulated_unavail, jobs)
           loss = baseline_profit - new_profit

           # Strictly greater preserves the smallest slot number on ties
           IF loss > max_loss THEN:
               max_loss = loss
               critical_slot = slot
               after_profit = new_profit
               after_schedule = new_sched
           END IF
       END FOR

    8. RETURN (critical_slot, max_loss, after_profit, after_schedule)
```

---

## 9. Example Execution & Step-by-Step Trace

### 9.1 Sample Input (`demo_input.txt`)
```text
5 5 1
3
101 2 100
102 1 50
103 3 80
104 2 120
105 4 60
```

### 9.2 Interpretation of Input Data
* $n = 5$ jobs, $H = 5$ time slots, $b = 1$ unavailable slot.
* Line 2 indicates that **Slot 3** is initially unavailable.
* Available slots initially: $\{1, 2, 4, 5\}$.
* Job table:

| Job ID | Deadline | Profit | Feasible Time Slots |
|:---:|:---:|:---:|:---|
| **101** | 2 | 100 | Slots 1, 2 |
| **102** | 1 | 50 | Slot 1 |
| **103** | 3 | 80 | Slots 1, 2 (Slot 3 is blocked) |
| **104** | 2 | 120 | Slots 1, 2 |
| **105** | 4 | 60 | Slots 1, 2, 4 (Slot 3 is blocked) |

---

### 9.3 Baseline Scheduling Trace

1. **Sort Jobs by Profit (Descending)**:
   * 1st: Job 104 (Profit 120, Deadline 2)
   * 2nd: Job 101 (Profit 100, Deadline 2)
   * 3rd: Job 103 (Profit 80, Deadline 3)
   * 4th: Job 105 (Profit 60, Deadline 4)
   * 5th: Job 102 (Profit 50, Deadline 1)

2. **Step-by-Step Allocation**:
   * **Job 104** ($d=2, P=120$): Checks slot 2 $\rightarrow$ Free! $\rightarrow$ **Placed in Slot 2**.
   * **Job 101** ($d=2, P=100$): Checks slot 2 (taken), checks slot 1 $\rightarrow$ Free! $\rightarrow$ **Placed in Slot 1**.
   * **Job 103** ($d=3, P=80$): Checks slot 3 (blocked), slot 2 (taken by 104), slot 1 (taken by 101) $\rightarrow$ No free slot $\rightarrow$ **Rejected**.
   * **Job 105** ($d=4, P=60$): Checks slot 4 $\rightarrow$ Free! $\rightarrow$ **Placed in Slot 4**.
   * **Job 102** ($d=1, P=50$): Checks slot 1 (taken by 101) $\rightarrow$ No free slot $\rightarrow$ **Rejected**.

3. **Baseline Result**:
   * Slots: `Slot 1: 101`, `Slot 2: 104`, `Slot 3: 0 (blocked)`, `Slot 4: 105`, `Slot 5: 0 (unused)`.
   * Total Profit: $100 + 120 + 60 = \mathbf{280}$.
   * Rejected Jobs: 2 jobs (`102`, `103`).

---

### 9.4 Resilience Analysis Trace

Candidate slots to test: $\{1, 2, 4, 5\}$. Slot 3 is already unavailable, so it is skipped.

| Candidate Slot Lost | Blocked Slots | Recomputed Schedule | Recomputed Profit | Profit Loss ($280 - P'$) |
|:---:|:---:|:---:|:---:|:---:|
| **Slot 1** | $\{3, 1\}$ | `[0, 104, 0, 105, 0]` | 180 | **100** |
| **Slot 2** | $\{3, 2\}$ | `[104, 0, 0, 105, 0]` | 180 | **100** |
| **Slot 4** | $\{3, 4\}$ | `[101, 104, 0, 0, 0]` | 220 | 60 |
| **Slot 5** | $\{3, 5\}$ | `[101, 104, 0, 105, 0]` | 280 | 0 |

**Critical Decision Points**:
1. Losing **Slot 1** causes Job 101 to be lost $\rightarrow$ Profit drops to $180$ ($\text{Loss} = 100$).
2. Losing **Slot 2** forces Job 104 into Slot 1, displacing Job 101 $\rightarrow$ Profit drops to $180$ ($\text{Loss} = 100$).
3. Both Slot 1 and Slot 2 cause the **maximum loss of 100**.
4. By the tie-breaking rule, we select the **smallest slot number**: $\min(1, 2) = \mathbf{1}$.
5. Resulting schedule after losing critical slot 1: `[0, 104, 0, 105, 0]`.

---

### 9.5 Exact Output Format

```text
BASE_PROFIT 280
BASE_SLOTS 101 104 0 105 0
REJECTED 2 102 103
CRITICAL_SLOT 1
LOSS 100
AFTER_PROFIT 180
AFTER_SLOTS 0 104 0 105 0
```

#### Meaning of Each Output Line:
* `BASE_PROFIT 280`: The maximum profit achievable under initial conditions.
* `BASE_SLOTS 101 104 0 105 0`: The job assigned to each slot from 1 to 5 ($0$ for blocked or unused).
* `REJECTED 2 102 103`: Exactly 2 jobs could not be scheduled, listed in ascending order (`102`, `103`).
* `CRITICAL_SLOT 1`: Slot 1 is the most vulnerable slot in the system.
* `LOSS 100`: Losing Slot 1 reduces total profit by 100 units.
* `AFTER_PROFIT 180`: The fallback profit achievable if Slot 1 fails ($280 - 100 = 180$).
* `AFTER_SLOTS 0 104 0 105 0`: The contingency schedule to deploy immediately if Slot 1 fails.

---

## 10. System Architecture

The project is structured with a modular, layered architecture ensuring separation of concerns:

```text
daa-internal-hackthon/
├── README.md                           # Main repository documentation & guide
├── DEMO_GUIDE.md                       # Presentation script & terminal commands
├── PROJECT_DOCUMENTATION.md            # Comprehensive technical & academic report
├── demo_input.txt                      # Verified demonstration test input
├── 25MVCAIR0112_code.py                # Standalone submission file (All-in-One)
├── CODE.py                             # Secondary single-file script
├── Deadline_Scheduler_Source_Code.zip  # Packaged submission archive
└── deadline_scheduler/                 # Modular Python Package
    ├── __init__.py                     # Package export declarations
    ├── scheduler.py                    # Phase 1: Core Greedy Job Sequencing
    ├── resilience.py                   # Phase 2: Single-Slot Failure Resilience Analysis
    ├── main.py                         # Phase 3: Stdin Parsing & 7-Line Output Engine
    └── test_cases.py                   # Phase 4 & 5: Automated 32-Test Validation Suite
```

### Module Responsibilities & Interactions

| File / Module | Responsibility | Key Exported Functions / Classes |
|:---|:---|:---|
| `scheduler.py` | Implements greedy job sequencing, sorting, backward allocation, and rejection tracking. | `schedule_jobs(n, H, unavailable, jobs)` |
| `resilience.py` | Iterates over available slots, executes scratch re-scheduling, computes profit loss, and applies tie-breaking. | `analyze_resilience(...)`, `ResilienceReport` |
| `main.py` | Reads and validates standard input, orchestrates scheduling and resilience calls, formats the 7-line output. | `parse_input()`, `format_num()`, `build_output_lines()`, `main()` |
| `test_cases.py` | Houses 32 automated unit tests, functional scenarios, randomized brute-force validation, and benchmarks. | `TestSchedulerUnit`, `TestResilienceUnit`, `TestMainIntegration`, `TestStressAndConstraints`, `TestBruteForceValidation` |
| `25MVCAIR0112_code.py` | Standalone single-file submission merging `main.py`, `scheduler.py`, and `resilience.py` for direct evaluation. | All core functions unified without dependencies |

---

## 11. Testing and Validation

The implementation is verified by an exhaustive 32-test automated test suite implemented in Python's standard `unittest` framework.

### 11.1 Test Suite Categories

1. **Core Scheduling Scenarios (Scenarios 1 to 10, 13)**:
   * Normal scheduling with initially blocked slots.
   * Boundary condition: Zero unavailable slots ($b = 0$).
   * Boundary condition: All slots unavailable ($b = H$).
   * Zero rejected jobs ($K = 0$).
   * All jobs rejected due to pre-deadline slot contention.
   * Equal-profit tie breaking (smaller Job ID wins).
   * Multiple jobs sharing identical deadlines cascading backward.
   * Slot 1 contention (multiple jobs with deadline 1).
   * Full horizon jobs (deadline = $H$).
   * Schedules with idle/unused intermediate slots.
   * Single-job boundary conditions.

2. **Resilience & Tie-Breaking Scenarios (Scenarios 1, 3, 11, 12)**:
   * Multi-slot maximum loss tie breaking (choosing smallest slot number).
   * Resilience under $b = H$ yielding critical slot 0 and loss 0.
   * Loss of an idle/unused slot causing 0 loss.
   * Verification that each simulation rebuilds independently from scratch.

3. **End-to-End & I/O Scenarios**:
   * Standard sample case matching specification.
   * Handling $b = 0$ with blank line vs omitted blank line.
   * Input format validation and error raising for invalid inputs.

4. **Stress & Boundary Constraints (Scenario 14)**:
   * Boundary: $n = 0$ jobs with $H = 5$.
   * Stress test: Maximum hackathon constraints ($n = 200$ jobs, $H = 60$ slots).
   * Numerical stability under large profit magnitudes ($10^9+$).

5. **Exhaustive Brute-Force Combinatorial Validation**:
   * Evaluated **200 deterministic randomized instances** (`seed=42`) using combinatorial permutations ($O(n!)$ search space).
   * **Baseline Optimality**: 200 / 200 matches with global brute-force optimum (**0 mismatches**).
   * **Resilience Accuracy**: 200 / 200 matches with brute-force counterfactuals (**0 mismatches**).

### 11.2 Actual Test Execution Output

```text
$ python -m unittest deadline_scheduler.test_cases -v
test_200_deterministic_random_cases_greedy_vs_brute_force ... ok
test_brute_force_sample_case_matches_greedy ... ok
test_performance_benchmarks ... ok
test_build_output_lines_all_unavailable_convention ... ok
test_build_output_lines_sample_case ... ok
test_build_output_lines_zero_rejected ... ok
test_e2e_full_application_b_zero ... ok
test_e2e_full_application_sample ... ok
test_parse_input_b_zero_with_blank_line ... ok
test_parse_input_standard ... ok
test_parse_input_validation_errors ... ok
test_resilience_independent_scratch_rebuild ... ok
test_resilience_report_accessors ... ok
test_scenario_01_and_11_sample_resilience_and_tie_breaking ... ok
test_scenario_03_resilience_all_slots_unavailable ... ok
test_scenario_11_explicit_equal_loss_tie_break ... ok
test_scenario_12_loss_of_unused_slot ... ok
test_job_dict_input_compatibility ... ok
test_scenario_01_normal_scheduling_with_unavailable_slots ... ok
test_scenario_02_no_unavailable_slots ... ok
test_scenario_03_all_slots_unavailable ... ok
test_scenario_04_no_rejected_jobs ... ok
test_scenario_05_all_jobs_rejected ... ok
test_scenario_06_equal_profit_tie_breaking ... ok
test_scenario_07_multiple_jobs_same_deadline ... ok
test_scenario_08_jobs_with_deadline_one ... ok
test_scenario_09_jobs_with_deadline_H ... ok
test_scenario_10_unused_time_slots ... ok
test_scenario_13_single_job_scheduling ... ok
test_boundary_zero_jobs ... ok
test_large_profit_values ... ok
test_scenario_14_maximum_constraints_stress ... ok

----------------------------------------------------------------------
Ran 32 tests in 0.091s

OK
```

### 11.3 Performance Benchmark Results

Measured on maximum constraints ($n = 200, H = 60$, 10 unavailable slots):

| Stage | Measured Runtime | Hackathon Limit | Margin of Safety |
|:---|:---:|:---:|:---:|
| **Baseline Greedy Scheduling** | **~0.57 ms** | $< 50 \text{ ms}$ | **~87x faster** |
| **Complete Resilience Analysis** | **~24.64 ms** | $< 500 \text{ ms}$ | **~20x faster** |
| **Total End-to-End Application** | **~25.21 ms** | $< 1000 \text{ ms}$ | **~40x faster** |

---

## 12. Time and Space Complexity

### 12.1 Baseline Greedy Scheduling (`schedule_jobs`)

* **Time Complexity**: $O(n \log n + n \cdot H)$
  1. **Job Sorting**: Sorting $n$ jobs by profit and ID takes $O(n \log n)$ time using Python's Timsort.
  2. **Backward Allocation**: For each of the $n$ jobs, we search backward from $\min(\text{deadline}, H)$ down to 1. In the worst case, this inspects at most $H$ slots. For $n$ jobs, this requires $O(n \cdot H)$ operations.
  3. **Sorting Rejected Jobs**: At most $n$ jobs are rejected. Sorting them takes $O(k \log k) \le O(n \log n)$ time.
  4. **Total Time**: $O(n \log n + n \cdot H)$.

* **Space Complexity**: $O(n + H)$
  * $O(H)$ memory to maintain the schedule mapping of slots $1 \dots H$.
  * $O(n)$ memory to store the parsed jobs and the rejected job IDs list.

---

### 12.2 Resilience Analysis (`analyze_resilience`)

* **Time Complexity**: $O(H \cdot (n \log n + n \cdot H))$
  1. **Candidate Loop**: Evaluates at most $H$ originally available slots.
  2. **Scratch Re-Scheduling**: For each candidate slot, `schedule_jobs()` is invoked from scratch, taking $O(n \log n + n \cdot H)$ time.
  3. **Total Time**: At most $H$ iterations $\times O(n \log n + n \cdot H) = O(H \cdot (n \log n + n \cdot H))$.
  4. Under maximum constraints ($n = 200, H = 60$):
     $$\text{Operations} \approx 60 \times (200 \log_2 200 + 200 \times 60) \approx 60 \times (1,530 + 12,000) \approx 8.1 \times 10^5 \text{ ops}$$
     This requires only ~25 milliseconds on modern CPU architectures.

* **Space Complexity**: $O(n + H)$
  * Reuses auxiliary storage of $O(n + H)$ across iterations for simulated unavailable sets and schedule dictionaries.

---

## 13. Advantages and Real-World Applications

### 13.1 Key Advantages
1. **Mathematical Optimality**: Leverages matroid theory to guarantee that no alternative assignment yields a higher baseline profit.
2. **Proactive Outage Defense**: Instead of panicking during runtime failures, the system pre-computes the contingency schedule in advance.
3. **Deterministic & Repeatable**: Zero randomness or heuristic instability. Same input always yields the exact same schedule and tie-breaks.
4. **Lightweight & Portable**: Zero pip dependencies. Runs on embedded devices, cloud servers, or basic developer environments.

### 13.2 Real-World Applications

```text
+-----------------------+-------------------------------------------------------+
| Domain                | Practical Real-World Use Case                         |
+-----------------------+-------------------------------------------------------+
| Cloud Computing       | Serverless batch scheduling where spot instances are  |
|                       | subject to unexpected revocation with 2-minute notice.|
+-----------------------+-------------------------------------------------------+
| Satellite Downlinks   | LEO satellites with fixed orbital ground-station passes|
|                       | where weather causes sudden lost transmission slots.  |
+-----------------------+-------------------------------------------------------+
| JIT Manufacturing     | Robotic automated assembly lines where planned machine|
|                       | maintenance or sudden tool failure blocks work hours. |
+-----------------------+-------------------------------------------------------+
| Financial Clearing    | Real-time settlement systems (RTGS) where high-value  |
|                       | transactions must clear before end-of-day bank cutoffs|
+-----------------------+-------------------------------------------------------+
| Medical Surgery Rooms | Hospital operating theatre scheduling where urgent    |
|                       | emergency surgeries displace scheduled procedures.    |
+-----------------------+-------------------------------------------------------+
```

---

## 14. Limitations and Future Enhancements

### 14.1 Current Limitations
1. **Unit Job Duration**: Assumes all jobs take exactly 1 unit of time. Real-world tasks may require variable durations ($p_i > 1$).
2. **Single-Processor Model**: Designed for a single shared execution resource; does not currently model multi-core or distributed parallel servers ($m > 1$).
3. **Single-Slot Failure Model**: Analyzes the independent failure of 1 slot at a time; simultaneous multi-slot outages are not simulated.
4. **Non-Preemptive Execution**: Once a slot starts, it cannot be interrupted or split.

### 14.2 Future Enhancements
1. **Variable Processing Times**: Extend the greedy framework using Interval Scheduling or Dynamic Programming to handle jobs with arbitrary processing times $p_i$.
2. **Multi-Processor Parallel Schedulers**: Extend the transversal matroid structure to $m$ identical or heterogeneous processors ($P_1, P_2, \dots, P_m$).
3. **Disjoint Multi-Slot Failures ($k$-Resilience)**: Simulate combinatorial simultaneous losses of $k \ge 2$ time slots to assess catastrophic outage scenarios.
4. **Interactive Dashboard**: Build a lightweight web-based Gantt-chart visualizer to graphically depict schedule changes before and after slot failure.

---

## 15. Conclusion

The **Deadline Scheduler – Survive a Lost Time Slot** project successfully delivers a mathematically rigorous, fault-tolerant scheduling system for unit-time jobs with deadlines. By uniting **Greedy Job Sequencing** with **Counterfactual Resilience Analysis**, the project achieves two vital industrial goals: maximizing revenue during normal operations and safeguarding business continuity during unexpected disruptions.

The implementation passes all 32 automated tests with 100% agreement against combinatorial brute-force benchmarks, executes in approximately 25 milliseconds under maximum constraints, and strictly adheres to the hackathon's input/output standards. It stands ready for academic evaluation and live demonstration.
