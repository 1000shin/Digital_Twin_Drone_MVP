# 🛸 數位孿生無人機系統 MVP (Digital Twin Drone MVP)
> **任務導向形態演化長成、參數化 CAD/SDF 生成、MAVLink 飛控閉環與 WebGL 3D 物理損害飛行模擬器**

[![Version](https://img.shields.io/badge/version-v7.0.0-blue.svg)](PROJECT_MASTER_REPORT.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)](flight_test_sim.py)
[![WebGL](https://img.shields.io/badge/WebGL-Three.js-orange.svg)](output/flight_test_simulator.html)
[![PX4 SITL](https://img.shields.io/badge/PX4-SITL%20%7C%20MAVLink-red.svg)](mavlink_controller.py)
[![Tests](https://img.shields.io/badge/tests-21%2F21%20passing-success.svg)](test_webgl_environments.py)

本專案提供一套純開源、任務導向的**數位孿生無人機端到端閉環研發環境**。無人機能根據任務目標需求（如載重、航程、狹窄空間避障、抗風性能）透過 DEAP 遺傳演化算法自動長出最佳幾何形態與電氣/感測配置，經由 CadQuery 自動生成 3D 幾何與 URDF/SDF 物理模型，並整合 MAVLink 自主控制協議、QGroundControl 地面站，以及**內建全動態 WebGL 3D 物理損毀飛行模擬器**進行實時驗證。

---

## 🌟 核心特色與功能亮點 (Key Features)

### 1. 🧬 任務導向形態與感測器演化長成 (Morphological Evolution)
- 基於 **DEAP (Distributed Evolutionary Algorithms in Python)** 遺傳演化算法。
- 根據環境與任務約束自動長出最適的無人機臂長、馬達 KV、螺旋槳尺寸、電池容量與感測器配置。

### 2. 📐 參數化 CAD 與 URDF/SDF 物理模型生成
- 利用 **CadQuery** 程式化實時產出無人機機架、馬達座、旋翼幾何。
- 自動生成符合 ROS 2 與 Gazebo Sim 規範的標準 `.urdf` 與 `.sdf` 物理描述檔（包含質量矩陣、轉動慣量與空氣動力係數）。

### 3. 🎮 全功能 WebGL 3D 物理損毀飛行模擬器 (WebGL 3D Flight Simulator)
直接在現代瀏覽器中以 60 FPS 順暢體驗無人機鍵盤試飛，內建最新三大核心功能：
- **📋 零件清單 BOM 抽屜面板 (DIG-8)**：
  - 現代化 Glassmorphism 暗色毛玻璃側邊抽屜，支援即時展開/收合。
  - 即時動態監控 7 大硬體零件（碳纖機臂、無刷馬達、旋翼、鋰電池、Pixhawk 6C 飛控、M10Q GPS、數位圖傳）規格、電氣狀態與推重比 (TWR)。
- **🌍 4 大無縫切換測試環境 (DIG-9)**：
  1. **🌊 離岸風場巡檢 (Offshore Wind Farm)**：動態波浪海水、巨大風電機葉片旋轉、海霧與強陣海風。
  2. **🏙️ 城市高樓搜救 (Urban City Search & Rescue)**：摩天大樓群、樓頂紅色急難救援信標與峽谷側風亂流。
  3. **⚡ 碰撞測試場地 (Collision Arena)**：全封閉線框防護護籠、FPV 發光穿越競速門框、黃黑警示防撞立柱。
  4. **🌙 夜間紅外線巡檢 (Night Thermal/Inspection)**：暗夜環境、機載高亮度探照燈、FLIR LWIR 8-14μm 熱成像偽色彩視覺與異常高溫設備警報 HUD。
- **💥 撞擊動態破損模擬系統 (DIG-10)**：
  - **真實局部破損網格**：碰撞速度大於閥值時，受撞機臂產生剪切彎折變形並切換焦黑碎裂材質，螺旋槳斷裂旋轉失衡。
  - **粒子特效與鏡頭震顫**：碰撞接觸點瞬間噴發 50+ 顆重力加算火花與碳纖維彈跳碎塊，鏡頭劇烈震動。
  - **HUD 完整度與 BOM 連動**：機身結構完整度儀即時警報，BOM 推重比動態暴跌，嚴重受損時觸發不可逆螺旋失速墜毀。
  - **🛠️ 一鍵維修復原**：按下 <kbd>R</kbd> 鍵一秒修復全機幾何外觀與飛航狀態。

### 4. 🛰️ MAVLink v2 & PX4 SITL 飛控支援
- 支援透過 UDP 14540 連接原生 PX4 SITL 進行 Offboard 模式自主導航。
- 支援透過 UDP 14550 即時串流至 **QGroundControl** 地面站，觀看人工姿態儀、GPS 軌跡與電池遙測。

---

## 🚀 快速上手指南 (Quick Start)

### 1. 立即體驗 WebGL 3D 試飛模擬器
直接使用瀏覽器開啟已生成的 HTML 檔案（無須任何後端伺服器）：

- 🚀 **鍵盤飛行試飛模擬器**：
  [`output/flight_test_simulator.html`](output/flight_test_simulator.html)
- 🛸 **幾何外觀與 CAD 場景檢視器**：
  [`output/view_3d_scene.html`](output/view_3d_scene.html)

### 2. 重新編譯與產生最新 WebGL 3D 場景
```bash
# 產生最新 WebGL 飛行模擬器
python3 flight_test_sim.py

# 產生最新 3D 幾何外觀檢視器
python3 view_3d_drone.py
```

### 3. 執行全套自動化單元測試
```bash
python3 -m unittest discover -s . -p "test_*.py"
```
*驗證包含幾何長成、MAVLink 控制、BOM 介面、4 大場景切換與撞擊破損模擬等 21 項測試（100% Pass）。*

### 4. 執行端到端數位孿生閉環管線
```bash
python3 run_mvp_pipeline.py
```

---

## 🕹️ 飛行模擬器鍵盤操控對照表 (Controls)

| 鍵位 | 操作功能 | 物理效果說明 |
| :---: | :--- | :--- |
| <kbd>W</kbd> | 俯仰低頭 (Pitch Down) | 向前飛行加速 |
| <kbd>S</kbd> | 俯仰抬頭 (Pitch Up) | 向後飛行減速 / 倒飛 |
| <kbd>A</kbd> | 左滾轉 (Roll Left) | 機體向左傾斜橫移 |
| <kbd>D</kbd> | 右滾轉 (Roll Right) | 機體向右傾斜橫移 |
| <kbd>Q</kbd> | 左偏航 (Yaw Left) | 機頭向左水平旋轉 |
| <kbd>E</kbd> | 右偏航 (Yaw Right) | 機頭向右水平旋轉 |
| <kbd>Space</kbd> | 垂直爬升 (Climb) | 增加總體油門與垂直升力 |
| <kbd>Shift</kbd> | 垂直下沉 (Descend) | 降低油門平穩降落 |
| <kbd>R</kbd> | **一鍵維修與重置** | **撞擊墜毀後修復機身結構、清除碎片並還原初始位置** |

---

## 📁 專案檔案結構清單 (Project Structure)

```text
Digital_Twin_Drone_MVP/
├── components_db.json         # 數位硬體規格資料庫（馬達/電調/螺旋槳/電池/感測器）
├── db_loader.py               # 零件庫數據加載與規格篩選 API
├── drone_builder.py           # 參數化幾何長成與 URDF/SDF 生成器
├── flight_test_sim.py         # WebGL 3D 飛行模擬器生成腳本（含環境切換與損壞模擬）
├── view_3d_drone.py           # WebGL 3D 幾何檢視器生成腳本（含 BOM 與 CAD 預覽）
├── mavlink_controller.py      # MAVLink Offboard 自主飛控介面
├── morph_evolution.py         # DEAP 任務導向基因演化長成引擎
├── run_mvp_pipeline.py        # 端到端閉環管線執行入口
├── world_builder.py           # 3D 風場地圖與障礙物場景生成器
├── sensor_sim.py              # 感測器視場 (FOV) 與盲區算力評估器
├── px4_sitl_bridge.py         # PX4 SITL 與地面站通信橋接器
├── test_webgl_environments.py # WebGL 3D 環境、BOM 與損壞模擬單元測試套件
├── output/                    # 數位孿生模型與 WebGL 體驗成果目錄
│   ├── flight_test_simulator.html   # WebGL 鍵盤試飛飛行模擬器
│   ├── view_3d_scene.html           # WebGL 幾何外觀與場景檢視器
│   ├── evolved_unit_test_inspection.urdf
│   └── evolved_unit_test_inspection.sdf
├── USER_MANUAL.md             # 使用者操作與系統運行完整手冊
└── PROJECT_MASTER_REPORT.md   # 全流程開發里程碑與技術演進 Master 報告
```

---

## 🤖 跨平台 Agent 協作與 Taskboard 整合規範

本專案全面支援跨 Agent 平台（Google Antigravity, Claude Code, OpenAI Codex, Hermes, Cursor）之自動化派工與看板同步：
- 依循 **[[dashi-taskboard-integration]]** 規範進行 `taskctl` 任務認領與結案。
- 採用 **[[smart-schedule-taskboard-orchestration]]** 規範之智能作息雙軌排程（醒時 30 分鐘巡邏、睡時 2 小時批次清空），達成零干擾背景動工與節省 86.8% Token 消耗。

---

## 📜 專案文檔與版本演進

- **[📜 全流程開發紀錄與版本追溯 Master 報告 (PROJECT_MASTER_REPORT.md)](PROJECT_MASTER_REPORT.md)**：記錄自 v1.0.0 至 v7.0.0 歷代功能迭代與里程碑。
- **[📖 使用者操作與系統運行工作手冊 (USER_MANUAL.md)](USER_MANUAL.md)**：包含 Gazebo Sim、QGroundControl 連線配置與飛控調試詳細指南。
