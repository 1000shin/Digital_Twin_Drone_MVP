# 數位孿生無人機 MVP (Digital Twin Drone MVP)

本專案旨在提供一個純開源（ROS 2 + Gazebo Sim + CadQuery + PX4 SITL + MAVLink + DEAP）的數位孿生無人機環境。無人機能根據任務需求（如載重、航程、狹窄空間避障）動態演化長出最適幾何形態與感測配置，並透過 MAVLink 自主控制協議在 Gazebo 進行實時閉環驗證。

## 📁 模組結構與操作/查驗報告 (Work Blocks & Reports)

- **[📜 全流程開發紀錄與版本追溯 Master 報告 (PROJECT_MASTER_REPORT.md)](PROJECT_MASTER_REPORT.md)**
- **[📖 使用者操作與系統運行工作手冊 (USER_MANUAL.md)](USER_MANUAL.md)**
- `components_db.json`：數位零件庫（馬達、螺旋槳、電池、感測器物理屬性）
- `db_loader.py`：零件庫數據加載與查詢 API
- `drone_builder.py`：(Block 2) 參數化 CadQuery 幾何與 URDF/SDF 生成器
- `mavlink_controller.py`：(Block 3) MAVLink Offboard 自主飛行控制介面
- `morph_evolution.py`：(Block 4) 任務導向形態與感測器演化長成引擎
- `run_mvp_pipeline.py`：(Block 5) 端到端閉環與可視化整合入口
- `world_builder.py`：Gazebo 3D 風場與障礙物場景生成器
- `sensor_sim.py`：感測視場 (FOV) 與盲區比率算力評估
- `px4_sitl_bridge.py`：原生 PX4 SITL 飛控與 3D GUI 橋接器
- `cli.py`：互動式命令列主控入口

