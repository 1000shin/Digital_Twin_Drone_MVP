# Feature Spec：[M2.1] 有機造型 3D 列印 CAD 生成模組 (Organic Generative CAD)

> **版本**: 1.0  
> **功能 ID**: `FEAT-M2.1-ORGANIC-CAD`  
> **狀態**: `Approved (Signed off by Architect)`  
> **對應專案憲章**: `Constitution Phase 2 [M2.1]`  
> **目標分支**: `feature/m2.1-organic-cad-generator`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **關聯模組**: `organic_cad_generator.py`, `drone_builder.py`, `morph_evolution.py`, `run_mvp_pipeline.py`, `test_organic_cad.py`

---

## 1. 功能概述與效益 (Overview & Problem Statement)

### 1.1 問題陳述 (The Problem)
在傳統無人機開發流程中，從設計到試飛往往面臨漫長且昂貴的硬體試錯循環。先前系統已具備形態演化引擎（Morph Evolution），可依據任務自主演化最佳機臂長度、旋翼數量與 COTS 動力組合，並導出 URDF/SDF 物理描述檔；然而，其外觀僅由簡單的圓柱與立方體幾何基元組成，無法直接交付實體 3D 列印機進行一鍵實體化組裝。

為落實專案憲章核心使命：
> 「在數位孿生世界內可重複試錯，幾乎零試錯成本，快速完成無人機適應環境自主演化出機構與零件需求之目標。並且可以在真實世界採購實際零組件，與 3D 列印機構件組裝後讓無人機在真實世界飛行。」

系統需要一套**「參數化有機幾何 3D 列印 CAD 自動生成模組」**，將演化產出的無人機構型自動轉化為符合拓撲輕量化（仿生骨架與多邊形減重鏤空）且可直接送入切片軟體（Cura / PrusaSlicer / Bambu Studio）的標準單體 STL 網格模型。

### 1.2 核心目標與使用者故事 (User Story)
* **As a** 無人機結構工程師與數位孿生架構師，  
* **I want to** 在形態演化引擎產出新機型或手動給定配置時，一鍵自動長出仿生有機幾何機身，並導出合規二進位/ASCII STL 檔案，  
* **So that** 無需透過手動手繪 CAD，即可直接將數位孿生演化出的機身投入實體 3D 列印與真實世界組裝試飛，並在 WebGL 3D 模擬環境中直接預覽高擬真有機外觀。

### 1.3 架構訪談共識與決策 (Architect Interview Decisions)
依據 SDD Stage 1 架構訪談，確立以下三大關鍵工程決策：
1. **交付標準**：採用**極簡單體 STL 模型（Single Merged Airframe Mesh）**，直接輸出單一合併機身網格，附帶標準馬達安裝孔位與電裝艙槽，供快速 3D 列印與 WebGL 檢視。
2. **有機幾何風格**：採用**仿生漸變骨架與多邊形輕量化鏤空（Bionic Tapered Truss & Ribs）**，機臂自中心中樞向外流線錐度漸變，沿力流方向配置輕量化肋條鏤空，兼顧結構剛性與推重比。
3. **工作流整合度**：**全流程自動聯動**，演化引擎與 `drone_builder` 導出模型時，自動生成 STL 並同步歸檔至 `output/models_archive/`，供 WebGL 檢視器與後續實機組裝使用。

### 1.4 非目標範疇 (Non-Goals / Out of Scope)
* ❌ **不引入外部重型 CAD 編譯器**：遵守憲章「零重型編譯依賴」原則，不引用 OpenCASCADE (pythonocc)、FreeCAD 或重型 C++ 擴展，全模組以純 Python 標準庫與 NumPy 實作 STL 網格拓撲與法向量計算。
* ❌ **暫不處理複雜多部件卡榫拆件**：依架構師決策，本次聚焦於「一體化單機身單體 STL 輸出」，多零件分體鉸接與卡榫結構留待後續進階擴充。
* ❌ **不內建 G-code 切片引擎**：本系統負責產出工業標準 STL 實體網格，切片與支撐由市售成熟切片軟體（Cura / PrusaSlicer 等）負責。

---

## 2. 詳細需求與驗證標準 (Requirements & Acceptance Criteria)

### 2.1 功能性需求 (Functional Requirements)

- [ ] **FR-1: 仿生有機幾何生成核心 (`organic_cad_generator.py`)**
  - **說明**: 接收任意旋翼數量（4/6/8 旋翼）、機臂長度、馬達規格與電池幾何尺寸，以純數學與幾何演算法長出仿生有機網格。
  - **驗證標準 (AC-1.1)**: 
    - **中心中樞艙 (Core Pod)**：長出流線過渡的六角/八角多面體艙體，預留電池安裝腔體與飛控安裝平面。
    - **仿生機臂 (Bionic Arms)**：自中心艙根部（較寬較厚）平滑過渡延伸至馬達座（漸變錐度 Tapered Lofting），機臂中段具備力流輕量化鏤空結構（Truss Cutouts）。
    - **馬達安裝基座 (Motor Nacelle & Mounts)**：於機臂末端生成相容標準無刷馬達之底座（支援 16×19mm 或 12×12mm M3 螺絲孔位定位）。
    - **起落架緩衝柱 (Landing Skids)**：機身下方一體化整合輕量仿生著陸支撐柱。
  - **驗證標準 (AC-1.2)**: 支援動態任意旋翼配置（$N \in [3, 8]$）與變臂長（$0.15\text{m} \sim 0.60\text{m}$）。

- [ ] **FR-2: 工業級二進位與 ASCII STL 導出器 (Industrial STL Exporter)**
  - **說明**: 提供工業標準 STL 輸出能力，支援標準 80-byte Header、三角形面數計數器、Facet Normal 單位法向量計算與 12-byte 頂點座標封裝。
  - **驗證標準 (AC-2.1)**: 產出標準二進位 STL (`.stl`)，格式完全符合 ISO/ASTM 3D 列印標準規範。
  - **驗證標準 (AC-2.2)**: 檔案大小緊湊（典型四旋翼約 100KB ~ 2MB），確保切片軟體與 Three.js STLLoader 能在 200ms 內毫秒級秒開。
  - **驗證標準 (AC-2.3)**: 同步支援 ASCII STL 格式可讀模式（用於除錯與純文字驗證）。

- [ ] **FR-3: 與 `drone_builder.py` 及形態演化引擎深度串接**
  - **說明**: 在 `drone_builder.py` 的 `export_files` 流程中加入有機 CAD 導出管線。
  - **驗證標準 (AC-3.1)**: `builder.export_files(spec_dict, output_dir)` 新增導出 `cad_stl`，生成 `output/<design_id>.stl`。
  - **驗證標準 (AC-3.2)**: 演化世代保存庫 `output/models_archive/<model_name>/` 自動歸檔對應的 `<model_name>.stl` 與製造規格清單。

- [ ] **FR-4: 可製造性驗證器與 BOM 實體規格輸出 (Manufacturability & Print Profiler)**
  - **說明**: 自動計算 3D 列印實體關鍵指標，輔助飛手採購耗材與切片設置。
  - **驗證標準 (AC-4.1)**: 輸出 3D 列印製造資訊清單（JSON / Markdown 報告）：
    - 體積估算 ($V\text{ cm}^3$)
    - 預估列印重量（依據 PLA/PETG/碳纖維尼龍 PA-CF 密度如 $1.25\text{ g/cm}^3$）
    - 實體最大包裝外框包絡尺寸 ($X \times Y \times Z\text{ mm}$)
    - 推薦列印參數（噴嘴 $0.4\text{mm}$、層高 $0.2\text{mm}$、壁厚 3 層、填充率 $25\%\sim 40\%$）

- [ ] **FR-5: WebGL 3D 視覺整合與展示**
  - **說明**: 在 3D 幾何檢視器 (`view_3d_drone.py`) 或 WebGL 模擬器中，支援一鍵切換「實體 3D 列印有機機身預覽」。
  - **驗證標準 (AC-5.1)**: 檢視器具備有機 CAD STL 網格渲染模式，並維持流暢 60 FPS。

### 2.2 非功能性需求 (Non-Functional Requirements)
* **極速計算效能**: 單一有機機身 STL 生成時間 $\le 0.5\text{ 秒}$。
* **零重型相依**: 僅使用 Python 標準庫 (`struct`, `math`, `pathlib`, `json`) 與 `numpy`，不依賴外部編譯套件。
* **測試覆蓋率**: 新增 `test_organic_cad.py`，全套測試執行時間維持在 10 秒內且 100% 通過。

### 2.3 邊界條件與異常處理 (Edge Cases)
* **極端機臂長度**: 若臂長 $< 0.12\text{m}$ 或 $> 0.8\text{m}$，自動進行物理厚度自適應縮放，防止機身幾何自相穿透或壁厚過薄無法列印。
* **奇數/非對稱旋翼**: 支援 3 旋翼 (Y3/Tricopter) 至 8 旋翼 (Octocopter) 正確環形陣列佈局。

---

## 3. 技術介面規格 (API Contracts)

### 3.1 核心 API 介面
```python
class OrganicCADGenerator:
    """Generates 3D-printable bionic organic airframe geometries in standard STL."""
    
    def __init__(self, db: Optional[ComponentDB] = None):
        ...
        
    def generate_airframe_mesh(self, spec_dict: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Returns vertices (N, 3) and triangle faces (M, 3) for the organic frame."""
        ...
        
    def export_stl(self, spec_dict: Dict[str, Any], output_path: Union[str, Path], binary: bool = True) -> Path:
        """Exports unified airframe mesh to binary or ASCII STL file."""
        ...
        
    def get_print_profile(self, spec_dict: Dict[str, Any], material: str = "PLA") -> Dict[str, Any]:
        """Calculates volume, print weight, bounding box, and recommended slicer settings."""
        ...
```

### 3.2 列印規格 JSON Schema (`<model_name>_print_profile.json`)
```json
{
  "model_id": "evolved_shield_sentinel_v3",
  "bounding_box_mm": { "x": 380.5, "y": 380.5, "z": 65.0 },
  "airframe_volume_cm3": 142.8,
  "material": "PETG-CF",
  "density_g_cm3": 1.25,
  "estimated_print_weight_g": 178.5,
  "recommended_slicer_settings": {
    "nozzle_size_mm": 0.4,
    "layer_height_mm": 0.2,
    "wall_loops": 4,
    "top_bottom_layers": 5,
    "infill_percentage": 30,
    "infill_pattern": "gyroid",
    "supports_required": true
  }
}
```

---

## 4. 驗收核對表 (Acceptance Checklist)

- [ ] `organic_cad_generator.py` 模組建立完成。
- [ ] 支援 4/6/8 旋翼仿生錐度骨架與鏤空減重結構長成。
- [ ] 支援二進位與 ASCII 標準 STL 匯出（經 `struct.pack` 封裝，標準 80-byte header）。
- [ ] 整合進 `drone_builder.py` 與 `morph_evolution.py`，世代保存庫自動導出 STL 與 Print Profile。
- [ ] 單元測試 `test_organic_cad.py` 全數通過，且全專案所有單元測試 100% 通過。
