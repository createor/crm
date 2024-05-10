local content_length = tonumber(ngx.req.get_headers()['content-length'])
local method = ngx.req.get_method() -- 获取请求方法
local ngxmatch = ngx.re.find

if ngx.var.http_Acunetix_Aspect then
	ngx.exit(444)
end
if ngx.var.http_X_Scan_Memo then
	ngx.exit(444)
end
if WhiteUrl() and Ua() and Url() and Args() and Cookie() then
	if PostCheck then
		if method == "POST" then
			local boundary = GetBoundary()
			if boundary then
				local len = string.len
				local sock, _ = ngx.req.socket()
				if not sock then
					return
				end
				ngx.req.init_body(128 * 1024) -- 初始化body长度
				sock:settimeout(0)
				local chunk_size = 4096 -- 请求内容长度
				if content_length < chunk_size then
					chunk_size = content_length
				end
				local size = 0
				while size < content_length do
					local data, _, partial = sock:receive(chunk_size)
					data = data or partial
					if not data then
						return
					end
					ngx.req.append_body(data)
					if Body(data) then
						return true
					end
					size = size + len(data)
					local m = ngxmatch(data, [[Content-Disposition: form-data;(.+)filename="(.+)\\.(.*)"]], "ijo") -- 表单上传文件
					local filetranslate
					if m then
						FileExtCheck(m[3])
						filetranslate = true
					else
						if ngxmatch(data, "Content-Disposition:", "isjo") then
							filetranslate = false
						end
						if filetranslate == false then
							if Body(data) then
								return true
							end
						end
					end
					local less = content_length - size
					if less < chunk_size then
						chunk_size = less
					end
				end
				ngx.req.finish_body()
			else
				ngx.req.read_body()
				local args = ngx.req.get_post_args()
				if not args then
					return
				end
				for key, val in pairs(args) do
					local data
					if type(val) == "table" then
						if type(val[1]) == "boolean" then
							return
						end
						data = table.concat(val, ", ")
					else
						data = val
					end
					if data and type(data) ~= "boolean" and Body(data) then
						Body(key)
					end
				end
			end
		end
	end
else
	SayHtml()
end
