#!/bin/bash
# 管理员密码重置脚本（忘记密码时用）
# 用法：./reset-password.sh <新密码>
# 原理：直接往 postgres 的 users 表写 bcrypt 哈希（cost 12，与服务端一致）
set -e
cd "$(dirname "$0")/../.."

if [ -z "$1" ]; then
  echo "用法: $0 <新密码>"
  exit 1
fi
NEWPW="$1"

# 生成 bcrypt 哈希（优先 php，其次 python3+bcrypt，其次 htpasswd）
if command -v php >/dev/null 2>&1; then
  HASH=$(php -r "echo password_hash('$NEWPW', PASSWORD_BCRYPT, ['cost'=>12]);")
elif python3 -c "import bcrypt" 2>/dev/null; then
  HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'$NEWPW', bcrypt.gensalt(12)).decode())")
elif command -v htpasswd >/dev/null 2>&1; then
  HASH=$(htpasswd -bnBC 12 "" "$NEWPW" | cut -d: -f2)
else
  echo "需要 php / python3-bcrypt / htpasswd 其中之一来生成哈希"
  exit 1
fi

docker compose exec postgres psql -U emby -d emby \
  -c "UPDATE users SET hash='$HASH' WHERE name='admin';"
docker compose exec postgres psql -U emby -d emby \
  -c "DELETE FROM tokens WHERE user_id=(SELECT id FROM users WHERE name='admin');"
echo "管理员密码已重置，请用新密码登录"
