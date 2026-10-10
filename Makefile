# ================== 变量区 ==================
# 这样改端口或路径只改一处
VENV    := /root/my-agent/.venv/bin/python3
SRC_DIR := /root/my-agent/src
PORT    := 8000
HOST    := 0.0.0.0
LOG     := /tmp/uvicorn.log

# ================== target 区 ==================

# 前台开发模式：能看到实时日志，Ctrl+C 停止
dev:
	cd $(SRC_DIR) && $(VENV) -m uvicorn server:app --host $(HOST) --port $(PORT) --reload

# 后台启动：服务在后台跑，日志写文件
start:
	cd $(SRC_DIR) && rm -f agent.db && $(VENV) -m uvicorn server:app --host $(HOST) --port $(PORT) --reload > $(LOG) 2>&1 &

# 重启：先杀旧的，再起新的
restart: stop start

# 只杀进程
stop:
	fuser -k $(PORT)/tcp 2>/dev/null || true

# 清临时文件
clean:
	rm -f $(SRC_DIR)/agent.db

# 声明这不是真实文件名（防止和 dev/start 目录重名冲突）
.PHONY: dev start restart stop clean