# Changelog

All notable changes to the **Morph-Twin UAV (Digital Twin Drone MVP)** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v11.0.0] - 2026-09-24

### Added
- **[M2.1] 有機造型 3D 列印 CAD 生成模組 (Organic Generative CAD)**:
  - 新增 `organic_cad_generator.py`：純 Python + NumPy 實作仿生有機幾何生成核心，具備中心流線艙體（Core Pod）、仿生漸變機臂（Bionic Tapered Arms）、沿力流多邊形輕量化鏤空肋條（Truss Cutouts）、末端馬達安裝座（Motor Mounts with M3 bolt patterns）與起落架支腳（Landing Skids）一體化長成。
  - 工業標準 STL 導出器：支援標準 80-byte header 之二進位 STL 與純文字 ASCII STL 導出，100% 符合 ISO/ASTM 規範，可直接載入 Cura / PrusaSlicer / Bambu Studio 切片列印。
  - 可製造性分析器 (`get_print_profile`)：自動計算外框包絡尺寸 ($X \times Y \times Z\text{ mm}$)、機身體積 ($V\text{ cm}^3$)、耗材預估重量（PLA / PETG / PA-CF）與推薦切片參數（層高、壁厚、填充率、支撐類型）。
  - 單元測試套件 `test_organic_cad.py`：7/7 項單元測試 100% 通過，涵蓋頂點/面數幾何、二進位 STL 結構、ASCII STL 語法、列印規格與模型庫資產驗證。
- **數位孿生工作流自動化聯動**:
  - `drone_builder.py`：`export_files` 自動導出 `output/<design_id>.stl` 與 `<design_id>_print_profile.json`。
  - `run_mvp_pipeline.py`：端到端管線自動生成 3D 列印 STL 與列印參數報告。
  - `cli.py`：命令列即時展示 3D 列印 STL 輸出路徑。
  - `output/models_archive/`：為所有歷史世代（Gen-1 ~ Gen-4）自動生成並永久封裝 STL 實體模型與 Print Profile。
  - `view_3d_drone.py`：WebGL 3D 檢視器 HUD 整合 3D 列印可製造性數據卡。

---

## [v10.0.0] - 2026-09-24

### Added
- **[M2.5] 虛擬環境無人干預強化學習 (RL) 訓練管線 (Autonomous RL Pipeline)**:
  - 新增 `drone_rl_env.py`：標準 Gymnasium 相容強化學習物理環境，包含 23 維觀測狀態向量、4 維連續動作推進、8 向 LiDAR 測距與穿門障礙物場景。
  - 新增 `autonomous_flight_learner.py`：人工勢能場（APF）引導與人類 2Hz 飛行遙測示範先驗策略學習器。
  - WebGL 試飛模擬器整合 AI Autopilot 控制面板與「兩階段起飛保護機制」。
  - 驅動形態演化長出 Gen-4 Sentinel Prime 哨兵領航機，歸檔至 `output/models_archive/gen_04_sentinel_prime_v4/`。

---

## [v9.0.0] - 2026-09-19

### Added
- **[DIG-13] 形態演化決策動機與血統溯源系統**:
  - 實作世代躍遷日誌、物理變革動機追蹤，自動導出 `output/evolution_lineage_report.md` 與 `output/evolution_history.json`。

---

## [v1.0.0 ~ v8.0.0] - 2026-09-18 ~ 2026-09-19

### Added
- Phase 1 MVP 核心管線（零件庫、URDF/SDF 生成、MAVLink v2 控制、形態基因長成）。
- Phase 2 進階 3D Gazebo 風場世界與感測器 3D FOV 覆蓋率評估。
- Phase 3 Foxglove Studio 3D 戰情室 (`.mcap`)、VTOL 傾轉旋翼幾何演化長成、Native PX4 SITL GUI 橋接器。
- WebGL 3D 飛行模擬器 4 大動態環境、碰撞局部結構損壞與 BOM 聯動維修系統。
