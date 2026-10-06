# go-emby 自定义版

基于官方镜像 `ghcr.io/sd87671067/go-emby:2026.10.06-051710`，在 `docker build` 时对二进制做等长原位补丁（不改变文件大小与 ELF 布局）。

官方前端通过 Go `embed` 编进二进制，无法外部覆盖，因此采用二进制补丁。补丁逻辑全在 `patch.py`，透明可审计。

## 补丁内容

| # | 说明 | 实现 |
|---|------|------|
| 1 | 前台点「后台管理」默认进入「控制台」（原默认「媒体管理」） | `admin()` 结尾 `mediaPage()` → `adminSection(12)`（33 字节等长替换） |
| 2 | 管理员密码下限 12 字节 → **3 字节** | 6 处 `cmp $0xc` → `cmp $0x3`（单字节）：初始化、改密码、建用户、改用户、后台管理内 2 处 |
| 3 | 错误提示文案同步 | `管理员密码需要 12–72 字节` → `管理员密码需要 3–72 字节`（36 字节等长） |

补丁地址通过解析 Go `gopclntab` 定位函数（`main.(*App).init/password/admin/userIdentity/userManagement`），再反汇编确认。未来官方镜像更新后，需重新核对 `patch.py` 中的地址。

## 构建与使用

```bash
docker build -t go-emby:custom .
```

`compose.yaml` 中：

```yaml
image: go-emby:custom
```

```bash
docker compose up -d
```

回滚：把 `image:` 改回官方 tag，`docker compose up -d` 即可。

## 忘记管理员密码

`ADMIN_PASSWORD` 环境变量只在首次初始化（用户表为空）时生效，之后改它没用。用附带的脚本直写数据库：

```bash
./scripts/reset-password.sh <新密码>
```

## 文件说明

- `Dockerfile`：多阶段构建（官方镜像 → python 补丁 → 官方镜像 + 补丁后二进制）
- `patch.py`：二进制补丁脚本
- `scripts/reset-password.sh`：密码重置脚本

> 注意：补丁针对 `linux/amd64`。ARM64 服务器需要重新定位补丁地址。
