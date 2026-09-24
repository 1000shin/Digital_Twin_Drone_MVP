# Implementation Plan：[M2.6] 「人類主飛，AI 輔助介入」協同飛控副駕駛 (Shared Autonomy Copilot)

> **功能 ID**: `FEAT-M2.6-SHARED-AUTONOMY-COPILOT`  
> **對應規格**: `spec.md`  
> **狀態**: `Completed & Verified`  
> **目標分支**: `feature/m2.6-shared-autonomy-copilot`  
> **最後更新**: 2026-09-24  

---

## 1. 架構異動與模組劃分 (Architecture & Components)

```
Digital_Twin_Drone_MVP/
├── shared_autonomy_copilot.py          # [NEW] 協同副駕駛核心運算器（連續動態混合、雙層安全區、TTC 計算、虛擬排斥力場）
├── test_shared_autonomy_copilot.py      # [NEW] 副駕駛核心演算法、向量混合、阻尼衰減與安全邊界單元測試
├── flight_test_sim.py                  # [MODIFY] WebGL 3D 模擬器增加 Copilot 開關 (C鍵)、HUD 防撞狀態徽章、虛擬防護光環渲染
├── mavlink_controller.py               # [MODIFY] 整合 Copilot 安全過濾器，提供 MAVLink 手動飛行防撞防護層
├── .specs/
│   ├── constitution.md                 # [MODIFY] 更新 Phase 2 路線圖 [M2.6]
│   └── features/m2_6_shared_autonomy_copilot/
│       ├── spec.md                     # 功能需求與驗收標準
│       └── plan.md                     # 本實作計畫書
└── output/
    └── flight_test_simulator.html      # 重新生成的 WebGL 模擬器（內建 Copilot 協同防撞體驗）
```

---

## 2. 實作任務拆解 (Task Groups Breakdown)

### Task Group 1: 核心協同副駕駛運算器實作 (`shared_autonomy_copilot.py`)
- [x] **Task 1.1**: 定義 `CopilotInterventionLevel` 枚舉 (`STANDBY`, `WARNING`, `DEFLECTING`) 與 `CopilotDecision` 資料結構。
- [x] **Task 1.2**: 實作 8 向 LiDAR 障礙物幾何解析器，計算最近距離 $d_{\min}$、最近障礙物相對向量 $\vec{r}_{\text{obs}}$ 及撞擊時間 $\text{TTC} = d / v_{\text{approach}}$。
- [x] **Task 1.3**: 實作「雙層動態安全區」判定與平滑平移曲線：
  - 自由區 ($d \ge 2.0\text{m}$): $\beta = 0.0$，零干預。
  - 警戒區 ($1.2\text{m} \le d < 2.0\text{m}$): 計算指向障礙物的速度分量並進行平滑阻尼縮放（$\alpha \in [0.4, 0.9]$）。
  - 緊急避險區 ($d < 1.2\text{m}$): 啟動人工勢能場反向排斥力 $\vec{F}_{\text{rep}}$ 與側向切線逃逸推力 $\vec{F}_{\text{tan}}$。
- [x] **Task 1.4**: 實作動態向量混合與人類逃逸通道保留：
  - 若人類輸入方向遠離障礙物（$\vec{u}_{\text{human}} \cdot \vec{r}_{\text{obs}} < 0$），允許人類操作 100% 執行，不施加反向阻礙。
  - 輸出混合後安全動作向量 $\vec{u}_{\text{safe}} = [pitch, roll, yaw\_rate, throttle]$。

### Task Group 2: WebGL 3D 模擬器即時副駕駛整合 (`flight_test_sim.py`)
- [x] **Task 2.1**: HUD 操控面板增設「🛡️ AI 協同副駕駛 (Copilot)」切換按鈕與鍵盤快速鍵（支援 `KeyC`, `c`, `C`，自動 `btn.blur()`）。
- [x] **Task 2.2**: HUD 儀表增設 Copilot 即時狀態徽章（`STANDBY` 綠色 / `WARNING` 黃色 / `DEFLECTING` 紅色閃爍）與排斥推力指標。
- [x] **Task 2.3**: 實作 3D 虛擬防護光環（Virtual Bumper Halo）：在機身外圍建立半透明防護光環，當進入緊急避險區時自動點亮，並依據排斥向量角度變換形變與光芒脈衝。
- [x] **Task 2.4**: 於 JavaScript 物理迴圈中整合即時 Copilot 向量計算：在手動飛行時自動過濾鍵盤推力，遇到立柱時自動懸停緩衝或側滑通過，防止炸機。

### Task Group 3: MAVLink 飛控通訊整合 (`mavlink_controller.py`)
- [x] **Task 3.1**: 在 `MAVLinkController` 類別中引入 `SharedAutonomyCopilot` 實例。
- [x] **Task 3.2**: 實作 `apply_copilot_safety_filter(position_target, current_telemetry)` 方法，在執行離線或手動路徑時提供底層安全防護網。

### Task Group 4: 全套自動化單元測試與驗證
- [x] **Task 4.1**: 實作 `test_shared_autonomy_copilot.py`，測試：
  - 自由空域零干預驗證
  - 警戒區平滑阻尼與法向速度箝位
  - 緊急避險區排斥向量強度與切線滑行推力
  - 飛手逃逸反向操縱無阻礙驗證
  - MAVLink 安全過濾器整合驗證
  - WebGL 模擬器 HTML 與快速鍵無 TDZ 衝突
- [x] **Task 4.2**: 執行全專案回歸測試，確保所有單元測試 100% 通過且執行時間在 10 秒內。

---

## 3. 測試與驗證計畫 (Validation Plan)

```bash
# 1. 執行協同副駕駛專屬單元測試
python3 -m unittest test_shared_autonomy_copilot.py

# 2. 執行全專案回歸測試（保持 100% 通過）
python3 -m unittest discover -s . -p "test_*.py"
```
