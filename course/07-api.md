# 第七章：HTTP API 速查

> **本章目标**：会用 `curl` 调用控制台的只读状态接口、相机取图，并正确调用受安全门控保护的运动与导航接口。
> **涉及文件**：`src/xr_arm_console/xr_arm_console/app.py`（全部接口实现）

控制台后端本身就是一套 HTTP API，前缀统一为 `http://<机器人IP>:8088`。约定：`GET` 接口全部只读无副作用；`POST` 接口凡涉及真实运动一律要求**运动三件套**（见下文）。

## 健康与状态（只读）

| 接口 | 用途 |
|---|---|
| `GET /api/health` | 存活探针 |
| `GET /api/status` | 总览聚合：模式/版本/系统/双臂关节/电池 |
| `GET /api/lift/status` | 升降：位置、报警、对地间隙 |
| `GET /api/body/head/status` | 头部：pitch/yaw 反馈 |
| `GET /api/arm/safety` | 双臂安全快照 |
| `GET /api/peripherals` | 相机/手柄等外设在线状态 |
| `GET /api/skills` | 技能注册表（第六章工作流的数据源） |

真机采样 `GET /api/health`：

```json
{"mode": "navigation_control_enabled", "ok": true, "version": "0.3.0"}
```

真机采样 `GET /api/lift/status`（节选，仅保留关键字段）：

```json
{
  "age_seconds": 134.49,
  "busy": false,
  "alarm": {"current_code": 0, "current_text": "正常", "received": true}
}
```

`alarm.current_code` 为 0 即无报警；非 0 时 `current_text` 给出报警文本。响应中还有 `position`（当前位置）与 `clearance`（对地间隙守卫状态）等字段，分别对应第四章升降面板与守卫态势。

## 相机取图

| 接口 | 用途 |
|---|---|
| `GET /api/cameras/{head\|left\|right}/frame.jpg` | 单帧 JPEG |
| `GET /api/cameras/{name}/stream.mjpeg` | MJPEG 视频流 |

相机是**按需发布**的：请求会触发订阅并在服务端短暂等待首帧（约 3 秒上限）。因此第一次请求可能返回 `503 {"code":"camera_frame_timeout"}`，**立即重试一次**通常即可拿到图。成功响应带两个有用的响应头：`X-XR-Frame-Sequence`（帧序号）与 `X-XR-Frame-Age`（帧龄，秒）。

```bash
curl -o head.jpg -w "%{http_code} %{size_download}B\n" \
  "http://<机器人IP>:8088/api/cameras/head/frame.jpg"
```

相机话题映射（`src/xr_arm_console/xr_arm_console/peripherals.py:10`）：

```python
CAMERAS = {
    "head": {"topic": "/head/camera/rgb", "device": "/dev/videoHead"},
    "left": {"topic": "/left/camera/rgb", "device": "/dev/videoLeft"},
    "right": {"topic": "/right/camera/rgb", "device": "/dev/videoRight"},
}
```

## 运动三件套（重点）

升降与头部运动接口强制三重校验，**缺任何一件都被拒绝**，顺序如下（`src/xr_arm_console/xr_arm_console/app.py:2834`）：

```python
        if request.headers.get("X-XR-Lift-Intent") != "lift-motion":
            return jsonify(
                {"ok": False, "code": "missing_intent", "message": "缺少明确的升降运动意图"}
            ), 403
        body = request.get_json(silent=True) or {}
        if body.get("confirm") is not True:
            return jsonify({"ok": False, "message": "需要确认升降运动"}), 409
```

| 接口 | 意图请求头 | 必填体字段 |
|---|---|---|
| `POST /api/lift/move` | `X-XR-Lift-Intent: lift-motion` | `confirm:true` + `delta_m`（相对，[-0.3,0.3] m）或 `target_m`；可选 `velocity_m_s` |
| `POST /api/lift/stop` | — | —（急停，随时可调） |
| `POST /api/body/head/move` | `X-XR-Body-Intent: head-motion` | `confirm:true` + `pitch_deg`/`yaw_deg`，`mode` 默认 `relative`（可 `absolute`） |

`POST /api/lift/move` 完整示例：

```bash
curl -X POST "http://<机器人IP>:8088/api/lift/move" \
  -H "Content-Type: application/json" \
  -H "X-XR-Lift-Intent: lift-motion" \
  -d '{"delta_m": 0.05, "confirm": true}'
```

成功返回 `202 {"ok": true, "message": "升降指令已下发，目标 1.245 m"}`。常见拒绝：缺意图头 `403 missing_intent`；缺 confirm `409 需要确认升降运动`；`delta_m` 越界 `400`；目标超行程 `409 目标高度超出允许范围`；导航任务进行中 `409 导航任务进行中，禁止升降运动`。

头部运动同样模式，头 `X-XR-Body-Intent: head-motion`，体 `{"pitch_deg": -10, "yaw_deg": 15, "mode": "relative", "confirm": true}`，yaw 取值须在 [-π, π]。

## 导航接口

| 接口 | 体字段 |
|---|---|
| `POST /api/navigation/start` | `confirm:true`（启动 lastpose 自主定位） |
| `POST /api/navigation/tasks` | `confirm:true` + `x`、`y`、`yaw`（米/弧度，yaw ∈ [-π,π]）；已有任务时需 `replace:true` 才会替换 |
| `POST /api/navigation/tasks/<task_id>/cancel` | — |
| `POST /api/navigation/reset` | `confirm:true`（停止任务并重置 SLAM） |
| `GET /api/navigation/status` / `GET /api/navigation/map` / `GET /api/navigation/waypoints` | 只读 |

目标坐标校验源码（`src/xr_arm_console/xr_arm_console/app.py:2508`）：

```python
        try:
            x = float(body["x"])
            y = float(body["y"])
            yaw = float(body["yaw"])
        except (KeyError, TypeError, ValueError):
            return jsonify({"ok": False, "message": "导航目标必须包含有效的 x、y、yaw"}), 400
        if not all(math.isfinite(value) for value in (x, y, yaw)):
            return jsonify({"ok": False, "message": "导航目标不能包含非有限数值"}), 400
        if not -math.pi <= yaw <= math.pi:
            return jsonify({"ok": False, "message": "yaw 必须位于 [-pi, pi]"}), 400
```

成功创建任务返回 `202 {"ok": true, "task_id": "<uuid>"}`，之后用 `GET /api/navigation/status` 轮询进度。

## 维护与标定接口

升降校准 `POST /api/body/lift/calibrate`、头部校准 `POST /api/body/head/calibrate`、清除升降报警 `POST /api/body/lift/clear-alarm`、夹爪端点采集 `POST /api/calibration/capture-gripper-endpoint` 等标定接口与第三章网页功能一一对应，均要求确认字段。集成测试建议优先使用只读接口，运动接口仅在有人监护时调用。

## 动手试试

1. 用 `curl` 依次请求 `/api/health`、`/api/status`、`/api/lift/status`，对照第四章界面数值。
2. 故意省略意图头调用一次 `POST /api/lift/move`，观察 `403 missing_intent` 响应——理解三件套的第一道闸（不会产生任何运动）。
3. 拉一帧左臂相机图并用图片查看器打开。

## 小结

- `GET` 全只读可放心轮询；运动/导航类 `POST` 一律三件套：产品门控 + 意图头 + `confirm:true`。
- 相机按需发布，首次 503 重试即可；帧龄看 `X-XR-Frame-Age`。
- 升降相对模式 `delta_m` 上限 ±0.3 m，越界/超程/导航互斥都会被拒绝。
- 所有可能运动的接口在代码层 fail-closed，异常输入只会得到 4xx 而不是危险动作。
