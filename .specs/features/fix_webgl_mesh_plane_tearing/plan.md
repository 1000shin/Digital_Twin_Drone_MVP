# Implementation Plan：[FIX-M2-WEBGL-PLANE-TEARING] 3D 檢視器 WebGL 網格渲染平面破圖修復

> **版本**: 1.0  
> **功能 ID**: `FIX-M2-WEBGL-PLANE-TEARING`  
> **目標分支**: `fix/webgl-mesh-plane-tearing`  
> **執行原則**: 小步前進、漸進提交、單元測試防禦、零上下文衰退。

---

## 任務拆解 (Task Groups & Milestones)

### Phase 1: 規格凍結與分支開立 (Spec & Branching)
- [x] **Task 1.1**: 開立獨立 Git 修復分支 `fix/webgl-mesh-plane-tearing`。
- [x] **Task 1.2**: 建立 `.specs/features/fix_webgl_mesh_plane_tearing/spec.md` 與 `plan.md`，定義驗收標準。

### Phase 2: 核心幾何檢視器修復 (`view_3d_drone.py`)
- [x] **Task 2.1**: 更新 `THREE.WebGLRenderer` 初始化，注入 `logarithmicDepthBuffer: true`。
- [x] **Task 2.2**: 擴充相機視椎體遠裁切面 `camera.far` 至 `1000`。
- [x] **Task 2.3**: 在 `animate()` 中的海面波動計算區段加入 `oceanGeo.computeVertexNormals()`。
- [x] **Task 2.4**: 調整離岸風場場景中的 `currentGrid` 位置或海面配置，並為地面材質加入 `side: THREE.DoubleSide` 與 `polygonOffset`。

### Phase 3: 3D 飛行模擬器與 STL 檢視器同步修復 (`flight_test_sim.py`, `stl_viewer.py`)
- [x] **Task 3.1**: 同步更新 `flight_test_sim.py` 中的 `logarithmicDepthBuffer: true`、`camera.far = 2000` 與 `oceanGeo.computeVertexNormals()`。
- [x] **Task 3.2**: 同步檢查與更新 `stl_viewer.py`，開啟 `logarithmicDepthBuffer: true` 與防破圖參數。

### Phase 4: 自動化單元測試擴充 (`test_webgl_environments.py`)
- [x] **Task 4.1**: 於 `test_webgl_environments.py` 新增防破圖斷言（檢查 `logarithmicDepthBuffer: true`、`computeVertexNormals()`、`far >= 1000`、`DoubleSide`）。
- [x] **Task 4.2**: 執行全套單元測試確保全數通過。

### Phase 5: 產出驗證與發布同步 (Validation & Release)
- [x] **Task 5.1**: 重新生成 `output/view_3d_scene.html`、`output/flight_test_simulator.html`、`output/stl_viewer.html`。
- [x] **Task 5.2**: 執行 Sub-Agent 深度代碼審查（Deep Code Review），產出審查報告。
- [x] **Task 5.3**: 填寫 `.specs/features/fix_webgl_mesh_plane_tearing/validation.md`。
- [x] **Task 5.4**: 更新 `CHANGELOG.md`，完成 Git Commit 與 PR 合併準備。
