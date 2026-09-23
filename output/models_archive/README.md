# 🛸 數位分身多世代無人機 3D CAD / 物理模型庫 (Multi-Generation Models Archive)

本資料夾完整永久留存此專案由第 1 代飛手手動試錯、第 2 代高敏捷環境感知、第 3 代涵道防撞哨兵，乃至第 4 代 AI 自主試錯閉環演化所催生出的全部 3D CAD 與物理動態模型（URDF / SDF / Spec JSON）。

---

## 🏛️ 機型演化世代全覽表 (Evolution Lineage Matrix)

| 世代 | 機型代號 | 核心特徵與定位 | 機臂/幾何規格 | 轉動慣量與動力 | 關鍵防護與感測配備 | 歷史驗證來源 |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| **Gen 1** | [`evolved_confined_space`](./gen_01_baseline_confined_v1/) | 初始基準機型（六軸對稱） | 6 臂 / 0.22m / 外徑 0.44m | $I_{zz}=0.016$ / TWR 2.4 | 無涵道、無航空燈、無測距雷達 | [Session 001 診斷](../../flight_audit_reports/session_confined_001_audit.md) |
| **Gen 2** | [`evolved_agile_confined_v2`](./gen_02_agile_confined_v2/) | 高敏捷環境感知飛行器 | 4 臂 / 0.20m / 外徑 0.40m | $I_{zz}=0.009$ / TWR 5.75 | 航行紅綠燈、機頭大燈、360° LiDAR 射線 HUD | [Session 002 診斷](../../flight_audit_reports/session_confined_002_audit.md) |
| **Gen 3** | [`evolved_shield_sentinel_v3`](./gen_03_shield_sentinel_v3/) | 涵道防撞哨兵飛行器 | 4 臂 / 0.18m / 外徑 0.42m | $I_{zz}=0.007$ / TWR 2.4 | 一體化涵道防撞圈、光流機腹、AI Copilot 虛擬力場 | [Session 003 診斷](../../flight_audit_reports/session_confined_003_audit.md) |
| **Gen 4** | [`evolved_sentinel_prime_v4`](./gen_04_sentinel_prime_v4/) | 超敏捷哨兵領航機 (AI 自主) | 4 臂 / 0.165m / 外徑 0.38m | $I_{zz}=0.0058$ / TWR 5.12 | 2.5mm 強化吸能涵道、AI 自主避障、航點路徑投影 | [Session AI 001 報告](../../flight_audit_reports/ai_session_001_audit.md) |

---

## 📂 檔案目錄結構

```bash
output/models_archive/
├── index.json                        # 機器可讀世代全覽索引庫 (含 STL 與列印規格路徑)
├── README.md                         # 世代技術演化綜合說明
├── gen_01_baseline_confined_v1/      # 第 1 代模型封裝 (URDF / SDF / STL / Print Profile)
├── gen_02_agile_confined_v2/         # 第 2 代模型封裝 (URDF / SDF / STL / Print Profile)
├── gen_03_shield_sentinel_v3/        # 第 3 代模型封裝 (URDF / SDF / STL / Print Profile)
└── gen_04_sentinel_prime_v4/         # 第 4 代 AI 自主試錯閉環模型封裝
    ├── evolved_sentinel_prime_v4.urdf              # ROS 2 / 物理計算描述
    ├── evolved_sentinel_prime_v4.sdf               # Gazebo 模擬描述
    ├── evolved_sentinel_prime_v4.stl               # [M2.1] 工業標準二進位 3D 列印單體網格
    ├── evolved_sentinel_prime_v4_print_profile.json # [M2.1] 3D 列印參數、耗材重量與包絡體積
    ├── model_spec.json
    └── METADATA.md
```
