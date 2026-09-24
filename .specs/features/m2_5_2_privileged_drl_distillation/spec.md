# Feature Spec：[M2.5.2] 深度強化學習與特權導師-學生蒸餾極限避障系統 (Privileged Teacher-Student DRL Obstacle Avoidance)

> **版本**: 1.0  
> **功能 ID**: `FEAT-M2.5.2-PRIVILEGED-DRL-DISTILLATION`  
> **狀態**: `Review Pending (Awaiting Architect Confirmation)`  
> **對應專案憲章**: `Constitution Phase 2 [M2.5.2]`  
> **目標分支**: `feature/m2.5.2-privileged-drl-distillation`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **技術選型決策**: 選項 A（解耦 PyTorch 離線特權訓練器 ➔ 匯出純 NumPy/JSON 輕量權重部署）

---

## 1. 系統架構與設計核心 (Overview & Architecture)

### 1.1 問題與核心價值 (The Problem & Value)
在傳統無人機避障中，直接以局部噪聲感知（如 8 向 LiDAR 或深度相機）進行端到端強化學習（RL）時，面臨**探索空間過大、局部可觀測性（POMDP）收斂極慢、以及容易陷入局部極值**的難題。
借鑒國際頂尖研究（UZH RPG *Learning High-Speed Flight in the Wild*, Science Robotics 2021 與 *Swift*, Nature 2023），本功能在數位孿生環境中建立**「特權導師-學生蒸餾架構（Privileged Teacher-Student Framework）」**：
1. **導師網絡（Teacher Policy）**：在虛擬世界中直接讀取**特權真值（Ground Truth）**（精確機體速度、障礙物立柱 3D 包圍盒、穿越門法線與環境風場），以 PPO 算法極速收斂出貼近物理極限的避障軌跡。
2. **學生網絡（Student Policy）**：僅允許接收機載局部感知（8 向 LiDAR 測距帶雜訊、IMU 歷史加速度與角速度、相對目標航點），透過 **DAgger / 策略蒸餾** 向導師網絡學習。
3. **極致輕量解耦部署**：訓練完畢後，將學生網絡權重匯出為標準 `student_policy_weights.json`。在 Python 執行端（`autonomous_flight_learner.py`）與瀏覽器端（`flight_test_simulator.html`）均以純矩陣乘法執行，**日常運行與單元測試 100% 保持純 Python/NumPy 零依賴，推論延遲 $< 0.05\text{ms}$**。

```mermaid
flowchart TD
    subgraph DigitalTwin [數位孿生模擬環境 (drone_rl_env.py)]
        GT[特權真值 Privileged Ground Truth<br/>精確位置/速度/全立柱座標/門法向]
        Obs[機載局部觀測 Onboard Observation<br/>帶噪聲 8向 LiDAR/IMU時序/相對目標]
    end

    subgraph OfflineTraining [離線解耦訓練器 (PyTorch Tooling)]
        GT -->|完全可觀測狀態| Teacher[特權導師網絡 Teacher Policy<br/>PPO 高速極限避障收斂]
        Teacher -->|最優推力標籤 u*| Distill[策略蒸餾 / DAgger 監督學習]
        Obs -->|局部噪聲觀測| Student[學生網絡 Student Policy<br/>輕量感知神經網絡]
        Distill -->|梯度反向傳播修正| Student
        Student -->|匯出數值權重矩陣| Weights[student_policy_weights.json<br/>(< 80KB 浮點矩陣)]
    end

    subgraph RuntimeDeployment [運行時零依賴部署]
        Weights --> PyRuntime[autonomous_flight_learner.py<br/>純 NumPy 矩陣前向推論 <0.05ms]
        Weights --> WebGLRuntime[output/flight_test_simulator.html<br/>純 JavaScript 原生矩陣計算 60FPS]
    end
```

---

## 2. 詳細需求與驗收標準 (Requirements & Acceptance Criteria)

### 2.1 功能性需求 (Functional Requirements)

- [ ] **FR-1: 強化學習環境特權真值與學生觀測介面擴充 (`drone_rl_env.py`)**
  - **說明**: 擴展現有 `DroneRLEnvironment`，明確劃分特權真值狀態與機載學生觀測。
  - **驗收標準 (AC-1.1)**: 提供 `get_privileged_state()` 介面，輸出包含機體精確狀態（12D：$p, v, q, \omega$）、目標門 3D 法向量與距中心距離、以及全場 6 根立柱精確相對向量與半徑（特權維度約 32D）。
  - **驗收標準 (AC-1.2)**: 提供 `get_student_observation(noise_std=0.05, dropout_prob=0.02)` 介面，模擬實機感測器的高斯測距雜訊與隨機 LiDAR 射線丟失。

- [ ] **FR-2: 解耦特權導師訓練與蒸餾工具鏈 (`train_privileged_distillation.py`)**
  - **說明**: 基於 PyTorch 實作獨立離線訓練腳本，支援 Apple Silicon MPS / CPU 自動加速。
  - **驗收標準 (AC-2.1)**: 實作 `TeacherPolicy`（MLP 架構：特權狀態 ➔ 隱藏層 [128, 128] ➔ 4D 動作），以 PPO 與多目標獎懲函數快速收斂，無碰撞穿門率達 $\ge 90\%$。
  - **驗收標準 (AC-2.2)**: 實作 `StudentPolicy`（輕量架構：學生觀測 ➔ 隱藏層 [64, 64] ➔ 4D 動作），透過 DAgger 蒸餾學習導師動作，輸出動作 MSE 損失 $< 0.05$。
  - **驗收標準 (AC-2.3)**: 實作權重匯出函式 `export_student_weights(path)`，將權重與偏置向量以標準 JSON 格式序列化儲存至 `output/neural_models/student_policy_weights.json`。

- [ ] **FR-3: 純 NumPy 輕量學生神經網絡推論器 (`autonomous_flight_learner.py`)**
  - **說明**: 在現有策略學習器中整合學生網絡推論引擎，完全不依賴 PyTorch。
  - **驗收標準 (AC-3.1)**: 實作 `StudentPolicyNumpy` 類別，直接載入 JSON 權重檔案，使用純 NumPy 矩陣乘法與 ReLU/Tanh 激活函數進行前向推論。
  - **驗收標準 (AC-3.2)**: 數值一致性驗證：NumPy 推論輸出與 PyTorch 原生推論輸出在相同輸入下的最大絕對誤差 $\le 10^{-5}$。
  - **驗收標準 (AC-3.3)**: 韌性回退（Graceful Degradation）：若找不到權重檔，自動平滑切換回現有的經典幾何 APF 避障控制，保證系統永不崩潰。

- [ ] **FR-4: WebGL 3D 模擬器即時神經副駕駛整合 (`flight_test_sim.py` & HTML)**
  - **說明**: 將蒸餾後的學生網絡矩陣整合至 Three.js 模擬器中，實現瀏覽器端原生神經自駕。
  - **驗收標準 (AC-4.1)**: 在 HTML 模擬器中內建或載入學生網絡權重，利用 JS 陣列乘法執行即時推論（單步計算耗時 $< 0.1\text{ms}$）。
  - **驗收標準 (AC-4.2)**: HUD 戰情面板顯示神經策略狀態：`[AI AGENT: DISTILLED STUDENT]` 與決策推力向量。
  - **驗收標準 (AC-4.3)**: 能在 WebGL 環境中平穩連續通過競技場門框，避開黃黑警示立柱。

- [ ] **FR-5: 全套自動化單元測試覆蓋 (`test_privileged_drl_distillation.py`)**
  - **說明**: 建立獨立單元測試，涵蓋特權狀態導出、學生噪聲生成、NumPy 推論精度、延遲效能與回退機制。
  - **驗收標準 (AC-5.1)**: 測試特權與學生觀測維度及數值邊界合規。
  - **驗收標準 (AC-5.2)**: 測試純 NumPy 前向推論單步延遲 $< 0.05\text{ms}$（滿足 100Hz 即時飛控）。
  - **驗收標準 (AC-5.3)**: 全專案單元測試維持 100% 通過（總耗時維持在 10 秒內）。

---

## 3. 非功能性需求 (Non-Functional Requirements)
1. **極致輕量與零相依**：日常執行（`python3 flight_test_sim.py`、單元測試）不強制要求安裝或載入 PyTorch，維持純 Python + NumPy 標準環境。
2. **微秒級推論延遲**：學生網絡單步推論速度必須嚴格限制在 $\le 0.1\text{ ms}$（實測目標 $< 0.05\text{ ms}$）。
3. **可解釋性與溯源性**：訓練產生之權重檔需附帶元數據（訓練步數、收斂損失、產生時間戳與對應憲章版本）。

---

## 4. 交付檔案清單
1. [`.specs/features/m2_5_2_privileged_drl_distillation/spec.md`](file:///Users/jasonzheng/Documents/Obsidian%20workspace/AI%20agent%20workspace/Digital_Twin_Drone_MVP/.specs/features/m2_5_2_privileged_drl_distillation/spec.md)
2. [`.specs/features/m2_5_2_privileged_drl_distillation/plan.md`](file:///Users/jasonzheng/Documents/Obsidian%20workspace/AI%20agent%20workspace/Digital_Twin_Drone_MVP/.specs/features/m2_5_2_privileged_drl_distillation/plan.md)
3. `drone_rl_env.py`（擴充特權真值與帶噪聲學生感知介面）
4. `train_privileged_distillation.py`（離線解耦 PyTorch 訓練與蒸餾工具）
5. `autonomous_flight_learner.py`（新增純 NumPy 學生網絡推論引擎）
6. `output/neural_models/student_policy_weights.json`（導出之神經網絡權重資產）
7. `flight_test_sim.py` / `output/flight_test_simulator.html`（WebGL 3D 模擬器神經推論整合）
8. `test_privileged_drl_distillation.py`（專案自動化測試套件）
