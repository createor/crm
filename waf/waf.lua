if ngx.var.http_Acunetix_Aspect then
	ngx.exit(403)
end

if ngx.var.http_X_Scan_Memo then
	ngx.exit(403)
end

if not (WhiteUrl() and Ua() and Url() and Args() and Cookie()) then
	SayHtml()
end
