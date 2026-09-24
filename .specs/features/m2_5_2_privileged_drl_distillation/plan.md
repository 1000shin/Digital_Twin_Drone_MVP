# Implementation Plan：[M2.5.2] 深度強化學習與特權導師-學生蒸餾極限避障系統

> **功能 ID**: `FEAT-M2.5.2-PRIVILEGED-DRL-DISTILLATION`  
> **對應規格**: [`spec.md`](./spec.md)  
> **狀態**: `Completed & Verified`  
> **最後更新**: 2026-09-25

---

## 1. 架構異動與模組劃分 (Architecture & Components)

```
Digital_Twin_Drone_MVP/
├── drone_rl_env.py                      # [MODIFY] 擴充特權真值 (get_privileged_state) 與機載學生感知介面
├── train_privileged_distillation.py     # [NEW] 離線解耦 PyTorch 特權 PPO 訓練與 DAgger 學生策略蒸餾器
├── autonomous_flight_learner.py         # [MODIFY] 整合純 NumPy 學生網絡前向推論器與 APF 韌性回退
├── flight_test_sim.py                   # [MODIFY] WebGL 模擬器整合純 JS 神經網絡推論與 HUD 狀態指示
├── test_privileged_drl_distillation.py  # [NEW] 全套自動化單元測試（特權狀態、蒸餾一致性、推論延遲）
├── .specs/
│   └── features/
│       └── m2_5_2_privileged_drl_distillation/
│           ├── spec.md                  # 功能規格需求書
│           ├── plan.md                  # 本實作計畫書
│           └── validation.md            # 驗收與稽核簽核報告
└── output/
    ├── flight_test_simulator.html       # WebGL 互動試飛模擬器發行檔 (內建學生網絡推論)
    └── neural_models/
        ├── student_policy_stages.json   # 三階段完整權重快照資產
        └── student_policy_weights.json  # 蒸餾產出之輕量化神經網絡權重資產
```

---

## 2. 實作任務拆解 (Task Groups Breakdown)

### Task Group 1: 強化學習環境介面擴充 (Environment Enhancements)
- [x] **Task 1.1**: 在 `drone_rl_env.py` 中實作 `get_privileged_state()`，打包機體精確狀態、當前門法向與距門距離、全場立柱相對幾何。
- [x] **Task 1.2**: 實作 `get_student_observation(noise_std, dropout_prob)`，加入真實感測器模擬的高斯雜訊與 LiDAR 射線丟失率。
- [x] **Task 1.3**: 擴展環境步進支援雙狀態回傳，確保訓練迴圈能同時採樣特權真值與受限觀測。

### Task Group 2: 離線特權導師訓練、多階段策略蒸餾與快照工具鏈 (PyTorch Tooling)
- [x] **Task 2.1**: 實作 `TeacherPolicy` 網絡與 PPO 策略梯度優化器，利用特權真值高速學習極限穿越避障策略。
- [x] **Task 2.2**: 實作 `StudentPolicy` 輕量網絡（[64, 64] MLP），透過 DAgger / 監督蒸餾最小化與導師動作差距。
- [x] **Task 2.3**: 實作多階段學習快照儲存：在 0% 初學（隨機）、40% 半熟（過渡）、100% 精通（完訓）三個關鍵里程碑自動匯出權重快照。
- [x] **Task 2.4**: 實作權重匯出邏輯，將三階段權重矩陣打包寫入 `output/neural_models/student_policy_stages.json` 與標準 `output/neural_models/student_policy_weights.json`。
- [x] **Task 2.5**: 執行輕量訓練驗證流程，確保模型在本地 MPS/CPU 能快速（< 3 秒）產出合格避障權重。

### Task Group 3: 運行時純 NumPy 學生推論器與整合 (Runtime Inference Engine)
- [x] **Task 3.1**: 在 `autonomous_flight_learner.py` 實作 `StudentPolicyNumpy`，載入 JSON 權重並以純 NumPy 矩陣前向推論。
- [x] **Task 3.2**: 實作平滑差分平坦性（Differential Flatness）前饋修正，將輸出動作對齊飛控控制合約。
- [x] **Task 3.3**: 實作權重遺失自動平滑回退（Fallback to APF）保護機制，確保在任何環境中均穩定運行。

### Task Group 4: WebGL 3D 模擬器即時神經推論與學習時光軸檢視器 (WebGL Simulator Integration)
- [x] **Task 4.1**: 在 `flight_test_sim.py` 與 `flight_test_simulator.html` 中嵌入學生網絡多階段權重矩陣。
- [x] **Task 4.2**: 實作純 JavaScript 神經網絡前向推論函數（ReLU + Tanh），在 60 FPS 循環中直接運算。
- [x] **Task 4.3**: HUD 控制台增設「🎓 學生網絡歷程」切換器：`[🌱 0% 初學 | 🌿 40% 半熟 | 🏆 100% 精通]`，支援一鍵即時切換當前推論權重。
- [x] **Task 4.4**: HUD 戰情面板新增 `[AI AGENT: DISTILLED STUDENT (STAGE X)]` 狀態徽章與神經推論數值顯示。

### Task Group 5: 單元測試、驗證與憲章同步 (Testing & Verification)
- [x] **Task 5.1**: 撰寫 `test_privileged_drl_distillation.py` 獨立單元測試套件（涵蓋特權資料維度、學生雜訊、NumPy 推論延遲 $<0.05\text{ms}$、數值精度 $\le 10^{-5}$、回退機制）。
- [x] **Task 5.2**: 執行全專案單元測試 (`python3 -m unittest discover -s . -p "test_*.py"`)，確認測試 100% 通過。
- [x] **Task 5.3**: 更新 `PROJECT_MASTER_REPORT.md` 與專案憲章追蹤狀態。

---

## 3. 測試與驗證標準 (Verification Commands)

```bash
# 1. 執行特權導師訓練與蒸餾產出權重
python3 train_privileged_distillation.py --episodes 50

# 2. 執行新增之特權學習單元測試
python3 -m unittest test_privileged_drl_distillation.py

# 3. 執行全專案自動化測試防線（預期 60+ 項測試 100% 通過，總耗時 < 10 秒）
python3 -m unittest discover -s . -p "test_*.py"
```
