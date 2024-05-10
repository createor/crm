require("config")                       -- 引入配置
local match = string.match
local ngxmatch = ngx.re.find            -- nginx的正则匹配模块
local unescape = ngx.unescape_uri       -- 获取解码后的url
local get_headers = ngx.req.get_headers -- 获取请求header
-- 转换:on-true,off-false
local optionIsOn = function(options) return options == "on" and true or false end
local rulepath = RulePath
local urldeny = optionIsOn(UrlDeny)
local cookiecheck = optionIsOn(CookieMatch)
local whitecheck = optionIsOn(WhiteModule)
PostCheck = optionIsOn(PostMatch)

-- 读取规则
function ReadRule(var)
    -- :param var: 规则文件名称
    local file = io.open(rulepath .. '/' .. var, "r")
    if file == nil then
        return
    end
    local t = {}
    for line in file:lines() do
        table.insert(t, line)
    end
    file:close()
    return (t)
end

local urlrules = ReadRule('url')
local argsrules = ReadRule('args')
local uarules = ReadRule('user-agent')
local wturlrules = ReadRule('whiteurl')
local postrules = ReadRule('post')
local ckrules = ReadRule('cookie')

-- 返回警告信息
function SayHtml()
    if Redirect then
        ngx.header.content_type = "text/html"
        ngx.status = ngx.HTTP_FORBIDDEN -- 403
        ngx.say(AlarmHtml)
        ngx.exit(ngx.status)
    end
end

-- 过滤白名单url
function WhiteUrl()
    if whitecheck then
        if wturlrules ~= nil then
            for _, rule in pairs(wturlrules) do
                -- ngx.var.uri,不带参数的uri
                if ngxmatch(ngx.var.uri, rule, "isjo") then -- 正则匹配,表示忽略大小写
                    return true
                end
            end
        end
    end
    return false
end

-- 文件后缀判断
function FileExtCheck(ext)
    -- :param ext: 文件后缀
    local items = Set(BlackFileExt)
    ext = string.lower(ext) -- 小写
    if ext then
        for rule in pairs(items) do
            if ngxmatch(ext, rule, "isjo") then
                return false
            end
        end
    end
    return true
end

-- 转换为table
-- 把{"xx","xx"} -> {"xx":true}
function Set(list)
    local set = {}
    for _, l in ipairs(list) do set[l] = true end
    return set
end

-- 参数判断
function Args()
    for _, rule in pairs(argsrules) do
        local args = ngx.req.get_uri_args() -- 获取url的参数
        local data
        for _, val in pairs(args) do
            if type(val) == 'table' then
                local t = {}
                for _, v in pairs(val) do
                    if v == true then
                        v = ""
                    end
                    table.insert(t, v)
                end
                data = table.concat(t, " ")
            else
                data = val
            end
            if data and type(data) ~= "boolean" and rule ~= "" and ngxmatch(unescape(data), rule, "isjo") then
                return false
            end
        end
    end
    return true
end

-- url判断
function Url()
    if urldeny then
        for _, rule in pairs(urlrules) do
            if rule ~= "" and ngxmatch(ngx.var.request_uri, rule, "isjo") then
                return false
            end
        end
    end
    return true
end

-- user-agent判断
function Ua()
    local ua = ngx.var.http_user_agent
    if ua ~= nil then
        for _, rule in pairs(uarules) do
            if rule ~= "" and ngxmatch(ua, rule, "isjo") then
                return false
            end
        end
    end
    return true
end

-- post的body判断
function Body(data)
    -- param data: 载荷
    for _, rule in pairs(postrules) do
        if rule ~= "" and data ~= "" and ngxmatch(unescape(data), rule, "isjo") then
            return false
        end
    end
    return true
end

-- cookie判断
function Cookie()
    local ck = ngx.var.http_cookie
    if cookiecheck and ck then
        for _, rule in pairs(ckrules) do
            if rule ~= "" and ngxmatch(ck, rule, "isjo") then
                return false
            end
        end
    end
    return true
end

-- 获取上传的二进制文件
function GetBoundary()
    local header = get_headers()["content-type"]
    if not header then
        return nil
    end

    if type(header) == "table" then
        header = header[1]
    end

    local m = match(header, ";%s*boundary=\"([^\"]+)\"")
    if m then
        return m
    end

    return match(header, ";%s*boundary=([^\",;]+)")
end
