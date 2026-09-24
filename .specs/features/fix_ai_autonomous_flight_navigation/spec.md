# Feature Spec：[FIX-M2-AI-AUTONOMOUS-MULTIGATE] WebGL AI 自主飛行多道穿越門導航與避障控制重構

> **版本**: 1.0  
> **功能 ID**: `FIX-M2-AI-AUTONOMOUS-MULTIGATE`  
> **狀態**: `Draft (Pending Human Sign-off)`  
> **對應專案憲章**: `Constitution Phase 2 [M2.5/M2.6] WebGL 3D 模擬環境 & AI 自主飛行巡檢`  
> **目標分支**: `fix/webgl-ai-autonomous-flight-multigate`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **關聯模組**: `flight_test_sim.py`, `output/flight_test_simulator.html`, `test_ai_autonomous_pipeline.py`, `autonomous_flight_learner.py`

---

## 1. 異常現象概述與根本原因分析 (Defect Overview & Root Cause Analysis)

### 1.1 異常現象回報 (Problem Statement)
使用者在 WebGL 3D 試飛模擬器（`output/flight_test_simulator.html`）中啟動「AI 自主試飛（Autopilot, 按鍵 P）」時，觀察到以下連續異常連鎖反應：
1. 紫色導航線出現，無人機起飛並飛向第一道門框（Gate #1）。
2. 無人機僅飛抵第一道門框下方或前緣，並未順利穿越門心。
3. 接著**未出現第二段紫色導航線**（航線中斷或消失）。
4. 無人機隨即發生飛行失控、劇烈偏航或翻滾撞擊競技場立柱與環境剛體障礙物，自主飛行徹底失敗。

### 1.2 深入除錯與 6 大根本原因 (In-Depth Root Cause Analysis)
經排查 `flight_test_sim.py` 與 WebGL 渲染／物理控制管線，確認該異常並非單一 Bug，而是由以下 6 個緊密相扣的架構與演算法缺陷共同引發：

1. **導航線僅支援單一頂點對，缺乏多航點全局航線走廊 (Single-Segment Line vs Global Trajectory Corridor)**：
   - 目前 `trajectoryLine` 僅配置 2 個頂點（`new Float32Array(6)`），硬編碼為無人機當前位置連接至 `aiGates[currentAIGateIndex]`。
   - 系統並未預先繪製 Gate 1 ➔ Gate 2 ➔ Gate 3 ➔ Gate 4 ➔ Gate 1 的連續閉合迴路導航走廊。
   - 當無人機在 Gate #1 發生碰撞或解編時，系統調用 `disengageAIAutopilot()` 直接將 `trajectoryLine.visible = false` 關閉，造成視覺上「第二段導航線憑空消失」的斷崖體驗。
2. **人工位能場（APF）目標門自斥相剋效應（The Invisible Wall Bug）**：
   - 在 `buildCollisionArena()` 中，門框的三大剛體（左立柱 `postL`、右立柱 `postR`、頂橫樑 `topMesh`）全數被加入 `activeObstacles` 障礙物列表。
   - 在 AI 控制迴圈中，APF 斥力半徑設定為 `safeDist = 3.2m`。
   - 然而門框開口寬度僅 $4.5\text{m}$（兩側立柱距中心各 $2.25\text{m} < 3.2\text{m}$），頂樑位於 $y = 4.95\text{m}, z = -7.0\text{m}$（距門心垂直高度 $1.75\text{m} < 3.5\text{m}$）。
   - 當無人機飛近門框時，**目標門框自身的三個構件同時向無人機施加高達 $+1.5 \sim +3.0$ 的反向斥力（$+Z$ 方向）**，直接抵銷了目標吸引力（`attractZ = -1.5`）。這在門框開口處形成了一道無形的「斥力空氣牆」，使無人機在門框下方失速懸停或被壓向地面。
3. **過早航點切換判定且缺乏門面穿透向量檢驗 (Premature Waypoint Switching)**：
   - 航點切換邏輯僅以歐氏距離 `dist3D < 1.8m` 判定。
   - 當無人機尚在 Gate #1 前方 $1.8\text{m}$（$z \approx -5.2\text{m}$，尚未跨過 $z = -7.0\text{m}$ 門面）時，系統便判定通過並切換為 Gate #2（位於 $x = +9.0, z = 0.0$）。
   - 無人機在尚未穿門的情況下立即執行向右急轉（$\Delta\text{Yaw} \approx 121^\circ$），直接朝 Gate #1 的右側立柱（$x = +2.25, z = -7.0$）加速撞擊。
4. **競技場 3D 門框朝向未對齊飛行航道 (Gate Orientation Mismatch)**：
   - 目前競技場中所有 4 道門均沿 Z 軸擺放（位於 X-Y 平面，未作旋轉）。
   - Gate #1 位於 $(0, 3.2, -7)$ 面向 Z 軸正常；但 Gate #2 位於 $(9, 4.5, 0)$，航道乃由西向東（沿 +X 方向）進入！
   - 因 Gate #2 未旋轉 90 度，其寬達 $4.25\text{m}$ 的橫樑與門框側面正對迎面而來的無人機，形成一道橫向阻擋牆。
5. **LiDAR 感測器於門洞穿梭時觸發神經質偏航迴避 (LiDAR False Evasive Yaw Panic)**：
   - 控制邏輯中包含 `if (latestLiDARReading.dist < 1.8) rotationSpeed = ...` 之硬性迴避。
   - 當無人機筆直穿過門洞時，前向與側向 LiDAR 射線偵測到門框立柱邊界（$< 1.8\text{m}$），瞬間強行覆蓋航向對齊控制，令無人機在進門前夕猛烈左右甩尾擦撞門柱。
6. **擦撞即失控解編的脆性機制 (Fragile Crash Disengagement)**：
   - 現有碰撞機制在輕微擦撞時迅速累積損傷，一旦損傷達到臨界值立即切斷 AI 控制（`isAIAutopilotActive = false`）。
   - 在無使用者手動接管的情況下，無人機瞬間失去推力與姿態補償，進入失速翻滾撞擊墜毀。

---

## 2. 核心目標與使用者故事 (User Story & Non-Goals)

### 2.1 使用者故事 (User Story)
* **As a** 數位孿生飛行模擬器測試工程師與使用者，
* **I want to** 在 WebGL 試飛環境中一鍵啟動 AI 自主飛行後，能清晰看見全局貫穿 4 道穿越門的完整導航走廊與當前目標導引線，
* **So that** 無人機能平穩順暢起飛、依序穿透 Gate #1 ➔ Gate #2 ➔ Gate #3 ➔ Gate #4 形成穩定閉合巡弋圈，並在遭遇輕微擾動時具備自穩定恢復能力，杜絕門前失控撞擊。

### 2.2 非目標範疇 (Non-Goals)
* ❌ **不更換物理引導算法框架**：維持以人工位能場（APF）、向量流引導與 6-DOF 飛行動力學為核心，不引入外部龐大的神經網路推論運行庫（ONNX WebGL runtime）。
* ❌ **不破壞現有手動／共用自主副駕駛功能**：手動鍵盤控制、Expo 桿量修形與 M2.6 Shared Autonomy Copilot 介入邏輯保持 100% 相容。

---

## 3. 功能性需求與驗收標準 (Requirements & Acceptance Criteria)

### 3.1 功能性需求 (Functional Requirements)

- [ ] **FR-1: 全局多段閉合 3D 導航走廊與動態高亮 (Full-Circuit Navigation Corridor)**
  - 渲染完整連結 Gate #1 ➔ Gate #2 ➔ Gate #3 ➔ Gate #4 ➔ Gate #1 的 3D 霓虹紫色導航迴路（Polyline / Tube / Spline）。
  - 當前目標航段（無人機至目標門）以高亮動態脈衝線顯著導引。
  - 當航點推進時，導引線平滑切換至下一目標門，航線走廊永不因正常過門而中斷。

- [ ] **FR-2: 門框智能感應與 APF 穿越通道過濾 (Smart Gate Tunnel Repulsion Filtering)**
  - 在 APF 位能場計算中，將「當前目標門」標記為通過目標，排除其頂橫樑與中心後方之反向斥力。
  - 僅在無人機距離立柱過近（如 $< 0.6\text{m}$）時施加微幅側向居中對齊力，徹底清除門前「斥力空氣牆」。

- [ ] **FR-3: 門面法向穿越判定狀態機 (Gate Plane Normal Crossing State Machine)**
  - 改進航點推進邏輯：由單純的三維半徑判斷，升級為「進門引導點 ➔ 門面穿越（穿過門面法向量平面）➔ 出門過渡點」之三態判定。
  - 確保無人機完全穿透門框物理深度後，才平滑過渡轉向下一個目標航向。

- [ ] **FR-4: 競技場 4 道穿越門 3D 朝向與法向量旋轉校準 (Gate 3D Rotation Alignment)**
  - 校準 `collision_arena` 中 4 道穿越門之擺放角度與碰撞 Bounding Box：
    * **Gate #1**: 位於 $(0.0, 3.2, -7.0)$，朝向 $0^\circ$（法向沿 $-Z$），迎接入場爬升。
    * **Gate #2**: 位於 $(9.0, 4.5, 0.0)$，旋轉 $90^\circ$（法向沿 $+X$），迎接向東巡檢。
    * **Gate #3**: 位於 $(0.0, 6.0, 9.0)$，旋轉 $180^\circ$（法向沿 $+Z$），迎接向北高空穿越。
    * **Gate #4**: 位於 $(-9.0, 3.8, 0.0)$，旋轉 $-90^\circ$（法向沿 $-X$），迎接向西返航閉環。

- [ ] **FR-5: 穿門階段 LiDAR 感測死區濾波 (Gate Passage LiDAR Deadzone Filter)**
  - 當無人機距離目標門框小於 $2.5\text{m}$ 且航向對準門心時，抑制 LiDAR 針對該門框幾何引發的恐慌性偏航迴避，保持目標導引航向穩定。

- [ ] **FR-6: 擦撞韌性恢復與姿態自穩 (Resilient Attitude Hold & Recovery)**
  - 當 AI 自主飛行遭遇輕微剛體接觸（速度低於破壞性極限）時，觸發自穩定姿態修正（自動 Leveling 與高度爬升），而非立即直接失控解編。

---

### 3.2 驗收標準 (Acceptance Criteria, AC)

- [ ] **AC-1: 全局導航走廊渲染驗收**
  - WebGL 畫面中存在包含 4 個航點以上之連續紫色導航迴線，且當前目標航段清晰可辨。
- [ ] **AC-2: 順暢穿越 Gate #1 且無門前斥力阻滯**
  - 無人機起飛後沿導引線平滑穿越 Gate #1 門心（穿越時垂直高度介於 $2.6\text{m} \sim 3.8\text{m}$），無門框下方懸停或失速下沉現象。
- [ ] **AC-3: 自動連續過門與航線平滑銜接**
  - 通過 Gate #1 後，導航線立即無縫指向 Gate #2，且無人機朝 Gate #2 順暢爬升轉向，不撞擊 Gate #1 立柱。
  - 連續自主飛行成功完成至少 1 圈（Gate #1 ➔ #2 ➔ #3 ➔ #4 ➔ #1）全場巡檢，累計巡航圈數 HUD 正常遞增。
- [ ] **AC-4: 自動化單元測試覆蓋**
  - 在 `test_ai_autonomous_pipeline.py` 新增多門導航走廊驗證、門面穿透判定驗證與門框幾何旋轉角度斷言，全數通過。
