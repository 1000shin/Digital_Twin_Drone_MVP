# Feature Spec：[FIX-M2.5.3-HTML-MODEL-LOAD] 修復 M2.5.3 模擬器 HTML 載入模型失敗與畫面全黑問題

> **版本**: 1.0  
> **功能 ID**: `FIX-M2.5.3-HTML-MODEL-LOAD`  
> **狀態**: `Completed & Validated`  
> **對應專案憲章**: `Constitution Phase 2 [M2.5.3] AI 自主飛行動力學三向優化`  
> **目標分支**: `fix/m2.5.3-html-model-load-fix`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **關聯模組**: `flight_test_sim.py`, `output/flight_test_simulator.html`, `test_webgl_environments.py`

---

## 1. 問題概述與根本原因分析 (Problem Statement & Root Cause Analysis)

### 1.1 🔴 現象描述 (Observed Symptoms)
在 M2.5.3（AI 自主飛行動力學三向優化：速度提升、向心轉彎、狹縫側傾穿障）實作完成後，開啟 WebGL 飛行測試模擬器（`output/flight_test_simulator.html`）時：
1. 3D 畫布完全漆黑，無法顯示或載入 3D 無人機模型與環境場景。
2. 畫面卡死，無任何 3D 渲染與飛行動力學更新。

### 1.2 🔍 根本原因分析 (Root Cause Analysis)
1. **ES6 Temporal Dead Zone (TDZ) 變數作用域死鎖**：
   - M2.5.3 在實作突發障礙物測試功能（`toggleTestObstacle()`）時，於場景切換函式 `switchEnvironment()` 注入了動態障礙物碰撞陣列更新邏輯：
     ```javascript
     if (typeof dynamicTestObstacleObj !== 'undefined' && dynamicTestObstacleObj) {
         activeObstacles.push(dynamicTestObstacleObj);
     }
     ```
   - 然而，`let dynamicTestObstacleObj = null;` 的變數宣告被放置在第 2251 行（`toggleTestObstacle()` 定義上方）。
   - 頁面載入至第 1498 行時，立即執行了初始化呼叫：
     ```javascript
     switchEnvironment('offshore_wind');
     ```
   - 在 ECMAScript 規範中，使用 `let` 宣告的識別字具備暫時死區（Temporal Dead Zone, TDZ）。在詞法宣告被執行前，任何對該識別字的訪問（**包括 `typeof` 運算子**）均會拋出不可攔截的致命例外：
     `ReferenceError: Cannot access 'dynamicTestObstacleObj' before initialization`
2. **連鎖崩潰阻斷主渲染迴圈**：
   - 第 1498 行拋出未捕獲之 `ReferenceError` 後，瀏覽器 JavaScript 引擎立即中止解析執行。
   - 位於檔案末端（第 3462 行）的主動畫渲染迴圈啟動器 `animate()` 永遠無法被呼叫，導致 3D 畫布完全未被繪製，無人機 3D 模型亦無法掛載。

---

## 2. 修正方案與架構防禦 (Remediation & Architectural Safeguards)

### 2.1 變數宣告前置化 (Hoisting to State Header)
1. 將 `let dynamicTestObstacleObj = null;` 提升宣告至全域狀態區（與 `let activeObstacles = [];` 並列，位於 `switchEnvironment()` 函式定義之前）。
2. 同步移除第 2251 行的多餘重複宣告，維持單一事實來源（Single Source of Truth）。
3. 同步修改 Python 產生器 `flight_test_sim.py` 與靜態預產出檔 `output/flight_test_simulator.html`。

### 2.2 自動化防護回歸測試 (Automated Regression Gate)
在 `test_webgl_environments.py` 中新增 `test_flight_simulator_dynamic_obstacle_declaration_order`，自動化驗證：
- `dynamicTestObstacleObj` 宣告位置必須嚴格早於 `switchEnvironment` 函式與初期化呼叫。
- 杜絕未來因代碼重構再度產生 TDZ ReferenceError。

---

## 3. 驗收標準 (Acceptance Criteria)

- [x] **AC-1**: 執行 `output/flight_test_simulator.html` 時，控制台拋出之致命例外由 1 降為 0（Zero Runtime Exceptions）。
- [x] **AC-2**: 3D 場景與無人機模型（32 個組件）正常掛載與渲染，物理引擎與動畫循環正常運作。
- [x] **AC-3**: 突發障礙物功能（按鍵 `O` / 按鈕）可正常動態插入與移除紅柱障礙物，不引發作用域錯誤。
- [x] **AC-4**: 自動化測試全數通過（`pytest` 69/69 通過，包含新增之 TDZ 迴歸測試）。
