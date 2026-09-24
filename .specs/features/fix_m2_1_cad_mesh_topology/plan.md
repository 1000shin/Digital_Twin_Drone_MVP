# Implementation Plan：[FIX-M2.1-CAD-MESH-TOPOLOGY] M2.1 3D 有機 CAD 機身實體網格拓撲缺陷與起落架破圖修復

> **版本**: 1.0  
> **功能 ID**: `FIX-M2.1-CAD-MESH-TOPOLOGY`  
> **目標分支**: `fix/m2.1-cad-mesh-manifold-topology`  
> **執行原則**: 小步前進、漸進提交、單元測試防禦、零上下文衰退、No Vibe Coding。

---

## 任務拆解 (Task Groups & Milestones)

### Phase 1: 規格起草與架構決策確認 (Spec & Human Gate)
- [x] **Task 1.1**: 開立獨立 Git 修復分支 `fix/m2.1-cad-mesh-manifold-topology`。
- [x] **Task 1.2**: 建立 `.specs/features/fix_m2_1_cad_mesh_topology/spec.md` 與 `plan.md`，定義驗收標準。
- [ ] **Task 1.3 [HUMAN GATE]**: 向 Human Architect 匯報架構選項，獲取簽核決策：
  - **決策項 A（機臂拓撲風格）**:
    - 選項 1：封閉式立體雙桁架（Volumetric Dual-Spar Truss）——上/下或左/右均為封閉立體管狀實體，具備完整立體側壁與密封外殼。
    - 選項 2：流線立體實心仿生機臂（Solid Bionic Tapered Beam）——流暢連續的實心漸變外殼，具備最高剛性、100% 水密性與切片相容性。
  - **決策項 B（起落架實體化形式）**:
    - 3D 實心錐體腳柱直接接合機臂底面 $z_{\text{arm\_bottom}}$，具備立體 4 稜柱厚度，徹底消除 11mm 斷空。

---

### Phase 2: 核心幾何生成器拓撲重構 (`organic_cad_generator.py`)
- [ ] **Task 2.1**: 修復馬達座中心座標計算，消除 `mid_z` 重複累加，與機臂末端端點中心幾何嚴密對齊。
- [ ] **Task 2.2**: 重構起落架生成幾何：
  - 根部基準 $Z$ 軸取自機臂底面真實高度 $z_{\text{arm\_bottom}}$。
  - 將 2D 零厚度雙面薄片升級為封閉 3D 錐體角柱（4 側面 + 底面實體），與機臂完全接合。
- [ ] **Task 2.3**: 依據架構師簽核之決策項 A，重構機臂切片長成幾何：
  - 若選「封閉式立體雙桁架」：實作立體側壁與密封隔板，修復退化三角形。
  - 若選「流線立體實心仿生機臂」：實作連續水密實體漸變機臂外殼。
  - 確保全部三角形頂點依 CCW 順序排列，法向量一致向外。
- [ ] **Task 2.4**: 驗證 STL 二進位與 ASCII 導出功能，更新散度定理體積計算邏輯。

---

### Phase 3: 自動化單元測試擴充與防禦 (`test_organic_cad.py`)
- [ ] **Task 3.1**: 於 `test_organic_cad.py` 新增拓撲水密性檢驗：
  - 斷言退化三角形數量為 0（所有面片面積 $> 0$）。
  - 斷言起落架根部與機臂底部間隙為 0（$|z_{\text{skid\_top}} - z_{\text{arm\_bottom}}| < 10^{-4}$）。
  - 斷言馬達座座標與機臂末端中心精確對齊。
- [ ] **Task 3.2**: 執行全套單元測試回歸（`python3 -m unittest discover -s . -p "test_*.py"`），確保 100% 通過。

---

### Phase 4: 模型資產重新導出與 3D 檢視器驗證
- [ ] **Task 4.1**: 重新導出 `output/models_archive/` 下所有 STL 世代模型與測試檔案。
- [ ] **Task 4.2**: 重新產出並檢查 `output/stl_viewer.html`，驗證 WebGL 渲染流暢度與無破面效果。

---

### Phase 5: Sub-Agent 深度審查與發布同步 (Review & Release)
- [ ] **Task 5.1**: 啟動 Sub-Agent 進行 Deep Code Review（需求忠實度、幾何拓撲、效能與架構規範）。
- [ ] **Task 5.2**: 填寫 `.specs/features/fix_m2_1_cad_mesh_topology/validation.md`。
- [ ] **Task 5.3**: 更新 `CHANGELOG.md` 與專案憲章/主報告，完成 Git Commit，準備發起合併。
