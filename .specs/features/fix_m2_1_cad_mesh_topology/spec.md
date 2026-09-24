# Feature Spec：[FIX-M2.1-CAD-MESH-TOPOLOGY] M2.1 3D 有機 CAD 機身實體網格拓撲缺陷與起落架破圖修復

> **版本**: 1.0  
> **功能 ID**: `FIX-M2.1-CAD-MESH-TOPOLOGY`  
> **狀態**: `Approved (Signed off by Human Architect at Human Gate)`  
> **架構決策**:  
>   - 機臂拓撲風格：`流線立體實心仿生機臂 (Solid Bionic Tapered Beam)`  
>   - 起落架形式：`3D 實心錐體腳柱直接接合機臂底面`  
> **對應專案憲章**: `Constitution Phase 2 [M2.1] 有機造型 3D 列印 CAD 生成模組`  
> **目標分支**: `fix/m2.1-cad-mesh-manifold-topology`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **關聯模組**: `organic_cad_generator.py`, `drone_builder.py`, `test_organic_cad.py`, `stl_viewer.py`, `output/models_archive/`

---

## 1. 異常現象概述與根本原因 (Defect Overview & Root Causes)

### 1.1 異常現象 (Problem Statement)
在 3D 模型檢視器（`stl_viewer.html` / `models_archive`）及 3D 切片軟體（Cura / PrusaSlicer / Bambu Studio）中，使用者與檢視者觀察到 M2.1 仿生有機機身 3D 模型出現多處嚴重的幾何破圖、拓撲撕裂與非水密幾何缺陷（Non-Manifold Mesh）：
1. **機臂中段破面與撕裂穿透**：機臂鏤空區域內外不通，兩側完全開口且穿插無厚度、法向量翻轉的 2D 破面，在 Three.js 旋轉時呈現黑色空洞與閃爍。
2. **起落架支腳完全懸空斷開**：起落架支柱與機臂底面脫節，漂浮在機臂下方約 11mm 空中，且為 0 厚度的雙面 2D 平面片。
3. **馬達座高度位置偏移**：馬達座安裝平面座標計算重複疊加中心高度，且與機臂末端端點中心存在 Z 軸斷差。

### 1.2 根本原因深入排查 (Root Causes Analysis)
經排查 `organic_cad_generator.py` 的幾何構建邏輯，鎖定下列三大核心缺陷根因：

1. **機臂鏤空切片缺少立體側壁與封閉外殼 (Open Ribs & Degenerate Triangles)**：
   - 在 `generate_airframe_mesh()` 中，切片 `s_idx in [2, 4]` 僅產生了頂部 rib 與底部 rib 的四邊形（`prev_quad[0..1]` 到 `curr_quad[0..1]`，`prev_quad[2..3]` 到 `curr_quad[2..3]`）。
   - 機臂左右側壁（Left: `quad[1]->quad[2]`，Right: `quad[3]->quad[0]`）完全沒有封閉面，形成開放式空洞。
   - 代碼中 `add_triangle(prev_quad[1], curr_quad[2], prev_quad[1])` 與 `add_triangle(prev_quad[0], curr_quad[3], prev_quad[0])` 第一個與第三個頂點完全相同，產生面積為零的退化三角形（Degenerate Triangles）。
   - 當從實心切片（`s_idx=1` 或 `s_idx=3`）過渡到鏤空切片時，實心管壁端面沒有任何隔板（Bulkhead/Cap），導致實心管腔內部直接對外暴露，在拓撲學上形成嚴重的邊界開口與非流形邊（Non-Manifold Edges）。
2. **起落架支柱錨定高度錯誤與零厚度退化面 (Floating Struts & Zero-Thickness 2D Planes)**：
   - 起落架根部錨定點計算採用了機身中心艙體底面 `bottom_z = -hub_height_m * 0.5 = -0.019m`。
   - 然而在機臂半徑 $r = 0.78 \cdot r_{\text{end}}$ 處，機臂下底面的真實高度為 $z_{\text{arm\_bottom}} \approx -0.008\text{m}$。
   - 導致起落架根部與機臂下底面存在 $(-0.008) - (-0.019) = 0.011\text{m} = 11\text{mm}$ 的懸空斷開間隙。
   - 起落架幾何僅由 4 個共面頂點以 `add_quad(sk_p0, sk_p1, sk_p2, sk_p3)` 與正反雙向疊加構成，本質為零厚度 2D 幾何薄片，違反 3D 可列印實體模型（Watertight Solid）要求。
3. **馬達座高度座標重複累加 (Motor Nacelle Coordinate Double Offset)**：
   - `tip_center = u * r_end + w * mid_z`（已包含 $w \cdot \text{mid\_z}$）。
   - 後續頂底環計算又使用 `pt_top = tip_center + ... + w * pad_top_z`，其中 `pad_top_z = mid_z + motor_pad_h_m * 0.5`，導致 `mid_z` 重複累加。
   - 此外，機臂端面中心在 $t=1.0$ 時的真實高度為 $z_{\text{tip}} = \text{mid\_z} - 0.003\text{m}$，馬達座幾何未與機臂端面中心精確共軸對齊。

---

## 2. 核心目標與使用者故事 (User Story & Non-Goals)

### 2.1 使用者故事 (User Story)
* **As a** 數位孿生飛行器硬體架構師與 3D 列印製造工程師，
* **I want to** 從 `organic_cad_generator.py` 產出完全水密（Watertight）、無退化三角形（Zero Degenerate Triangles）、無懸空脫節（Zero Floating Shells）的 3D 有機機身 CAD 幾何，
* **So that** 在 Three.js WebGL 檢視器中不會發生破圖與背面穿透，且導出的二進位/ASCII STL 檔案可直接通過 Cura、PrusaSlicer、Bambu Studio 切片進行實體列印製造。

### 2.2 非目標範疇 (Non-Goals)
* ❌ **不引入外部龐大 CAD/CSG 套件**：堅持純 Python 3 標準庫 + NumPy 幾何運算架構，不引進 `OpenCASCADE`、`cadquery` 或 `trimesh` 等外部龐大 C++ 編譯依賴，維持極速單元測試。
* ❌ **不破壞現有上層呼叫介面**：維持 `OrganicCADGenerator.generate_airframe_mesh()`、`export_stl()` 與 `get_print_profile()` 簽名與傳回格式完全相容。
* ❌ **不修改非相關之飛控或模擬器邏輯**：本次變更範圍嚴格限制於機身 CAD 拓撲幾何長成與對應之 3D 模型歸檔/檢視器。

---

## 3. 功能需求與驗收標準 (Requirements & Acceptance Criteria)

### 3.1 功能性需求 (Functional Requirements)

- [ ] **FR-1: 機臂立體水密實體拓撲長成 (Watertight Solid Arm Topology)**
  - **說明**: 重構機臂幾何長成管線，消除所有邊界開口與零厚度薄片。依據架構決策（雙桁架立體封閉或實心仿生漸變柱體），確保機臂由外殼壁面與立體封閉單元嚴密縫合。
  - **驗收標準 (AC-1.1)**: 機臂無任何兩側裸露開口，切片間過渡幾何具備完整立體側壁與密封外殼。
  - **驗收標準 (AC-1.2)**: 消除所有退化三角形（不存在共線、重複頂點或面積為零之面片）。

- [ ] **FR-2: 起落架 3D 實體錐體化與機臂底面實體縫合 (Volumetric Struts Anchored to Arm Bottom)**
  - **說明**: 起落架根部基準點 $Z$ 軸精確取自機臂在該半徑下的真實下表面高度 $z_{\text{arm\_bottom}}$；起落架本體由 2D 薄片升級為具備 X/Y 厚度的 3D 錐形實體角柱（4 稜柱或 3 稜台實體）。
  - **驗收標準 (AC-2.1)**: 起落架頂部頂點 $Z$ 軸嚴格等於機臂底面 $Z$ 軸（或略向上嵌入機臂實體內），懸空裂隙距離為 $0.0\text{mm}$。
  - **驗收標準 (AC-2.2)**: 起落架幾何為封閉的 3D 實體（包含前後左右 4 個側面與底部封板），不再包含正反對貼的 2D 零厚度面片。

- [ ] **FR-3: 馬達座座標幾何精確對齊與端面縫合 (Motor Nacelle Height & Axis Realignment)**
  - **說明**: 修正馬達座中心 $Z$ 軸計算，消除 `mid_z` 重複疊加缺陷，並與機臂在 $r = r_{\text{end}}$ 處的端面高度幾何嚴密對齊。
  - **驗收標準 (AC-3.1)**: 馬達安裝座中心精確定位於機臂端面中心延長線上，上下厚度均勻分佈於設計安裝基準面。

- [ ] **FR-4: 全表面外法向量一致性 (Outward Normal Consistency)**
  - **說明**: 所有三角面片的頂點順序嚴格遵循逆時針（CCW）右手定則，外法向量 $\vec{N}$ 統一朝向實體幾何外側，消除內翻面片導致的 Three.js 光影反轉撕裂。
  - **驗收標準 (AC-4.1)**: `normals` 陣列各面片單位向量與外向幾何一致，點積驗證均無反向翻轉。

- [ ] **FR-5: 3D 列印分析器與模型資產同步更新 (Profile & Models Archive Regeneration)**
  - **說明**: 實體水密化後，利用散度定理（Divergence Theorem）計算出的機身體積更加精準可靠；同步重新導出 `output/models_archive/` 中的演化模型與 `output/stl_viewer.html`。
  - **驗收標準 (AC-5.1)**: 執行 `OrganicCADGenerator.get_print_profile()` 輸出之體積與重量指標合理（容積率 $> 0$，非虛擬保底值）。
  - **驗收標準 (AC-5.2)**: 重新產出所有標準 STL 檔案與 3D 檢視器 HTML。

### 3.2 非功能性需求 (Non-Functional Requirements)
* **網格可製造性 (Printability / Manifoldness)**: 導出的二進位與 ASCII STL 檔案必須符合水密性幾何規範，切片軟體無未閉合網格警告。
* **輕量計算效能**: 生成 4/6/8 旋翼機身網格之運算時間 $\le 0.1$ 秒，單元測試執行時間保持在極速水準。
* **零依賴架構**: 維持純 Python 3 標準庫 + NumPy，嚴禁引入重量級幾何編譯依賴。

---

## 4. 驗證與測試策略 (Validation Strategy)
1. **單元測試擴充 (`test_organic_cad.py`)**：
   - 新增幾何水密與拓撲檢驗測試：檢驗退化三角形數量為 0。
   - 新增起落架根部高度檢驗：斷言起落架根部頂點 $Z \ge z_{\text{arm\_bottom}} - 10^{-4}$，杜絕 11mm 懸空。
   - 新增體積計算真實性測試：斷言散度定理體積大於零且非保底 fallback 粗估值。
2. **自動化全套回歸測試**：
   - 執行 `python3 -m unittest discover -s . -p "test_*.py"`，確保所有 40+ 項測試 100% 通過。
3. **視覺與切片雙軌驗證**：
   - 重新生成 `output/stl_viewer.html`，檢查 3D 檢視器光影渲染無撕裂與破面。
