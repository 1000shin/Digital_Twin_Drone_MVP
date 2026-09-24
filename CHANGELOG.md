# Changelog

All notable changes to the **Morph-Twin UAV (Digital Twin Drone MVP)** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v12.0.2] - 2026-09-24

### Fixed
- **[FIX-M2-AI-AUTONOMOUS-MULTIGATE] WebGL AI 自主飛行多道穿越門導航與避障控制重構**:
  - **全局閉合巡檢走廊 (`circuitLine`)**: 新增 5 頂點霓虹紫虛線走廊貫穿 Gate 1 ➔ 2 ➔ 3 ➔ 4 ➔ 1，搭配動態高亮青色即時導引線（`trajectoryLine`），消除了過門時導航線憑空消失問題。
  - **APF 目標門自斥解耦（根除空氣牆）**: 在障礙物斥力計算中識別 `obs.gateId === targetGate.id`，徹底過濾頂樑垂直排斥力；立柱僅保留 $< 0.85\text{m}$ 極近距離的純切向置中推力，引入前方 $1.6\text{m}$ 超前引導點（`leadTarget`）牽引機身平穩穿透。
  - **門面法向穿越狀態機**: 廢除無方向歐氏半徑切換，改採帶符號法向投影距離（`signedDot >= 0.35m`）與橫向距軸心限制（`lateralDist < 2.5m`），確保機身完全穿透門框物理厚度後才推進航點，徹底杜絕早熟轉向撞柱。
  - **競技場門框 3D 朝向旋轉**: 4 道門均賦予精確 `yaw`（$0^\circ, 90^\circ, 180^\circ, -90^\circ$）並以 `gateGroup` 封裝旋轉，呼叫 `updateMatrixWorld(true)` 生成世界座標系精準 `Box3` 碰撞盒。
  - **LiDAR 門洞穿梭死區濾波**: 靠近門框 $< 2.8\text{m}$ 且對準門心時，主動抑制 LiDAR 針對門柱引發的恐慌性偏航甩尾，穩定保持進門航向。
  - **輕微碰撞韌性自穩**: 臨界解編閾值收斂至 $\le 15$，配合主動姿態回正（Active Leveling）與高度爬升補償，消除極輕微擦撞失速墜毀。
  - **單元測試全綠燈**: 新增多門走廊與狀態機單元測試，51/51 項全套單元測試 100% 通過（耗時 9.0s）。

## [v12.0.1] - 2026-09-24

### Fixed
- **[FIX-M2-WEBGL-PLANE-TEARING] 3D 檢視器 WebGL 網格渲染平面破圖與 Z-Fighting 修復**:
  - 修復離岸風場動態海面網格缺乏即時法向量計算引發的面片撕裂與陰影斷裂，在 `view_3d_drone.py` 與 `flight_test_sim.py` 的逐幀渲染迴圈注入 `oceanGeo.computeVertexNormals()`。
  - 全域啟用 `THREE.WebGLRenderer({ antialias: true, logarithmicDepthBuffer: true })`，大幅提高大跨度深度緩衝精度，根除微小高度差平面的深度閃爍。
  - 擴展相機視椎體遠裁切面 `camera.far`（檢視器擴至 `1000m`，模擬器擴至 `2000m`），消除大場景拉遠時 350m 大地平面邊緣發生的直線對角硬裁切。
  - 離岸風場場景將基準空間格線 `currentGrid.position.y` 調整至 `-0.8m`，徹底避免正弦波峰穿刺格線；全地面材質加入 `side: THREE.DoubleSide` 與 `polygonOffset: true`（factor 1.0, units 1.0），徹底解決 Z-Fighting 穿透。
  - 單元測試套件 `test_webgl_environments.py` 新增防破圖斷言驗證，50/50 項全套單元測試 100% 通過（耗時 9.0s）。

## [v12.0.0] - 2026-09-24

### Added
- **[M2.6] 「人類主飛，AI 輔助介入」協同飛控副駕駛 (Shared Autonomy Copilot)**:
  - 新增 `shared_autonomy_copilot.py`：以雙層動態安全邊界（警戒區 2.0m ~ 1.2m 與緊急避險區 < 1.2m）為核心的自適應向量混合控制器。
  - 人類主控權優先與逃逸通道：支援操縱桿自由穿透（$\beta = 0.0$）、指向障礙物的速度平滑法向阻尼（$\alpha \in [0.4, 0.9]$）、人工勢能場主動排斥力（APF）與切線偏轉滑行推力。當飛手反向逃逸時完全釋放操縱阻力。
  - WebGL 3D 飛行模擬器 HUD 深度整合：新增鍵盤快捷鍵 `C` / HUD 切換按鈕、動態防護狀態徽章（`STANDBY` / `WARNING` / `DEFLECTING`）、即時排斥力場指示器與 3D 機身虛擬防護光環（Virtual Bumper Halo）。
  - MAVLink 飛控橋接整合：在 `MAVLinkController` 注入安全防撞過濾器 (`apply_copilot_safety_filter`)。
  - 單元測試套件 `test_shared_autonomy_copilot.py`：9/9 項測試 100% 通過，全專案 49 項單元測試 100% 通過（耗時 9.1s）。
- **[M2.1 Viewer] 3D STL 列印實體檢視器升級**:
  - 新增 `stl_viewer.py` 與 `output/stl_viewer.html`：獨立 Three.js WebGL STL 檢視器，內置 4 個世代（Gen 1 ~ Gen 4）Base64 幾何切換、500mm 工業級加溫底板、三角網格檢視、360° 自動巡檢、多重材質切換與本地 STL 拖放支援。
  - 修復毫米座標系下霧化遮蔽 Bug（Fog density 轉換為線性景深）與標準 CAD $Z$-up 旋轉修正。

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
