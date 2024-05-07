// crm_user module
layui.use(function(){
    const table = layer.table;
    const $ = layui.jquery;

    // 查询用户
    $.ajax({
        url: "",
        type: "get",
        async: false,
        success: function(data) {
            table.render();
        },
        error: function(data) {}
    });

    // 创建用户的弹层
    layer.

    // 创建用户
    $.ajax({
        url: "",
        type: "post",
        data: JSON.stringify(),
        async: false,
        success: function(data) {},
        error: function(data) {}
    });
});
