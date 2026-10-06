# go-emby 自定义版：官方最新镜像 + 构建时二进制补丁
#
# 补丁内容（patch.py）：
#  1. 后台管理默认进入「控制台」（原默认「媒体管理」）
#  2. 管理员密码下限 12 字节 → 3 字节（初始化/改密码/建用户/改用户/后台管理，共 6 处）
#  3. 错误提示文案同步
#
# 构建：
#   docker build -t go-emby:custom .
# 使用（compose.yaml）：
#   image: go-emby:custom
# 回滚：改回官方 tag 后 docker compose up -d

ARG BASE=ghcr.io/sd87671067/go-emby:2026.10.06-051710

FROM ${BASE} AS base

FROM python:3-alpine AS patcher
COPY --from=base /usr/local/bin/go-emby /tmp/go-emby
COPY patch.py /tmp/patch.py
RUN python3 /tmp/patch.py /tmp/go-emby && chmod 755 /tmp/go-emby

FROM ${BASE}
COPY --from=patcher /tmp/go-emby /usr/local/bin/go-emby
