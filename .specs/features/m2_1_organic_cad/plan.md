# Implementation Plan：[M2.1] 有機造型 3D 列印 CAD 生成模組 (Organic Generative CAD)

> **功能 ID**: `FEAT-M2.1-ORGANIC-CAD`  
> **對應規格**: `spec.md`  
> **狀態**: `Completed & Verified`  
> **目標分支**: `feature/m2.1-organic-cad-generator`  
> **最後更新**: 2026-09-24  

---

## 1. 架構異動與模組劃分 (Architecture & Components)

```
Digital_Twin_Drone_MVP/
├── organic_cad_generator.py      # [NEW] 仿生有機機身幾何生成器、STL 二進位/ASCII 導出器、3D 列印分析器
├── test_organic_cad.py           # [NEW] 有機幾何網格、STL 規範、體積計算與管線整合單元測試
├── drone_builder.py              # [MODIFY] 整合 OrganicCADGenerator，導出 .urdf / .sdf 時同步產出 .stl
├── morph_evolution.py            # [MODIFY] 世代模型庫自動歸檔 .stl 與 print_profile.json
├── run_mvp_pipeline.py           # [MODIFY] 閉環管線報告加入 3D 列印可製造性數據摘要
├── view_3d_drone.py              # [MODIFY] WebGL 3D 預覽增加有機仿生幾何渲染支援
├── .specs/
│   ├── constitution.md           # [MODIFY] 更新 Phase 2 路線圖 [M2.1]
│   └── features/m2_1_organic_cad/ # [NEW] SDD 規格與實作計畫
│       ├── spec.md               # 功能需求與驗收標準
│       └── plan.md               # 本實作計畫書
└── output/
    ├── *.stl                     # 導出之實體 3D 列印標準二進位網格檔
    ├── *_print_profile.json      # 實體列印參數、重量與包絡尺寸清單
    └── models_archive/           # 跨世代 (Gen-1 ~ Gen-4) 歸檔之 STL 實體資產
```

---

## 2. 實作任務拆解 (Task Groups Breakdown)

### Task Group 1: 仿生有機幾何生成核心 (`organic_cad_generator.py`)
- [x] **Task 1.1**: 實作基礎網格幾何運算（頂點建立、面索引映射、三角形法向量標準化計算）。
- [x] **Task 1.2**: 實作中心中樞艙（Core Pod）流線幾何生成，內建電池/電裝容納包絡與光滑過渡面。
- [x] **Task 1.3**: 實作仿生漸變機臂（Bionic Tapered Arms），自艙體根部向外錐度漸變，沿力流配置多邊形輕量化鏤空肋條（Truss Cutouts）。
- [x] **Task 1.4**: 實作末端馬達安裝座（Motor Nacelle & Mounts）與起落架緩衝支腳（Landing Skids）。
- [x] **Task 1.5**: 實作網格拓撲合併器，輸出單一封閉流形（Single Merged Manifold Mesh）之頂點矩陣與三角面矩陣。

### Task Group 2: 工業級 STL 導出器與 3D 列印製造分析器
- [x] **Task 2.1**: 實作標準二進位 STL 導出（80-byte header, uint32 面數, float32 法向量與三頂點座標, 100% 格式合規）。
- [x] **Task 2.2**: 實作 ASCII STL 文本導出（支援除錯與純文字驗證）。
- [x] **Task 2.3**: 實作可製造性分析器（`get_print_profile`）：精確計算機身體積 ($V\text{ cm}^3$)、材料耗量重量（依據 PLA/PETG/PA-CF 密度）、最大外框包絡尺寸 ($X \times Y \times Z\text{ mm}$) 與推薦切片參數（層高、壁厚、填充率、支撐建議）。

### Task Group 3: 數位孿生工作流深度整合
- [x] **Task 3.1**: 修改 `drone_builder.py`：在 `export_files` 階段自動調用 `OrganicCADGenerator`，生成 `output/<design_id>.stl` 及 `<design_id>_print_profile.json`。
- [x] **Task 3.2**: 世代模型庫聯動：在 `output/models_archive/` 各世代歷史目錄（Gen-1 ~ Gen-4）中補全並自動歸檔對應的 STL 與製造設定。
- [x] **Task 3.3**: 整合 `run_mvp_pipeline.py` 與 `cli.py`：在終端機與 Markdown 報告中輸出 3D 列印尺寸與耗材重量。

### Task Group 4: WebGL 視覺整合與全套單元測試
- [x] **Task 4.1**: 於 `view_3d_drone.py` / WebGL 檢視器加入有機幾何展示支援。
- [x] **Task 4.2**: 撰寫獨立測試套件 `test_organic_cad.py`（驗證 STL 格式標頭、面數一致性、非退化法向量、不同旋翼數長成、以及列印分析精確度）。
- [x] **Task 4.3**: 執行全專案全套自動化測試，確認 100% 通過（全數測試在 10 秒內跑完）。

---

## 3. 測試與驗證計畫 (Validation Plan)

```bash
# 1. 執行有機 CAD 模組單元測試
python3 -m unittest test_organic_cad.py

# 2. 執行全專案回歸測試（保持 100% 通過）
python3 -m unittest discover -s . -p "test_*.py"
```
