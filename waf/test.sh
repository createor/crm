#!/bin/bash
# @Desc: waf功能测试脚本
# @Time: 2024/05/09

# 测试地址
TestUrl="https://172.17.0.4"
# 白名单url
WhiteUrl="/crm/api/v1/user"
# 黑名单url
BlackUrl="/.svn"
# 非法header
IllegalHeader="X-Scan-Memo"
# 非法参数
IllegalArgs="/test.php?id=../etc/passwd"
# 非法ua
IllegalUA="HTTrack"
# 非法cookie
IllegalCookie="select * from user"

# 测试白名单地址,放行
echo "测试白名单地址"
if [ $(curl -o /dev/null -s -w "%{http_code}" -k -L ${TestUrl}${WhiteUrl}) -eq 200 ]; then
    echo "  结果:测试通过"
else
    echo "  结果:测试失败"
fi
# 测试黑名单地址,拦截
echo "测试黑名单地址"
if [ $(curl -o /dev/null -s -w "%{http_code}" -k -L ${TestUrl}${BlackUrl}) -eq 403 ]; then
    echo "  结果:测试通过"
else
    echo "  结果:测试失败"
fi
# 测试非法header,拦截
echo "测试非法header"
if [ $(curl -o /dev/null -s -w "%{http_code}" -k -L -H "${IllegalHeader}: test" ${TestUrl}${WhiteUrl}) -eq 403 ]; then
    echo "  结果:测试通过"
else
    echo "  结果:测试失败"
fi
# 测试非法参数,拦截
echo "测试非法参数"
if [ $(curl -o /dev/null -s -w "%{http_code}" -k -L ${TestUrl}${IllegalArgs}) -eq 403 ]; then
    echo "  结果:测试通过"
else
    echo "  结果:测试失败"
fi
# 测试非法user-agent,拦截
echo "测试非法user-agent"
if [ $(curl -o /dev/null -s -w "%{http_code}" -k -L -H "User-Agent: ${IllegalUA}" ${TestUrl}${WhiteUrl}) -eq 403 ]; then
    echo "  结果:测试通过"
else
    echo "  结果:测试失败"
fi
# 测试非法cookie,拦截
echo "测试非法cookie"
if [ $(curl -o /dev/null -s -w "%{http_code}" -k -L -H "Cookie: ${IllegalCookie}" ${TestUrl}${WhiteUrl}) -eq 403 ]; then
    echo "  结果:测试通过"
else
    echo "  结果:测试失败"
fi
