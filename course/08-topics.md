# 第八章：ROS 话题速查

> **本章目标**：知道机器人上有哪些可订阅的状态话题、命令链路如何走、订阅时的 QoS 注意事项，避免把自己的节点接到错误的话题上。
> **涉及文件**：`src/xr_motion_guard/`（网关节点）、`docs/architecture/motion-guard.md`（合同文档）

XR-AIH1 的 ROS 2（Jazzy）话题分为三类：**我方网关发布的状态话题**、**命令链路**、**传感器/原厂话题**。核心原则：`xr-body-gateway`（motion-guard）是身体的**唯一命令出口**，机械臂 CAN 由 Driver1 独占，任何集成代码都应接到网关话题上，而不是绕过它。

## 状态话题（可放心订阅）

| 话题 | 内容 | 频率 |
|---|---|---|
| `/xr/arm/joint_states` | 14 关节状态（左 7 + 右 7，D-Bus 桥接自 Driver1） | 持续流 |
| `/xr/arm/status` | `ArmStatus`，guard 策略重算后的投影 | 持续流 |
| `/xr/motion/clearance` | 对地间隙裁决态势（`ClearanceStatus`） | ~10 Hz |
| `/xr/motion/gate/status` | 每次命令请求的关卡处置（放行/拦截原因） | 事件驱动 |
| `/xr/arm_lift/state` | 升降归一化状态（显示用转发） | 持续流 |
| `/xr/gamepad/joy` | 手柄整帧（`sensor_msgs/Joy`） | 按输入 |

状态数据管线（`docs/architecture/motion-guard.md:59`）：

```text
/lift/joint_states(原厂)──┐
                          │ 归一化 → /xr/arm_lift/state(显示用转发)
D-Bus StateChanged ───────┤► 桥接发布 /xr/arm/joint_states(本节点唯一发布)
(Driver1, 阶段 H)         │   + /xr/arm/status(guard 策略重算的投影)
                          │► 10Hz 裁决 → /xr/motion/clearance(态势)
                          │   每请求处置 → /xr/motion/gate/status(态势显示)
```

注意 `/xr/arm/joint_states` 使用 `BEST_EFFORT/VOLATILE` QoS，订阅端不要用 `RELIABLE` 去匹配。

## 命令链路（集成方入口）

| 入口 | 类型 | 说明 |
|---|---|---|
| `/xr/motion/request/arm` | 服务（`ArmGateCommand`） | **臂命令关卡**：规划执行、示教回放、安全卸力、高温回零统一走它；网页第七章的 HTTP 运动接口底层即此 |
| `/xr/motion/request/lift/move` | 动作入口 | 升降目标高度 |
| `/xr/arm_lift/driver/cmd_vel` | 话题 | 网关**唯一发布**、原厂 bodycontrol 独占消费——集成方**不要**直接往这写 |

关卡拒绝原因（`/xr/motion/gate/status` 与网页角标可见）主要是三类：状态过期（stale）、对地间隙不足（ground_clearance）、帷幕/互斥条件。被拒绝是保护，不是故障；先看 `/xr/motion/clearance` 与 `/xr/motion/gate/status` 找原因。

## 传感器与原厂话题

| 话题 | 说明 |
|---|---|
| `/head/camera/rgb`、`/left/camera/rgb`、`/right/camera/rgb` | 三路相机（BEST_EFFORT，按需发布） |
| `/lift/alarm`、`/head/stall` | 升降报警/头部堵转，**锁存话题** |
| `/task_status_v2` | 原厂导航任务状态——**空闲时 0Hz 静默属正常**，只有任务运行期才发布 |

**锁存话题订阅必须带 transient_local**，否则收不到最后一条 retained 消息、看起来"没数据"：

```bash
ros2 topic echo /head/stall --qos-durability transient_local --once
```

## 给集成方的三条军规

1. **单写者**：`/xr/arm_lift/driver/cmd_vel` 只有网关能写；臂 CAN 只有 Driver1 能碰。自己的节点一律走 `/xr/motion/request/*` 关卡。
2. **DDS 名额有限**：RK 上 DDS 参与者名额紧张（常驻约 33 个），`ros2 CLI` 探针用完即关（`ros2 daemon stop`）；长期订阅优先用代码内 rclcpp/rclpy，短诊断用 `tools/xr-doctor`（零参与者设计）。
3. **fail-closed 心态**：任何状态新鲜度存疑（`age_seconds` 超限），守卫一律拒绝运动。集成逻辑里同样不要用过期状态做决策。

## 动手试试

1. 订阅 `/xr/motion/clearance` 十秒，观察升降静止与运动时对地间隙数值的变化。
2. 用第七章的 `POST /api/lift/move`（不带意图头）触发一次拒绝，再订阅 `/xr/motion/gate/status` 找到这次请求的处置记录。

## 小结

- 订状态找 `/xr/arm/*` 与 `/xr/motion/*`，发命令走 `/xr/motion/request/*` 关卡，绝不直写驱动层话题。
- 锁存话题（`/lift/alarm`、`/head/stall`）订阅要带 `--qos-durability transient_local`。
- `/task_status_v2` 空闲 0Hz 是原厂行为，不代表导航故障。
- DDS 名额紧张：CLI 短用快关，诊断首选 `xr-doctor`。
