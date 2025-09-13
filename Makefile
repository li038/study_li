# AI文档问答系统 Makefile

.PHONY: help install dev test lint format clean docker-build docker-run

# 默认目标
help:
	@echo "AI文档问答系统"
	@echo ""
	@echo "可用命令:"
	@echo "  make install     - 安装依赖"
	@echo "  make dev         - 启动开发模式"
	@echo "  make test        - 运行测试"
	@echo "  make lint        - 代码检查"
	@echo "  make format      - 代码格式化"
	@echo "  make clean       - 清理缓存"
	@echo "  make docker-build - 构建Docker镜像"
	@echo "  make docker-run  - 运行Docker容器"
	@echo "  make setup       - 完整初始化"

# 安装依赖
install:
	pip install -r requirements.txt

# 开发模式
dev:
	python main.py

# 生产模式
prod:
	python main.py --host 0.0.0.0 --port 7860

# 基础模式
basic:
	python main.py

# 运行测试
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# 代码检查
lint:
	flake8 src/ --max-line-length=88 --ignore=E203,W503
	black src/ --check

# 代码格式化
format:
	black src/
	isort src/

# 清理缓存
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf cache/*
	rm -rf logs/*

# 构建Docker镜像
docker-build:
	docker build -t ai-langchain:latest .

# 运行Docker容器
docker-run:
	docker-compose up -d

# 停止Docker容器
docker-stop:
	docker-compose down

# 查看日志
docker-logs:
	docker-compose logs -f

# 完整初始化
setup: install
	@echo "创建必要目录..."
	mkdir -p uploads logs cache src/core src/utils tests
	@echo "复制环境变量模板..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "请编辑 .env 文件配置API密钥"; fi
	@echo "初始化完成！"

# 备份数据
backup:
	@tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz uploads/ logs/ docs/ .env

# 恢复数据
restore:
	@echo "请将备份文件放在当前目录"
	@echo "使用: tar -xzf backup_*.tar.gz"

# 性能测试
benchmark:
	python -m pytest tests/ -v --benchmark-only

# 代码覆盖率
coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "查看覆盖率报告: htmlcov/index.html"