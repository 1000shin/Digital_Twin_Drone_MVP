# Feature Spec：[M2.5] 虛擬環境無人干預強化學習 (RL) 訓練管線 (Autonomous RL Training Pipeline)

> **版本**: 1.0  
> **功能 ID**: `FEAT-M2.5-RL-PIPELINE`  
> **狀態**: `Approved (Feature Spec Established)`  
> **對應專案憲章**: `Constitution v9.0 Phase 2 [M2.5] & [M2.6]`  
> **目標分支**: `feature/m2.5-autonomous-rl-pipeline`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **關聯實作**: `drone_rl_env.py`, `autonomous_flight_learner.py`, `flight_test_sim.py`, `test_ai_autonomous_pipeline.py`

---

## 1. 功能概述與效益 (Overview & Problem Statement)

### 1.1 問題陳述 (The Problem)
在無人機研發與試飛過程中，依賴單純的人工手動試飛面臨兩大瓶頸：
1. **試錯成本極高**：實機或手動試飛若遭遇失控或碰撞將造成機體結構永久損毀（炸機），無法在未知狹窄空間探索極限邊界。
2. **樣本採集週期冗長**：人工操縱無法進行 24/7 不間斷的高頻率大量試錯，且人類飛行習慣存在固有盲點，難以自主發掘超越常規的避障動力學軌跡。

為了解決此痛點，需在數位孿生體系內構建一套**「零人工干預的自律強化學習（RL）訓練管線」**，讓無人機在虛擬 3D 世界透過高擬真獎懲機制（Reward Function）進行數萬次高速自主試錯，並將試錯瓶頸數據自動回饋至形態演化引擎（Morph Evolution），實現「軟體學策略、硬體長骨肉」的虛實閉環。

### 1.2 核心目標與使用者故事 (User Story)
* **As a** 無人機自主飛控工程師與數位孿生架構師，  
* **I want to** 在虛擬環境中啟動標準 Gymnasium 強化學習環境，並在 WebGL 模擬器中一鍵切換 AI 自主試飛與觀摩，  
* **So that** AI 能夠在海量情境中自主習得穿門避障神經策略網絡，並自動統計碰撞熱點回饋驅動新一代 3D 機身形態演化，徹底解放人力試飛負擔。

### 1.3 非目標範疇 (Non-Goals / Out of Scope)
* **不引入重型編譯機器學習框架**：嚴格遵守專案憲章「零重型編譯依賴」原則，不引進 PyTorch / TensorFlow / Stable-Baselines3 等需 C++ 編譯或龐大相依之套件，全演算法以 Python 標準庫與 NumPy 實作。
* **本階段暫不直連實體飛控硬體 (HITL)**：實機 Pixhawk 6C 韌體在環驗證保留給 Phase 3 [M3.1]，本規格專注於 Sim-to-Sim 虛擬閉環。
* **不破壞既有 6-DOF 物理與破損特效**：保持 WebGL 破損變形、火花碎屑粒子與 BOM 維修系統的獨立性與相容性。

---

## 2. 詳細需求與驗證標準 (Requirements & Acceptance Criteria)

### 2.1 功能性需求 (Functional Requirements)

- [x] **FR-1: 標準 Gymnasium 相容強化學習環境 (`drone_rl_env.py`)**
  - **說明**: 提供標準 RL 介面 `reset()` 與 `step(action)`，支援 60Hz 物理積分步進與無頭（Headless）高速運算。
  - **驗證標準 (AC-1.1)**: 觀測空間（Observation Space）為 23 維標準化向量：
    - `[0:12]`: 機體運動學狀態 `[x, y, z, vx, vy, vz, pitch, roll, yaw, wx, wy, wz]`。
    - `[12:20]`: 360° 8 向 LiDAR 測距射線 `[前, 前左, 左, 後左, 後, 後右, 右, 前右]`（歸一化至 `[0.0, 1.0]`，代表 0~12m）。
    - `[20:23]`: 目標穿越門相對向量 `[rel_x, rel_y, rel_z]`。
  - **驗證標準 (AC-1.2)**: 動作空間（Action Space）為 4 維連續向量：
    - `[pitch_cmd, roll_cmd, yaw_rate_cmd, throttle_cmd]`，數值範圍嚴格箝位於 `[-1.0, 1.0]`。

- [x] **FR-2: 複合式高擬真獎懲函數矩陣 (Reward Function Design)**
  - **說明**: 建立引導 AI 在狹窄障礙物世界高速穿門且避免碰撞的多目標獎懲機制：
  - **驗證標準 (AC-2.1)**: 目標進展獎勵：以歐式距離變化量計算 $+R_{\text{progress}} = (d_{\text{prev}} - d_{\text{curr}}) \times 12.0$。
  - **驗證標準 (AC-2.2)**: 穿越門框突破獎勵：成功穿過門框中心給予 $+100.0$ 分；完成全場 4 門巡檢圈給予 $+300.0$ 分。
  - **驗證標準 (AC-2.3)**: 姿態平穩維持分：抑制極端角速度與劇烈翻滾，平穩飛行每步獲得 $+0.05$ 分。
  - **驗證標準 (AC-2.4)**: 障礙物動態斥力懲罰：當 LiDAR 測距 $< 1.8\text{m}$ 時，依距離施加指數懲罰 $-R_{\text{prox}} = \exp((1.8 - d)/1.8) \times 1.5$。
  - **驗證標準 (AC-2.5)**: 剛體碰撞終止重罰：碰觸立柱、橫樑或邊界墜地給予 $-200.0$ 分並觸發 `terminated = True`。

- [x] **FR-3: 輕量自律策略學習器 (`autonomous_flight_learner.py`)**
  - **說明**: 結合人工勢能場（APF）引導與人類飛行示範資料集（Behavioral Cloning Prior）。
  - **驗證標準 (AC-3.1)**: 能載入人類飛手 2Hz 遙測資料集 (`flight_training_data_sample.json`) 完成策略先驗暖機。
  - **驗證標準 (AC-3.2)**: 策略推論函式 `predict(obs)` 輸出合規 4 維動作，在無碰撞狀況下保持高決策信賴度（$\ge 90\%$）。
  - **驗證標準 (AC-3.3)**: 無頭訓練每秒處理步數（Steps per Second）$\ge 5,000$ 步，10 秒內可完成 1,000 回合自我博弈。

- [x] **FR-4: WebGL 3D 模擬器即時自主飛行與視覺走廊 (`flight_test_sim.py`)**
  - **說明**: 在瀏覽器中提供可視化觀摩 AI 導航、穿門與避障的雙軌整合。
  - **驗證標準 (AC-4.1)**: HUD 提供「🤖 AI 自主飛行巡弋」獨立狀態面板，顯示目標航點、巡航圈數、信賴度與累積獎勵分。
  - **驗證標準 (AC-4.2)**: 兩階段起飛保護：垂直起飛階段（高度 $< 1.6\text{m}$）鎖定水平零傾角（Pitch=0, Roll=0），提供 $14.5\text{ m/s}^2$ 純垂直高推力脫離地面鉗制；安全高度以上平滑切入 APF 導航。
  - **驗證標準 (AC-4.3)**: 空間渲染動態紫色雷達導引線（`trajectoryLine`），穿門時動態跳轉至下一門框，關閉視錐體剔除（`frustumCulled = false`）確保全程可見。
  - **驗證標準 (AC-4.4)**: 人類主飛安全接管機制（Shared Autonomy Copilot / M2.6）：碰觸任何手動控制鍵（`W/A/S/D/↑/↓/Space`）立即以最高優先權解除 AI 接管，切回手動模式。

- [x] **FR-5: 試錯數據回饋與 Gen-4 機構演化閉環**
  - **說明**: 將自主飛行的碰撞弱點與能耗數據統計萃取，觸發形態基因庫進化。
  - **驗證標準 (AC-5.1)**: 自動導出 `output/training_datasets/ai_autonomous_flight_session_001.json` 與 Markdown 飛行診斷報告。
  - **驗證標準 (AC-5.2)**: 觸發 `morph_evolution.py` 自動長出第四代無人機（Gen-4 Sentinel Prime），導出 URDF/SDF 物理模型至 `output/models_archive/`，並更新演化血統樹。

### 2.2 非功能性需求 (Non-Functional Requirements)
* **效能約束**: 全套自動化單元測試在本地環境必須於 10 秒內跑完（當前 32/32 項單元測試執行時間 $< 9$ 秒）。
* **記憶體與環境清潔**: 純標準 Python 庫運行，無多餘背景常駐 Daemon，無大型 PyPI 外部相依。
* **架構邊界**: 嚴格劃分 WebGL 視覺試飛軌（視覺檢驗）與 Python RL 訓練軌（算力加速）。

### 2.3 邊界條件與異常處理 (Edge Cases & Error Handling)
* **嚴重損壞安全鎖定**: 若機身結構完整度 $\le 20\%$ 或斷槳數超過一半，禁止啟動 AI 自主飛行，並於 HUD 顯示紅色警告 Toast。
* **中文輸入法（IME）按鍵攔截容錯**: 鍵盤監聽支援 `e.code === 'KeyP'`、`e.key === 'p'`、`e.key === 'P'`，並在點擊按鈕後自動執行 `btn.blur()` 避免焦點滯留。

---

## 3. 技術設計與介面合約 (Technical Design & Contracts)

### 3.1 核心模組架構圖
```
┌────────────────────────────────────────────────────────┐
│                   Gymnasium RL Environment             │
│                     (drone_rl_env.py)                  │
├───────────────────────────┬────────────────────────────┤
│ 23-dim Observation Vector │ 4-dim Continuous Action    │
│ • Pos/Vel/Attitude (12D)  │ • Pitch Command            │
│ • 8-Ray LiDAR Scan (8D)   │ • Roll Command             │
│ • Target Gate Vector (3D) │ • Yaw Rate Command         │
│                           │ • Throttle Climb Command   │
└─────────────┬─────────────┴─────────────▲──────────────┘
              │                           │
              │ State                     │ Action
              ▼                           │
┌─────────────────────────────────────────┴──────────────┐
│             Autonomous Flight Learner Policy           │
│              (autonomous_flight_learner.py)            │
├────────────────────────────────────────────────────────┤
│ • Parametric APF Obstacle Repulsion Vector Field       │
│ • Human Behavioral Cloning Prior (2Hz Telemetry)       │
│ • Target Gate Waypoint Attraction & Yaw Alignment      │
└────────────────────────────────────────────────────────┘
```

### 3.2 遙測日誌 JSON Schema
```json
{
  "session_id": "ai_autonomous_session_001",
  "drone_model": "evolved_shield_sentinel_v3",
  "flight_mode": "autonomous_rl_guided",
  "summary": {
    "total_duration_sec": 30.5,
    "gates_cleared": 4,
    "laps_completed": 1,
    "collisions": 0,
    "cumulative_reward": 845.2
  },
  "samples": [
    {
      "timestamp": 0.5,
      "position": [0.0, 1.65, -1.2],
      "velocity": [0.0, 1.8, -2.1],
      "attitude": { "pitch": -0.25, "roll": 0.0, "yaw": 0.0 },
      "lidar_min_dist": 2.45,
      "ai_confidence": 98.5
    }
  ]
}
```

---

## 4. 驗收與簽核紀錄 (Sign-off)

| 檢驗項目 | 狀態 | 驗證證明 / 檔案路徑 |
| :--- | :--- | :--- |
| **RL 環境與 23 維觀測空間** | ✅ PASSED | `test_ai_autonomous_pipeline.py::test_drone_rl_environment_reset_and_step` |
| **8 向 LiDAR 測距與碰撞重罰** | ✅ PASSED | `test_ai_autonomous_pipeline.py::test_rl_env_lidar_and_collision` |
| **自律勢能場策略預測** | ✅ PASSED | `test_ai_autonomous_pipeline.py::test_autonomous_flight_policy_predict` |
| **WebGL AI HUD 與兩階段起飛** | ✅ PASSED | `test_ai_autonomous_pipeline.py::test_webgl_simulator_ai_autopilot_elements` |
| **Gen-4 模型系譜與永久模型庫** | ✅ PASSED | `output/models_archive/gen_04_sentinel_prime_v4/` |
| **32 項全專案自動化測試覆蓋** | ✅ PASSED | `python3 -m unittest discover -s . -p "test_*.py"` (32/32 OK, 8.8s) |

---
*簽核狀態*: **APPROVED & COMMITTED**  
*架構師*: Jason Zheng (Human Architect)  
*更新日期*: 2026-09-24  
