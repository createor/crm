#!/bin/bash
# @Desc: 生成自制ssl证书
# @Time: 2024/05/09

read -p "输入服务器IP: " DOMAIN

openssl genpkey -algorithm RSA -out server.key -aes256 -pkeyopt rsa_keygen_bits:4096

SUBJECT="/C=CN/ST=FuJian/L=XiaMen/O=nobody/OU=nobody/CN=$DOMAIN"

openssl req -new -subj $SUBJECT -key server.key -out server.csr -sha256

mv server.key server.origin.key
openssl rsa -in server.origin.key -out server.key

openssl x509 -req -days 3650 -in server.csr -signkey server.key -out server.crt -sha256 -extensions v3_req -extfile <(printf "[v3_req]\nkeyUsage=digitalSignature, keyEncipherment\nextendedKeyUsage=serverAuth\n")

