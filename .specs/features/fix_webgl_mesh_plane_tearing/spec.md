# Feature Spec：[FIX-M2-WEBGL-PLANE-TEARING] 3D 檢視器 WebGL 網格渲染平面破圖修復

> **版本**: 1.0  
> **功能 ID**: `FIX-M2-WEBGL-PLANE-TEARING`  
> **狀態**: `Approved (Signed off by Architect)`  
> **對應專案憲章**: `Constitution Phase 2 [M2.1/M2.6] WebGL 3D 模擬環境`  
> **目標分支**: `fix/webgl-mesh-plane-tearing`  
> **負責架構師**: Human Architect (Brain)  
> **執行 Agent**: Antigravity (Muscle)  
> **關聯模組**: `view_3d_drone.py`, `flight_test_sim.py`, `stl_viewer.py`, `test_webgl_environments.py`

---

## 1. 異常現象概述與根本原因 (Defect Overview & Root Causes)

### 1.1 異常現象 (Problem Statement)
在 WebGL 3D 檢視器（`view_3d_drone.py`、`flight_test_sim.py`、`stl_viewer.py`）中，使用者在旋轉、縮放與切換環境（特別是離岸風場與大型場景）時，觀察到幾何網格渲染平面發生破圖、面片閃爍穿透（Z-Fighting）與遠端硬切破口等嚴重視覺瑕疵。

### 1.2 深入除錯與根本原因分析 (Root Causes Analysis)
經過對 Three.js 渲染管線的深度排查，確定破圖是由以下 5 個聯動的幾何與渲染缺陷引起：

1. **動態波浪頂點變形缺乏法向量即時重算 (Missing Vertex Normal Recomputation)**：
   - 在 `animate()` 迴圈中，離岸風場海面網格 `oceanGeo.attributes.position` 逐幀動態位移，但未呼叫 `oceanGeo.computeVertexNormals()`。
   - 導致頂點位移後，網格法向量仍停留在初始平面法線 $(0, 0, 1)$。光影計算產生破片、黑面斑塊與高光斷裂，視覺上如同網格撕裂。
2. **網格輔助線 (GridHelper) 與動態海面波浪高度重疊產生 Z-Fighting**：
   - 基準空間網格 `currentGrid` 固定在 $y = 0.0$。
   - 海面基準高為 $y = -0.15$，但動態正弦波峰振幅高達 $+0.35\text{m}$，使水面動態上升至 $y = +0.20\text{m}$。
   - 海面每秒數十次穿刺穿插過 $y = 0.0$ 的網格平面，在深度緩衝區形成劇烈的 Z-Fighting 幾何破碎。
3. **視椎體遠裁剪面截斷 (Camera Frustum Far-Plane Truncation)**：
   - `camera = new THREE.PerspectiveCamera(..., 0.1, 200)`，遠裁剪面設定僅為 $200\text{m}$。
   - 海面與地面網格尺寸達 $350\text{m} \times 350\text{m}$（半徑 $175\text{m}$）與 $300\text{m} \times 300\text{m}$。
   - 當使用者以軌道視角（OrbitControls）稍微拉遠或傾斜視角時，網格遠端邊緣直接超出 $200\text{m}$ 視距，被視椎體硬性切斷，在視窗中呈現突兀的對角線破圖斷面。
4. **WebGLRenderer 缺乏對數深度緩衝 (Logarithmic Depth Buffer)**：
   - 預設 24-bit 線性深度緩衝在近距（$0.1\text{m}$）至大範圍（$200\text{m} \sim 2000\text{m}$）跨度下，遠端精度大幅衰減。
   - 未開啟 `logarithmicDepthBuffer: true`，導致共面或微小高度差平面在斜視視角下產生嚴重深度跳變。
5. **材質單面剔除與缺乏深度多邊形偏移 (Material SingleSide & Missing PolygonOffset)**：
   - 地面材質預設未指定 `side: THREE.DoubleSide`，低角度時被背面剔除產生空洞。
   - 地面與標記平面未設置 `polygonOffset`，導致輔助標記與地面發生像素級深度爭奪。

---

## 2. 核心目標與使用者故事 (User Story & Non-Goals)

### 2.1 使用者故事 (User Story)
* **As a** 數位孿生飛行器工程師與檢視者，
* **I want to** 在 3D 檢視器與飛行模擬器中，無瑕疵平滑瀏覽無人機在離岸風場、城市搜救、碰撞競技場與夜間紅外場景的 3D 幾何網格，
* **So that** 不會因海面波浪法向量撕裂、視椎體裁切破圖或 Z-Fighting 閃爍干擾評估與展示體驗。

### 2.2 非目標範疇 (Non-Goals)
* ❌ **不重構渲染引擎**：維持純 Three.js r128 原生無伺服器單 HTML 架構，不升級至需要額外建置工具的 WebGPU。
* ❌ **不增加外部相依性**：不引入肥大 Shader 函式庫或外部海浪外掛，使用 Three.js 數學核心。

---

## 3. 功能需求與驗收標準 (Requirements & Acceptance Criteria)

### 3.1 功能性需求 (Functional Requirements)

- [ ] **FR-1: 動態網格法向量即時重算與平滑著色**
  - **說明**: 在離岸風場的海面網格動態位移後，每幀調用 `oceanGeo.computeVertexNormals()`，確保光照與法向量嚴格同步。
  - **驗收標準 (AC-1.1)**: `view_3d_drone.py` 與 `flight_test_sim.py` 中的 `animate()` 迴圈內，海面位置屬性更新後必定執行 `oceanGeo.computeVertexNormals()`。

- [ ] **FR-2: 啟用 WebGLRenderer 對數深度緩衝 (Logarithmic Depth Buffer)**
  - **說明**: 在初始化 `THREE.WebGLRenderer` 時，明確宣告 `logarithmicDepthBuffer: true`。
  - **驗收標準 (AC-2.1)**: 檢視器在 $0.1\text{m} \sim 2000\text{m}$ 深度範圍內保持高精度深度排序，消除共面閃爍。

- [ ] **FR-3: 擴展相機視椎體遠裁剪面 (Far Clipping Plane) 與地平線邊界**
  - **說明**: 將相機遠裁剪面由 `200` 擴展至 `1000`（檢視器）與 `2000`（飛行模擬器）。
  - **驗收標準 (AC-3.1)**: 使用者拉遠視角至全景時，350m 渲染平面絕無任何邊界幾何被硬裁切產生的直線破圖。

- [ ] **FR-4: 消除網格輔助線與海面波浪的高度碰撞 (Wave & Grid Decoupling)**
  - **說明**: 在離岸風場（海面動態波動）情境下，若海面波動高度在 $[-0.5\text{m}, +0.28\text{m}]$，將基準網格調整為水下海床高度（如 $y = -2.0\text{m}$）或設定海面網格深度偏移，並對平坦地面（城市、測試場、夜間）配置 `polygonOffset` 與 `THREE.DoubleSide`。
  - **驗收標準 (AC-4.1)**: 動態水浪與空間格線無任何 Z-Fighting 與穿刺交錯現象。

- [ ] **FR-5: 全檢視器統一同步修復 (`view_3d_drone.py`, `flight_test_sim.py`, `stl_viewer.py`)**
  - **說明**: 確保所有 3D 檢視器與模擬器均具備相同標準的防破圖幾何渲染配置。
  - **驗收標準 (AC-5.1)**: 重新產出 HTML 檔案，執行單元測試 100% 通過。

### 3.2 非功能性需求 (Non-Functional Requirements)
* **影格率表現**: 在標準瀏覽器中維持穩定 60 FPS，動態重演法向量與對數深度緩衝不引入任何感知卡頓。
* **零外部相依**: 維持純標準庫與單 HTML 零安裝架構。

---

## 4. 驗證與測試規劃 (Validation Strategy)
1. 在 `test_webgl_environments.py` 中擴充專門針對 WebGL 渲染平面防破圖特性的單元測試。
2. 檢查產出 HTML 中包含 `logarithmicDepthBuffer: true`、`computeVertexNormals()`、`far >= 1000`、`DoubleSide` 等關鍵防禦碼。
3. 執行全套單元測試套件確保 100% 通過。
