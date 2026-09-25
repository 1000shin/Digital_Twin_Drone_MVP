# Feature Specification: [FEAT-M2.5.3] AI 自主飛行動力學三向優化 (速度提升、圓滑轉彎、狹縫防撞)

> **功能標識**: `feat-m2.5.3-flight-dynamics-optimization`  
> **目標分支**: `feat/m2.5.3-flight-dynamics-optimization`  
> **關聯議題**: 1. AI 巡弋速度慢 2. 轉彎不夠圓滑順暢 3. 過小障礙間距碰撞擦撞  
> **階段**: `Draft (Pending Architecture Review & Sign-off)`  
> **更新日期**: 2026-09-25  

---

## 1. 痛點診斷與根本原因分析 (Root Cause Analysis)

### 1.1 議題 1：AI 自主飛行巡弋速度過慢 (Excessively Slow Cruise Speed)
- **現狀表現**：無人機在空曠長直線航段與全場巡弋時，飛行速度極度緩慢（平均約 $1.2 \sim 1.5\text{ m/s}$，相當於步行動態），缺乏真實競速無人機或高敏捷無人機的巡航推進力。
- **根本原因**：
  1. **靜態吸引力限速過低**：吸引目標速度在各航段均被硬編碼為固定值 $1.6\text{ m/s}$（`attract = 1.6`）。
  2. **姿態指令雙重折扣**：前向速度誤差反饋增益偏低（`0.45`），且被二次衰減係數（`0.70`）打折，有效最大俯仰前傾角（Pitch）僅約 $15^\circ$；產生的水平推力分量 $T \sin(\theta)$ 不足，機體無法快速累積前向動量。
  3. **非門框 LiDAR 阻尼過早介入**：當感測到 $1.6\text{m}$ 內有障礙物時，前向與側向速度直接乘上衰減因子（最低壓至 $0.3$），造成機體在接近障礙物或路徑收窄時嚴重停滯。

### 1.2 議題 2：轉彎生硬、缺乏圓滑順暢感 (Jerky Turns & Discontinuous Trajectory)
- **現狀表現**：無人機通過門後向外環轉角（Corner）前進、或由轉角折向下一道門時，轉向動作突兀、帶有強烈 90 度直角折線感與甩尾抽動，飛行姿態僵硬。
- **根本原因**：
  1. **折線航點階躍突變（Discrete Step Waypoint Jump）**：導航狀態機在切換階段（例如從出門點 `LEADOUT` 切換到 `CORNER`）時，引導點 `(leadX, leadZ)` 瞬間跳躍至數米外的幾何頂點，導致期望偏航角 `desiredYaw` 產生高達 $90^\circ$ 的步階躍進。
  2. **偏航控制缺乏階數平滑（No Angular Acceleration / Jerk Limit）**：偏航率 `rotationSpeed` 直接被限制為常數 $\pm 0.08\text{ rad/tick}$，機頭瞬間以最大角速度暴力轉動，在到達目標角度時又立即煞停，產生明顯的直角折線與抽蓄。
  3. **缺乏向心滾轉協同（Absence of Coordinated Banking Turn）**：目前的轉彎全靠純偏航（Flat Yaw）旋轉機身，向心力全由機體側滑後的誤差反饋被動拉回；缺乏航空動力學中藉由傾斜盤滾轉（Banking Roll）主動產生向心加速度 $a_c = \frac{v^2}{R}$ 的機制，導致轉彎時向外滑移（Skid）嚴重。

### 1.3 議題 3：過小的障礙間距直接以碰撞方式飛過 (Narrow Gap Collision & Clipping)
- **現狀表現**：在障礙物密集、門柱立柱間隔狹小（或突發障礙物緊貼航道）的狹窄走廊，無人機往往直接擦撞立柱或被機翼削切而過，甚至引發結構性損壞墜毀。
- **根本原因**：
  1. **等向性人工勢場（Isotropic APF）在狹縫中心相消**：傳統排斥勢場在兩側柱體間距小於斥力半徑之和時，左右兩側產生的排斥力向量方向相反、大小接近，在通道中心線附近合成斥力幾乎為零（Saddle Point 鞍點死鎖）；而前向吸引力依然存在，驅使無人機盲目往前衝。
  2. **姿態傾斜造成機體幾何外廓外擴（Attitude-Induced Bounding Sphere Inflation）**：無人機在有傾角（Pitch/Roll）狀態下，傾斜的機臂與旋翼上下延伸，佔用的空間包圍球比水平懸停時多出 $30\% \sim 50\%$。在窄縫中一旦機身側傾，旋翼梢端直接掃到立柱。
  3. **缺少狹縫可通行性分析（Gap Traversability Analysis）與微速置中策略**：系統未評估兩側障礙淨間距是否大於機體最小安全通過寬度（翼展 $1.1\text{m}$ + 安全餘裕），也未在通過窄縫時強制拉平機身姿態與限制低速。

---

## 2. 規格需求與技術架構 (Requirements & Architecture)

```
┌────────────────────────────────────────────────────────────────────────┐
│               AI 自主飛行控制架構 (FEAT-M2.5.3 三向優化)                │
├────────────────────────────────────────────────────────────────────────┤
│ 1. 自適應速度曲線 (Adaptive Velocity Profiling)                        │
│    - 直道空曠段: 4.5 ~ 5.0 m/s                                         │
│    - 轉角過渡段: 2.8 ~ 3.2 m/s                                         │
│    - 門框穿透段: 2.0 ~ 2.4 m/s                                         │
│    - 狹窄走廊段: 1.2 ~ 1.5 m/s                                         │
├────────────────────────────────────────────────────────────────────────┤
│ 2. 航跡平滑與協同向心轉彎 (Smooth Trajectory & Coordinated Turn)       │
│    - 前瞻純追蹤引導 (Lookahead Pure Pursuit, L_d = 2.5m)               │
│    - 二階臨界阻尼偏航角平滑 (Yaw S-Curve Acceleration Profiling)        │
│    - 空氣動力向心滾轉傾角補償: phi_bank = atan(v * omega_z / g)        │
├────────────────────────────────────────────────────────────────────────┤
│ 3. 狹道可行性預判與高敏捷側傾加速穿障 (Knife-Edge Slit Traversal)       │
│    - 過小狹縫 (0.65m <= W_gap < 1.6m < 翼展1.1m):                       │
│      * 預判穿越可行性: 求解 W_proj(phi) = W*cos(phi) + H*sin(phi) < W_gap│
│      * 側傾縮身加速衝刺: 變更傾角 Roll 至 55°~65° + 彈射加速 4.5m/s 穿透│
│      * 出縫極速回正: 迅速恢復水平姿態 (|Roll| -> 0°) 與高度補償          │
│    - 常規狹道/門框 (W_gap >= 1.6m): 微速對稱居中 (|Roll| <= 8°, 雙邊平衡)│
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1 FR-1: 階段自適應速度曲線 (Adaptive Speed Profiling)
- 根據 `aiNavStage` 與環境淨空間動態調節目標吸引速度 $V_{\text{target}}$：
  - **大直道衝刺（`CORNER` ➔ `APPROACH` 區間）**：當與目標門距離 $> 4.0\text{m}$ 且前方空曠時，設定 $V_{\text{target}} = 4.8\text{ m/s}$，前傾角上限放寬至 $28^\circ$（$0.49\text{ rad}$），實現強勁推力加速。
  - **入彎減速（`CORNER` 轉角過渡）**：進入轉角引導區時，設定 $V_{\text{target}} = 3.0\text{ m/s}$，平順轉向。
  - **穿門對準（`APPROACH` ➔ `THROUGH` 區間）**：設定 $V_{\text{target}} = 2.2\text{ m/s}$，以高精度保證門框穿越姿態穩定。
  - **狹窄通道（距離兩側障礙物 $< 1.4\text{m}$）**：速度自動降至 $1.3\text{ m/s}$ 微速精細調整。

### 2.2 FR-2: 前瞻軌跡引導與空氣動力協同向心轉彎 (Smooth Turn & Coordinated Banking)
- **前瞻純追蹤（Pure Pursuit Lookahead）**：
  - 廢除折線頂點硬切換，在轉角點與門出入口之間引入前瞻切線引導點：
    $$\mathbf{p}_{\text{lead}}(t) = (1 - \alpha) \mathbf{p}_{\text{current}} + \alpha \mathbf{p}_{\text{target\_waypoint}}$$
    藉由動態前瞻距離（$L_d = 2.5\text{m}$），使無人機在距離轉角前即提早平順進入圓弧外側過彎軌跡。
- **二階偏航加速度平滑濾波（Yaw S-Curve Smoothing）**：
  - 偏航角速度不再使用硬截斷，而採用角加速度限制（$\alpha_{\text{max}} = 0.015\text{ rad/tick}^2$）與臨界阻尼低通濾波，使航向角變化連續且平滑無抽動。
- **向心滾轉傾角補償（Coordinated Banking Roll）**：
  - 根據無人機目前切線航速 $v_{\text{fwd}}$ 與偏航轉向速率 $\omega_z$，計算向心傾角：
    $$\phi_{\text{coordinated}} = -\text{clamp}\left(\arctan\left(\frac{v_{\text{fwd}} \cdot \omega_z \cdot 1.2}{g}\right), -0.35, 0.35\right)$$
  - 將 $\phi_{\text{coordinated}}$ 作為主動前饋融入滾轉角指令 `targetRoll` 中，使機身在高速過彎時自然傾斜內切，利用升力水平分量提供向心力，實現如同航模或真機般的流暢圓弧轉向。

### 2.3 FR-3: 狹道可通行性預判與高敏捷側傾加速穿障 (Narrow Gap Predictive Traversability & Tilted Sprint Traversal)
- **核心設計變更（User Directive）**：
  - **刪除過小狹縫繞道目標**：無人機任務不採消極迂迴繞道，而是直面挑戰狹窄障礙間距。
  - **預判穿越可行性（Predictive Traversability Feasibility Check）**：
    - 在距離前方障礙物狹縫 $2.5\text{m}$ 處，利用 8 向 LiDAR 與障礙包圍盒計算狹縫淨寬 $W_{\text{gap}}$ 與高度 $H_{\text{gap}}$。
    - **幾何投影可穿透性診斷**：
      - 水平狀態機身翼展 $W_{\text{drone}} = 1.10\text{m}$，機體高度 $H_{\text{drone}} = 0.25\text{m}$。
      - 當無人機側傾滾轉角為 $\phi$ 時，其水平投影寬度為：
        $$W_{\text{proj}}(\phi) = W_{\text{drone}} \cos(\phi) + H_{\text{drone}} \sin(\phi)$$
      - 求解最佳側傾穿障角 $\phi_{\text{slit}} \in [45^\circ, 65^\circ]$，使得：
        $$W_{\text{proj}}(\phi_{\text{slit}}) < W_{\text{gap}} - \Delta_{\text{margin}} \quad (\text{其中 } \Delta_{\text{margin}} \ge 0.15\text{m})$$
      - 同步檢查狹縫高度是否滿足垂直投影高度：$H_{\text{proj}}(\phi_{\text{slit}}) = W_{\text{drone}} \sin(\phi) + H_{\text{drone}} \cos(\phi) < H_{\text{gap}}$。
- **變更機身傾角彈射加速穿越（Knife-Edge Ballistic Sprint Traversal）**：
  - **階段 1：提早對準與翻滾變更傾角（Slit Approach & Roll-In）**：
    - 航點對齊狹縫中心軸線，在進縫前 $1.2\text{m}$ 迅速翻滾至預判目標傾角 $\phi_{\text{slit}}$（約 $55^\circ \sim 65^\circ$），水平投影寬度由 $1.1\text{m}$ 驟減至 $0.65\text{m} \sim 0.72\text{m}$。
  - **階段 2：大推力加速彈射穿透（Ballistic Velocity Boost）**：
    - 由於大側傾角下垂直升力 $T \cos(\phi)$ 劇降，若以慢速通過會因重力掉高墜毀；因此系統在此階段自動釋放強勁前向加速度，將穿障速度加速提升至 $4.2 \sim 5.0\text{ m/s}$，利用高動能慣性「穿針引線」瞬間射出狹縫！
  - **階段 3：出縫極速姿態回正（Rapid Attitude Recovery & Altitude Hold）**：
    - 機身尾端一脫離狹縫（$\text{signedDot} > 0.8\text{m}$），立即施加最大反向滾轉力矩將姿態拉回水平（$\phi \to 0^\circ$），並給予垂直高度油門補償，平穩回歸常態巡航。
- **常規可行狹縫／門框（$W_{\text{gap}} \ge 1.6\text{m}$）**：
  - 啟用「微速平身對稱居中穿透」：
    1. **姿態水平化（Attitude Leveling）**：限制最大傾角 $|\theta| \le 10^\circ, |\phi| \le 8^\circ$，防止機翼梢端削切立柱。
    2. **雙邊距差平衡導引（Bilateral Center Seeking）**：依據左右 LiDAR 測距差 $(d_L - d_R)$ 自動平衡微調橫向推力，沿中軸線穩定通過。

---

## 3. 驗收標準 (Acceptance Criteria, AC)

- [ ] **AC-1: AI 巡航速度顯著提升且具備自適應變速**
  - 在空曠直線航段（Gate 1 到 Corner 1、Corner 1 到 Gate 2）飛行速度提升至 $\ge 3.8\text{ m/s}$（較原先 $1.5\text{ m/s}$ 提升 $> 150\%$）。
  - 在接近門框及轉向時平穩降速至 $2.0 \sim 2.5\text{ m/s}$，單圈巡航秒數明顯縮短。
- [ ] **AC-2: 轉彎圓滑流暢並具備向心側傾姿態**
  - 過彎航跡呈現圓滑連續曲線，消除 90 度直角劇烈硬折與機頭劇烈抽動。
  - 過彎時可觀察到無人機機身自然向內側傾斜（Roll Bank $\sim 10^\circ - 20^\circ$）進行流暢協同轉向。
- [ ] **AC-3: 狹窄間隙預判可行性、側傾縮身加速穿越零碰撞**
  - 面對常規門框（寬度充足）：機身保持水平姿態（$|\phi| \le 8^\circ$），雙邊距差精確居中無刮碰通過。
  - 面對過小狹窄間隙（小於水平翼展 $1.1\text{m}$）：AI 提早完成可行性預判，不迂迴繞道，主動變更機身側傾角至 $50^\circ \sim 65^\circ$ 並加速彈射穿透，出縫瞬間平穩回正，機體完整度維持 $\ge 95\%$。
- [ ] **AC-4: 全單元測試與回歸測試 100% PASS**
  - 現有 66 項單元測試持續 100% 通過，並新增對應之速度、轉向與狹縫側傾加速穿障單元測試。

---

## 4. 非目標 (Non-Goals)

- **非目標 1**：不重訓離線強化學習策略權重（`student_policy_stages.json`），保持現有 3 階段權重相容性，所有動力學優化於前端 APF 與控制律中融合生效。
- **非目標 2**：不變更既有鍵盤人工遙控手感與 Shared Autonomy Copilot 介入閾值。
