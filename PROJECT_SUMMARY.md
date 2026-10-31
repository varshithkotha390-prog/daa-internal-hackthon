# Project Summary: Deadline Scheduler – Survive a Lost Time Slot

**Course**: Design and Analysis of Algorithms (DAA)  
**Event**: DAA Internal Hackathon  
**Registration Number**: 25MVCAIR0112  
**Implementation**: Python 3.8+ (Zero External Dependencies)  

---

### 1. Project Overview
The **Deadline Scheduler** is a fault-tolerant job sequencing engine designed to optimize batch processing in environments vulnerable to resource outages. In systems such as cloud computing, satellite downlinks, robotic manufacturing, and financial clearing, unit-length jobs have strict deadlines and non-negative profits. This project delivers an optimal scheduling engine that produces the maximum possible profit and proactively simulates single-slot infrastructure failures to discover system bottlenecks before disruptions occur.

---

### 2. Problem Statement
Given $n$ unit-duration jobs, a discrete scheduling horizon $H$ (slots $1 \dots H$), and $b$ initially blocked slots ($0 \le b \le H$), each job offers profit $p_i$ if completed on or before deadline $d_i$.
1. **Baseline Scheduling**: Select and assign an optimal subset of jobs to available slots $t \in [1, \min(d_i, H)]$ to maximize total revenue.
2. **Resilience Challenge**: If an active time slot unexpectedly fails during execution, which slot causes the worst-case profit drop (**Critical Slot**), what is the maximum financial loss (**Maximum Loss**), and what is the optimal contingency plan (**After Profit & After Slots**)?

---

### 3. Key Objectives
* **Optimality**: Maximize earned revenue by allocating high-profit jobs first using Matroid Theory.
* **Deterministic Tie-Breaking**: Guarantee 100% reproducible schedules (break profit ties by ascending Job ID).
* **Counterfactual Resilience**: Simulate the loss of every operational slot independently from scratch to guarantee global contingency optimality.
* **Smallest-Slot Tie-Breaking**: When multiple slots cause identical worst-case losses, select the smallest slot index.
* **Boundary Resilience**: Seamlessly handle $b = 0$, $b = H$, all jobs rejected, and stress loads ($n = 200, H = 60$).

---

### 4. Algorithms & Complexity

| Algorithm Phase | Technique | Time Complexity | Space Complexity |
|:---|:---|:---:|:---:|
| **Baseline Scheduling** | Greedy Backward Slot Allocation | $O(n \log n + n \cdot H)$ | $O(n + H)$ |
| **Resilience Analysis** | Independent Scratch Re-scheduling | $O(H \cdot (n \log n + n \cdot H))$ | $O(n + H)$ |
| **End-to-End Pipeline** | Stdin Parsing $\rightarrow$ Schedule $\rightarrow$ Resilience $\rightarrow$ Output | $O(H \cdot (n \log n + n \cdot H))$ | $O(n + H)$ |

* **Greedy Backward Allocation**: Jobs are sorted by profit descending. Each job scans backward from $\min(\text{deadline}, H)$ down to 1. Placing jobs as late as possible preserves earlier slots for tighter deadlines.
* **Counterfactual Scratch Re-scheduling**: For each available slot $s$, the scheduler adds $s$ to the blocked set and rebuilds the schedule from scratch. The slot yielding $\max(\text{Baseline Profit} - \text{New Profit})$ is the critical slot.

---

### 5. Technologies Used
* **Programming Language**: Pure Python 3 (Tested on 3.8, 3.10, 3.11).
* **Standard Modules**: `sys` (I/O streaming), `typing` (type safety), `unittest` (automated testing), `itertools` & `random` (brute-force combinatorial validator), `time` (benchmarking).
* **Dependencies**: **Zero third-party pip packages**. Fully cross-platform on Windows, Linux, and macOS.

---

### 6. Verification and Benchmark Results

```text
+---------------------------------------------------------------------------------+
| Benchmark / Test Metric       | Measured Result       | Hackathon Requirement   |
+---------------------------------------------------------------------------------+
| Automated Unit Tests          | 32 / 32 Passed (100%) | 100% Pass Rate          |
| Brute-Force Validation Cases  | 200 / 200 Agreement   | 0 Discrepancies         |
| Baseline Execution Time       | ~0.57 ms              | < 50 ms                 |
| Resilience Analysis Time      | ~24.64 ms             | < 500 ms                |
| Total Application Runtime     | ~25.21 ms             | < 1000 ms (40x margin)  |
+---------------------------------------------------------------------------------+
```

---

### 7. Sample Execution Parity

#### Input (`demo_input.txt`):
```text
5 5 1
3
101 2 100
102 1 50
103 3 80
104 2 120
105 4 60
```

#### Exact 7-Line Output:
```text
BASE_PROFIT 280
BASE_SLOTS 101 104 0 105 0
REJECTED 2 102 103
CRITICAL_SLOT 1
LOSS 100
AFTER_PROFIT 180
AFTER_SLOTS 0 104 0 105 0
```
* **Critical Slot Tie-Break**: Both Slot 1 and Slot 2 cause a loss of 100 ($280 - 180$). Smallest slot index $\min(1, 2) = 1$ is chosen.

---

### 8. Conclusion
The **Deadline Scheduler** project bridges theoretical algorithm design and fault-tolerant system engineering. By combining greedy matroid optimality with independent counterfactual resilience simulation, the solution guarantees maximum revenue under standard operations and provides pre-calculated contingency plans before unexpected outages occur.
