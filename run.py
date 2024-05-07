#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  run.py
@Time    :  2024/04/18 19:00:21
@Version :  1.0
@Desc    :  入口函数
'''
from app import app


if __name__ == '__main__':
    # 运行项目
    app.run(port=8080, host="127.0.0.1", debug=True)
