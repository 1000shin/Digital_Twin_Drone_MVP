# Implementation Plan: [FEAT-M2.5.3] AI 自主飛行動力學三向優化

> **關聯 Spec**: `.specs/features/m2_5_3_flight_dynamics_optimization/spec.md`  
> **目標分支**: `feat/m2.5.3-flight-dynamics-optimization`  
> **狀態**: `Draft (Pending Architecture Review & Sign-off)`  
> **更新日期**: 2026-09-25  

---

## 1. 任務拆解 (Task Groups & Phased Roadmap)

### 📌 Task Group 1: 實作自適應速度曲線與動態推力釋放 (Speed Profiling)
- **目標**：解決 AI 飛行巡航速度過慢問題，在大直道空曠區加速至 $4.5 \sim 5.0\text{ m/s}$，並在穿門與轉向時平穩降速。
- **改動檔案**：
  - `flight_test_sim.py`
  - `output/flight_test_simulator.html`
- **實作步驟**：
  1. 引入航段目標速度計算函數 `computeAdaptiveCruiseSpeed(stage, distToGate, obstacleClearance)`：
     - 直線空曠（`CORNER` ➔ `APPROACH`，前方無近距障礙）：目標速度設為 $4.5 \sim 4.8\text{ m/s}$。
     - 轉彎過渡（`CORNER` 轉角前）：目標速度降至 $2.8 \sim 3.0\text{ m/s}$。
     - 門框穿透（`APPROACH` ➔ `THROUGH`）：目標速度穩定在 $2.0 \sim 2.2\text{ m/s}$。
  2. 動態調整姿態傾角限制：空曠直線時前傾角限制放寬至 $0.48\text{ rad}$（約 $27.5^\circ$），大幅增加水平推力加速度；穿門與狹窄區收攏至 $0.18\text{ rad}$（約 $10^\circ$）。
  3. 調整 LiDAR 阻尼閾值，避免空曠飛行時過早降速。

---

### 📌 Task Group 2: 前瞻軌跡平滑、二階偏航平滑與向心滾轉協同 (Smooth Turning & Banking)
- **目標**：解決轉彎生硬直角折線與甩尾抽動問題，使航跡呈現連續圓弧，並具備真機般自然內傾側翻的向心轉向姿態。
- **改動檔案**：
  - `flight_test_sim.py`
  - `output/flight_test_simulator.html`
- **實作步驟**：
  1. **前瞻切線引導點（Pure Pursuit Lookahead）**：
     - 在轉角過渡區計算圓弧切線引導點，以距離前瞻量 $L_d = 2.5\text{m}$ 進行軌跡插值，消除折線頂點硬切。
  2. **二階偏航角加速度平滑（Yaw S-Curve Acceleration Profiling）**：
     - 對偏航角速度施加角加速度限制（$|\Delta \omega| \le 0.012\text{ rad/frame}$），配合低通濾波，使航向轉動平順連續。
  3. **空氣動力向心滾轉傾角補償（Coordinated Banking Turn）**：
     - 依據航空動力學公式計算向心傾角：
       $$\phi_{\text{coordinated}} = -\text{clamp}\left(\frac{v_{\text{fwd}} \cdot \omega_z \cdot 1.2}{9.81}, -0.32, 0.32\right)$$
     - 融入滾轉指令中，轉彎時機身自動向內側傾斜 $10^\circ \sim 18^\circ$ 提供向心力。

---

### 📌 Task Group 3: 狹道可通行性預判與高敏捷側傾加速穿障 (Narrow Gap Predictive Traversability & Tilted Sprint Traversal)
- **目標**：解決過窄障礙間距擦碰削切問題；過小狹縫刪除消極繞道，改由預判可通行性並變更機身傾角加速彈射穿透，出縫瞬間快速回正。
- **改動檔案**：
  - `flight_test_sim.py`
  - `output/flight_test_simulator.html`
- **實作步驟**：
  1. **狹道幾何與動態通行性預判（Predictive Traversability Feasibility Check）**：
     - 機載 LiDAR 提前在進縫前 $2.5\text{m}$ 掃描前方障礙柱橫向淨寬 $W_{\text{gap}}$ 與高度 $H_{\text{gap}}$。
     - 若 $0.65\text{m} \le W_{\text{gap}} < 1.6\text{m}$（小於機身水平翼展 $1.1\text{m}$），求解最佳側傾角：
       $$W_{\text{proj}}(\phi_{\text{slit}}) = W_{\text{drone}} \cos(\phi) + H_{\text{drone}} \sin(\phi) < W_{\text{gap}} - 0.15\text{m}$$
       得到目標翻滾傾角 $\phi_{\text{slit}} \in [50^\circ, 65^\circ]$。
  2. **高敏捷變更機身傾角與彈射加速穿透（Tilted Sprint Traversal）**：
     - 進縫前 $1.2\text{m}$ 主動將滾轉角切換至 $\phi_{\text{slit}}$，水平寬度驟縮至 $0.65\text{m} \sim 0.72\text{m}$。
     - 釋放前向大推力，將航速推升至 $4.2 \sim 5.0\text{ m/s}$，藉由高動能慣性「彈射穿透」狹縫，避免大傾角下掉高。
  3. **出縫極速姿態回正（Rapid Attitude Recovery）**：
     - 通過狹縫瞬間（$\text{signedDot} > 0.8\text{m}$），立即反扭矩拉回水平姿態（$\text{Roll} \to 0^\circ$）並補償高度。
  4. **常規門框／寬道微速對稱居中（Bilateral Center Seeking）**：
     - 若 $W_{\text{gap}} \ge 1.6\text{m}$，維持姿態平整（$|\text{Roll}| \le 8^\circ$），左右雙邊測距差平衡居中穿越。

---

### 📌 Task Group 4: 自動化測試擴充、回歸測試與編譯產出驗證
- **目標**：驗證全部 AC 驗收標準，確保現有 66 項測試與新增測試 100% 通過。
- **改動檔案**：
  - `test_privileged_drl_distillation.py`
  - `output/flight_test_simulator.html`
- **實作步驟**：
  1. 在 `test_privileged_drl_distillation.py` 新增單元測試：
     - `test_adaptive_velocity_profiling_in_simulator`：驗證自適應速度曲線相關參數與直道提速邏輯。
     - `test_coordinated_banking_turn_in_simulator`：驗證向心傾角計算與偏航平滑邏輯。
     - `test_narrow_gap_clearance_and_attitude_leveling`：驗證狹道可通行性診斷與姿態水平化限制。
  2. 執行 `python3 flight_test_sim.py` 重新生成 `output/flight_test_simulator.html`。
  3. 執行 `pytest` 確保所有測試 100% 通過。
