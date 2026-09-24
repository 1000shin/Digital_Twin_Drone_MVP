# Feature Spec：[FIX-M2.5.2-FLIGHT-BUGS] 飛行航線穿障回正與 AI 學習階段切換異常修復

> **版本**: 1.0  
> **功能 ID**: `FIX-M2.5.2-FLIGHT-BUGS`  
> **狀態**: `Under Review (Human Sign-off Required)`  
> **對應專案憲章**: `Constitution Phase 2 [M2.5.2] 特權深度強化學習蒸餾與多階段學習檢查器`  
> **目標分支**: `fix/m2.5.2-bugs`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **關聯模組**: `flight_test_sim.py`, `output/flight_test_simulator.html`, `test_privileged_drl_distillation.py`

---

## 1. 問題概述與試飛異常現場分析 (Problem Statement & Root Cause Analysis)

在 M2.5.2（特權深度強化學習蒸餾與多階段學習檢查器）上線後，使用者在 WebGL 飛行模擬器中回報兩項重大缺陷：

### 1.1 Bug 1: 飛行路徑未依循紫色規劃路徑，持續碰撞門框，第二門後由門後穿出（未由門前進入）

#### 🔴 現象描述
1. 競技場中繪製的紫色虛線為閉環巡檢走廊（`circuitPts`）。
2. 無人機起飛後通過 Gate #1 後，在飛向 Gate #2、Gate #3、Gate #4 時，並未依循紫色引導線「門前進門點 ➔ 門心穿透 ➔ 門後引導點 ➔ 外環轉角」的順序穿障。
3. 無人機自 Corner #1 飛往 Gate #2 時，航跡大幅偏出，直接由 Gate #2 的「後方/外側」掠過或嚴重撞擊 Gate #2 右立柱與橫樑。
4. 在第二道門之後，無人機完全在門框背面飛行，無法達成由門正面穿越的標準巡檢姿態。

#### 🔍 根本原因（Root Cause 1）
1. **導航狀態機缺失「門前進門引導點（APPROACH / ENTRY）」階段**：
   - 場景中繪製的紫色引導線 `circuitPts` 明確定義了四點式穿門走廊：
     $$\text{Corner}_{i-1} \longrightarrow \left(\text{Gate}_i - \mathbf{n}_i \times 2.2\text{m}\right) \longrightarrow \text{Gate}_i \longrightarrow \left(\text{Gate}_i + \mathbf{n}_i \times 2.2\text{m}\right) \longrightarrow \text{Corner}_i$$
     其中 $\text{Gate}_i - \mathbf{n}_i \times 2.2\text{m}$ 為**門前進入點**。
   - 然而，`flight_test_sim.py` 與前端模擬器的巡航狀態機僅實作了三階段：
     `aiNavStage` $\in \{\text{'THROUGH'}, \text{'LEADOUT'}, \text{'CORNER'}\}$。
   - 當無人機抵達轉角點 $\text{Corner}_1 (7.0, -9.5)$ 後，狀態機直接跳入 `'THROUGH'`，且其目標點立即設為**門後穿出點**：
     $$\text{leadX} = \text{targetGate.x} + \text{targetGate.nx} \times 1.6\text{m}$$
   - 以 Gate #2 為例，其法向量朝東（$\mathbf{n}_2 = [1, 0]$），門中心在 $X=9.0, Z=0.0$，其後方出門點為 $(10.6, 0.0)$。
   - 無人機由 Corner #1 $(7.0, -9.5)$ 筆直飛向 $(10.6, 0.0)$ 時，在 $Z=-2.0$ 處的軌跡座標已達 $X \approx 9.57$（位於門框後方/外側），恰好迎面切入 Gate #2 的右側立柱 $(9.0, -2.0)$！
2. **通門判定（`hasCrossedGate`）存在「後門穿越假陽性」**：
   - 目前判定公式為：
     $$\text{signedDot} = (X - \text{Gate.x}) \cdot \mathbf{n}_x + (Z - \text{Gate.z}) \cdot \mathbf{n}_z \ge 0.35\text{m} \quad \text{且} \quad \text{lateralDist} < 2.5\text{m}$$
   - 因為無人機是由門後方切入，其在門後的投影距離 $\text{signedDot}$ 一開始就是正值（$> 0.35\text{m}$）。一旦橫向距離進入 $2.5\text{m}$ 範圍，系統立即誤判「已成功穿門」，直接切換為 `'LEADOUT'` 與下一階段，導致無人機永遠由門後繞過，從未真正由正面穿門。
3. **門框側柱與頂樑近身斥力死角**：
   - 門框側柱的橫向推擠門檻過窄（$d < 0.85\text{m}$ 才啟動），在高速巡航時煞車與偏轉響應不足；且頂樑完全被遮蔽排除（`if (obs.isGateTop) return;`），導致爬升高度不精準時直接削切橫樑。

---

### 1.2 Bug 2: 切換至 40% 學習程度 AI（`stage_1_half_trained`）時，整個場景完全停止 (Freeze)

#### 🔴 現象描述
在模擬器 UI 點擊「🌿 40% 半熟」神經網絡切換按鈕，或調用 `switchAIStage('stage_1_half_trained')` 時，3D 畫布與無人機飛行完全凍結，HUD 停止更新，幀率驟降為 0 FPS。

#### 🔍 根本原因（Root Cause 2）
1. **變數作用域未宣告直接引用（JavaScript `ReferenceError`）**：
   - 檢視 `flight_test_sim.py` 第 2660~2688 行與 `output/flight_test_simulator.html`：
     ```javascript
     } else if (currentStudentStageKey === 'stage_1_half_trained' && neuralAct) {
         // Stage 1: Half-trained network - partial obstacle evasion, slight wobble
         rawPitchCmd = Math.max(-0.75, Math.min(0.75, neuralAct[0] * 0.6 + (-errFwd * 0.45) * 0.4));
         rawRollCmd = Math.max(-0.75, Math.min(0.75, neuralAct[1] * 0.6 + (-errRight * 0.45) * 0.4));
         targetPitch = rawPitchCmd * 0.70;
         targetRoll = rawRollCmd * 0.70;
         rotationSpeed = Math.max(-0.09, Math.min(0.09, neuralAct[2] * 0.08));
         throttleAcc = Math.max(-6.0, Math.min(14.0, altErr * 2.5 - velocity.y * 1.5 + neuralAct[3] * 3.0)); // 💥 altErr 在此處尚未宣告！
         aiConfidence = 78.5;
     } else {
         // Stage 2: Mastered - full agile APF + neural blend
         ...
         // 7. Damped Altitude Hold & Vertical Climb Control
         const altErr = targetAlt - drone.position.y; // ⚠️ altErr 被封裝在 else 區塊中！
         throttleAcc = Math.max(-6.0, Math.min(14.0, altErr * 3.8 - velocity.y * 1.8));
         ...
     }
     ```
   - 在 `stage_1_half_trained` 分支中，直接引用了變數 `altErr` 計算高度油門補償；但 `const altErr` 卻是在隨後的 `else` 區塊（`stage_2_mastered`）內部才使用 `const` 宣告。
   - 在 JavaScript 規範下，存取未宣告或在該塊級作用域外的變數會立即拋出 `Uncaught ReferenceError: altErr is not defined`。
   - 由於此例外發生在每秒執行 60 次的 `requestAnimationFrame(animate)` 主渲染循環中，未捕獲的例外導致渲染隊列永久中斷，造成整個 3D 場景與模擬器完全死鎖凍結。

---

## 2. 核心架構需求與技術方案 (Requirements & Technical Solutions)

### 2.1 FR-1: 導航狀態機升級為四階段完整閉環 (`APPROACH` ➔ `THROUGH` ➔ `LEADOUT` ➔ `CORNER`)
- **四階段狀態定義**：
  1. `APPROACH`（門前對齊進門點）：目標點設為 $\text{Gate}_i - \mathbf{n}_i \times 2.2\text{m}$，高度對齊門框高度 $\text{Gate}_i.y$。
     - **切換條件**：當無人機抵達門前引導區（距離進門點 $< 1.5\text{m}$，且位於門前方 $\text{signedDot} \le -0.2\text{m}$、橫向偏差 $< 2.0\text{m}$）時，切換為 `THROUGH`。
  2. `THROUGH`（直線貫通穿門點）：目標點設為 $\text{Gate}_i + \mathbf{n}_i \times 1.8\text{m}$。
     - **切換條件**：無人機必須由門前（負 $\text{signedDot}$）切入門後（正 $\text{signedDot} \ge 0.35\text{m}$），且通過時橫向偏差 $< 2.0\text{m}$、高度偏差 $< 1.8\text{m}$。
  3. `LEADOUT`（出門緩衝走廊）：目標點設為 $\text{Gate}_i + \mathbf{n}_i \times 2.6\text{m}$。
     - **切換條件**：距出門點 $< 1.2\text{m}$ 或 $\text{signedDot} \ge 2.2\text{m}$ 時，切換至 `CORNER`。
  4. `CORNER`（外環轉角巡航）：目標點設為 $\text{Corner}_i$。
     - **切換條件**：距轉角點 $< 2.2\text{m}$ 時，`currentAIGateIndex = (currentAIGateIndex + 1) % 4`，切換至下一道門的 `APPROACH` 狀態。
- **初始起飛適應**：
  - 機體自地面發射台 $(0, 0.05, 0)$ 垂直爬升至安全高度後，初始狀態直接設為 Gate #1 之 `APPROACH` 點 $(0, 3.2, -4.8)$，不再直接暴衝穿越點。

### 2.2 FR-2: 嚴格正面進門狀態防護與門框 APF 斥力走廊優化
- 根除從門後繞過誤計分：在 `THROUGH` 階段建立歷史標記 `approachedFromFront = true`，非自正面進門者不觸發通門完成與獎勵。
- 門柱避碰緩衝：目標門側柱排斥範圍擴大至 $1.2\text{m}$，並在橫樑上方 $0.6\text{m}$ 處引入平滑垂直推力防切頂。

### 2.3 FR-3: 作用域提升與渲染循環防禦健全化 (Scope Hoisting & Exception Shield)
- 將 `const altErr = targetAlt - drone.position.y;` 提升（Hoist）至所有 AI 策略分支（`stage_0_untrained`, `stage_1_half_trained`, `stage_2_mastered`）之前，確保所有分支均可安全存取高度誤差。
- 在神經網絡推理與動態分支控制外層加入防禦性 `try-catch` 包裹，若模型推理或變數發生異常時記錄警告並自動降級回穩態 APF 巡航，防止任何運行時例外使 `animate()` 死鎖。

---

## 3. 驗收標準 (Acceptance Criteria, AC)

- [ ] **AC-1: 航向嚴格依循紫色規劃路徑進出每一道門**
  - 無人機在所有 4 道門（Gate #1 ~ Gate #4）均確實依序走完：
    `進門引導點 (正面進入)` ➔ `門心穿透` ➔ `出門走廊` ➔ `外環轉角`。
  - 徹底終結「第二道門由後方飛過」現象，進門時門面法線與飛行向量夾角 $\le 30^\circ$。
- [ ] **AC-2: 4 道門無碰撞完整穿越全場**
  - AI 自主巡航在碰撞競技場中完成至少 1 圈（4 道門）連續飛行，不發生卡死在立柱或削切門框現象，機體完整度維持在 $\ge 85\%$。
- [ ] **AC-3: 40% 學習階段 AI 平順切換零崩潰**
  - 點擊「🌿 40% 半熟」切換按鈕，WebGL 模擬器持續 60 FPS 流暢運行，畫面不卡死，無人機呈現對應之半熟學步姿態（輕微晃動但維持空中高度與航向推進）。
- [ ] **AC-4: 全單元測試與回歸測試 100% 通過**
  - 既有 64 項單元測試全數 PASS，新增之導航路徑與狀態機測試 PASS。

---

## 4. 非目標 (Non-Goals)

- **非目標 1**：不重訓神經網絡底層權重檔案（`student_policy_stages.json`），本修正聚焦於飛行控制狀態機、幾何路徑走廊與前端變數調用健全度。
- **非目標 2**：不變更風力、霧氣、外觀材質等無關之 WebGL 環境渲染特徵。
