# xrlab-ros2 发布仓库

本仓库**只承载发布流水线与产物**,不承载源码。源码在私有仓库
`xr-esp-private/xr-h1-ros2` 开发;每次私有仓库打 `v*` tag,会自动触发本仓库的
`build-deb` 工作流:按指定 commit 拉取私有源码,双架构(Ubuntu 24.04 amd64 /
arm64 原生 runner)构建、测试并发布 Release。

## 安装

到 [Releases](../../releases) 下载对应架构的 `xrlab-ros2_<版本>_<arch>.deb`
(目标机需先安装 ROS 2 Jazzy):

```bash
sudo apt install ./xrlab-ros2_<版本>_<arch>.deb
sudoedit /etc/xrlab/device.json        # 可选设备 overlay;省略 = 纯产品默认
sudo xr-config apply-local --product xr-aih1 --restart
```

纯双臂产品使用 `--product xr-h1arm`。

## 维护者须知(流水线配置)

| 位置 | 名称 | 用途 |
| --- | --- | --- |
| 本仓库 Secrets | `PRIVATE_SOURCE_TOKEN` | 构建时只读拉取私有源码 |
| 私有仓库 Secrets | `MIRROR_TOKEN` | 打 tag 后触发本仓库 workflow_dispatch |

工作流由私有仓库 `packaging/github/workflows/build-deb.yml` 的内容同步维护
(该文件随私有仓库演进,更新时覆盖本仓库同名文件)。
