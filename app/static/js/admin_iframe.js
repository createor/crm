// admin_iframe.js
// iframe调用父页面方法

// 白名单IP
var showWhiteIp = function () {
    // 新建白名单
    layer.open({
        type: 1,
        area: ['500px', '300px'],
        title: "白名单IP",
        shade: 0.6,
        shadeClose: true,
        maxmin: false,
        anim: 0,
        content: `<div>
                    <table class="layui-hide" id="myWhiteIp" lay-filter="myWhiteIp"></table>
                  </div>`,
        success: function () {
            table.render({
                elem: "#myWhiteIp",
                url: "",
                cols: [[
                    { field: "id", title:"ID", hide: true },
                    { field: "ip", title:"IP", width:100 },
                    { field: "desc", title: "备注" }
                ]]
            });
        }
    });
}

// 新建用户
var addNewUser = function () {
    layer.open({
        type: 1,
        title: "新建用户",
        area: ["500px", "400px"],
        anim: 0,
        content: `<div style="width:300px;padding-top:10px;">
                    <form class="layui-form" lay-filter="editUser">
                        <div class="layui-form-item">
                            <label class="layui-form-label">用户名</label>
                            <div class="layui-input-block">
                                <input type="text" name="username" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">昵称</label>
                            <div class="layui-input-block">
                                <input type="text" name="name" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">类型</label>
                            <div class="layui-input-block">
                                <div class="layui-inline">
                                    <input type="radio" name="type" value="1" title="永久用户" checked>
                                    <input type="radio" name="type" value="2" title="临时用户">
                                </div>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">所属组织</label>
                            <div class="layui-input-block">
                                <input type="text" name="company" class="layui-input" autocomplete="off">
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
            form.render();
        }
    })
}

// 编辑用户
var showUserEdit = function (userData) {
    layer.open({
        type: 1,
        title: "编辑",
        area: ["500px", "300px"],
        anim: 0,
        content: `<div style="width:300px;padding-top:10px;">
                    <form class="layui-form" lay-filter="editUser">
                        <div class="layui-form-item">
                            <label class="layui-form-label">用户名</label>
                            <div class="layui-input-block">
                                <input type="text" name="username" class="layui-input" autocomplete="off" readonly>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">昵称</label>
                            <div class="layui-input-block">
                                <input type="text" name="name" class="layui-input" autocomplete="off">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">类型</label>
                            <div class="layui-input-block">
                                <input type="text" name="type" class="layui-input" autocomplete="off" readonly>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label">所属组织</label>
                            <div class="layui-input-block">
                                <input type="text" name="company" class="layui-input" autocomplete="off" readonly>
                            </div>
                        </div>
                    </form>
                  </div>`,
        success: function () {
            form.render();
            form.val("editUser", userData)
        }
    });
}

// 删除用户
var showUserDel = function (userId) {
    layer.confirm("是否删除用户?", {
        title: "删除",
        btn: ["确定", "取消"],
        function () {
            // 删除用户
            $.ajax({
                url: "",
                type: "post",
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
var showUserLock = function (userId) {
    layer.confirm("是否锁定用户?", {
        title: "锁定",
        btn: ["确定", "取消"],
        function () {
            // 解锁用户
            $.ajax({
                url: "",
                type: "post"
            });
        },
        function () {
            layer.closeAll();
        }
    });  //弹窗确认
}

// 解锁用户
var showUserUnlock = function (userId) {
    layer.confirm("是否解锁用户?", {
        title: "解锁",
        btn: ["确定", "取消"],
        function () {
            // 解锁用户
            $.ajax({
                url: "",
                type: "post"
            });
        },
        function () {
            layer.closeAll();
        }
    });  // 弹窗确认
}

// 重置密码
var showUserReset = function (userId) {
    layer.confirm("是否重置密码?", {
        title: "重置密码",
        btn: ["确定", "取消"],
        function () {
            // 解锁用户
            $.ajax({
                url: "",
                type: "post"
            });
        },
        function () {
            layer.closeAll();
        }
    });  // 弹窗确认
}
