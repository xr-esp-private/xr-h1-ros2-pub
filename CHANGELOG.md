# Changelog

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/);版本遵循语义化。
发版纪律:打 `v*` tag 前必须存在对应 `## [x.y.z]` 段落(预发布 `-rc*` 取 `[Unreleased]`)。

## [Unreleased]

- 发布说明改由本文件驱动:打 tag 自动同步 CHANGELOG 到公开仓库并作为 Release 说明展示;稳定版 tag 缺少对应版本段落时发版守卫直接失败。

## [0.4.0] - 2026-08-22

运行时/治理定位分离改造完成:xrlab 单向配置链路、部署工具化与 dispatch-pull 发布流水线。

### Added

- 单向配置链路:`config/products/<product>.json` + 设备 overlay → `tools/xr-config resolve` → `/etc/xrlab/robot-config.json`,Console/arm launch/driver 三处统一消费;模块与 operation 三态门控(`disabled/observe/control`)。
- 部署工具 `tools/xrctl`:`apply`(远端快照 → 安装 → 验收 → 失败自动恢复)、`rollback`(快照回滚)、`status`(本地/远端 digest 对账)、`doctor`;配置工具新增 `apply-local`(deb 装机收口)。
- body-gateway 从 resolved config 读取升降行程限位与命令授权(`hardware.lift` 为 xr-aih1 必填,缺失拒启)。
- 字段消费矩阵 `docs/architecture/config-fields.md` 与 schema 全量 description。
- 发布流水线(dispatch-pull):公开仓库只承载流水线定义与 Release 产物;私有打 tag 自动触发双架构(Ubuntu 24.04 amd64/arm64)构建、测试并发布 `xrlab-ros2_<ver>_<arch>.deb`,同时上传私有 apt 源。

### Changed

- 品牌与路径统一为 xrlab:`/opt/xrlab/ros2`、`/etc/xrlab/robot-config.json`、`/var/lib/xrlab/data`、`/usr/share/xrlab/{config,tools}`;deb 包名 `xrlab-ros2`。
- Console 产品投影与 3D 模型改为从 resolved config 的 `profiles` 读取;导航只读订阅由 `modules.body.mode` 推导。
- systemd unit 模板路径迁移至上述新布局;body-gateway 新增 `robot_config` 参数,unit 不再手写限位副本。
- 发布模型从"源码镜像导出"重构为"公开仓库仅含流水线,构建时私拉源码"。

### Fixed

- `xr_arm_core` 静态库缺 PIC 导致全新环境链接共享库失败(CI 全量构建暴露)。
- package.xml 中不可解析的 `ament_python` rosdep 键。
- 容器 CI 一揽子修复:dash 缺 pipefail、ros:jazzy 无 pip、colcon test 布局、SIGPIPE 误判、容器作业 workspace 路径。

### Removed

- 旧产品合同包 `src/xr_product_profiles/`(registry/manifest/schema/validator)及 relock 脚本;Console 投影不再依赖任何 registry。
- 全部功能型启动开关与环境变量:`--enable-*`、`--read-only-*`、`--disable-navigation`、`--device`、`XR_DEPLOY_*`、`XR_FLAT_CONFIG_ROOT`。
- `tools/xr-deploy` 与其测试(被 `tools/xrctl` 取代)。
