# 專案憲章 (Project Constitution) - Morph-Twin UAV（自適應形態演化與虛實閉環飛行器系統）

> **說明**：本憲章為規格驅動開發（Spec-Driven Development, SDD）的最高核心基石。作為專案的持久化技術資產，本文件旨在為人類架構師（Brain）與 AI 結對工程師（Muscle）提供統一且不可動搖的最高開發準則，防止上下文衰退（Context Decay）並降低認知負債（Cognitive Debt）。

> [!IMPORTANT] 🧠 人類架構師原始需求與任務定義 (Architect's Original Directive)
> **「任務需求：解決過去人類開發無人機需要組裝，再到實際物理世界測試碰撞後所產生的經驗值，再反饋回整體設計。目前要改變的是利用數位孿生世界內可重複試錯，幾乎零試錯成本，快速完成無人機適應環境環境，自主演化出機構與零件需求之目標。並且可以在真實世界採購實際零組件，與3D列印機構件，組裝後讓無人機在真實世界飛行，校準在數位孿生世界的參數誤差，使情境使用與自主適應進化，節約硬體開發資源，與drone自主飛行能力，並且保留未來在晶片需求及感測器軟韌體的開發規格，實體世界使用MVlink及P4X。」**

---

## 1. 專案使命與願景 (Mission & Vision)

### 1.1 核心使命 (Core Mission)
* **一句話定義**：以任務需求為導向，透過數位孿生零成本自主演化有機飛行構型與 COTS 配置；在虛擬環境以無人干預強化學習（RL 百萬次試錯訓練）自主習得極限避障策略，並藉由全機 3D 列印製造、PX4/MAVLink 實機試飛進行 Real-to-Sim 參數自動反向校準，落實「人類主飛、AI 輔助介入」的虛實共生閉環系統。
* **產品願景**：徹底終結無人機硬體設計的經驗試錯與炸機成本，根據任務約束（載重、航程、狹小避障、抗風）自動演化長出最適幾何與電氣配置，在純瀏覽器 60 FPS WebGL 與原生 PX4/Gazebo 環境中以強化學習進行百萬次無人試錯訓練；透過實機飛行自動校準參數，實現飛行器的自主適應進化。

### 1.2 目標受眾與核心情境 (Target Audience & Primary Use Cases)
* **主要使用者**：無人機演算法工程師、數位孿生研究員、自主飛行/強化學習 (RL) 開發者、硬體選型架構師、無人機飛手。
* **關鍵使用場景 (Key Scenarios)**：
  1. **狹窄空間避障巡檢（如橋樑/管道）**：演化引擎自動縮短臂長以消除直徑空間懲罰，生成超緊湊高機動性有機 4 旋翼無人機。
  2. **海上風電長航程巡航（Offshore Wind Farm）**：演化出 VTOL 傾轉旋翼複合幾何、高升阻比機翼與大容量電池，在強陣風動態海面巡檢。
  3. **重載緊急醫療物資運輸**：演化出 6-8 旋翼重載結構、高推重比 (TWR) 馬達與螺旋槳配置。
  4. **夜間紅外線檢測與撞擊損壞評估**：暗夜環境熱成像 HUD 檢驗異常過熱管線，並透過高擬真局部破損物理模擬（折損、斷槳、火花碎屑、BOM 聯動）評估結構極限。
  5. **虛擬無人干預強化學習試錯 (Reinforcement Learning)**：在數位孿生環境中建立獎懲機制（成功到達目標給分、碰撞扣分），無人干預進行百萬次試錯訓練，習得極限避障策略模型。
  6. **實機人類主飛與 AI 輔助介入 (Shared Autonomy Copilot)**：實機飛行中維持「人類主飛，AI 輔助介入」，RL 避障模型在背景守護，於即將碰撞時自動啟動排斥力避障與速度箝位。

### 1.3 非目標範疇 (Non-Goals / Out of Scope)
> *明確劃定專案界線，防止 AI Agent 在開發過程中發生範疇蔓延（Scope Creep）與無謂猜測。*
* ❌ **非目標 1：硬體底層韌體燒錄器**：本專案聚焦於「數位孿生、形態演化與模擬驗證環境」，不包含直接向實體微控制器（STM32 / ESP32）編譯燒錄 PX4/ArduPilot 韌體的工具鏈。
* ❌ **非目標 2：雲端多租戶 SaaS 平台與使用者帳號驗證系統**：定位為本機研發模擬與演化演算法套件，不包含多用戶認證、資料庫雲託管或付費金流。
* ❌ **非目標 3：重型 AAA 級遊戲引擎綁定**：優先維護 WebGL/Three.js 單 HTML 零伺服器極速體驗與原生 Gazebo Sim 輕量整合，不依賴 Unreal Engine 5 等超重型商業軟體。
* ❌ **非目標 4：外圍開發工具之業務侵入**：`TokenUsageInsights/`、`sync_ide_tokens.py` 與 `watch_taskboard.py` 為工作區輔助工具，業務程式碼不得對其產生依賴。
* ❌ **非目標 5：過早技術框架死鎖**：感測器軟韌體規範維持抽象介面合約（頻寬、延遲、採樣率），不提早綁死特定單一通訊框架或中介軟體。

---

## 2. 技術堆疊與架構規範 (Tech Stack & Architectural Constraints)

### 2.1 核心技術堆疊 (Core Tech Stack)
* **核心語言**：Python 3.10+ (純標準庫優先設計，無重型 C 擴展依賴，極速單元測試)
* **形態演化引擎**：Python 遺傳演化算法 (`morph_evolution.py`, `vtol_evolution.py`)，內建物理變革動機、世代躍遷決策歷史與系譜溯源報告導出。
* **物理模型與 CAD 生成**：參數化慣性矩計算器 (`drone_builder.py`, `vtol_builder.py`)，導出標準 ROS 2 / Gazebo 相容之 `.urdf` 與 `.sdf` 描述檔，並具備 3D 列印可製造性 CAD (`.stl` / `.step`) 輸出能力。
* **3D 模擬環境**：
  - 輕量展示軌：WebGL + Three.js（單 HTML 自包含無伺服器架構，4 大動態環境、Glassmorphism BOM 抽屜面板、撞擊動態破損模擬、2Hz 遙測示範錄製器）。
  - 專業物理軌：Gazebo Sim (GZ) + 風場/障礙物場景 (`world_builder.py`)。
* **自主自駕學習管線**：
  - **強化學習 (RL) 訓練環境**：標準 Gym/Gymnasium 介面，內建狀態空間（State Space）、動作空間（Action Space）與可自訂獎懲函數（Reward Function）。
* **飛控協議與地面站**：原生 MAVLink v2 (`0xFD` 標頭，支援 UDP 14540 PX4 SITL 與 UDP 14550 QGroundControl)、Foxglove Studio 3D 戰情室 (`.mcap` 格式)。
* **自動化測試**：Python 原生 `unittest`（覆蓋率涵蓋演化長成、URDF/SDF 物理量、MAVLink 通訊、WebGL 環境與損壞模擬，維持 100% 通過率）。

### 2.2 目錄結構與模組架構 (Directory Structure & Architecture)
```text
Digital_Twin_Drone_MVP/
├── .specs/                    # SDD 規格資產目錄
│   ├── constitution.md        # 專案最高技術憲章（本檔案）
│   └── features/              # 獨立功能規格目錄 (<feature-id>/spec.md, plan.md, validation.md)
├── components_db.json         # 數位硬體規格資料庫（市售 COTS 馬達/螺旋槳/電池/感測器/材質物理屬性）
├── mission_profiles.json      # 標準任務 Prompt 與環境約束設定檔
├── db_loader.py               # 零件庫加載、推重比與航程物理估算 API
├── morph_evolution.py         # 多旋翼形態基因演化引擎（含解釋性動機日誌與血統追蹤）
├── vtol_evolution.py          # VTOL 傾轉旋翼幾何與氣動升阻比 (L/D) 演化引擎
├── drone_builder.py           # 多旋翼參數化 CAD、慣性張量與 URDF/SDF 生成器
├── vtol_builder.py            # VTOL 複合翼幾何與 Gazebo Lift-Drag 外掛生成器
├── world_builder.py           # Gazebo 3D 風場向量與障礙物場景生成器
├── sensor_sim.py              # 感測器 3D FOV 視場覆蓋率與盲區比率算力評估
├── mavlink_controller.py      # 原生 MAVLink v2 Offboard 自主飛控與 UDP 廣播器
├── px4_sitl_bridge.py         # PX4 SITL 與 Gazebo 連線啟動橋接器
├── foxglove_bridge.py         # Foxglove Studio 3D 遙測串流橋接器
├── mcap_exporter.py           # 原生 .mcap 數據容器導出器
├── flight_test_sim.py         # WebGL 3D 試飛模擬器生成器（4 大環境、BOM、破損物理、2Hz 錄製）
├── view_3d_drone.py           # WebGL 3D 幾何檢視器生成器（CAD 預覽與情境切換）
├── cli.py                     # 全功能互動式命令列主控入口
├── run_mvp_pipeline.py        # 端到端閉環管線入口 (Mission -> Evolve -> Model -> Flight -> Report)
├── output/                    # 數位孿生模型、模擬器 HTML、MCAP 與 Markdown 報表目錄
└── test_*.py                  # 完整的自動化單元測試套件
```

### 2.3 架構原則與開發規範 (Coding Standards & Principles)
* **無人干預強化學習原則 (Reward-Driven Reinforcement Learning)**：在數位孿生環境中建立精準獎懲機制（成功到達目標給分、碰撞扣分、姿態平穩給分），支援百萬次無人試錯自主演化避障策略。
* **人類主飛，AI 輔助介入 (Shared Autonomy Copilot)**：實機飛行中自駕演算法定位為飛手的安全副駕駛，在手動操控時提供動態排斥力避障與速度箝位安全防線。
* **有機造型 3D 列印原則 (Organic Generative Airframe)**：支持全機身參數化 3D 列印長成，充分利用幾何自由度融入拓撲最佳化與仿生流線骨骼，輸出標準可列印網格。
* **雙軌自動回補校準 (Automated Dual-Track Calibration)**：實機飛完後上傳日誌，自動比對動力（推力曲線、電壓陡降）與氣動（$C_d$ 阻力）偏差，自動回補更新 `components_db.json`。
* **演化後算力規格推薦 (Post-Evolution Compute Profiling)**：演化完成後根據演算法複雜度推薦 TOPS 算力、記憶體、功耗與載重規格書，避免初期被硬體綁死。
* **感測軟韌體規格抽象化 (Abstract Sensor Interface Contract)**：遵循 SDD 規範，優先定義採樣率、頻寬、延遲與視場（FOV），暫不提早綁定特定中介層。
* **零重型編譯依賴 (Zero Heavy Compiling Dependency)**：核心物理計算、演化演算法與模型導出保持以 Python 標準庫優先，確保單元測試在 10 秒內跑完。
* **解耦雙軌模擬架構 (Decoupled Dual-Track Simulation)**：WebGL 輕量瀏覽器試飛環境與 Gazebo/PX4 原生物理環境分立解耦，互不阻斷。

---

## 3. 開發路線圖與階段目標 (Roadmap & Milestones)

### Phase 1: MVP 核心骨幹與高階特性 (已完成 Baseline - v1.0.0 ~ v9.0.0)
* [x] **[M1.1]** 數位硬體庫 (`components_db.json`) 與物理屬性估算 (`db_loader.py`)
* [x] **[M1.2]** 參數化幾何長成與 URDF/SDF 物理描述檔導出 (`drone_builder.py`, `vtol_builder.py`)
* [x] **[M1.3]** 原生 MAVLink v2 (0xFD) 協定與 UDP 14540/14550 SITL/QGC 整合 (`mavlink_controller.py`)
* [x] **[M1.4]** 任務導向形態演化引擎與 VTOL 傾轉旋翼長成 (`morph_evolution.py`, `vtol_evolution.py`)
* [x] **[M1.5]** 3D Gazebo 風場世界與感測器 3D FOV 算力評估 (`world_builder.py`, `sensor_sim.py`)
* [x] **[M1.6]** Foxglove Studio 3D 戰情室與 `.mcap` 容器檔串流導出 (`foxglove_bridge.py`, `mcap_exporter.py`)
* [x] **[M1.7]** WebGL 3D 飛行模擬器：BOM 抽屜、4 大動態環境 (離岸風場/城市搜救/碰撞場/夜間紅外)
* [x] **[M1.8]** WebGL 碰撞動態破損系統：剪切變形、焦黑裂紋、火花碎屑粒子系統、BOM 聯動與一鍵維修
* [x] **[M1.9]** 飛航遙測與示範數據錄製系統 (DIG-12)：2Hz 採樣、靜默自動存檔、經驗問卷
* [x] **[M1.10]** 形態演化決策動機與血統溯源系統 (DIG-13)：世代躍遷日誌、溯源報告導出
* [x] **[M1.11]** 全套自動化單元測試覆蓋 (27/27 項測試 100% 通過)

### Phase 2: 虛實閉環與智慧自駕 (當前進行中 - 納入 5 大對齊決策)
* [x] **[M2.1] 有機造型 3D 列印 CAD 生成模組 (Organic Generative CAD)**：從參數化演化長成升級至可製造性有機幾何與標準 3D 列印檔案輸出 (`.stl` / `.step`)。
* [ ] **[M2.2] PX4 日誌自動解析與 Real-to-Sim 雙軌校準腳本 (System Identification)**：接收 PX4 ULog / MAVLink 日誌，自動比對動力（PWM-推力、電壓陡降）與氣動（$C_d$、升阻比）誤差，自動回寫 `components_db.json`。
* [ ] **[M2.3] 演化後邊緣晶片模組化規格推薦器 (Compute Profiler)**：演化完成後根據任務自駕演算法複雜度，自動輸出建議算力 TOPS、記憶體、功耗與載重規格書。
* [ ] **[M2.4] 抽象感測器軟韌體介面合約定義 (Abstract Sensor Contract)**：定義採樣頻率、延遲限制、頻寬與 FOV 規格，暫不硬性綁定特定中介層。
* [x] **[M2.5] 虛擬環境無人干預強化學習 (RL) 訓練管線與 AI 自駕巡航系統 (Autonomous RL Training & Cruise Pipeline)**（規格詳見 [`.specs/features/m2_5_rl_pipeline/spec.md`](./features/m2_5_rl_pipeline/spec.md)）：
  * [x] **[M2.5.1] 強化數位孿生擬真環境的建立**：建立標準 Gymnasium 相容強化學習環境 (`drone_rl_env.py`)，涵蓋 23 維觀測狀態、4 維連續動作、8 向 360° LiDAR 測距、剛體解穿透防卡死機制，以及複合式多目標高擬真獎懲函數矩陣（進展距離獎勵、穿門獎勵、平穩飛行獎勵、貼障指數懲罰、碰撞終止重罰）。
  * [x] **[M2.5.2] AI 自主極限避障演算法的升級**：實作輕量自律策略學習器 (`autonomous_flight_learner.py`)，融合人類飛手 2Hz 遙測示範先驗暖機（Behavioral Cloning Prior）與非線性人工勢能場（APF），升級引力-斥力動態解耦與已過門冷卻遮罩，達成微秒級超低延遲（<0.05ms）極限避障推論。
  * [x] **[M2.5.3] AI 自主巡航完成任務**：在 3D WebGL 模擬器 (`flight_test_sim.py`) 落地兩階段起飛保護、全場閉環多門巡檢導航狀態機（`THROUGH` ➔ `LEADOUT` ➔ `CORNER`）與動態引導走廊，達成健康度 $\ge 80\%$ 零卡死完成全場穿門巡航，並萃取試錯數據回饋閉環驅動第四代機身形態演化。
* [x] **[M2.6] 「人類主飛，AI 輔助介入」協同飛控副駕駛 (Shared Autonomy Copilot)**：將虛擬環境透過 RL 訓練出的策略模型部署為實機飛行的安全副駕駛；飛手掌握最高操縱權，當飛手操作即將導致碰撞或失控時，AI 即時介入推力與排斥力場避障。（規格詳見 [`.specs/features/m2_6_shared_autonomy_copilot/spec.md`](./features/m2_6_shared_autonomy_copilot/spec.md)）

### Phase 3: 實機落地與蜂群協同 (未來藍圖)
* [ ] **[M3.1] 實體飛控硬體在環 (HITL) 驗證**：對接實體 Pixhawk 6C 飛控與 COTS 零組件實裝機型，執行真實物理世界試飛與閉環參數校準。
* [ ] **[M3.2] 多機蜂群協同 (Multi-UAV Swarm) 數位孿生**：支援多台不同有機構型無人機在同一場景中進行協同分工巡檢。

---

## 4. AI Agent 開發協定 (Agent Governance)

### 4.1 變更審查原則 (Change Review Policy)
1. **嚴格遵循 SDD 循環**：新增功能前必須在 `.specs/features/<feature-id>/` 建立 `spec.md` 與 `plan.md`，經人類架構師確認後方可動工。
2. **小步提交與單元測試防線**：每次程式碼變更必須執行全套單元測試 (`python3 -m unittest discover -s . -p "test_*.py"`)，維持 100% 通過率。
3. **極小化架構變動**：未經人類授權，不得變更核心套件依賴或破壞無外部編譯之純 Python 輕量原則。

### 4.2 上下文與衛生管理 (Context Hygiene)
* **清理機制**：完成每個 Feature 實作或重大架構異動後，必須提示執行 `/clear` 徹底清空 Session 上下文，防止注意力稀釋與 Context Decay。
* **資產同步**：重大架構調整或需求變更後，必須同步更新 `PROJECT_MASTER_REPORT.md`、`README.md`、`obsidian/專案/morph-twin-uav/README.md` 與本憲章。
