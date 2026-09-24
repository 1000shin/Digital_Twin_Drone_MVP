# Implementation Plan：[FIX-M2.6-AI-CIRCUIT-COMPLETION] WebGL AI 自主飛行全場多門閉環導航與防撞解鎖

> **版本**: 1.0  
> **功能 ID**: `FIX-M2.6-AI-CIRCUIT-COMPLETION`  
> **目標分支**: `fix/m2.6-ai-autonomous-flight-circuit-completion`  
> **執行原則**: 小步前進、漸進提交、單元測試防禦、實機瀏覽器驗收。

---

## 任務拆解 (Task Groups & Milestones)

### Task Group 1: 規格凍結與環境準備
- [x] **Task 1.1**: 開立修復分支 `fix/m2.6-ai-autonomous-flight-circuit-completion`。
- [x] **Task 1.2**: 建立 `.specs/features/fix_m2_6_flight_circuit_completion/spec.md` 與 `plan.md`。
- [ ] **Task 1.3**: 建立 `.specs/features/fix_m2_6_flight_circuit_completion/validation.md`。

### Task Group 2: 碰撞物理位置解穿透重構 (`flight_test_sim.py`)
- [ ] **Task 2.1**: 在 `flight_test_sim.py` 的 `activeObstacles.forEach` 碰撞檢驗中，加入 Axis-Aligned 最小穿透深度計算與法向推移（Positional Depenetration），使機體在接觸障礙物表面時立刻被彈至外部，消除速度衰減死鎖陷阱。
- [ ] **Task 2.2**: 同步更新 `output/flight_test_simulator.html`。

### Task Group 3: 導航航線多段過渡點與 APF 舊門冷卻遮罩 (`flight_test_sim.py`)
- [ ] **Task 3.1**: 在 `flight_test_sim.py` 中引入 `clearedGateId` 與 `clearedGateCooldownTimer`，在過門後 2.5 秒內持續對剛通過的門框應用穿透通道遮罩（免頂樑斥力、側柱居中對齊），消除新舊引斥力相剋夾死。
- [ ] **Task 3.2**: 升級 `aiGates` 與航點切換狀態機：加入「門前進門對齊點（Entry）」、「門心穿越（Center）」與「門後出門緩衝點（Lead-Out, +2.0m）」三階狀態機，徹底終結出門過早切換導致的「回頭殺」。
- [ ] **Task 3.3**: 於 Gate 1 ➔ Gate 2 ➔ Gate 3 ➔ Gate 4 各航段間加入外環中繼轉角點（Corner Waypoints），形成避開中央立柱群 $(\pm 3, \pm 3)$ 的平滑外繞閉合迴圈。
- [ ] **Task 3.4**: 同步更新 `circuitLine` 全局閉合迴路走廊與動態 `trajectoryLine`。

### Task Group 4: 自動化測試與實機瀏覽器試飛閉環驗證
- [ ] **Task 4.1**: 於 `test_ai_autonomous_pipeline.py` 更新或新增航線走廊與解穿透關鍵演算法驗證。
- [ ] **Task 4.2**: 執行全套單元測試 (`pytest`)，確保 100% 通過。
- [ ] **Task 4.3**: 透過無頭 Chrome 實跑 `scratch/flight_test_runner.js`，在瀏覽器沙盒中實測至少完成 1 圈全場巡檢，取得完整通過遙測日誌與最終成效截圖。

### Task Group 5: 驗證報告、代碼審查與日誌發布
- [ ] **Task 5.1**: 撰寫 `validation.md` 紀錄瀏覽器實測遙測數據。
- [ ] **Task 5.2**: 更新 `CHANGELOG.md`，完成 Git Commit 與分支合併。
