# Implementation Plan：[FIX-M2.5.2-FLIGHT-BUGS] 飛行航線穿障回正與 AI 學習階段切換異常修復

> **關聯 Spec**: `.specs/features/fix_m2_5_2_flight_bugs/spec.md`  
> **目標分支**: `fix/m2.5.2-bugs`  
> **狀態**: `Draft (Pending Architecture Sign-off)`

---

## 1. 任務拆解 (Task Groups & Phased Roadmap)

### 📌 Task Group 1: 修復 WebGL 40% 學習階段變數作用域死鎖 Bug
- **目標**：解決點擊「🌿 40% 半熟」按鈕引發的 `Uncaught ReferenceError: altErr is not defined` 導致整個 WebGL 渲染循環死鎖的問題。
- **改動檔案**：
  - `flight_test_sim.py`
  - `output/flight_test_simulator.html`
- **實作步驟**：
  1. 將 `const altErr = targetAlt - drone.position.y;` 自 `else` 區塊提升至所有 stage 判斷之前。
  2. 在 `stage_1_half_trained` 與 `stage_0_untrained` 中統一使用已正確宣告之 `altErr` 計算高度控制量。
  3. 加入外層防禦性 `try-catch` 包裹神經網絡推理與 stage 控制邏輯，保障 `animate()` 永不死鎖。

---

### 📌 Task Group 2: 重構 AI 巡航狀態機為四階段走廊（正面進入 ➔ 穿門 ➔ 出門 ➔ 轉角）
- **目標**：解決無人機未由門前進入、第二道門後自門後繞過並碰撞門框之重大導航缺陷，使其嚴格契合紫色規劃線。
- **改動檔案**：
  - `flight_test_sim.py`
  - `output/flight_test_simulator.html`
- **實作步驟**：
  1. 擴充 `aiNavStage` 狀態集合：`'APPROACH' | 'THROUGH' | 'LEADOUT' | 'CORNER'`。
  2. 起飛爬升完成後，初始目標點設為 Gate #1 之 `APPROACH` 點：
     $$\text{leadX} = \text{targetGate.x} - \text{targetGate.nx} \times 2.2\text{m}, \quad \text{leadZ} = \text{targetGate.z} - \text{targetGate.nz} \times 2.2\text{m}$$
  3. 新增 `APPROACH` 轉 `THROUGH` 條件：當機體接近門前進門點（距離 $< 1.5\text{m}$ 且位於門面正面前方 $\text{signedDot} \le -0.2\text{m}$）時切換至 `THROUGH`。
  4. 加強 `hasCrossedGate` 判定：要求無人機必須經過門前進入（前置狀態必為 `APPROACH` 或歷史標記），且通過門面（$\text{signedDot} \ge 0.35\text{m}$，橫向偏差 $< 2.0\text{m}$，高度偏差 $< 1.8\text{m}$）方可完成穿門，切換至 `LEADOUT`。
  5. 在 `CORNER` 完成後（距離轉角 $< 2.2\text{m}$），切換至下一道門的 `APPROACH` 點，嚴格保證每道門均由正面進入。

---

### 📌 Task Group 3: 優化門框 APF 斥力緩衝與動態導航引導線
- **目標**：消除門框立柱與橫樑的近身切削碰撞風險，並使動態引向射線（青色）與紫色走廊完美同動。
- **改動檔案**：
  - `flight_test_sim.py`
  - `output/flight_test_simulator.html`
- **實作步驟**：
  1. 調校 `activeObstacles` 中目標門立柱側向推力，推離範圍由 $0.85\text{m}$ 擴大至 $1.15\text{m}$，給予足夠反應時間。
  2. 加入橫樑頂部安全垂直推力防護（避免因高度震盪切削頂樑）。
  3. 更新 HUD 狀態字串，即時顯示 `AI 門前進門對齊 (Gate #X 迎角校準)` ➔ `AI 航線巡檢中 (Gate #X)` ➔ `AI 出門走廊導引` ➔ `AI 外環轉角巡航`。
  4. 同步更新 `trajectoryLine`，確保無人機前端的青色導引線段精準指引向四個階段的即時航點。

---

### 📌 Task Group 4: 自動化測試卡與模擬器重新生成驗證
- **目標**：驗證兩大 Bug 之修復成果，執行全套 64+ 單元測試並確認無回歸錯誤。
- **改動檔案**：
  - `test_privileged_drl_distillation.py`
  - `output/flight_test_simulator.html`
- **實作步驟**：
  1. 在 `test_privileged_drl_distillation.py` 新增單元測試：
     - `test_simulator_html_stage_1_no_scope_error`：靜態與語法檢驗 HTML 中 `stage_1_half_trained` 變數作用域與 `altErr` 宣告先後關係。
     - `test_simulator_html_approach_navigation_stage`：檢驗模擬器 JS 代碼是否具備 `APPROACH` 狀態與前進進門點運算（$- \mathbf{n} \times 2.2$）。
  2. 執行 `flight_test_sim.py` 重新生成 `output/flight_test_simulator.html`。
  3. 執行全量 `pytest` 確保 100% 通過。
