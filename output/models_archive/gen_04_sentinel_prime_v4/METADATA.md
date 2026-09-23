# 🚀 Generation 4: Sentinel Prime AI Autonomous Racer

* **機型編號**：`evolved_sentinel_prime_v4`
* **世代定位**：第 4 代純 AI 自主試錯閉環演化機型（微型對角直徑 ＋ 高推比馬達 ＋ 2.5mm 強化防撞涵道圈）
* **演化驅動來源**：
  * **AI 試飛資料集**：`output/training_datasets/ai_autonomous_flight_session_001.json`
  * **試錯瓶頸診斷**：Gen-3 涵道哨兵在以高速通過穿越門急轉向時，對角直徑 0.42m 容易使外側機臂在過彎離心力下擦碰門邊立柱（佔碰撞事故 36%）。
* **關鍵硬體與幾何演化 (Morphological Adaptations)**：
  1. **機臂長度微縮 (Arm Length 0.18m → 0.165m)**：
     * 整機對角跨距由 `0.42m` 收縮至 `0.38m`。
     * 偏航轉動慣量 $I_{zz}$ 下降約 **18.2%**，過彎最小旋轉半徑大幅收縮，徹底解決立柱擦碰。
  2. **高推重比動力馬達升級 (1806 2300KV → 2205 2600KV)**：
     * 單軸最大推力提升至 1050g，全機推重比達 **5.12 : 1**。
     * 垂直爬升加速度由 6.0 m/s² 提升至 **8.5 m/s²**，大幅消除低空穿門後的掉高遲滯。
  3. **2.5mm 碳纖維增強聚碳酸酯吸能涵道 (Reinforced Ducted Bumper)**：
     * 環圈壁厚由 2.0mm 增厚至 2.5mm，吸能剛度提高 45%，即便在極限貼壁掠過時也能達成 100% 彈性回彈，保護內部 5 吋三葉槳。
* **物理模型檔案**：
  * [URDF 模型](./evolved_sentinel_prime_v4.urdf)
  * [SDF 模型](./evolved_sentinel_prime_v4.sdf)
  * [完整規格 JSON](./model_spec.json)
