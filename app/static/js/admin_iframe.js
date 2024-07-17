// admin_iframe.js
// iframe调用父页面方法

// system模块
/**
 * @description 添加白名单IP 
*/
var addNewWhiteIp = () => {
    layer.open({
        type: 1,
        title: "添加白名单IP",
        area: ["300px", "220px"],
        shade: 0.8,
        shadeClose: false,
        move: false,
        resize: false,
        maxmin: false,
        content: `<div class="layui-form" style="padding: 10px 0 0 0;">
                    <div class="layui-form-item" lay-filter="addIpForm">
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
                        <button type="button" class="layui-btn" lay-submit lay-filter="add" style="margin-left: 120px;">添加</button>
                    </div>
                  </div>`,
        success: (_, index) => {
            form.verify({
                isAddress: (value) => {
                    if (!value) return;
                    // 使用正则校验是否是IP
                    if (!/^(([1-9]|([1-9]\d)|(1\d\d)|(2([0-4]\d|5[0-5])))\.)(([1-9]|([1-9]\d)|(1\d\d)|(2([0-4]\d|5[0-5])))\.){2}([1-9]|([1-9]\d)|(1\d\d)|(2([0-4]\d|5[0-5])))$/.test(value)) {
                        return '请输入正确的IP地址';
                    }
                }
            })
            form.render(null, "addIpForm");
            form.on("submit(add)", (data) => {
                let field = data.field;
                let loadIndex = "";
                $.ajax({
                    url: "/crm/api/v1/system/add_white_list",
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        ip: field.ip,
                        description: field.remark
                    }),
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index);
                            layer.msg("添加IP成功", { icon: 1 });
                        } else {
                            layer.msg(`添加IP失败: ${res.message}`, { icon: 2 });  
                        }
                        return false;
                    },
                    error: (err) => {
                        layer.close(loadIndex);
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(errMsg.message, { icon: 2 });
                        return false;
                    }
                });
                return false;
            });
        }
    });
}

/**
 * @description 删除白名单IP
 * @param {string} id id值
 * @param {string} ip ip值
*/
var delWhiteIp = (id, ip) => {
    layer.confirm("确定删除该IP吗?", {
        title: "删除IP",
        btn: ["确定", "取消"]
    }, (index) => {
        let loadIndex = "";
        $.ajax({
            url: "/crm/api/v1/system/delete_white_list",
            type: "POST",
            contentType: "application/json;charset=utf-8",
            data: JSON.stringify({
                id: id,
                ip: ip
            }),
            beforeSend: () => {
                loadIndex = layer.load(2);
            },
            success: (res) => {
                layer.close(loadIndex);
                if (res.code === 0) {
                    layer.close(index);
                    layer.msg("删除成功", { icon: 1 });
                    table.reloadData("myWhiteIp");
                } else {
                    layer.msg(`删除失败: ${res.message}`, { icon: 2 });
                }
                return false;
            },
            error: (err) => {
                layer.close(loadIndex);
                let errMsg = err.responseJSON || JSON.parse(err.responseText);
                layer.msg(errMsg.message, {icon: 2});
                return false;
            }
        });
    }, (index) => {
        layer.close(index);
        return false;
    });
}

/**
 * @description 查看白名单IP信息
*/
var showWhiteIp = () => {
    layer.open({
        type: 1,
        area: ["500px", "310px"],
        title: "白名单IP",
        shade: 0.6,
        shadeClose: false,
        maxmin: false,
        move: false,
        resize: false,
        content: `<div>
                    <div style="margin: 5px 0 5px 10px;">
                        <div class="layui-form" lay-filter="showIpForm">
                            <div class="layui-input-wrap" style="width: 250px;">
                                <input name="ip" placeholder="搜索IP" autocomplete="off" type="text" class="layui-input" style="width: 250px;" lay-filter="ip" lay-affix="search" lay-options="{split:true}">
                            </div>
                        </div>
                        <button type="button" class="layui-btn layui-btn-sm layui-btn-normal" style="position: absolute; top: 10px; right: 30px;" onclick="addNewWhiteIp()">新增IP</button>
                    </div>
                    <table class="layui-hide" id="myWhiteIp" lay-filter="myWhiteIp"></table>
                  </div>`,
        success: () => {
            table.render({
                elem: "#myWhiteIp",
                id: "myWhiteIp",
                url: "/crm/api/v1/system/get_white_list",
                height: "200",
                page: true,
                limit: 3,
                limits: [3],
                parseData: (res) => {
                    return {
                        "code": res.code,
                        "msg": res.code === 0 ? "" : res.message,
                        "count": res.message.total,
                        "data": res.message.data
                    }
                },
                cols: [[
                    { field: "id", title:"ID", hide: true },
                    { field: "ip", title:"IP", width: 200 },
                    { field: "desc", title: "备注" },
                    { field: "operate", title: "操作", templet: (d) => {
                        return `<button type="button" class="layui-btn layui-btn-sm layui-btn-danger" onclick="delWhiteIp('${d.id}', '${d.ip}')">删除</button>`;
                    } }
                ]]
            });
            form.render(null, "showIpForm");
            // 搜索事件
            form.on("input-affix(ip)", (data) => {
                let elem = data.elem;
                let value = elem.value; 
                table.reloadData("myWhiteIp", {
                    where: {
                        ip: value
                    }
                });
            });
        }
    });
}

// user模块
/**
 * @description 重载用户数据
*/
function reloadUserData () {
    let win = window.frames["crm_user"];
    win.contentWindow.reloadData();  // 调用iframe内方法
}

/**
 * @description 新建用户
*/
var addNewUser = () => {
    layer.open({
        type: 1,
        title: "新建用户",
        area: ["500px", "400px"],
        shade: 0.6,
        shadeClose: false,
        maxmin: false,
        move: false,
        resize: false,
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
                            <div class="layui-btn-container" style="width: 200px;">
                                <button type="button" class="layui-btn" style="margin-right: 50px;" lay-submit lay-filter="create">创建</button>
                                <button type="button" class="layui-btn layui-btn-primary layui-border" lay-submit lay-filter="cancel">取消</button>
                            </div>
                        </div>
                    </form>
                  </div>`,
        success: (_, index) => {
            form.verify({
                // 校验用户名是否是英文字符
                isEnglish: (value) => {
                    if (!value) return;
                    if (!/^[a-zA-Z]+$/.test(value)) {
                        return "用户名只能包含英文字符";
                    }
                }
            });
            form.render(null, "editUser");  // 渲染表格
            // 日期渲染
            laydate.render({
                elem: "#expire-time",
                max: 30,
                disabledDate: (date) => {
                    return date.getTime() < Date.now();
                }
            });
            form.on("radio(type)", (data) => {
                if (data.value === "2") {
                    $("#showExpire").show();
                } else {
                    $("#showExpire").hide();
                }
                return false;
            });
            // 创建用户事件
            form.on("submit(create)", (data) => {
                let field = data.field;
                let loadIndex = "";
                if (field.type === "2" && !$("#expire-time").val()) {
                    layer.msg("请选择到期时间", {icon: 2});
                    return false;
                }
                $.ajax({
                    url: "/crm/api/v1/user/add",
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        username: field.username,
                        name: field.name,
                        type: field.type,
                        company: field.company,
                        expire_time: field.type === "2" ? $("#expire-time").val() : ""
                    }),
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index);
                            layer.msg("创建成功", { icon: 1 });
                            reloadUserData();  // 重载用户表格
                        } else {
                            layer.msg(`创建失败: ${res.message}`, { icon: 2 });
                       }
                       return false;
                    },
                    error: (err) => {
                        layer.close(loadIndex);
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(errMsg.message, { icon: 2 });
                        return false;
                    }
                });
                return false;
            });
            form.on("submit(cancel)", () => {
                layer.close(index);
                return false;
            });
        }
    })
}

/**
 * @description 编辑用户
 * @param {object} userData 用户数据
 */
var showUserEdit = (userData) => {
    layer.open({
        type: 1,
        title: "编辑",
        area: ["500px", "320px"],
        shade: 0.6,
        shadeClose: false,
        maxmin: false,
        move: false,
        resize: false,
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
                                <input type="radio" name="type" value="1" title="永久用户" lay-filter="type">
                                <input type="radio" name="type" value="2" title="临时用户" lay-filter="type">
                                <div style="width: 210px;position: absolute;margin: -33px 0px 0px 100px;display: none;" id="showExpire">
                                    <label class="layui-form-label" style="width: 60px;">到期时间:</label>
                                    <input type="text" class="layui-input" id="expire-time" name="expire" placeholder="yyyy-MM-dd" style="width: 120px;">
                                </div>                            
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">所属组织</label>
                            <div class="layui-input-block">
                                <input type="text" name="company" placeholder="请输入组织/公司名称" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <button class="layui-btn" lay-submit lay-filter="update" style="margin-top: 10px;margin-left: 200px;">更新信息</button>
                        </div>
                    </form>
                  </div>`,
        success: (_, index) => {
            form.render(null, "editUser");
            laydate.render({
                elem: "#expire-time",
                max: 30,
                disabledDate: (date) => {
                    return date.getTime() < Date.now();
                }
            });
            form.val("editUser", userData);  // 表单赋值
            if ($("input[name=type]:checked").val() === "2") {
                $("#showExpire").show();
            }
            form.on("radio(type)", (data) => {
                if (data.value === "2") {
                    $("#showExpire").show();
                } else {
                    $("#showExpire").hide();
                }
                return false;
            });
            form.on("submit(update)", (data) => {
                let field = data.field;
                let loadIndex = "";
                $.ajax({
                    url: "/crm/api/v1/user/edit",
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        uid: userData.id,
                        username: userData.username,
                        name: field.name,
                        type: field.type,
                        company: field.company,
                        expire_time: field.type === "2" ? $("#expire-time").val() : ""
                    }),
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index);
                            layer.msg("更新成功", { icon: 1 });
                            reloadUserData();  // 重载用户表格
                        } else {
                            layer.msg(`更新失败: ${res.message}`, {icon: 2});
                        }
                        return false;
                    },
                    error: (err) => {
                        layer.close(loadIndex);
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(errMsg.message, { icon: 2 });
                        return false;
                    }
                });
                return false;
            });
        }
    });
}

/**
 * @description 删除用户
 * @param {object} data 用户数据
*/
var showUserDel = (data) => {
    layer.confirm("是否删除用户?", {
            title: "删除用户",
            btn: ["确定", "取消"]
        }, (index) => {
            // 删除用户
            let loadIndex = "";
            $.ajax({
                url: "/crm/api/v1/user/del",
                type: "POST",
                contentType: "application/json;charset=utf-8",
                data: JSON.stringify({
                    "uid": data.id,
                    "username": data.username
                }),
                beforeSend: () => {
                    loadIndex = layer.load(2);
                },
                success: (res) => {
                    layer.close(loadIndex);
                    if (res.code === 0) {
                        layer.close(index);
                        layer.msg("删除成功", {icon: 1});
                        reloadUserData();
                    } else {
                        layer.msg(`删除失败: ${res.message}`, {icon: 2});
                    }
                    return false;
                },
                error: (err) => {
                    layer.close(loadIndex);
                    let errMsg = err.responseJSON || JSON.parse(err.responseText);
                    layer.msg(errMsg.message, { icon: 2 });
                    return false;
                }
            });
        },
        (index) => {
            layer.close(index);  // 关闭窗口
            return false;
        }
    );
}

/**
 * @description 锁定用户
 * @param {object} data 用户数据
*/
var showUserLock = (data) => {
    layer.confirm("是否锁定用户?", {
            title: "锁定用户",
            btn: ["确定", "取消"]
        }, (index) => {
            // 锁定用户
            let loadIndex = "";
            $.ajax({
                url: "/crm/api/v1/user/lock",
                type: "POST",
                contentType: "application/json;charset=utf-8",
                data: JSON.stringify({
                    "uid": data.id,
                    "username": data.username
                }),
                beforeSend: () => {
                    loadIndex = layer.load();
                },
                success: (res) => {
                    layer.close(loadIndex);
                    if (res.code === 0) {
                        layer.close(index);
                        layer.msg("已锁定", {icon: 1});
                        reloadUserData();
                    } else {
                        layer.msg("锁定失败: " + res.message, {icon: 2});
                    }
                    return false;
                },
                error: function (err) {
                    layer.close(loadIndex);
                    let errMsg = err.responseJSON || JSON.parse(err.responseText);
                    layer.msg(errMsg.message, {icon: 2});
                    return false;
                }
            });
        },
        (index) => {
            layer.close(index);
        }
    );
}

/**
 * @description 解锁用户
 * @param {object} data 用户数据
*/
var showUserUnlock = (data) => {
    layer.confirm("是否解锁用户?", {
            title: "解锁用户",
            btn: ["确定", "取消"]
        }, (index) => {
            // 解锁用户
            let loadIndex = "";
            $.ajax({
                url: "/crm/api/v1/user/unlock",
                type: "POST",
                contentType: "application/json;charset=utf-8",
                data: JSON.stringify({
                    "uid": data.id,
                    "username": data.username
                }),
                beforeSend: () => {
                    loadIndex = layer.load(2);
                },
                success: (res) => {
                    layer.close(loadIndex);
                    if (res.code === 0) {
                        layer.close(index);
                        layer.msg("解锁成功", {icon: 1});
                        reloadUserData();
                    } else {
                        layer.msg(`解锁失败: ${res.message}`, {icon: 2});
                    }
                    return false;
                },
                error: (err) => {
                    layer.close(loadIndex);
                    let errMsg = err.responseJSON || JSON.parse(err.responseText);
                    layer.msg(errMsg.message, {icon: 2});
                    return false;
                }
            });
        },
        (index) => {
            layer.close(index);
            return false;
        }
    );
}

/**
 * @description 重置密码
 * @param {object} data 用户数据 
*/
var showUserReset = (data) => {
    layer.confirm("是否重置密码?", {
            title: "重置密码",
            btn: ["确定", "取消"]
        }, (index) => {
            // 重置用户密码
            let loadIndex = "";
            $.ajax({
                url: "/crm/api/v1/user/reset",
                type: "POST",
                contentType: "application/json;charset=utf-8",
                data: JSON.stringify({
                    "uid": data.id,
                    "username": data.username
                }),
                beforeSend: () => {
                    loadIndex = layer.load(2);
                },
                success: (res) => {
                    layer.close(loadIndex);
                    if (res.code === 0) {
                        layer.close(index);
                        layer.msg("重置成功", { icon: 1 });
                    } else {
                        layer.msg(`重置失败: ${res.message}`, { icon: 2 });
                    }
                    return false;
                },
                error: (err) => {
                    layer.close(loadIndex);
                    let errMsg = err.responseJSON || JSON.parse(err.responseText);
                    layer.msg(errMsg.message, { icon: 2 });
                    return false;
                }
            });
        },
        (index) => {
            layer.close(index);
            return false;
        }
    );
}
