require("config")                 -- 引入配置文件
local ngxmatch = ngx.re.find      -- nginx的正则匹配模块
local unescape = ngx.unescape_uri -- 获取解码后的url
-- 字符串转换布尔类型: on-true,off-false
local optionIsOn = function(options) return options == "on" and true or false end
local rulepath = RulePath
local urldeny = optionIsOn(UrlDeny)
local allowredirect = optionIsOn(Redirect)
local cookiecheck = optionIsOn(CookieMatch)
local whitecheck = optionIsOn(WhiteModule)

-- 读取规则
function ReadRule(var) -->规则文件名称var
    local file = io.open(rulepath .. "/" .. var, "r")
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

local urlrules = ReadRule("url")
local argsrules = ReadRule("args")
local uarules = ReadRule("user-agent")
local wturlrules = ReadRule("whiteurl")
local ckrules = ReadRule("cookie")

-- 返回警告信息
function SayHtml()
    if allowredirect then
        ngx.header.content_type = "text/html" -- 设置响应头
        ngx.status = ngx.HTTP_FORBIDDEN       -- 状态码: 403
        ngx.say(AlarmHtml)
        ngx.exit(ngx.status)
    end
end

-- 过滤白名单url
function WhiteUrl()
    if whitecheck then
        if wturlrules ~= nil then
            for _, rule in pairs(wturlrules) do
                if ngxmatch(ngx.var.uri, rule, "isjo") then
                    return true
                end
            end
        end
    end
    return false
end

-- 请求的url参数判断
function Args()
    local args = ngx.req.get_uri_args()
    for _, rule in pairs(argsrules) do
        for _, val in pairs(args) do
            local data
            if type(val) == "table" then
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

-- 黑名单url判断
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

-- 请求的header的user-agent字段判断
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

-- 请求的cookie判断
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
