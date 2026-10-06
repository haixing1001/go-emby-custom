#!/usr/bin/env python3
"""对官方 go-emby 二进制做等长原位补丁。

基线：ghcr.io/sd87671067/go-emby:2026.10.06-051710, linux/amd64
（16,404,606 字节；未来官方更新后需重新核对地址）

补丁：
 1. 后台管理默认进入「控制台」（admin() 结尾 mediaPage() -> adminSection(12)，33 字节）
 2. 管理员密码下限 12 -> 3 字节（6 处 cmp $0xc -> cmp $0x3，单字节）
 3. 错误提示文案同步（管理员密码需要 12–72 字节 -> 3–72 字节，36 字节等长）

用法：python3 patch.py /path/to/go-emby
所有补丁均为等长替换，不改变文件大小与 ELF 布局。
"""
import sys

# (fileoff, old, new, desc) —— 全部按地址精确定位
ADDR_PATCHES = [
    (0x406a46, b"\x48\x83\xfb\x0c", b"\x48\x83\xfb\x03", "init/bootstrap"),
    (0x410ba8, b"\x48\x83\xfe\x0c", b"\x48\x83\xfe\x03", "password"),
    (0x412c10, b"\x83\xfa\x0c",     b"\x83\xfa\x03",     "admin#1"),
    (0x4132cc, b"\x48\x83\xfe\x0c", b"\x48\x83\xfe\x03", "admin#2"),
    (0x4e6c86, b"\x48\x83\xf9\x0c", b"\x48\x83\xf9\x03", "userIdentity"),
    (0x4e8140, b"\x49\x83\xf8\x0c", b"\x49\x83\xf8\x03", "userManagement"),
]

CONSOLE_OLD = b"  mediaPage();\n  renderUsers();\n}"
CONSOLE_NEW = b"  adminSection(12);renderUsers()}"

MSG_OLD = "管理员密码需要 12–72 字节".encode()
MSG_NEW = "管理员密码需要 3–72 字节 ".encode()


def main(path):
    data = bytearray(open(path, "rb").read())
    orig_len = len(data)

    # 1. 控制台补丁（33 字节，整个二进制唯一出现）
    assert len(CONSOLE_OLD) == len(CONSOLE_NEW) == 33
    assert bytes(data).count(CONSOLE_OLD) == 1, "console target not unique"
    data[:] = bytes(data).replace(CONSOLE_OLD, CONSOLE_NEW)
    print("[ok] console-default")

    # 2. 密码下限补丁（按地址）
    for fo, old, new, desc in ADDR_PATCHES:
        assert data[fo:fo + len(old)] == old, f"mismatch at {hex(fo)} {desc}"
        data[fo:fo + len(old)] = new
        print(f"[ok] {desc} at {hex(fo)}")

    # 3. 错误文案（36 字节等长）
    assert len(MSG_OLD) == len(MSG_NEW) == 36
    pos = bytes(data).find(MSG_OLD)
    assert pos > 0, "message not found"
    data[pos:pos + 36] = MSG_NEW
    print(f"[ok] error message at {hex(pos)}")

    assert len(data) == orig_len, "size changed!"
    open(path, "wb").write(bytes(data))
    print(f"done, size unchanged: {orig_len}")


if __name__ == "__main__":
    main(sys.argv[1])
