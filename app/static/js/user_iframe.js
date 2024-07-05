// user_iframe.js
// iframe调用父页面的方法集合

/**
 * @description 绑定进度条步骤
 */
var renderStepProgress = function () {
    let stepItems = [
        {
            title: "开始",
            code: "01"
        },
        {
            title: "初始化",
            code: "02"
        },
        {
            title: "创建中",
            code: "03"
        },
        {
            title: "完成",
            code: "04"
        }
    ];
    stepprogress.render({
        elem: "#stepProgressBar",  // 绑定元素
        stepItems: stepItems,
        position: 0  // 起始位置0
    });
}

/**
 * @description 文本输入长度
 * @param {*} that 
 */
var checkLength = function (that) {
    $("#char-count").text(that.value.length);
}

/**
 * @description 新建资产表
 */
var addNewTable = function () {
    // 新建资产表 
    layer.open({
        type: 1,
        area: ["500px", "400px"],
        title: "新建资产表",
        shade: 0.6,
        shadeClose: false,
        move: false,
        resize: false,
        maxmin: false,
        content: `<div class="layui-container" style="width: 100%;height: 100%;padding-top: 10px;">
                    <div id="stepProgressBar"></div>
                    <div class="stepContent layui-form" style="padding-top: 10px;text-align: left;">
                        <div class="layui-form-item">
                            <div class="layui-inline">
                                <label class="layui-form-label" style="width: 100px;">表名(必填)</label>
                                <div class="layui-input-inline" style="width: 250px;">
                                    <input type="text" name="manageName" id="manageName" autocomplete="off" lay-verify="required" placeholder="请输入中文名称" class="layui-input">
                                </div>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <div class="layui-inline">
                                <label class="layui-form-label" style="width: 100px;">表别名(必填)</label>
                                <div class="layui-input-inline" style="width: 250px;">
                                    <input type="text" name="emanegName" id="emanegName" autocomplete="off" lay-verify="required|isEnglish" placeholder="仅支持英文组成" class="layui-input">  
                                </div>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 100px;">备注信息(选填)</label>
                            <div class="layui-input-inline" style="width: 250px;">
                                <textarea name="remark" id="remark" placeholder="请输入备注信息" maxlength="50" rows="3" class="layui-textarea" style="resize: none;min-height: 80px;" oninput="checkLength(this)"></textarea>
                                <div><span id="char-count">0</span>/50</div>
                            </div>
                        </div>
                    </div>
                    <div class="stepContent layui-form">
                        <div style="text-align: left; margin: 5px 45px;">
                            <input type="radio" name="mode" value="1" title="表格导入数据" checked>
                        </div>
                        <input type="hidden" name="filename" id="filename" value="">
                        <div class="layui-upload-drag" style="display: block;width: 50%;margin-left: 19%;padding-top: 15px;" id="uploadExcel">
                            <i class="layui-icon layui-icon-upload"></i> 
                            <div>点击上传，或将文件拖拽到此处</div>
                            <div class="layui-hide" id="upload-preview" style="padding: 15px 0 0 0;">
                                <span></span><i class="layui-icon layui-icon-success" style="color: #16baaa;font-size: 18px;margin-left: 5px;"></i>
                            </div>
                        </div>
                        <div style="text-align: left; margin: 5px 45px;">
                            <input type="radio" name="mode" value="2" title="立即创建">
                        </div>
                    </div>
                    <!-- 显示进度 -->
                    <div class="stepContent layui-form">
                       <div style="padding: 35px 0;margin-left: -10px;">
                            <i class="layui-icon layui-icon-loading layui-anim layui-anim-rotate layui-anim-loop" style="font-size: 100px;"></i>
                       </div>
                       <span style='margin-left: -10px;font-size: 18px;'>创建中</span>
                    </div>
                    <!-- 显示结果 -->
                    <div class="stepContent layui-form">
                    </div>
                    <div class="layui-btn-container" style="position: absolute;bottom: 15px;left:200px;">
                        <div style="text-align: center;margin-top: 10px;">
	                        <button type="button" id="pre" class="layui-btn layui-btn-sm" style="margin-top: 10px;margin-left: -20px;">上一步</button>
	                        <button type="button" id="next" class="layui-btn layui-btn-sm" style="margin: 0 20px;">下一步</button>
                            <button type="button" id="rightUse" class="layui-btn layui-btn-sm" style="display: none;">立即使用</button>
                        </div>
                    </div> 
                  </div>`,
        success: function () {
            let uploadFilename = "";  // 文件名
            let layerIndex = "";  // load的index
            // 文件上传
            upload.render({
                elem: "#uploadExcel",
                url: "/crm/api/v1/upload",
                accet: "file",
                acceptMime: "application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                exts: "xlsx|xls",
                choose: function (obj) {
                    obj.preview(function(_,file) {
                        uploadFilename = file.name;
                    });
                },
                before: function () {
                    layerIndex = layer.load();
                },
                done: function (res) {
                    layer.close(layerIndex);
                    if (res.code === 0) {
                        // 写入filename
                        $("input[name='filename']").val(res.message);
                        $("#upload-preview span").text(uploadFilename);
                        $("#upload-preview").removeClass("layui-hide");
                        layer.msg("上传成功", {icon: 1});
                    }
                }
            });
            form.verify({
                // 校验输入是否是英文
                isEnglish: function(value) {
                    if (!value) return;
                    if (!(/^[A-Za-z]+$/.test(value))) {
                        return "只能由英文组成";
                    }
                }
            });
            form.render();      // 渲染表格
            let currIndex = 0;  // 定义当前步骤
            $("#pre").hide();   // 隐藏上一步
            $(".stepContent").eq(0).show();  // 显示第一步
            renderStepProgress();  // 渲染步骤进度
            // 点击下一步触发函数
            $("#next").click(function(){
                if (currIndex === 0) {
                    let isEmpty = form.validate("#manageName");  // 验证是否为空
                    let isValid = form.validate("#emanegName");  // 验证是否是英文
                    if (!isEmpty) {
                        return false;
                    }
                    if (!isValid) {
                        return false;
                    }
                }
                if (currIndex === 1) {
                    let checkStatus = $("input[name='mode']:checked").val();
                    if (checkStatus === "1") {
                        if (!$("input[name='filename']").val()) {
                            layer.msg("请上传表格文件", {icon: 2});
                            return false;
                        }
                    }
                }
                currIndex += 1;
		        stepprogress.next('stepProgressBar');
	        });
            // 点击上一步触发函数
	        $("#pre").click(function(){
                currIndex -= 1;
		        stepprogress.pre('stepProgressBar');
	        });
            // 绑定进度变化事件
            stepprogress.on('change(stepProgressBar)', function (options) {
                if (options.position == 0) {
                    $(".stepContent").eq(0).show();
                    $(".stepContent").eq(1).hide();
                    $(".stepContent").eq(2).hide();
                    $(".stepContent").eq(3).hide();
                    $("#pre").hide();
                    $("#next").show();
                    return false;
                }
                if (options.position == 1) {
                    $(".stepContent").eq(0).hide();
                    $(".stepContent").eq(1).show();
                    $(".stepContent").eq(2).hide();
                    $(".stepContent").eq(3).hide();
                    $("#pre").show();
                    $("#next").show();
                    return false;
                }
                if (options.position == 2) {
                    $(".stepContent").eq(0).hide();
                    $(".stepContent").eq(1).hide();
                    $(".stepContent").eq(2).show();
                    $(".stepContent").eq(3).hide();
                    $("#pre").hide();
                    $("#next").hide();
                    $.ajax({
                        url: "/crm/api/v1/manage/add",
                        type: "post",
                        contentType: "application/json;charset=utf-8",
                        data: JSON.stringify({
                            "name": $("input[name='manageName']").val(),
                            "keyword": $("input[name='emanegName']").val(),
                            "filename": $("input[name='filename']").val() ? $("input[name='filename']").val() : "",
                            "desc": $("#remark").val(),
                        }),
                        success: function (data) {
                            if (data.code === 0) {
                                // 成功提示
                                $(".stepContent").eq(3).html("<div style='padding: 35px 0;margin-left: -10px;'> \
                                    <i class='layui-icon layui-icon-success' style='font-size: 100px;color: green;'></i> \
                                    </div> \
                                    <span style='margin-left: -10px;font-size: 20px;'>创建成功</span>");
                                $("#rightUse").show();  // 显示立即使用按钮
                            } else {
                                // 失败提示
                                $(".stepContent").eq(3).html("<div style='padding: 35px 0;margin-left: -10px;'> \
                                    <i class='layui-icon layui-icon-error' style='font-size: 100px;color: red;'></i> \
                                    </div> \
                                    <span style='margin-left: -10px;font-size: 20px;'>创建失败: " + data.message + "</span>");
                            }
                            stepprogress.next('stepProgressBar');
                            $(".stepContent").eq(2).hide();
                            $(".stepContent").eq(3).show();
                            return false;
                        },
                        error: function (err) {
                            let errMsg = err.responseJSON || JSON.parse(err,responseText);
                            $(".stepContent").eq(3).html("<div style='padding: 35px 0;margin-left: -10px;'> \
                                    <i class='layui-icon layui-icon-error' style='font-size: 100px;color: red;'></i> \
                                    </div> \
                                    <span style='margin-left: -10px;font-size: 20px;'>创建失败: " + errMsg.message + "</span>");
                            stepprogress.next('stepProgressBar');
                            $(".stepContent").eq(2).hide();
                            $(".stepContent").eq(3).show();
                            return false;
                        }
                    });
                    return false;
                }
            });
        }
    });
    return false;
}

/**
 * @description 获取图表配置
 * @param type 图表类型
 * @param title 图表标题
 * @param data 图表数据
 */ 
function getConfig (type, title, data) {
    // 默认配置
    let base_option = {
        title: { text: title },
        tooltip: { trigger: "axis" },
        legend: { data: data.legend },
        toolbox: { feature: { saveAsImage: {} } },  // 保存图片
        xAxis: {
            type: "category",
            boundaryGap: false,
            data: data.xAxis,
        },  // x轴
        yAxis: {
            type: "value",
        }, // y轴
        series: data.series
    };
    switch(type) {
        // 饼图
        case "1":
            option = {};
            break;
        // 折线图
        case "2":
            break;
        // 柱形图
        case "3":
            base_option.title.left = "center";
            base_option.tooltip.trigger = "item";
            break;
    }
    return base_option;
}

/**
 * @description 新增图表规则
 * @param {String} tableId 表uuid
 */
var addNewRule = function (tableId) {
    let id = tableId || localStorage.getItem("tableUid");
    let header = JSON.parse(localStorage.getItem("header"))[id];
    let option_template = "";
    header.forEach(item => {
        option_template += `<option value="${item.field}">${item.title}</option>`;
    });
    layer.open({
        type: 1,
        title: "自定义规则",
        area: ["500px", "400px"],
        content: `<div class="layui-tab" layui-tab-card lay-filter="ruleTab">
                    <ul class="layui-tab-title">
                        <li class="layui-this">规则1</li>
                        <li>规则2</li>
                        <li>规则3</li>
                    </ul>
                    <div class="layui-form">
                        <div class="layui-tab-content">
                            <div class="layui-tab-item layui-show">
                                <div class="layui-form-item">
                                    <div class="layui-input-inline echart_options" style="width:100%;">
                                        <fieldset class="layui-elem-field" style="width:180px;float:left;margin: 0 10px 0 10px;">
                                            <legend>选择图表类型</legend>
                                            <div class="layui-field-box">
                                                <select name=""rule_1_type>
                                                    <option value="">请选择</option>
                                                    <option value="1">柱形图</option>
                                                    <option value="2">折线图</option>
                                                    <option value="3">饼图</option>
                                                </select>
                                            </div>
                                        </fieldset>
                                        <fieldset class="layui-elem-field" style="width:180px;">
                                            <legend>选择数据来源</legend>
                                            <div class="layui-field-box">
                                                <select name="rule_1_value">
                                                    <option value="">请选择</option>
                                                    ${option_template}
                                                </select>
                                            </div>
                                        </fieldset>
                                    </div>
                                </div>
                            </div>
                            <div class="layui-tab-item">
                                <div class="layui-form-item">
                                    <div class="layui-input-inline echart_options" style="width:100%;">
                                        <fieldset class="layui-elem-field" style="width:180px;float:left;margin: 0 10px 0 10px;">
                                            <legend>选择图表类型</legend>
                                            <div class="layui-field-box">
                                                <select name=""rule_2_type>
                                                    <option value="">请选择</option>
                                                    <option value="1">柱形图</option>
                                                    <option value="2">折线图</option>
                                                    <option value="3">饼图</option>
                                                </select>
                                            </div>
                                        </fieldset>
                                        <fieldset class="layui-elem-field" style="width:180px;">
                                            <legend>选择数据来源</legend>
                                            <div class="layui-field-box">
                                                <select name="rule_2_value">
                                                    <option value="">请选择</option>
                                                    ${option_template}
                                                </select>
                                            </div>
                                        </fieldset>
                                    </div>
                                </div>
                            </div>
                            <div class="layui-tab-item">
                                <div class="layui-form-item">
                                    <div class="layui-input-inline echart_options" style="width:100%;">
                                        <fieldset class="layui-elem-field" style="width:180px;float:left;margin: 0 10px 0 10px;">
                                            <legend>选择图表类型</legend>
                                            <div class="layui-field-box">
                                                <select name=""rule_3_type>
                                                    <option value="">请选择</option>
                                                    <option value="1">柱形图</option>
                                                    <option value="2">折线图</option>
                                                    <option value="3">饼图</option>
                                                </select>
                                            </div>
                                        </fieldset>
                                        <fieldset class="layui-elem-field" style="width:180px;">
                                            <legend>选择数据来源</legend>
                                            <div class="layui-field-box">
                                                <select name="rule_3_value">
                                                    <option value="">请选择</option>
                                                    ${option_template}
                                                </select>
                                            </div>
                                        </fieldset>
                                    </div>
                                </div>
                            </div>  
                        </div>
                        <div style="position: absolute;left: 200px;bottom: 40px;">
                            <button type="button" class="layui-btn" lay-submit lay-filter="updateChart">更新</button>
                        </div>
                    </div>
                </div>`,
        success: function () {
            form.render();
            // tab切换
            element.on("tab(ruleTab)", function(data) {
                $(".layui-tab-content .layui-tab-item").each(function(){
                    $(this).removeClass("layui-show");
                });
                $(".layui-tab-content .layui-tab-item").eq(data.index).addClass("layui-show");
            });
            form.on("submit(updateChart)", function(data) {
                // 获取表格id
                let field = data.field;
                $.ajax({
                    url: "/crm/api/v1/manage/",
                    type: "post",
                    data: JSON.stringify({
                        "id": tableId
                    }),
                    success: function (data) {
                        if (data.code === 0) {
                            layer.msg("更新成功", {icon: 1});
                            layer.closeAll();
                        }
                    },
                    error: function () {}
                })
                return false;
            });
        }
    });
}

/**
 * @description 删除选中行的数据
 * @param {*} tableId 
 * @param {*} data 
 */
var delColData = function (tableId, data) {
    let table_id = tableId || localStorage.getItem("tableUid");
    layer.confirm(`是否删除本页已选中的${data.length}条数据`, {
        title: "删除数据",
        btn: ["确定", "取消"],
        function () {
            if (data.length > 0) {
                let id_array = [];  // 要删除数据的id数组
                data.forEach((item) => {
                    id_array.push(item._id);
                });
                $.ajax({
                    url: "/crm/api/v1/manage/",
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        "table_uuid": table_id,
                        "data": id_array
                    }),
                    beforeSend: function () {
                        layer.load(0);
                    },
                    success: function (res) {
                        layer.closeAll();
                        if (res.code === 0) {
                            layer.msg("删除成功", {icon: 1});
                        } else {
                            layer.msg("删除失败: " + res.message, {icon: 2});
                        }
                        return false;
                    },
                    error: function (err) {
                        layer.closeAll();
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(errMsg.message, {icon: 2});
                        return false;
                    }
                });
            }
        },
        function () {
            layer.closeAll();
        }
    });
}

/**
 * @description 录入或者编辑数据
 * @param {String} tableId 表uuid
 * @param {Object} colData 列数据
 */
var addOrEditData = function (tableId, colData) {
    let table_id = tableId || localStorage.getItem("tableUid");
    let header =JSON.parse(localStorage.getItem("header"))[table_id] || "";
    let formData = colData;
    let date_array = [];
    let time_array = [];
    if (header) {
        let form_item_templ = "";
        header.forEach((item) => {
            if (item.col_type === 2) { // 设置下列列表
                form_item_templ += `<div class="layui-form-item">
                                        <label class="layui-form-label">${item.title}</label>
                                        <div class="layui-input-block" style="width: 250px">
                                            <select name="${item.field}" ${item.must_input ? "lay-verify='required'" : ""}>
                                                <option value="">请选择</option>
                                                ${Object.keys(item.option).map((key) => {
                                                    return `<option value="${key}">${item.option[key]}</option>`;
                                                }).join("")}
                                            </select>
                                        </div>
                                    </div>`;
            } else {
                if (item.value_type === 3) {  // 设置选择日期
                    form_item_templ += `<div class="layui-form-item">
                                            <label class="layui-form-label">${item.title}</label>
                                            <div class="layui-input-block" style="width: 250px">
                                                <input type="text" name="${item.field}" ${item.must_input ? "lay-verify='required'" : ""} id="date_${item.field}" placeholder="yyyy-MM-dd" autocomplete="off" class="layui-input">
                                            </div>
                                        </div>`;
                    date_array.push(item.field);
                } else if (item.value_type === 4) {  // 设置选择时间
                    form_item_templ += `<div class="layui-form-item">
                                            <label class="layui-form-label">${item.title}</label>
                                            <div class="layui-input-block" style="width: 250px">
                                                <input type="text" name="${item.field}" ${item.must_input ? "lay-verify='required'" : ""} id="time_${item.field}" placeholder="yyyy-MM-dd HH:mm:ss" autocomplete="off" class="layui-input">
                                            </div>
                                        </div>`;
                    time_array.push(item.field);
                } else {
                    form_item_templ += `<div class="layui-form-item">
                                            <label class="layui-form-label">${item.title}</label>
                                            <div class="layui-input-block" style="width: 250px">
                                                <input type="text" name="${item.field}" ${item.must_input ? "lay-verify='required'" : ""} autocomplete="off" class="layui-input"></input>
                                            </div>
                                        </div>`;
                }
            }
        });
        layer.open({
            type: 1,
            title: "数据操作",
            area: ["500px", "auto"],
            maxHeight: 680,
            shade: 0.6,
            shadeClose: false,
            move: false,
            resize: false,
            maxmin: false,
            content: `<div style="max-height: 680px;overflow-y: auto;padding-top: 5px;">
                        <form class="layui-form" lay-filter="tableData">
                            ${form_item_templ}
                            <div class="layui-form-item">
                                <button type="button" class="layui-btn" lay-submit lay-filter="add" style="margin-left: 200px;">${formData ? "修改" : "新增"}数据</button>
                            </div>
                        </form>
                      </div>`,
            success: function () {
                // 脱敏数据要展示全
                form.render();   // 渲染表格
                date_array.forEach((item) => {
                    laydate.render({ // 渲染日期
                        elem: `#date_${item}`
                    });
                });
                time_array.forEach((item) => {
                    laydate.render({ // 渲染时间
                        elem: `#time_${item}`,
                        type: "datetime"
                    });
                });
                if (formData) {  // 填充表单
                    form.val("tableData", formData);
                }
                form.on("submit(add)", (data) => {
                    let field = data.field;
                    $.ajax({
                        url: `/crm/api/v1/manage/add_or_edit`,
                        type: "POST",
                        contentType: "application/json",
                        data: JSON.stringify(Object.assign({}, {
                            "mode": formData ? "edit" : "add",
                            "table_id": table_id  
                        }, field)),
                        beforeSend: function () {
                            layer.load(2);
                        },
                        success: function (res) {
                            layer.closeAll();
                            if (res.code === 0) {
                                layer.msg("成功", {icon: 1});
                            } else {
                                layer.msg("失败: " + res.message, {icon: 2});
                            }
                            return false;
                        },
                        error: function (err) {
                            layer.closeAll();
                            let errMsg = err.responseJSON || JSON.parse(err.responseText);
                            layer.msg(errMsg.message, {icon: 2});
                            return false;
                        }
                    })
                    return false;
                });
            }
        });
    }
}

/**
 * @description 新增或修改列
 * @param {String} tableId 表uuid
 */ 
var addOrAlterCol = function (tableId) {
    let table_id = tableId || localStorage.getItem("tableUid");
    layer.open({
        type: 1,
        title: "新增列",
        area: ["500px", "630px"],
        shade: 0.6,
        shadeClose: false,
        resize: false,
        move: false,
        maxmin: false,
        content: `<div>
                    <form class="layui-form" style="margin-top: 10px;" lay-filter="column">
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 85px;">列名</label>
                            <div class="layui-input-block">
                                <input type="text" name="col_name" lay-verify="required" placeholder="请输入中文" autocomplete="off" class="layui-input" style="width: 200px;">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 85px;">列别名</label>
                            <div class="layui-input-block">
                                <input type="text" name="col_name_en" lay-verify="required" placeholder="请输入英文" autocomplete="off" class="layui-input" style="width: 200px;">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 85px;">数据类型</label>
                            <div class="layui-input-block" style="padding-left: 5px;">
                                <input type="radio" name="data_type" value="1" title="字符串(默认255个字符内)" checked><br/>
                                <input type="radio" name="data_type" value="2" title="固定长度"><input type="number" name="length" value="10" step="1" min="1" max="50" class="layui-input" style="width: 60px;display: inline;"><br/>
                                <input type="radio" name="data_type" value="3" title="大文本(超过255个字符)"><br/>
                                <input type="radio" name="data_type" value="4" title="日期(年-月-日)"><br/>
                                <input type="radio" name="data_type" value="5" title="时间(年-月-日 时:分:秒)"><br/>
                                <input type="radio" name="data_type" value="6" title="下拉列表"><div style="width: 140px;display: inline-block;"><select id="down_options"></select></div><button type="button" class="layui-btn layui-btn-primary layui-btn-sm" id="addNewOption" style="height: 37px;margin-left: 3px;"><i class="layui-icon layui-icon-add-1"></i></button>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 85px;">是否唯一</label>
                            <div class="layui-input-block">
                                <input type="radio" name="is_unique" value="1" title="是">
                                <input type="radio" name="is_unique" value="0" title="否" checked>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 85px;">是否必填</label>
                            <div class="layui-input-block">
                                <input type="radio" name="is_required" value="1" title="是">
                                <input type="radio" name="is_required" value="0" title="否" checked>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 85px;">是否脱敏展示</label>
                            <div class="layui-input-block">
                                <input type="radio" name="is_mask" value="1" title="是">
                                <input type="radio" name="is_mask" value="0" title="否" checked>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <button type="button" class="layui-btn" lay-submit lay-filter="addNewCol" style="margin: 0 210px;">新增</button>
                        </div>
                    </form>
                  </div>`,
        success: function () {
            form.render();
            $("#addNewOption").on("click", function() {
                layer.open({
                    type: 1,
                    title: "新增下拉选项",
                    shade: 0.8,
                    shadeClose: false,
                    resize: false,
                    move: false,
                    maxmin: false,
                    area: ["320px", "240px"],
                    content: `<div class="layui-form" style="padding: 10px 0 0 0;">
                                <div class="layui-form-item">
                                    <label class="layui-form-label" style="width: 70px;">选项名</label>
                                    <div class="layui-input-inline">
                                        <input type="text" name="option_name" lay-verify="required" autocomplete="off" placeholder="请输入中文" class="layui-input">
                                    </div>
                                </div>
                                <div class="layui-form-item">
                                    <label class="layui-form-label" style="width: 70px;">选项别名</label>
                                    <div class="layui-input-inline">
                                        <input type="text" name="option_value" lay-verify="required" autocomplete="off" placeholder="请输入英文" class="layui-input">
                                    </div>
                                </div>
                                <div class="layui-form-item">
                                    <button class="layui-btn" lay-submit lay-filter="add" style="margin-left: 120px;">添加</button>
                                </div>
                              </div>`,
                    success: function (_, index) {
                        form.render();
                        form.on("submit(add)", function (data) {
                            let field = data.field;
                            // 判断是否和已有的重复

                            // 没有则添加
                            $("#down_options").append(`<option value="${field.option_value}">${field.option_name}</option>`);  // 追加元素
                            form.render("select", "column");
                            layer.close(index);
                            return false;
                        });
                    }
                });
            });
            form.on("submit(addNewCol)", function (data){
                let field = data.field;
                // 获取select下列列表元素
                let option = [];
                $("#down_options").each(function () {
                    $("option", this).each(function() {
                        option.push({"name": $(this).text(), "value": $(this).val()});
                    });
                });
                $.ajax({
                    url: "/crm/api/v1/manage/add_or_alter_column",
                    type: "post",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        "mode": "add",
                        "table_uuid": table_id,
                        "col_name": field.col_name,
                        "col_alias": field.col_name_en,
                        "type": field.data_type,
                        "options": option,
                        "must_input": field.is_required,
                        "is_desence": field.is_mask,
                        "is_unique": field.is_unique,
                        "length": field.length
                    }),
                    success: function (data) {
                        if (data.code === 0) {
                            layer.closeAll();
                            layer.msg("新增列成功", {icon: 1});
                        } else {
                            layer.msg(data.message, {icon: 2});
                        }
                        return false;
                    },
                    error: function (err) {
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(errMsg.message, {icon: 2});
                        return false;
                    }
                });
            })
        }
    })
}

/**
 * @description 批量检测
 * @param {String} tableId 表uuid
 */ 
var mulitDetect = function (tableId) {
    let table_id = tableId || localStorage.getItem("tableUid");
    let header =JSON.parse(localStorage.getItem("header"))[table_id] || "";
    let option_template = "";
    header.forEach((item) => {
        if (item.type !== 2 && item.col_type !== 4 && item.col_type !== 5) {
            option_template += `<option value="${item.field}">${item.title}</option>`;
        }
    });
    layer.open({
        type: 1,
        title: "Ping探测任务",
        area: ["500px", "300px"],
        shade: 0.6,
        shadeClose: false,
        move: false,
        resize: false,
        maxmin: false,
        content: `<div>
                    <div class="layui-tab" layui-tab-card lay-filter="pingTask">
                        <ul class="layui-tab-title">
                            <li class="layui-this">创建任务</li>
                            <li>历史任务</li>
                        </ul>
                        <div>
                            <div class="layui-tab-content">
                                <div class="layui-tab-item layui-show" id="showTask">
                                    <form class="layui-form" id="showTaskForm">
                                        <div class="layui-form-item">
                                            <label class="layui-form-label">IP列</label>
                                            <div class="layui-input-inline">
                                                <select name="ip_col" id="ip_col" lay-verify="required">
                                                    <option value="">请选择IP列</option>
                                                    ${option_template}
                                                </select>
                                            </div>
                                        </div>
                                        <div class="layui-form-item">
                                            <button type="button" class="layui-btn" lay-submit lay-filter="createTask" style="margin-left: 200px;margin-top: 30px;">创建任务</button>
                                        </div>
                                    </form>
                                </div>
                                <div class="layui-tab-item" id="showHistory">
                                    <table class="layui-table" id="historyTable" lay-filter="historyTable"></table>
                                </div>
                            </div>
                        </div>
                    </div>
                  </div>`,
        success: function () {
            element.on("tab(pingTask)", (data) => {
                if (data.index === 0) {
                    $("#showHistory").hide();
                    $("#showTask").show();
                    $("#showTaskForm").show();
                } else {
                    $("#showTaskForm").hide();
                    $("#showTask").hide();
                    $("#showHistory").show();
                    table();
                }
            });
            form.render();
            form.on("submit(createTask)", function(){
                if (!$("#ip_col").val()) {
                    layer.msg("请选择IP列", { icon: 2 });
                    return false;
                }
                console.log($("#ip_col").val());
                return false;
            });
        }
    });
}

/**
 * @description 新建到期通知
 * @param {String} tableId 表uuid
 */
var createNotify = function (tableId) {
    let id = tableId || localStorage.getItem("tableUid");
    let header = JSON.parse(localStorage.getItem("header"))[id];
    let option_template = "";
    // 判断header中是否有date、datetime属性列
    header.forEach((item) => {

    });
    if (1 === 1) {
        layer.open({
            type: 1,
            title: "到期提醒任务",
            area: ["500px", "300px"],
            shade: 0.6,
            shadeClose: false,
            resize: false,
            move: false,
            maxmin: false,
            content: `<div style="padding: 10px;">
                        <form class="layui-form">
                            <div class="layui-form-item">
                                <label class="layui-form-label">时间列</label>
                                <div class="layui-input-inline">
                                    <select>
                                    <option value="">请选择</option>
                                    ${option_template}
                                    </select>
                                </div>
                            </div>
                            <div class="layui-form-item">
                                <button class="layui-btn" lay-submit lay-filter="add">创建任务</button>
                            </div>
                        </form>
                      </div>`,
            success: function () {
                form.render();
                form.on("submit(add)", function(data) {
                    $.ajax({
                        url: `/crm/api/v1/manage/id=${id}`,
                        type: "post",
                        success: function (data) {},
                        error: function (err) {}
                    });
                    return false;
                })
            }
        });
    } else {
        layer.msg("未存在时间列,请新增或修改列", { icon: 2 });
        return false;
    }
}


/**
 * @description 显示历史记录
 * @param {String} tableId
 */
var showHistory = function (tableId) {
    let table_id = tableId || localStorage.getItem("tableUid");
    layer.open({
        type: 1,
        area: ["500px", "300px"],
        title: "显示详情",
        shade: 0.6,
        shadeClose: false,
        resize: false,
        move: false,
        maxmin: false,
        content: `<div>
                    <div class="layui-tab" layui-tab-card lay-filter="history">
                        <ul class="layui-tab-title">
                            <li class="layui-this">导入记录</li>
                            <li>导出记录</li>
                        </ul>
                        <div>
                            <div class="layui-tab-content">
                                <div class="layui-tab-item layui-show">
                                    <table class="layui-table" id="importTable" lay-filter="importTable"></table>
                                </div>
                                <div class="layui-tab-item">
                                    <table class="layui-table" id="exportTable" lay-filter="exportTable"></table>
                                </div>
                            </div>
                        </div>
                    </div>
                  </div>`,
        success: function () {
            element.on("tab(history)", (data) => {
                if (data.index === 0) {
                    $("#showHistory").hide();
                    $("#showTask").show();
                    table.reload({});
                } else {
                    $("#showTask").hide();
                    $("#showHistory").show();
                    table.reload({});
                }
            });
        } 
    });
}
