# Feature Spec：[M2.6] 「人類主飛，AI 輔助介入」協同飛控副駕駛 (Shared Autonomy Copilot)

> **版本**: 1.0  
> **功能 ID**: `FEAT-M2.6-SHARED-AUTONOMY-COPILOT`  
> **狀態**: `Approved (Feature Spec Established)`  
> **對應專案憲章**: `Constitution v9.0 Phase 2 [M2.6]`  
> **目標分支**: `feature/m2.6-shared-autonomy-copilot`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **關聯實作**: `shared_autonomy_copilot.py`, `flight_test_sim.py`, `mavlink_controller.py`, `test_shared_autonomy_copilot.py`

---

## 1. 功能概述與核心價值 (Overview & Problem Statement)

### 1.1 問題陳述 (The Problem)
在傳統無人機手動飛行操作（尤其是狹窄室內、橋樑涵洞或複雜管線檢測）中，飛手面臨以下嚴峻挑戰：
1. **視線盲區與深度知覺失真**：透過 FPV 鏡頭或遠程視線操控時，飛手難以精準估算機身邊緣與障礙物的即時微小距離（如 0.5m ~ 1.5m 之間），極易因手抖、風切變或盲區誤判導致「擦撞立柱或橫樑」而瞬間炸機。
2. **全自動接管破壞操作自由度**：若採用傳統離散式「碰撞急停鎖定（Hard Emergency Brake）」，會頻繁打斷飛手的飛行意圖與操作節奏，使得貼近結構檢測任務難以順暢執行。

為了解決此痛點，本專案提出**「人類主飛，AI 輔助介入（Shared Autonomy Copilot）」**：由人類飛手全權主導飛行航向與任務節奏，AI 策略在背景運行作為「虛擬防撞保險桿（Virtual Bumper）」，僅在機體進入危險防護區時，以平滑連續向量方式介入速度阻尼與排斥力場，達成「飛手自由操縱、系統守護防撞」的極致人機協同體驗。

### 1.2 核心目標與使用者故事 (User Story)
* **As a** 無人機手動巡檢飛手與自駕演算法工程師，  
* **I want to** 在手動操控無人機穿越複雜障礙物時，啟動「🛡️ 協同副駕駛（Copilot）」模式，  
* **So that** 當我正常巡航時享有 100% 手動操縱手感；而當飛行軌跡即將擦撞立柱或牆壁時，AI 自動注入平滑反向推力與動態偏航，引導機體沿著安全邊界滑行，徹底杜絕人為失誤炸機。

### 1.3 非目標範疇 (Non-Goals / Out of Scope)
* ❌ **非目標 1：取代 M2.5 全自主導航**：本功能專注於「人類主飛 + AI 防撞輔助」，不取代 `[M2.5]` 的無人干預全自主穿門 AI 巡弋。
* ❌ **非目標 2：實體微控制器韌體燒錄**：定位為軟體層協同飛控推論演算法與 WebGL 互動，不直接向實體 Pixhawk/STM32 晶片燒錄二進位韌體。
* ❌ **非目標 3：重型外部相依庫**：嚴格恪守專案憲章「零重型編譯依賴」原則，以 Python 標準庫與 NumPy 實作，確保單元測試在 10 秒內跑完。

---

## 2. 詳細需求與驗收標準 (Requirements & Acceptance Criteria)

### 2.1 功能性需求 (Functional Requirements)

- [ ] **FR-1: 獨立協同副駕駛核心運算模組 (`shared_autonomy_copilot.py`)**
  - **說明**: 實作 `SharedAutonomyCopilot` 類別，負責過濾與混合人類飛手輸入指令與 AI 安全排斥力場。
  - **驗證標準 (AC-1.1)**: 輸入介面包含人類控制輸入 $\vec{u}_{\text{human}} = [pitch, roll, yaw\_rate, throttle]$、機體運動學狀態與 8 向 360° LiDAR 測距向量。
  - **驗證標準 (AC-1.2)**: 支援動態連續向量混合演算法：
    $$\vec{u}_{\text{out}} = (1 - \beta) \vec{u}_{\text{human}} + \beta \vec{u}_{\text{repulsion}}$$
    其中 $\beta \in [0.0, 1.0]$ 為危險介入權重係數。
  - **驗證標準 (AC-1.3)**: 當所有障礙物距離 $> 2.0\text{m}$ 且撞擊時間 $\text{TTC} > 2.0\text{s}$ 時，$\beta = 0.0$，人類輸入 100% 透傳（零干預、無延遲）。

- [ ] **FR-2: 雙層動態安全邊界與撞擊時間預警 (Two-Tier Safety Zones & TTC)**
  - **說明**: 依據 LiDAR 測距 $d_{\min}$ 與相對逼近速度動態計算介入層級：
  - **驗證標準 (AC-2.1) 警戒區 (Warning Zone, $1.2\text{m} \le d < 2.0\text{m}$)**:
    - 狀態標註為 `WARNING`。
    - 啟動平滑速度阻尼（Velocity Damping），對朝向障礙物分量的輸入進行平滑箝位（阻尼係數 $\alpha \in [0.4, 0.8]$）。
    - 允許遠離障礙物的逃逸輸入 100% 通過。
  - **驗證標準 (AC-2.2) 緊急避險區 (Emergency Zone, $d < 1.2\text{m}$)**:
    - 狀態標註為 `DEFLECTING`（緊急介入）。
    - 啟動非線性人工勢能場反向排斥向量 $\vec{u}_{\text{repulsion}}$，強制抵消朝向障礙物的衝力。
    - 自動依據障礙物法向產生側向逃逸切線推力（Tangential Deflection），實現沿障礙物表面滑行避障。

- [ ] **FR-3: WebGL 3D 模擬器即時副駕駛系統 (`flight_test_sim.py`)**
  - **說明**: 在瀏覽器 3D 試飛模擬器中整合即時副駕駛開關與全套視覺化反饋。
  - **驗證標準 (AC-3.1)**: HUD 控制台增設「🛡️ AI 協同副駕駛 (Copilot)」開關（快捷鍵 `C`），具備獨立狀態徽章：`[COPILOT: STANDBY / WARNING / DEFLECTING]`。
  - **驗證標準 (AC-3.2)**: 當進入緊急避險區時，無人機周圍動態顯現青藍色/橙色虛擬防護光環（Virtual Bumper Forcefield），即時呈現排斥力作用方向。
  - **驗證標準 (AC-3.3)**: 飛手進行手動操作（`W/A/S/D`）推向立柱時，機體在距離立柱 0.6m~1.0m 處自動懸停阻擋或側滑繞開，無法蓄意撞毀立柱。
  - **驗證標準 (AC-3.4)**: 與 `[M2.5]` 全自主自駕相容：若啟動全自主 AI 巡弋，副駕駛自動轉為後設防線；若切換為手動主飛，副駕駛即刻接管人機混合。

- [ ] **FR-4: MAVLink 飛控通訊整合與控制合約 (`mavlink_controller.py`)**
  - **說明**: 在 MAVLink Offboard / Manual Control 控制流中提供協同副駕駛安全過濾管線。
  - **驗證標準 (AC-4.1)**: 提供 `filter_manual_control(telemetry, manual_sp)` 接口，在發送 PX4 SET_POSITION_TARGET 之前完成防撞安全箝位。

- [ ] **FR-5: 全套自動化單元測試覆蓋 (`test_shared_autonomy_copilot.py`)**
  - **說明**: 建立獨立單元測試套件，涵蓋 6 大測試場景。
  - **驗證標準 (AC-5.1)**: 測試自由空域 100% 人類操作穿透率。
  - **驗證標準 (AC-5.2)**: 測試警戒區速度阻尼衰減率。
  - **驗證標準 (AC-5.3)**: 測試緊急避險區主動排斥向量與側向切線推力生成。
  - **驗證標準 (AC-5.4)**: 測試飛手逃逸反向操縱不受阻擋。
  - **驗證標準 (AC-5.5)**: 測試 WebGL 模擬器 HTML 腳本語法合規與快捷鍵無 TDZ 衝突。
  - **驗證標準 (AC-5.6)**: 全專案測試套件維持 100% 通過（執行時間 $< 10$ 秒）。

---

## 3. 非功能性需求 (Non-Functional Requirements)
* **低延遲運算**：Copilot 推論單步延遲必須小於 1 毫秒（$\le 1.0\text{ ms}$），滿足 60Hz~100Hz 飛控即時迴圈。
* **手感連續性**：介入係數 $\beta$ 必須採用平滑 S 曲線（Sigmoid / Cosine Blend），嚴禁階躍震盪（Jerk-Free）。
* **極致輕量**：全演算法保持純 Python 標準庫與 NumPy 實作，零外部編譯相依。
