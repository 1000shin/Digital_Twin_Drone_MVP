# Feature Spec：[FIX-M2.6-AI-CIRCUIT-COMPLETION] WebGL AI 自主飛行全場多門閉環導航與防撞解鎖

> **版本**: 1.0  
> **功能 ID**: `FIX-M2.6-AI-CIRCUIT-COMPLETION`  
> **狀態**: `Approved (Auto-Review Proceed to Execution)`  
> **對應專案憲章**: `Constitution Phase 2 [M2.5/M2.6] WebGL 3D 模擬環境 & AI 自主飛行巡檢`  
> **目標分支**: `fix/m2.6-ai-autonomous-flight-circuit-completion`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **關聯模組**: `flight_test_sim.py`, `output/flight_test_simulator.html`, `test_ai_autonomous_pipeline.py`

---

## 1. 問題概述與試飛遙測實證 (Problem Statement & Telemetry Evidence)

### 1.1 瀏覽器試飛實測現象 (70 秒連續監控)
在 WebGL 3D 飛行模擬器實體沙盒中執行無人機試飛，觀測到無人機無法完成 AI 自主飛行全場巡檢，具體時序如下：
1. **Gate #1 穿過後「回頭殺」擦撞**：在 $T+8\text{s}$ 穿過 Gate #1 門心後，航點過早跳轉為東側 Gate #2，引發無人機向右後方倒飛切入 Gate #1 右立柱與橫樑，完整度降至 51%。
2. **APF 舊門斥力相剋**：切換至 Gate #2 後，Gate #1 喪失目標門特權，其頂樑與立柱對無人機產生巨大斥力，與 Gate #2 引力激烈衝突。
3. **碰撞物理速度死鎖（No Depenetration）**：每一影格速度乘上 $-0.45$，無人機被吸附在 Gate #1 右立柱長達 53 秒（$T+14\text{s} \sim T+67\text{s}$）。
4. **航線直切立柱 #3 撞毀迫降**：在 $T+68\text{s}$ 滑脫後，以 $3.6\text{ m/s}$ 高速直奔 Gate #2，路徑貫穿「立體立柱 #3」$(3.0, -3.0)$，於 $T+69.25\text{s}$ 致命撞擊，完整度暴跌至 6%，AI 巡航失控終止。

---

## 2. 核心架構需求與修復方案 (Requirements & Technical Solutions)

- **FR-1: 門後出門走廊與航點狀態機緩衝 (Post-Gate Lead-Out Corridor)**
  - 穿過門心後，無人機必須先沿門法線方向直行延伸 $\ge 2.0\text{m}$ 至出門緩衝點，確保機身與旋翼徹底脫離門框幾何後，方可切換航向。
- **FR-2: 已通過門框 APF 斥力冷卻遮罩 (Cleared Gate Repulsion Mask)**
  - 門通過後賦予該門框 2.5 秒的斥力遮罩（Cooldown Mask），期間維持通道穿梭特權（忽略頂樑斥力、側柱僅輕微防貼近），根除新舊航點引力與斥力相剋夾死問題。
- **FR-3: 剛體碰撞位置解穿透 (Positional Depenetration Resolution)**
  - 重構 `activeObstacles` 碰撞檢驗：當 `droneBox` 侵入障礙物包圍盒時，沿最小穿透軸將無人機位置向量推離至障礙物表面外側（+0.05m 安全邊距），徹底終結速度幾何衰減歸零死鎖 Bug。
- **FR-4: 外環賽道轉角中繼點與立柱群避讓 (Perimeter Corner Waypoints)**
  - 在 Gate 1 ➔ 2 ➔ 3 ➔ 4 之間配置外環平滑中繼轉角點（Corner Waypoints），使導航線形成外繞競技場立柱群 $(\pm 3, \pm 3)$ 的優美安全走廊。
- **FR-5: 門前對齊進門點 (Pre-Gate Entry Alignment Waypoints)**
  - 在門前方 1.5m 設立進門引導點，使無人機在穿門前已提早將姿態與航向垂直校準於門面法線。

---

## 3. 驗收標準 (Acceptance Criteria, AC)

- [ ] **AC-1: 剛體碰撞無卡死吸附 (Zero Depenetration Trap)**
  - 任何與立柱或門柱之擦撞均能正常彈開並推離表面，速度不發生持續數十秒歸零吸附。
- [ ] **AC-2: 順暢連續完成至少 1 圈全場 4 門巡檢 (Full Circuit Completion)**
  - 啟動 AI 自主飛行後，無人機能連續平穩穿過 Gate #1 ➔ Gate #2 ➔ Gate #3 ➔ Gate #4 ➔ Gate #1，達成 `aiLapsCompleted >= 1`，全程不發生致命撞柱解編。
- [ ] **AC-3: 完整度維持健康安全水準 (Flight Integrity Health)**
  - 完成 1 圈巡檢後，機身結構完整度保持在 $\ge 80\%$（無災難性斷臂墜毀）。
- [ ] **AC-4: 自動化測試 100% 通過**
  - 現有 55 項單元測試與新擴充測試 100% 通過。
