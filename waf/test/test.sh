#!/bin/bash
# @Desc: waf功能测试脚本
# @Time: 2024/05/09

TestUrl="https://172.17.0.3"

BASE_DIR=$(cd $(dirname $0); pwd)  # 当前路径

# 正常访问白名单地址,放行
curl -v -k -L ${TestUrl}/crm/api/v1/user
# 测试参数,拦截
curl -v -k -L ${TestUrl}/test.php?id=../etc/passwd
# 测试上传文件,拦截
curl -v -k -X POST -L ${TestUrl}/crm/api/v1/user -F "file=@/root/crm/nginx/test/test.php" -H "Content-Disposition: form-data; filename=test.php"
