# Algorithm Explanation: Deadline Scheduler – Survive a Lost Time Slot

**Course**: Design and Analysis of Algorithms (DAA)  
**Project**: Deadline Scheduler – Survive a Lost Time Slot  
**Registration Number**: 25MVCAIR0112  
**Implementation**: Pure Python 3 (Standard Library Only)  

---

## 1. Introduction and Theoretical Background

The problem addressed by this project is the **Job Sequencing with Deadlines Problem** augmented with **Single-Slot Failure Resilience Analysis**.

### 1.1 The Transversal Matroid Foundation
In algorithm design, job sequencing with unit times and deadlines forms a classic **Matroid** $(S, \mathcal{I})$:
* **Ground Set $S$**: The set of $n$ candidate jobs.
* **Independent Sets $\mathcal{I}$**: Any subset of jobs that can be scheduled such that every job finishes on or before its deadline without two jobs occupying the same time slot.

Because this system satisfies the **Hereditary** and **Exchange Properties** of a matroid, a **Greedy Algorithm** that considers jobs in decreasing order of profit is mathematically guaranteed to find an independent subset with the maximum possible total profit.

---

## 2. Baseline Greedy Scheduling Algorithm

### 2.1 Problem Formulation
We are given:
* A scheduling horizon $H$ representing discrete time slots $\{1, 2, \dots, H\}$.
* An initially unavailable set of slots $B \subseteq \{1, \dots, H\}$ with $|B| = b$.
* $n$ jobs, each defined as $J_i = (\text{job\_ID}_i, \text{deadline}_i, \text{profit}_i)$.
* Duration of each job = $1$ time unit.

### 2.2 Algorithmic Mechanics

#### Step 1: Normalization & Sorting
Jobs are sorted using a multi-level deterministic key:
1. **Primary Sort Key**: **Profit descending** ($-\text{profit}$). Higher-revenue tasks are processed before lower-revenue tasks.
2. **Secondary Sort Key**: **Job ID ascending** ($\text{job\_ID} \uparrow$). If two jobs yield identical profit, the job with the smaller numerical ID is given precedence. String identifiers are compared lexicographically.

#### Step 2: Greedy Backward Allocation
For each job $J_i$ in sorted order:
1. Identify the latest feasible time slot:
   $$\text{latest\_slot} = \min(\text{deadline}_i, H)$$
2. Scan backwards from $\text{latest\_slot}$ down to slot $1$:
   $$\text{for slot } t = \text{latest\_slot}, \text{latest\_slot} - 1, \dots, 1:$$
   * If slot $t \notin B$ and $\text{schedule}[t] == \text{None}$ (free):
     * Allocate job $J_i$ to slot $t$.
     * Add $\text{profit}_i$ to total baseline profit.
     * Terminate the search for this job immediately.
3. **Why search backwards?**
   Allocating a job to its latest possible feasible slot leaves earlier slots open for subsequent jobs that have tighter (earlier) deadlines. Placing a job with deadline 4 into slot 1 would prematurely block a job with deadline 1.

#### Step 3: Rejection Tracking
* If no available slot exists in $[1, \min(\text{deadline}_i, H)]$, the job cannot be scheduled.
* The job is marked as **rejected**.
* At the end of the scheduling pass, all rejected IDs are sorted in ascending numerical order.

---

### 2.3 Baseline Scheduling Pseudocode

```text
================================================================================
Algorithm 1: Baseline Greedy Job Scheduling
================================================================================
INPUT:
    n           : Total number of jobs (Integer >= 0)
    H           : Scheduling horizon length (Integer >= 0)
    unavailable : Set of initially blocked time slots B
    jobs        : List of tuples (job_id, deadline, profit)

OUTPUT:
    total_profit : Sum of profits of scheduled jobs
    schedule     : Array of size H mapping slot t -> job_id (or 0)
    rejected     : Sorted list of unassigned job IDs

PROCEDURE SCHEDULE_JOBS(n, H, unavailable, jobs):
    1. Initialize schedule[1..H] = 0
    2. Define sort_key(j):
           numeric_id = INT(j.id) if IS_DIGIT(j.id) else INFINITY
           return (-j.profit, numeric_id, STRING(j.id))
    3. sorted_jobs = SORT(jobs, key=sort_key)
    4. total_profit = 0
    5. rejected = []

    6. FOR EACH job IN sorted_jobs DO:
           allocated = FALSE
           latest_slot = MIN(job.deadline, H)

           FOR slot = latest_slot DOWNTO 1 DO:
               IF slot NOT IN unavailable AND schedule[slot] == 0 THEN:
                   schedule[slot] = job.id
                   total_profit = total_profit + job.profit
                   allocated = TRUE
                   BREAK
               END IF
           END FOR

           IF NOT allocated THEN:
               APPEND job.id TO rejected
           END IF
       END FOR

    7. SORT rejected in ascending numeric order
    8. RETURN (total_profit, schedule, rejected)
================================================================================
```

---

## 3. End-to-End System Workflow Diagram

```text
               +-------------------------------------------+
               |               Standard Input              |
               |  Line 1: n H b                            |
               |  Line 2: initially unavailable slots      |
               |  Next n lines: job_id deadline profit     |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |               parse_input()               |
               |  - Validates positive integers            |
               |  - Normalizes b=0 blank line handling     |
               |  - Extracts jobs and slot lists           |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |          schedule_jobs() Baseline         |
               |  - Sort: Profit Descending, ID Ascending  |
               |  - Backward search: min(d, H) down to 1   |
               |  - Computes: BASE_PROFIT, BASE_SLOTS,     |
               |              REJECTED list                |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |            analyze_resilience()           |
               |  - Candidate slots = [1..H] \ unavailable |
               |  - FOR each candidate slot s:             |
               |      * new_blocked = unavailable U {s}    |
               |      * new_profit, new_sched =            |
               |            schedule_jobs(new_blocked)     |
               |      * loss = BASE_PROFIT - new_profit    |
               |      * Update max_loss, critical_slot     |
               |        (strictly greater preserves min s) |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |            build_output_lines()           |
               |  Line 1: BASE_PROFIT P                    |
               |  Line 2: BASE_SLOTS s_1 ... s_H           |
               |  Line 3: REJECTED K id_1 ... id_K         |
               |  Line 4: CRITICAL_SLOT T                  |
               |  Line 5: LOSS L                           |
               |  Line 6: AFTER_PROFIT P_after             |
               |  Line 7: AFTER_SLOTS s_1 ... s_H          |
               +-------------------------------------------+
                                     |
                                     v
               +-------------------------------------------+
               |              Standard Output              |
               +-------------------------------------------+
```

---

## 4. Resilience Analysis & Critical Slot Identification

### 4.1 Why Scratch Re-Scheduling is Essential
A common naive approach to slot failure is **local patching**: when slot $s$ is lost, take the job that was in slot $s$ and try to move it to an earlier slot.

**Why local patching fails**:
* If job $A$ in slot $s$ cannot be shifted, discarding job $A$ directly loses its profit.
* However, a previously rejected job $B$ (with deadline later than slot $s$) might now fit into a slot freed up by moving other jobs.
* In combinatorial scheduling, an outage triggers a ripple effect across multiple jobs.
* Re-executing `schedule_jobs()` completely from scratch with the tested slot added to the unavailable set guarantees that the resulting contingency schedule is **provably optimal**.

### 4.2 Candidate Slot Evaluation
1. Only slots that were **originally available** ($s \in \{1, \dots, H\} \setminus B$) can experience a runtime outage.
2. Initially blocked slots ($s \in B$) are skipped because they are already unavailable.
3. For each candidate slot $s$:
   $$\text{Unavailable}_{\text{simulated}} = B \cup \{s\}$$
4. Execute `schedule_jobs(n, H, Unavailable_simulated, jobs)`.
5. Compute the profit loss:
   $$\text{Loss}(s) = \text{Baseline Profit} - \text{Profit}_{\text{simulated}}(s)$$

### 4.3 The Maximum Loss & Smallest Slot Tie-Breaking Rule
* The slot producing the largest profit loss is the critical slot:
  $$\text{Critical Slot} = \arg\max_{s} \text{Loss}(s)$$
* **Tie-Breaking Rule**: When two or more slots produce the exact same maximum loss, the specification mandates selecting the **smallest slot number**:
  $$\text{Critical Slot} = \min \{ s \mid \text{Loss}(s) = \max_j \text{Loss}(j) \}$$
* **Implementation Technique**:
  By iterating through candidate slots in strictly increasing numerical order ($s = 1, 2, \dots, H$) and updating the critical slot only when:
  $$\text{loss} > \text{max\_loss} \quad (\text{strictly greater than})$$
  an existing critical slot candidate with a smaller index is never overwritten by a subsequent slot that merely ties the current maximum.

### 4.4 Boundary Condition: All Slots Unavailable ($b = H$)
If every slot in the horizon is initially blocked, no operational slot exists to fail. In this case:
* Candidate slots list is empty.
* $\text{Critical Slot} = 0$.
* $\text{Loss} = 0$.
* $\text{After Profit} = 0$.
* $\text{After Slots} = [0, 0, \dots, 0]$.

---

### 4.5 Resilience Analysis Pseudocode

```text
================================================================================
Algorithm 2: Counterfactual Resilience Analysis
================================================================================
INPUT:
    n               : Number of jobs
    H               : Scheduling horizon
    unavailable     : Set of initially unavailable slots B
    jobs            : List of job tuples
    baseline_profit : (Optional) Maximum baseline profit

OUTPUT:
    critical_slot   : Slot index whose loss causes maximum profit reduction
    max_loss        : Magnitude of the maximum loss
    profit_after    : Profit achievable after losing critical slot
    schedule_after  : Fallback schedule after losing critical slot

PROCEDURE ANALYZE_RESILIENCE(n, H, unavailable, jobs, baseline_profit):
    1. IF baseline_profit IS NULL THEN:
           (baseline_profit, _, _) = SCHEDULE_JOBS(n, H, unavailable, jobs)
       END IF

    2. available_slots = [s FOR s = 1 TO H IF s NOT IN unavailable]

    # Handle boundary case: no available slots in horizon
    3. IF available_slots IS EMPTY THEN:
           RETURN (critical_slot=0, max_loss=0, profit_after=baseline_profit,
                   schedule_after=[0]*H)
       END IF

    4. max_loss = -INFINITY
    5. critical_slot = 0
    6. profit_after = 0
    7. schedule_after = [0]*H

    # Evaluate candidate slots in strictly ascending order
    8. FOR EACH slot IN available_slots DO:
           simulated_unavailable = unavailable U {slot}
           (new_profit, new_sched, _) = SCHEDULE_JOBS(n, H, simulated_unavailable, jobs)
           loss = baseline_profit - new_profit

           # Strictly greater preserves the smallest slot on ties
           IF loss > max_loss THEN:
               max_loss = loss
               critical_slot = slot
               profit_after = new_profit
               schedule_after = new_sched
           END IF
       END FOR

    9. RETURN (critical_slot, max_loss, profit_after, schedule_after)
================================================================================
```

---

## 5. Step-by-Step Walkthrough with Sample Input

### 5.1 Input Data (`demo_input.txt`)
```text
5 5 1
3
101 2 100
102 1 50
103 3 80
104 2 120
105 4 60
```

* $n = 5$ jobs, $H = 5$ horizon, $b = 1$ unavailable slot.
* Line 2 indicates that **Slot 3** is initially blocked.
* Available slots initially: $\{1, 2, 4, 5\}$.

---

### 5.2 Baseline Scheduling Execution Trace

#### Step 1: Sort Jobs by Profit (Descending)
1. **Job 104**: Profit = 120, Deadline = 2
2. **Job 101**: Profit = 100, Deadline = 2
3. **Job 103**: Profit = 80, Deadline = 3
4. **Job 105**: Profit = 60, Deadline = 4
5. **Job 102**: Profit = 50, Deadline = 1

#### Step 2: Backward Allocation Trace

| Job Processed | Deadline | Profit | Slots Checked | Outcome & State | Schedule Map $[S_1, S_2, S_3, S_4, S_5]$ |
|:---:|:---:|:---:|:---:|:---|:---:|
| **Job 104** | 2 | 120 | Slot 2 (Free) | **Assigned to Slot 2** | `[0, 104, X, 0, 0]` |
| **Job 101** | 2 | 100 | Slot 2 (Taken) $\rightarrow$ Slot 1 (Free) | **Assigned to Slot 1** | `[101, 104, X, 0, 0]` |
| **Job 103** | 3 | 80 | Slot 3 (Blocked) $\rightarrow$ Slot 2 (Taken) $\rightarrow$ Slot 1 (Taken) | **Rejected** (No free slot) | `[101, 104, X, 0, 0]` |
| **Job 105** | 4 | 60 | Slot 4 (Free) | **Assigned to Slot 4** | `[101, 104, X, 105, 0]` |
| **Job 102** | 1 | 50 | Slot 1 (Taken) | **Rejected** (No free slot) | `[101, 104, X, 105, 0]` |

*(Note: `X` represents blocked Slot 3).*

#### Baseline Summary:
* Total Baseline Profit: $120 + 100 + 60 = \mathbf{280}$.
* Baseline Schedule: `Slot 1: 101`, `Slot 2: 104`, `Slot 3: 0`, `Slot 4: 105`, `Slot 5: 0`.
* Rejected Jobs: 2 jobs (`102`, `103`).

---

### 5.3 Resilience Analysis Execution Trace

Candidate slots to simulate: $\{1, 2, 4, 5\}$ (Slot 3 is skipped).

#### Simulation 1: Test Losing Slot 1
* Blocked slots: $\{3, 1\}$. Available slots: $\{2, 4, 5\}$.
* Job 104 ($d=2, P=120$): Gets Slot 2.
* Job 101 ($d=2, P=100$): Slot 2 taken, Slot 1 blocked $\rightarrow$ Rejected.
* Job 103 ($d=3, P=80$): Slot 3 blocked, Slot 2 taken, Slot 1 blocked $\rightarrow$ Rejected.
* Job 105 ($d=4, P=60$): Gets Slot 4.
* Job 102 ($d=1, P=50$): Slot 1 blocked $\rightarrow$ Rejected.
* **Profit after loss**: $120 + 60 = 180$.
* **Profit Loss**: $280 - 180 = \mathbf{100}$.
* **Schedule**: `[0, 104, 0, 105, 0]`.

#### Simulation 2: Test Losing Slot 2
* Blocked slots: $\{3, 2\}$. Available slots: $\{1, 4, 5\}$.
* Job 104 ($d=2, P=120$): Slot 2 blocked, gets Slot 1.
* Job 101 ($d=2, P=100$): Slot 2 blocked, Slot 1 taken $\rightarrow$ Rejected.
* Job 103 ($d=3, P=80$): Slot 3 blocked, Slot 2 blocked, Slot 1 taken $\rightarrow$ Rejected.
* Job 105 ($d=4, P=60$): Gets Slot 4.
* Job 102 ($d=1, P=50$): Slot 1 taken $\rightarrow$ Rejected.
* **Profit after loss**: $120 + 60 = 180$.
* **Profit Loss**: $280 - 180 = \mathbf{100}$.
* **Schedule**: `[104, 0, 0, 105, 0]`.

#### Simulation 3: Test Losing Slot 4
* Blocked slots: $\{3, 4\}$. Available slots: $\{1, 2, 5\}$.
* Job 104 gets Slot 2; Job 101 gets Slot 1.
* Jobs 103, 105, and 102 cannot find an available slot $\rightarrow$ Rejected.
* **Profit after loss**: $120 + 100 = 220$.
* **Profit Loss**: $280 - 220 = \mathbf{60}$.

#### Simulation 4: Test Losing Slot 5
* Blocked slots: $\{3, 5\}$. Available slots: $\{1, 2, 4\}$.
* Job 104 gets Slot 2; Job 101 gets Slot 1; Job 105 gets Slot 4.
* **Profit after loss**: $120 + 100 + 60 = 280$.
* **Profit Loss**: $280 - 280 = \mathbf{0}$ (Slot 5 was unused).

---

### 5.4 Resolving the Critical Slot Tie

| Candidate Slot | Blocked Set | Recomputed Profit | Profit Loss ($280 - P'$) | Evaluation |
|:---:|:---:|:---:|:---:|:---|
| **Slot 1** | $\{3, 1\}$ | **180** | **100** | Maximum Loss Candidate |
| **Slot 2** | $\{3, 2\}$ | **180** | **100** | Maximum Loss Candidate (Tied) |
| **Slot 4** | $\{3, 4\}$ | **220** | **60** | Suboptimal Loss |
| **Slot 5** | $\{3, 5\}$ | **280** | **0** | Idle Slot (Zero Loss) |

* **Tie-Breaking Rule Application**:
  Both Slot 1 and Slot 2 cause the maximum loss of 100.
  $$\text{Critical Slot} = \min(1, 2) = \mathbf{1}$$
* Resulting output values:
  * `CRITICAL_SLOT 1`
  * `LOSS 100`
  * `AFTER_PROFIT 180`
  * `AFTER_SLOTS 0 104 0 105 0`

---

## 6. Asymptotic Complexity Analysis

### 6.1 Baseline Scheduling Complexity
* **Job Sorting**: Sorting $n$ jobs by profit and ID takes $O(n \log n)$ time.
* **Backward Slot Search**: For each job, the backward scan checks at most $H$ slots. Across $n$ jobs, this requires $O(n \cdot H)$ steps.
* **Sorting Rejected Jobs**: Sorting at most $n$ rejected IDs takes $O(k \log k) \le O(n \log n)$.
* **Total Time Complexity**:
  $$T_{\text{baseline}}(n, H) = O(n \log n + n \cdot H)$$
* **Space Complexity**:
  $$S_{\text{baseline}}(n, H) = O(n + H)$$
  Requires $O(H)$ storage for the schedule map and $O(n)$ for job data.

### 6.2 Resilience Analysis Complexity
* **Outer Loop**: Evaluates at most $H$ available candidate slots.
* **Inner Re-scheduling**: For each candidate slot, `schedule_jobs()` is executed from scratch: $O(n \log n + n \cdot H)$.
* **Total Time Complexity**:
  $$T_{\text{resilience}}(n, H) = O(H \cdot (n \log n + n \cdot H))$$
* **Space Complexity**:
  $$S_{\text{resilience}}(n, H) = O(n + H)$$
  Memory is reused across iterations.

---

## 7. Summary of Algorithmic Invariants

1. **Feasibility Invariant**: Every scheduled job $J_i$ placed in slot $t$ satisfies $1 \le t \le \min(\text{deadline}_i, H)$.
2. **Mutual Exclusion Invariant**: No two jobs are ever assigned to the same time slot ($|\text{jobs}(t)| \le 1$).
3. **Availability Invariant**: No job is ever placed in an initially unavailable slot or a simulated failed slot ($t \notin B$).
4. **Matroid Optimality Invariant**: The total profit achieved by greedy backward allocation equals the global combinatorial maximum.
5. **Deterministic Invariant**: All ties (both profit ties and loss ties) are resolved deterministically, guaranteeing reproducible results across runs.
