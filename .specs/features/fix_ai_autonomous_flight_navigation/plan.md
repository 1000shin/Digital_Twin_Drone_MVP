# Implementation Plan：[FIX-M2-AI-AUTONOMOUS-MULTIGATE] WebGL AI 自主飛行多道穿越門導航與避障控制重構

> **版本**: 1.0  
> **功能 ID**: `FIX-M2-AI-AUTONOMOUS-MULTIGATE`  
> **目標分支**: `fix/webgl-ai-autonomous-flight-multigate`  
> **執行原則**: 小步前進、漸進提交、單元測試防禦、零上下文衰退。

---

## 任務拆解 (Task Groups & Milestones)

### Phase 1: 規格凍結與分支開立 (Spec & Branching)
- [x] **Task 1.1**: 開立獨立 Git 修復分支 `fix/webgl-ai-autonomous-flight-multigate`。
- [x] **Task 1.2**: 建立 `.specs/features/fix_ai_autonomous_flight_navigation/spec.md` 與 `plan.md`，定義驗收標準。
- [x] **Task 1.3**: 建立 `.specs/features/fix_ai_autonomous_flight_navigation/validation.md` 驗證記錄卡。

### Phase 2: 競技場 3D 門框朝向與幾何旋轉重構 (`flight_test_sim.py`)
- [ ] **Task 2.1**: 在 `aiGates` 與 `buildCollisionArena` 的 `gates` 資料結構中加入 `yaw` 朝向角度（Gate 1: $0^\circ$, Gate 2: $90^\circ$, Gate 3: $180^\circ$, Gate 4: $-90^\circ$）與法向量。
- [ ] **Task 2.2**: 重構門框 Mesh 生成邏輯，將立柱與橫樑以 `Group` 封裝並旋轉 `yaw`，使門洞切面精準對齊飛行進入方向。
- [ ] **Task 2.3**: 針對旋轉後的門柱與頂樑正確計算世界座標系之 `Box3` 碰撞包圍盒與中心點。

### Phase 3: APF 人工位能場與門面穿透狀態機重構 (`flight_test_sim.py`)
- [ ] **Task 3.1**: 在 `updatePhysics()` 障礙物斥力計算中加入目標門識別過濾：排除 `currentAIGate` 之頂橫樑與立柱對無人機的向後排斥力，消除「門前空氣牆」。
- [ ] **Task 3.2**: 升級航點切換判定：由單純半徑判定改為「門前引導 ➔ 穿越門面法向（signed projection > 0.3m）」，確保無人機完全穿出門框後再下達轉向下一門的指令。
- [ ] **Task 3.3**: 在穿門引導階段引入 LiDAR 門洞感測死區（Deadzone Filter），防止射線照射立柱引發恐慌性左右偏航甩尾。
- [ ] **Task 3.4**: 優化垂直爬升與門心高度鎖定（PID / Damped Altitude Hold），確保平穩通過各門設定高度（Gate 1: 3.2m, Gate 2: 4.5m, Gate 3: 6.0m, Gate 4: 3.8m）。

### Phase 4: 全局多段導航走廊 3D 視覺化 (`flight_test_sim.py`)
- [ ] **Task 4.1**: 在 Three.js 場景中建立全局閉合迴圈導航走廊（`circuitLine`），以霓虹半透明紫色線段連結 Gate 1 ➔ 2 ➔ 3 ➔ 4 ➔ 1。
- [ ] **Task 4.2**: 重構動態導引線（`trajectoryLine`），專注繪製從無人機即時位置指向當前目標門心的高亮動態脈衝線。
- [ ] **Task 4.3**: 航點推進時，動態導引線平滑且連續地銜接至下一道門，永不中斷；更新 HUD 目標門顯示與巡航圈數統計。

### Phase 5: 自動化單元測試擴充與全套回歸測試 (`test_ai_autonomous_pipeline.py`)
- [ ] **Task 5.1**: 於 `test_ai_autonomous_pipeline.py` 新增 WebGL 門框朝向參數、全局導航迴線結構與門洞穿越狀態機關鍵字斷言。
- [ ] **Task 5.2**: 執行全套單元測試確保全數通過，無任何回歸破壞。

### Phase 6: 驗收報告、代碼審查與日誌發布 (`CHANGELOG.md`, `validation.md`)
- [ ] **Task 6.1**: 重新生成 `output/flight_test_simulator.html`，驗證無人機能流暢連續穿越 4 道門。
- [ ] **Task 6.2**: 衍生獨立 Sub-Agent 進行三維度 Deep Code Review，產出審查報告。
- [ ] **Task 6.3**: 填寫 `.specs/features/fix_ai_autonomous_flight_navigation/validation.md`。
- [ ] **Task 6.4**: 更新專案根目錄之 `CHANGELOG.md`，完成 Git Commit。
