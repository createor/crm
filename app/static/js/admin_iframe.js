// admin_iframe.js
// iframe调用父页面方法

// crm_user module
//
var addNewWhiteIp = function () {
    layer.open({
        type: 1,
        title: '添加白名单IP',
        shadeClose: true,
        shade: 0.8,
        area: ['300px', '220px'],
        content: `<div class="layui-form" style="padding: 10px 0 0 0;">
                    <div class="layui-form-item">
                        <label class="layui-form-label" style="width: 40px;">IP</label>
                        <div class="layui-input-inline">
                            <input type="text" name="ip" lay-verify="required|isAddress" maxlength="15" autocomplete="off" placeholder="请输入IP" class="layui-input">
                        </div>
                    </div>
                    <div class="layui-form-item">
                        <label class="layui-form-label" style="width: 40px;">备注</label>
                        <div class="layui-input-inline">
                            <input type="text" name="remark" maxlength="20" autocomplete="off" placeholder="请输入备注" class="layui-input">
                        </div>
                    </div>
                    <div class="layui-form-item">
                        <button class="layui-btn" lay-submit lay-filter="add" style="margin-left: 120px;">添加</button>
                    </div>
                  </div>`,
        success: function () {
            form.verify({
                isAddress: function(value) {
                    if (!value) return;
                    // 使用正则校验是否是IP
                    if (!/^(([1-9]|([1-9]\d)|(1\d\d)|(2([0-4]\d|5[0-5])))\.)(([1-9]|([1-9]\d)|(1\d\d)|(2([0-4]\d|5[0-5])))\.){2}([1-9]|([1-9]\d)|(1\d\d)|(2([0-4]\d|5[0-5])))$/.test(value)) {
                        return '请输入正确的IP地址';
                    }
                }
            })
            form.render();
            form.on("submit(add)", function (data) {
                let field = data.field;
                $.ajax({
                    url: "/crm/api/v1/system/add_white_list",
                    type: "post",
                    contentType: "application/json",
                    data: JSON.stringify(field),
                    success: function (res) {
                    }
                });
                return false;
            });
        }
    });
}

// 删除白名单IP
var delWhiteIp = function (id) {
    layer.confirm("确定删除该IP吗?", {
        btn: ["确定", "取消"]
    }, function () {
        $.ajax({
            url: "/crm/api/v1/system/del_white_list",
            type: "post",
            contentType: "application/json",
            data: JSON.stringify({
                id: id
            }),
            success: function (res) {
                layer.msg("删除成功", { icon: 1 });
                return false;
            }
        });
    });
}

// 白名单IP
var showWhiteIp = function () {
    // 新建白名单
    layer.open({
        type: 1,
        area: ['500px', '310px'],
        title: "白名单IP",
        shade: 0.6,
        shadeClose: true,
        maxmin: false,
        anim: 0,
        content: `<div>
                    <div style="margin: 5px 0 5px 10px;">
                        <input name="ip" placeholder="搜索IP" autocomplete="off" type="text" class="layui-input" style="width: 250px;">
                        <div class="layui-input-split layui-input-suffix" style="cursor: pointer;height: 38px;left: 259px;top: 5px;">
                            <i class="layui-icon layui-icon-search" style="line-height: 40px;"></i>
                        </div>
                        <button type="button" class="layui-btn layui-btn-sm layui-btn-normal" style="position: absolute; top: 10px; right: 30px;" onclick="addNewWhiteIp()">新增IP</button>
                    </div>
                    <table class="layui-hide" id="myWhiteIp" lay-filter="myWhiteIp"></table>
                  </div>`,
        success: function () {
            table.render({
                elem: "#myWhiteIp",
                url: "/crm/api/v1/system/get_white_list",
                height: "200",
                page: true,
                limit: 3,
                limits: [3],
                parseData: function (res) {
                    return {
                        "code": res.code,
                        "msg": res.code === 0 ? "" : res.message,
                        "count": res.message.count,
                        "data": res.message.data
                    }
                },
                cols: [[
                    { field: "id", title:"ID", hide: true },
                    { field: "ip", title:"IP", width: 200 },
                    { field: "desc", title: "备注" },
                    { field: "operate", title: "操作", templet: function(d) {
                        return `<button type="button" class="layui-btn layui-btn-sm layui-btn-danger" onclick="delWhiteIp(${d.id})">删除</button>`;
                    } }
                ]]
            });
        }
    });
}

/**
 * @description 新建用户
 */
var addNewUser = function () {
    layer.open({
        type: 1,
        title: "新建用户",
        area: ["500px", "400px"],
        shade: 0.6,
        shadeClose: false,
        maxmin: false,
        anim: 0,
        content: `<div style="width: 300px;padding-top: 10px;">
                    <form class="layui-form" lay-filter="editUser">
                        <div class="layui-form-item">
                            <label class="layui-form-label">用户名</label>
                            <div class="layui-input-block">
                                <input type="text" name="username" lay-verify="required|isEnglish" placeholder="请输入用户名" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">昵称</label>
                            <div class="layui-input-block">
                                <input type="text" name="name" placeholder="请输入昵称" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">类型</label>
                            <div class="layui-input-block">
                                <div class="layui-inline">
                                    <input type="radio" name="type" value="1" title="永久用户" lay-filter="type" checked>
                                    <input type="radio" name="type" value="2" title="临时用户" lay-filter="type">
                                    <!-- 临时用户日期选择 -->
                                    <div style="width: 210px;position: absolute;margin: -33px 0px 0px 100px;display: none;" id="showExpire">
                                        <label class="layui-form-label" style="width: 60px;">到期时间:</label>
                                        <input type="text" class="layui-input" id="expire-time" placeholder="yyyy-MM-dd" style="width: 120px;">
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">所属组织</label>
                            <div class="layui-input-block">
                                <input type="text" name="company" placeholder="请输入组织/公司名称" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item" style="margin-left: 140px; margin-top: 40px;">
                            <div class="layui-btn-container" style="width:200px;">
                                <button type="button" class="layui-btn" style="margin-right: 50px;" lay-submit lay-filter="create">创建</button>
                                <button type="button" class="layui-btn layui-btn-primary layui-border" lay-submit lay-filter="cancel">取消</button>
                            </div>
                        </div>
                    </form>
                  </div>`,
        success: function() {
            form.verify({
                // 校验用户名是否是英文字符
                isEnglish: function(value) {
                    if (!value) return;
                    if (!/^[a-zA-Z]+$/.test(value)) {
                        return "用户名只能包含英文字符";
                    }
                }
            });
            form.render();  // 渲染表格
            // 日期渲染
            laydate.render({
                elem: "#expire-time",
                disabledDate: function(date){
                    return date.getTime() < Date.now();
                }
            });
            form.on("radio(type)", function(data){
                if (data.value === "2") {
                    $("#showExpire").show();
                } else {
                    $("#showExpire").hide();
                }
                return false;
            });
            form.on("submit(create)", function(data) {
                let field = data.field;
                $.ajax({
                    url: "/crm/api/v1/user/add",
                    type: "post",
                    contentType: "application/json",
                    data: JSON.stringify(field),
                    success: function(data) {
                        if (data.code === 0) {
                            layer.closeAll();
                            layer.msg("创建成功", {icon: 1});
                            // 重载用户表格
                            table.reload("user");
                            return false;
                        } else {
                            layer.msg(data.message, {icon: 2});
                            return false;
                       }
                    },
                    error: function(err) {
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(errMsg.message, {icon: 2});
                        return false;
                    }
                });
                return false;
            });
            form.on("submit(cancel)", function() {
                layer.closeAll();
                return false;
            });
        }
    })
}

/**
 * @description 编辑用户
 * @param {object} userData 用户数据
 */
var showUserEdit = function (userData) {
    layer.open({
        type: 1,
        title: "编辑",
        area: ["500px", "300px"],
        shade: 0.6,
        shadeClose: false,
        maxmin: false,
        anim: 0,
        content: `<div style="width:300px;padding-top:10px;">
                    <form class="layui-form" lay-filter="editUser">
                        <div class="layui-form-item">
                            <label class="layui-form-label">昵称</label>
                            <div class="layui-input-block">
                                <input type="text" name="name" placeholder="请输入昵称" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">类型</label>
                            <div class="layui-input-block">
                                <input type="text" name="type" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">所属组织</label>
                            <div class="layui-input-block">
                                <input type="text" name="company" placeholder="请输入组织/公司名称" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <button class="layui-btn" lay-submit lay-filter="update">更新信息</button>
                        </div>
                    </form>
                  </div>`,
        success: function () {
            form.render();
            form.val("editUser", userData);  // 表单赋值
            form.on("submit(update)",function (data) {
                $.ajax({
                    url: "",
                    type: "post",
                    contentType: "application/json",
                    data: JSON.stringify(data.field),
                    success: function (data) {
                        if (data.code === 0) {
                            layer.closeAll();
                            layer.msg("更新成功", {icon: 1});
                            // 重载用户表格
                            table.reload("user");
                            return false;
                        } else {
                        }
                    }
                });
            });
        }
    });
}

// 删除用户
var showUserDel = function (userId, username) {
    layer.confirm("是否删除用户?", {
        title: "删除",
        btn: ["确定", "取消"],
        function () {
            // 删除用户
            $.ajax({
                url: "/crm/api/v1/user/",
                type: "post",
                data: JSON.stringify({
                    "uid": userId,
                    "username": username
                }),
                success: function (data) { }
            });
        },
        function () {
            // 关闭窗口
            layer.closeAll();
        }
    });  // 弹窗确认
}

// 锁定用户
var showUserLock = function (userId, username) {
    layer.confirm("是否锁定用户?", {
        title: "锁定",
        btn: ["确定", "取消"],
        function () {
            // 解锁用户
            $.ajax({
                url: "/crm/api/v1/user/lock",
                type: "post",
                data: JSON.stringify({
                    "uid": userId,
                    "username": username
                }),
                success: function (data) {
                    if (data.code === 0) {
                        layer.msg("已锁定", {icon: 1});
                    } else {
                        layer.msg("锁定失败:" + data.message, {icon: 2});
                    }
                    return false;
                },
                error: function () {
                    return false;
                }
            });
        },
        function () {
            layer.closeAll();
        }
    });  //弹窗确认
}

// 解锁用户
var showUserUnlock = function (userId, username) {
    layer.confirm("是否解锁用户?", {
        title: "解锁",
        btn: ["确定", "取消"],
        function () {
            // 解锁用户
            $.ajax({
                url: "/crm/api/user/unlock",
                type: "post",
                data: JSON.stringify({
                    "uid": userId,
                    "username": username
                }),
                success: function (data) {

                },
                error: function () {}
            });
        },
        function () {
            layer.closeAll();
        }
    });  // 弹窗确认
}

/**
 * @description 重置密码
 * @param {*} userId 
 */
var showUserReset = function (data) {
    layer.confirm("是否重置密码?", {
        title: "重置密码",
        btn: ["确定", "取消"],
        function () {
            // 解锁用户
            $.ajax({
                url: "/crm/api/v1/user/reset",
                type: "post",
                data: JSON.stringify({
                    "uid": data.id,
                    "username": data.username
                }),
                success: function (data) {},
                error: function () {}
            });
        },
        function () {
            layer.closeAll();
        }
    });  // 弹窗确认
}
