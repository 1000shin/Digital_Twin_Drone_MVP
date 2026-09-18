# 📜 數位孿生無人機系統 - 全流程開發紀錄與版本追溯 Master 報告 (Master Audit Report)

> **本檔案為本專案之「全流程開發紀錄與版本追溯 Master 報告 (Single Source of Truth)」。**  
> 詳細記錄從 **Phase 1 基礎 MVP 搭建** 至 **Phase 3 三大進階功能全數完成** 的技術架構演進、版本動態、檔案清單與測試驗證紀錄，供未來查驗、版本追溯與審核。

---

## 🏷️ 1. 版本演進與里程碑歷史 (Version Changelog & History)

| 版本號 | 日期 | 開發里程碑與核心變更 | 通過測試與驗證檔 |
| :--- | :--- | :--- | :--- |
| **v1.0.0** | 2026-09-18 | **MVP 核心 5 大工作方塊完成**：建立 `components_db.json` 零件庫、`drone_builder.py` (URDF/SDF 計算質心與慣性矩)、`mavlink_controller.py` (MAVLink 控航)、`morph_evolution.py` (基因演算法形態長成)、`run_mvp_pipeline.py` (閉環總控)。 | `test_db_loader.py`<br/>`test_drone_builder.py`<br/>`test_mavlink_controller.py`<br/>`test_morph_evolution.py`<br/>`test_run_mvp_pipeline.py` |
| **v2.0.0** | 2026-09-18 | **Phase 2 進階環境與感測器算力模組**：加入 `world_builder.py` (3D Gazebo 風場向量與障礙物場景)、`sensor_sim.py` (3D FOV 視場覆蓋率與盲區比率)、`mission_profiles.json` (真實任務 Prompt 庫) 與 `cli.py` (互動式命令列)。 | `test_next_phase.py` |
| **v3.0.0** | 2026-09-18 | **Phase 3 選擇 3 完成**：開發 `launch_simulation.sh` 與 `px4_sitl_bridge.py` 實現原生 PX4 SITL 飛控與 Gazebo 3D 物理 GUI 視窗連線整合，開放 **UDP 14540/14550** 連線。 | `test_choice_3.py` |
| **v4.0.0** | 2026-09-18 | **Phase 3 選擇 1 完成 (MAVLink v2 協定修復與 Foxglove 3D)**：升級通訊為原生 MAVLink v2 (`0xFD` 標頭)，加入 QGC 航點自動回應；開發 `foxglove_layout.json` (3D 戰情室)、`foxglove_bridge.py` 與 `mcap_exporter.py`，匯出原生 `.mcap` 檔案。 | `test_choice_1.py` |
| **v5.0.0** | 2026-09-18 | **Phase 3 選擇 2 完成**：開發 `vtol_builder.py` 與 `vtol_evolution.py` 實現 **VTOL 垂直起降與傾轉旋翼 (Tilt-Rotor) 複合幾何演化長成**，支援空氣動力升阻比 ($L/D$) 最佳化與 Gazebo Lift-Drag 外掛。 | `test_choice_2.py` |
| **v6.0.0** | 2026-09-18 | **3D WebGL 幾何外觀與測試場景檢視器**：開發 `view_3d_drone.py` 自動生成可直接在瀏覽器開啟的 `view_3d_scene.html` 網頁檔，提供無人機 CAD 長相與 3D 測試空間 360° 旋轉檢視。 | 瀏覽器 WebGL 實機驗證 |

---

## 🏛️ 2. 全系統軟體架構與資料流 (System Architecture & Dataflow)

全系統採用開源鬆散耦合 (Decoupled Architecture) 架構，資料對接流程如下：

```mermaid
graph TD
    A[mission_profiles.json / Prompt 任務需求] --> B[vtol_evolution / morph_evolution 基因演化長成]
    B -->|輸出 drone_spec.json| C[vtol_builder / drone_builder CAD & URDF/SDF 生成器]
    B -->|輸出環境需求| D[world_builder 3D 風場/障礙物世界生成器]
    C -->|產出 .sdf + .urdf| E[Gazebo 3D 物理與感測器模擬環境]
    D -->|產出 .world| E
    C -->|產出幾何數據| F[view_3d_drone 3D WebGL 外觀檢視器]
    F -->|生成| G[view_3d_scene.html (瀏覽器開啟看長相)]
    B -->|執行離線航點| H[mavlink_controller MAVLink v2 自主控制器]
    H <-->|UDP 14540 / 14550| I[PX4 SITL / QGroundControl 地面站 GUI]
    H -->|導出數據| J[mcap_exporter 導出 .mcap 戰情室紀錄]
    J -->|載入| K[foxglove_layout.json (Foxglove Studio 3D 儀表板)]
```

---

## 📁 3. 完整原始碼與產出檔案清單 (Source File Inventory)

所有原始碼與報告均妥善保存在工作區 `/Users/jasonzheng/Documents/Obsidian workspace/AI agent workspace/Digital_Twin_Drone_MVP/` 目錄下：

### 核心程式碼 (Python & Shell)
1. **`db_loader.py`**：數位零件庫載入與質量/推重比/航程物理估算。
2. **`drone_builder.py`**：多旋翼無人機幾何與 URDF/SDF 物理描述檔生成器。
3. **`vtol_builder.py`**：VTOL 垂直起降/傾轉旋翼幾何與 Gazebo Lift-Drag 氣動外掛生成器。
4. **`mavlink_controller.py`**：原生 MAVLink v2 (0xFD) 通訊介面與 UDP 廣播器。
5. **`morph_evolution.py`**：多旋翼無人機形態基因演化長成引擎。
6. **`vtol_evolution.py`**：VTOL 傾轉旋翼幾何與氣動升阻比 ($L/D$) 演化長成引擎。
7. **`world_builder.py`**：Gazebo 3D 風速向量與障礙物幾何場景生成器。
8. **`sensor_sim.py`**：感測器 3D FOV 視場覆蓋率與空間盲區比率算力評估。
9. **`px4_sitl_bridge.py`** & **`launch_simulation.sh`**：PX4 SITL 與 3D GUI 連線啟動橋接器。
10. **`foxglove_bridge.py`** & **`mcap_exporter.py`**：Foxglove Studio 3D 數據與 `.mcap` 容器檔導出器。
11. **`view_3d_drone.py`**：互動式 WebGL 3D 幾何外觀與測試場景 HTML 生成器。
12. **`cli.py`**：全功能互動式命令列主控入口。

### 設定檔與資料庫
1. **`components_db.json`**：馬達、螺旋槳、電池、感測器、材質物理資料庫。
2. **`mission_profiles.json`**：四大真實任務 Prompt 設定檔。
3. **`foxglove_layout.json`**：Foxglove Studio 3D 戰情室版面配置檔。

### 說明檔與查驗手冊
1. **`PROJECT_MASTER_REPORT.md`**：(本檔案) 全流程開發紀錄與版本追溯 Master 報告。
2. **`USER_MANUAL.md`**：使用者系統運行與操作 SOP 工作手冊。
3. **`README.md`**：專案結構說明檔。

---

## 🧪 4. 自動化測試與查驗結果矩陣 (Test Matrix)

本專案具備完整的自動化單元與整合測試套件，確保程式碼修改後隨時可進行品質查驗：

```bash
cd "/Users/jasonzheng/Documents/Obsidian workspace/AI agent workspace/Digital_Twin_Drone_MVP"

python3 test_db_loader.py          # ✅ PASSED (3/3 tests)
python3 test_drone_builder.py      # ✅ PASSED (2/2 tests)
python3 test_mavlink_controller.py # ✅ PASSED (2/2 tests)
python3 test_morph_evolution.py   # ✅ PASSED (1/1 test)
python3 test_run_mvp_pipeline.py   # ✅ PASSED (1/1 test)
python3 test_next_phase.py         # ✅ PASSED (2/2 tests)
python3 test_choice_1.py           # ✅ PASSED (2/2 tests)
python3 test_choice_2.py           # ✅ PASSED (2/2 tests)
python3 test_choice_3.py           # ✅ PASSED (2/2 tests)
```

---

## 🔍 5. 未來稽核、版本復原與成果查驗指引 (Audit Verification SOP)

1. **查驗無人機 3D 外觀長相**：
   開啟 `output/view_3d_scene.html` 或執行 `python3 view_3d_drone.py`，即可在網頁瀏覽器中進行 360° 旋轉查驗。
2. **查驗 3D 戰情室與飛行遙測**：
   在 Foxglove Studio 中開啟 `output/digital_twin_bridge_confined_inspection.mcap` 與 `foxglove_layout.json`。
3. **查驗地面站連線**：
   開啟 QGroundControl 並執行 `python3 cli.py 1`，確認左上角顯示 `Armed | Offboard`。
4. **版本變更覆核**：
   所有新增與更新紀錄均遵循 Obsidian Wiki-Links 標準，並已連結至 `AI Agent工作區MOC.md` 與 `Scriptable_Apps_MOC.md`。

---

*報告維護者：AI Agent (Antigravity)*  
*版本：v6.0.0 (Master Final)*  
*最後更新日期：2026-09-18*
