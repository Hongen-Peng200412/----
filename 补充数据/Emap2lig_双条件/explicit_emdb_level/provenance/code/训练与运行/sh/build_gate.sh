#!/usr/bin/env bash
set -euo pipefail

# Job 423330 启动时登记了此门控路径, 保留名称以让现有控制器验证 release; 正式任务直接调用 with_level.sh.
exec bash "${TASK_PROJECT_ROOT:?}/训练与运行/sh/with_level_gate.sh"
