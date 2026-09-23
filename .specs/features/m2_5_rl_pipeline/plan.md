# Implementation Plan：[M2.5] 虛擬環境無人干預強化學習 (RL) 訓練管線

> **功能 ID**: `FEAT-M2.5-RL-PIPELINE`  
> **對應規格**: `spec.md`  
> **狀態**: `Completed & Verified`  
> **最後更新**: 2026-09-24

---

## 1. 架構異動與模組劃分 (Architecture & Components)

```
Digital_Twin_Drone_MVP/
├── drone_rl_env.py                  # [NEW] 23-dim 觀測空間與 4-dim 動作空間 Gymnasium 相容物理環境
├── autonomous_flight_learner.py     # [NEW] 人工勢能場 (APF) + 行為克隆先驗策略推論器與自我博弈管線
├── test_ai_autonomous_pipeline.py   # [NEW] RL 環境、策略收斂、WebGL UI 整合與模型溯源測試套件
├── flight_test_sim.py               # [MODIFY] WebGL 試飛模擬器整合「兩階段起飛保護」與 APF 自主穿門導航
├── .specs/
│   ├── constitution.md              # [MODIFY] 更新 Phase 2 路線圖 [M2.5]
│   └── features/m2_5_rl_pipeline/   # [NEW] SDD 標準規格與計畫工作區
│       ├── spec.md                  # 功能需求、使用者故事與驗收標準
│       └── plan.md                  # 本實作計畫書
└── output/
    ├── flight_test_simulator.html   # WebGL 互動試飛模擬器發行檔 (含 🤖 AI 自主飛行)
    ├── training_datasets/           # 2Hz 遙測示範與 AI 試錯數據庫
    └── models_archive/              # 跨世代 3D 模型實體資產與系譜報告 (Gen-1 ~ Gen-4)
```

---

## 2. 實作任務拆解 (Task Groups Breakdown)

### Task Group 1: 建立 Gymnasium 強化學習無人機物理環境
- [x] **Task 1.1**: 實作 `DroneRLEnvironment` 類別，繼承標準環境介面 (`reset()`, `step(action)`)。
- [x] **Task 1.2**: 定義 23 維觀測空間向量（12 維機體動力學 + 8 向 360° LiDAR 射線 + 3 維穿越門相對座標）。
- [x] **Task 1.3**: 實作 4 維連續動作空間（`[pitch, roll, yaw_rate, throttle]`）物理推進映射。
- [x] **Task 1.4**: 實作多目標獎懲函數（進展加分、穿門大獎、平穩給分、近距斥力阻尼、碰撞重罰終止）。

### Task Group 2: 實作自律勢能場策略學習器
- [x] **Task 2.1**: 實作 `AutonomousFlightPolicy`，融合目標吸引力與立柱障礙物斥力場（APF）。
- [x] **Task 2.2**: 實作 `AutonomousFlightLearner`，支援人類示範遙測資料集先驗暖機與無人高速試錯。
- [x] **Task 2.3**: 建立每秒 5,000 步以上的高速無頭（Headless）訓練循環。

### Task Group 3: WebGL 3D 模擬器即時 AI 自主飛行整合
- [x] **Task 3.1**: HUD 介面新增「🤖 AI 自主飛行巡弋」控制開關與即時決策數值面板。
- [x] **Task 3.2**: 實作「兩階段自主起飛機制」：高度 $< 1.6\text{m}$ 保持姿態零傾角，輸出純垂直動力爬升；離開地面後平滑轉入 APF 導航。
- [x] **Task 3.3**: 動態渲染紫色目標雷達導航光束（`trajectoryLine`），動態追蹤當前 Gate #1 ~ Gate #4 目標。
- [x] **Task 3.4**: 實作人工主飛安全優先接管邏輯：任意手動控制鍵（`W/A/S/D/↑/↓/Space`）即時解除 AI。

### Task Group 4: 試錯數據驅動之 Gen-4 形態演化閉環
- [x] **Task 4.1**: 萃取 AI 試錯數據，自動產出稽核報表與示範資料集。
- [x] **Task 4.2**: 驅動形態演化長出第四代無人機（Gen-4 Sentinel Prime），儲存 URDF/SDF 至模型庫。
- [x] **Task 4.3**: 撰寫全套單元測試 (`test_ai_autonomous_pipeline.py`)，確認 32 項測試 100% 通過。

---

## 3. 測試與驗證指令 (Verification Command)

```bash
# 執行全專案單元測試（包含 RL 環境、策略預測、WebGL UI 元件與 Gen-4 模型資產）
python3 -m unittest discover -s . -p "test_*.py"
```
