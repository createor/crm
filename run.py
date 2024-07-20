#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  run.py
@Time    :  2024/04/18 19:00:21
@Version :  1.0
@Desc    :  入口函数
'''
from app import app, SERVER_HOST, SERVER_PORT


if __name__ == "__main__":
    app.run(port=int(SERVER_PORT), host=SERVER_HOST, debug=False)  # 运行项目
