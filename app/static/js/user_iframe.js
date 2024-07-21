// user_iframe.js
// iframe调用父页面的方法集合

/**
 * @description 重定向页面
 * @param {String} url 
 */
function redirectPage(url) {
    window.parent.location.href = url;
}

/**
 * @description 绑定进度条步骤
 */
var renderStepProgress = () => {
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
        position: 0                // 起始位置0
    });
}

/**
 * @description 文本输入长度
 * @param {this} that 
 */
var checkLength = (that) => {
    $("#char-count").text(that.value.length);
}

/**
 * @description 新建资产表
 */
var addNewTable = () => {
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
                    <!-- 顶部步骤 -->
                    <div id="stepProgressBar"></div>
                    <div class="stepContent layui-form" style="padding-top: 10px;text-align: left;" lay-filter="stepFrom">
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
                    <div class="stepContent layui-form" lay-filter="methodForm">
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
                    <div class="layui-btn-container" style="position: absolute;bottom: 15px;left: 200px;">
                        <div style="text-align: center;margin-top: 10px;">
	                        <button type="button" id="pre" class="layui-btn layui-btn-sm" style="margin-top: 10px;margin-left: -20px;">上一步</button>
	                        <button type="button" id="next" class="layui-btn layui-btn-sm" style="margin: 0 20px;">下一步</button>
                            <button type="button" id="rightUse" class="layui-btn layui-btn-sm" style="display: none; margin-left: 10px;">立即使用</button>
                        </div>
                    </div> 
                  </div>`,
        success: (_, index) => {
            let uploadFilename = "";  // 文件名
            let layerIndex = "";      // load的index
            // 文件上传
            upload.render({
                elem: "#uploadExcel",
                url: "/crm/api/v1/upload",
                accet: "file",
                acceptMime: "application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                exts: "xlsx|xls",
                choose: (obj) => {
                    obj.preview((_, file) => {
                        uploadFilename = file.name;
                    });
                },
                before: () => {
                    layerIndex = layer.load(2);
                },
                done: (res) => {
                    layer.close(layerIndex);
                    if (res.code === 0) {
                        // 写入filename
                        $("input[name='filename']").val(res.message);
                        $("#upload-preview span").text(uploadFilename);
                        $("#upload-preview").removeClass("layui-hide");
                        layer.msg("上传成功", {icon: 1});
                    } else if (res.code === 302) {
                        window.location.href = res.message;
                    } else {
                        layer.msg(`上传失败: ${res.message}`, { icon: 2 });
                    }
                    return false;
                }
            });
            form.verify({
                // 校验输入是否是英文
                isEnglish: (value) => {
                    if (!value) return;
                    if (!(/^[A-Za-z]+$/.test(value))) {
                        return "只能由英文组成";
                    }
                }
            });
            form.render(null, "stepFrom");      // 渲染表格
            form.render(null, "methodForm");
            let currIndex = 0;                  // 定义当前步骤
            $("#pre").hide();                   // 隐藏上一步
            $(".stepContent").eq(0).show();    // 显示第一步
            renderStepProgress();              // 渲染步骤进度
            // 点击下一步触发函数
            $("#next").click(() => {
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
		        stepprogress.next("stepProgressBar");
	        });
            // 点击上一步触发的函数
	        $("#pre").click(() => {
                currIndex -= 1;
		        stepprogress.pre("stepProgressBar");
	        });
            // 点击立即使用触发的函数
            $("#rightUse").click(() => {
                layer.close(index);
                // 重载列表
                let win = window.frames["crm_manage"];
                win.contentWindow.reloadCardTable();
            });
            // 绑定进度变化事件
            stepprogress.on("change(stepProgressBar)", (options) => {
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
                        type: "POST",
                        contentType: "application/json;charset=utf-8",
                        data: JSON.stringify({
                            "name": $("input[name='manageName']").val(),
                            "keyword": $("input[name='emanegName']").val(),
                            "filename": $("input[name='filename']").val() ? $("input[name='filename']").val() : "",
                            "desc": $("#remark").val(),
                        }),
                        success: (res) => {
                            if (res.code === 0) {
                                // 成功提示
                                $(".stepContent").eq(3).html("<div style='padding: 35px 0;margin-left: -10px;'> \
                                    <i class='layui-icon layui-icon-success' style='font-size: 100px;color: green;'></i> \
                                    </div> \
                                    <span style='margin-left: -10px;font-size: 20px;'>创建成功</span>");
                                $("#rightUse").show();  // 显示立即使用按钮
                            } else if (res.code === 302) {
                                window.location.href = res.message;
                            } else {
                                // 失败提示
                                $(".stepContent").eq(3).html("<div style='padding: 35px 0;margin-left: -10px;'> \
                                    <i class='layui-icon layui-icon-error' style='font-size: 100px;color: red;'></i> \
                                    </div> \
                                    <span style='margin-left: -10px;font-size: 20px;'>创建失败: " + res.message + "</span>");
                            }
                            stepprogress.next("stepProgressBar");
                            $(".stepContent").eq(2).hide();
                            $(".stepContent").eq(3).show();
                            return false;
                        },
                        error: (err) => {
                            let errMsg = err.responseJSON || JSON.parse(err,responseText);
                            $(".stepContent").eq(3).html("<div style='padding: 35px 0;margin-left: -10px;'> \
                                    <i class='layui-icon layui-icon-error' style='font-size: 100px;color: red;'></i> \
                                    </div> \
                                    <span style='margin-left: -10px;font-size: 20px;'>创建失败: " + errMsg.message + "</span>");
                            stepprogress.next("stepProgressBar");
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
 * @description 在创建、修改图表规则后刷新图表
 * @param {String} tableUid 表uuid
 */
function refreshCharts (tableUid) {
    let win = window.frames["crm_manage"];
    win.contentWindow.showCharts(tableUid);
}

/**
 * @description 在录入数据或者修改数据后刷新数据
 */
function refreshManage () {
    let win = window.frames["crm_manage"];
    win.contentWindow.refreshData();
}

/**
 * @description 新增图表规则
 */
var addNewRule = () => {
    let table_id = localStorage.getItem("tableUid");
    let header = JSON.parse(localStorage.getItem("header"))[table_id];
    let option_template = "";  // 字段选项模板
    let date_template = "";    // 时间选项模板
    header.forEach((item) => {
        option_template += `<option value="${item.field}">${item.title}</option>`;
        if (item.value_type === 4 || item.value_type === 5) {
            date_template += `<option value="${item.field}">${item.title}</option>`;
        }
    });
    let tab_template = "";     // tab页模板
    let number = new Array(0, 1, 2);
    number.forEach((item) => {
        tab_template += `<div class="layui-tab-item${item === 0 ? " layui-show" : ""}"}>
                            <div class="layui-form-item">
                                <label class="layui-form-label">规则名称</label>
                                <div class="layui-input-inline">
                                    <input type="text" name="rule_${item}_name" placeholder="请输入规则名称" autocomplete="off" class="layui-input">
                                </div>
                            </div>
                            <div style="margin-left: 10px;margin-bottom: 5px;"><span style="color: red;">*</span>仅当图表类型为折线图时时间字段为必选值</div>
                            <div class="layui-form-item">
                                <div class="layui-input-inline echart_options" style="width:100%;">
                                    <fieldset class="layui-elem-field" style="width:140px;float:left;margin: 0 10px 0 10px;">
                                        <legend>图表类型</legend>
                                        <div class="layui-field-box">
                                            <select name="rule_${item}_type">
                                                <option value="">请选择</option>
                                                <option value="1">饼图</option>
                                                <option value="2">柱形图</option>
                                                <option value="3">折线图</option>
                                            </select>
                                        </div>
                                    </fieldset>
                                    <fieldset class="layui-elem-field" style="width:160px;float:left;margin: 0 10px 0 10px;">
                                        <legend>数据来源</legend>
                                        <div class="layui-field-box">
                                            <select name="rule_${item}_value">
                                                <option value="">请选择</option>
                                                ${option_template}
                                            </select>
                                        </div>
                                    </fieldset>
                                    <fieldset class="layui-elem-field" style="width:160px;">
                                        <legend>时间字段</legend>
                                        <div class="layui-field-box">
                                            <select name="rule_${item}_date">
                                                <option value="">请选择</option>
                                                ${date_template}
                                            </select>
                                        </div>
                                    </fieldset>
                                </div>
                            </div>
                        </div>`
    });
    layer.open({
        type: 1,
        title: "自定义图表规则",
        area: ["540px", "420px"],
        shade: 0.6,
        shadeClose: false,
        resize: false,
        move: false,
        maxmin: false,
        content: `<div class="layui-tab layui-tab-card" lay-filter="ruleTab" style="border-bottom-style: none;box-shadow: none;">
                    <ul class="layui-tab-title">
                        <li class="layui-this">规则1</li>
                        <li>规则2</li>
                        <li>规则3</li>
                    </ul>
                    <div class="layui-form" lay-filter="ruleForm">
                        <div class="layui-tab-content">
                            ${tab_template}
                            <div style="position: absolute;left: 240px;bottom: 40px;">
                                <button type="button" class="layui-btn" lay-submit lay-filter="updateChart">更新</button>
                            </div>    
                        </div>
                    </div>
                </div>`,
        success: (_, index) => {
            // 渲染tab
            element.render("tab", "ruleTab");
            // tab切换事件
            element.on("tab(ruleTab)", function (data) {
                $(".layui-tab-content .layui-tab-item").each(function () {
                    $(this).removeClass("layui-show");
                });
                $(".layui-tab-content .layui-tab-item").eq(data.index).addClass("layui-show");
            });
            form.render(null, "ruleForm");  // 渲染表单
            $.ajax({
                url: `/crm/api/v1/manage/rule?id=${table_id}`,
                type: "GET",
                success: (res) => {
                    if (res.code === 0) {
                        let has_options = res.message;
                        if (has_options.length > 0) {
                            let hasValue = new Object();
                            has_options.forEach((item, index) => {
                                hasValue[`rule_${index}_name`] = item.name;
                                hasValue[`rule_${index}_type`] = item.type;
                                hasValue[`rule_${index}_value`] = item.keyword;
                                if (item.date_keyword) {
                                    hasValue[`rule_${index}_date`] = item.date_keyword;
                                }
                            });
                            form.val("ruleForm", hasValue);     // 存在规则则赋值表单
                            form.render("select", "ruleForm");  // 渲染表单的select元素
                        }
                    } else if (res.code === 302) {
                        window.location.href = res.message;
                    }
                    return false;
                },
                error: (err) => {
                    console.log(err);
                    return false;
                }
            });
            form.on("submit(updateChart)", (data) => {
                let field = data.field;  // 获取字段值
                let loadIndex = "";
                let verify = true;
                // 校验
                number.forEach((item) => {
                    if (field[`rule_${item}_type`] !== "") {
                        if (field[`rule_${item}_name`] === "") {
                            layer.msg(`请填写规则${item + 1}的名称`, { icon: 2 });
                            verify = false;
                            return false;
                        }
                        if (field[`rule_${item}_value`] === "") {
                            layer.msg(`请选择规则${item + 1}的数据来源字段`, { icon: 2 });
                            verify = false;
                            return false;
                        }
                        if (field[`rule_${item}_type`] === "3" && field[`rule_${item}_date`] === "") {
                            layer.msg(`请选择规则${item + 1}的时间字段`, { icon: 2 });
                            verify = false;
                            return false;
                        }
                    }
                });
                if (!verify) return false;
                $.ajax({
                    url: "/crm/api/v1/manage/rule",
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        "table_uuid": table_id,
                        "rules": number.map((item) => {return {"name": field[`rule_${item}_name`], "type": field[`rule_${item}_type`], "keyword": field[`rule_${item}_value`], "date_keyword": field[`rule_${item}_date`]}})
                    }),
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index);
                            layer.msg("更新成功", { icon: 1 });
                            // 刷新图表
                            refreshCharts(table_id);
                        } else if (res.code === 302) {
                            window.location.href = res.message;
                        } else {
                            layer.msg(`更新失败: ${res.message}`, { icon: 2 });
                        }
                        return false;
                    },
                    error: (err) => {
                        layer.close(loadIndex);
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(`更新失败: ${errMsg.message}`, { icon: 2 });
                        return false;
                    }
                })
                return false;
            });
        }
    });
}

/**
 * @description 删除选中行的数据
 * @param {Array} data 要删除的数据
 */
var delColData = (data) => {
    let table_id = localStorage.getItem("tableUid");
    layer.confirm(`是否删除本页已选中的${data.length}条数据`, {
            title: "删除数据",
            btn: ["确定", "取消"]
        }, () => {
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
                    beforeSend: () => {
                        layer.load(2);
                    },
                    success: (res) => {
                        layer.closeAll();
                        if (res.code === 0) {
                            layer.msg("删除成功", { icon: 1 });
                            // reload数据
                            refreshManage();
                            refreshCharts(table_id);
                        } else if (res.code === 302) {
                            window.location.href = res.message;
                        } else {
                            layer.msg(`删除失败: ${res.message}`, { icon: 2 });
                        }
                        return false;
                    },
                    error: (err) => {
                        layer.closeAll();
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(errMsg.message, { icon: 2 });
                        return false;
                    }
                });
            }
        },
        (index) => {
            layer.close(index);
            return false;
        }
    );
}

/**
 * @description 录入或者编辑数据
 * @param {Object} colData 列数据
 */
var addOrEditData = (colData) => {
    let table_id = localStorage.getItem("tableUid");                    // 资产表uuid
    let header = JSON.parse(localStorage.getItem("header"))[table_id];  // 资产表header
    let formData = colData;
    let date_array = [];       // 日期数组
    let time_array = [];       // 时间数组
    let mark_array = [];       // 脱敏的数组
    let form_item_templ = "";  // 表单模板
    header.forEach((item) => {
        if (item.is_mark) {
            mark_array.push(item.field);
        }
        if (item.col_type === 2) {      // 设置下列列表
            form_item_templ += `<div class="layui-form-item">
                                    <label class="layui-form-label">${item.title}</label>
                                    <div class="layui-input-block" style="width: 250px;">
                                        <select name="${item.field}" ${item.must_input ? "lay-verify='required'" : ""}>
                                            <option value="">请选择</option>
                                            ${Object.keys(item.option).map((key) => {
                                                return `<option value="${key}">${item.option[key]}</option>`;
                                            }).join("")}
                                        </select>
                                    </div>
                                </div>`;
        } else {
            if (item.value_type === 4) {  // 设置选择日期
                form_item_templ += `<div class="layui-form-item">
                                        <label class="layui-form-label">${item.title}</label>
                                        <div class="layui-input-block" style="width: 250px;">
                                            <input type="text" name="${item.field}" ${item.must_input ? "lay-verify='required'" : ""} id="date_${item.field}" placeholder="yyyy-MM-dd" autocomplete="off" class="layui-input">
                                        </div>
                                    </div>`;
                date_array.push(item.field);
            } else if (item.value_type === 5) {  // 设置选择时间
                form_item_templ += `<div class="layui-form-item">
                                        <label class="layui-form-label">${item.title}</label>
                                        <div class="layui-input-block" style="width: 250px;">
                                            <input type="text" name="${item.field}" ${item.must_input ? "lay-verify='required'" : ""} id="time_${item.field}" placeholder="yyyy-MM-dd HH:mm:ss" autocomplete="off" class="layui-input">
                                        </div>
                                    </div>`;
                time_array.push(item.field);
            } else {
                form_item_templ += `<div class="layui-form-item">
                                        <label class="layui-form-label">${item.title}${item.must_input ? `<span style="color: red;">*</span>` : ""}</label>
                                        <div class="layui-input-block" style="width: 250px;">
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
        success: (_, index) => {
            form.render(null, "tableData");   // 渲染表格
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
                if (mark_array.length > 0) {  // 脱敏数据要展示全
                    let undeseData = new Object();
                    $.ajax({
                        url: `/crm/api/v1/manage/undesense?table_id=${table_id}&row_id=${formData._id}&key=${mark_array.toString()}`,
                        type: "GET",
                        success: (res) => {
                            if (res.code === 0) {
                                undeseData = res.message;
                            } else if (res.code === 302) {
                                window.location.href = res.message;
                            }
                            return false;
                        },
                        error: (err) => {
                            console.log(err);
                            return false;
                        },
                        complete: () => {
                            formData = Object.assign({}, formData, undeseData);  // 合并对象
                            form.val("tableData", formData);
                        }
                    });
                } else {
                    form.val("tableData", formData);
                }
            }
            form.on("submit(add)", (data) => {
                let field = data.field;
                let loadIndex = "";
                $.ajax({
                    url: `/crm/api/v1/manage/add_or_edit`,
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify(Object.assign({}, {
                        "mode": formData ? "edit" : "add",
                        "id": formData ? formData._id : "",
                        "table_id": table_id  
                    }, field)),
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index);
                            layer.msg("成功", { icon: 1 });
                            refreshManage();
                            refreshCharts(table_id);
                        } else if (res.code === 302) {
                            window.location.href = res.message;
                        } else {
                            layer.msg(`失败: ${res.message}`, { icon: 2 });
                        }
                        return false;
                    },
                    error: (err) => {
                        layer.close(loadIndex);
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(errMsg.message, { icon: 2 });
                        return false;
                    }
                })
                return false;
            });
        }
    });
    
}

/**
 * @description 新增或修改列
 */ 
var addOrAlterCol = () => {
    let table_id = localStorage.getItem("tableUid");
    let header = JSON.parse(localStorage.getItem("header"))[table_id];
    let all_header_options = "";
    header.forEach((item) => {
        all_header_options += `<option value="${item.field}">${item.title}</option>`;
    });
    layer.open({
        type: 1,
        title: "列操作",
        area: ["510px", "670px"],
        shade: 0.6,
        shadeClose: false,
        resize: false,
        move: false,
        maxmin: false,
        content: `<div>
                    <form class="layui-form" style="margin-top: 10px;" lay-filter="column">
                        <div class="layui-form-item">
                            <div class="layui-input-block">
                                <input type="radio" name="mode" lay-filter="mode" value="add" title="新增列" checked>
                                <input type="radio" name="mode" lay-filter="mode" value="alter" title="修改列"><div style="width: 150px;display: inline-block;"><select name="hasColumn" lay-filter="hasColumn"><option value="">选择要修改的列</option>${all_header_options}</select></div>
                            </div>
                        </div>
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
                                <input type="radio" name="data_type" value="6" title="下拉列表"><div style="width: 140px;display: inline-block;"><select id="down_options"></select></div><button type="button" class="layui-btn layui-btn-primary layui-btn-sm" id="addNewOption" style="height: 37px;margin-left: 3px;"><i class="layui-icon layui-icon-add-1"></i></button><button type="button" class="layui-btn layui-btn-primary layui-btn-sm" id="delOldOption" style="height: 37px;margin-left: 3px;"><i class="layui-icon layui-icon-subtraction"></i></button>
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
                            <button type="button" class="layui-btn" lay-submit lay-filter="addNewCol" style="margin: 0 210px;" id="colMethod">新增</button>
                        </div>
                    </form>
                  </div>`,
        success: (_, index) => {
            form.render(null, "column");    // 渲染表单
            let has_options = new Object(); // 下拉选项
            // 新增选项
            $("#addNewOption").on("click", () => {
                layer.open({
                    type: 1,
                    title: "新增下拉选项",
                    area: ["320px", "240px"],
                    shade: 0.8,
                    shadeClose: false,
                    resize: false,
                    move: false,
                    maxmin: false,
                    content: `<div class="layui-form" style="padding: 10px 0px 0px 0px;" lay-filter="option">
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
                                    <button type="button" class="layui-btn" lay-submit lay-filter="add" style="margin-left: 120px;">添加</button>
                                </div>
                              </div>`,
                    success: (_, oindex) => {
                        form.render(null, "option");
                        form.on("submit(add)", (data) => {
                            let field = data.field;
                            // 判断是否和已有的重复
                            if (Object.values(has_options).indexOf(field.option_name) !== -1) {
                                layer.msg("选项名重复", { icon: 2 });
                                return false;
                            }
                            if (Object.keys(has_options).indexOf(field.option_value) !== -1) {
                                layer.msg("选项别名重复", { icon: 2 });
                                return false;
                            }
                            // 没有则添加
                            $("#down_options").append(`<option value="${field.option_value}">${field.option_name}</option>`);  // 追加元素
                            has_options[field.option_value] = field.option_name;
                            form.render("select", "column");  // 渲染下拉选项
                            layer.close(oindex);
                            return false;
                        });
                    }
                });
            });
            // 删除选项
            $("#delOldOption").on("click", () => {
                if (Object.keys(has_options).length === 0) {
                    layer.msg("没有可删除的选项", { icon: 2 });
                    return false;
                }
                layer.open({
                    type: 1,
                    title: "删除下拉选项",
                    area: ["320px", "240px"],
                    shade: 0.8,
                    shadeClose: false,
                    resize: false,
                    move: false,
                    maxmin: false,
                    content: `<div>
                                ${Object.keys(has_options).map((k) => {
                                    return `<div style="width: 80%;margin: 5px 5px 5px 15px;border: 1px solid #eee;line-height: 30px;"><span style="margin-left: 10px;">${has_options[k]}</span><button class="layui-btn layui-btn-primary layui-border layui-btn-xs" style="position: absolute;right: 50px;margin: 4px;border: none;" onclick="delMap('${k}', this)"><i class="layui-icon layui-icon-close"></i></button></div>`;
                                }).join("")}
                              </div>`,
                    success: () => {
                        // 删除字段
                        function delMap(k, that) {
                            $(that).parent().remove();
                            delete has_options[k];
                            $("#down_options").find(`option[value="${k}"]`).remove();
                            form.render("select", "column");
                        }
                        window.delMap = window.delMap || delMap;
                    }
                })
            });
            form.on("radio(mode)", (data) =>{
                $("#colMethod").text("新增");
                let elem = data.elem
                let value = elem.value;
                if (value === "add") {
                    // 清空表单
                    form.val("column", {
                        "col_name": "",
                        "col_name_en": "",
                        "data_type": 1,
                        "length": 10,
                        "is_unique": 0,
                        "is_required": 0,
                        "is_mask": 0
                    });
                    $("#down_options").empty();
                    has_options = {};
                    form.render("select", "column");
                } else if (value === "alter") {
                    $("#colMethod").text("修改");
                    if ($("[name='hasColumn']").val() !== "") {
                        let c_o = $("[name='hasColumn']").val();
                        header.forEach((item) => {
                            if (item.field === c_o) {
                                // 表单赋值
                                form.val("column", {
                                    "col_name": item.title,
                                    "col_name_en": item.field,
                                    "data_type": item.col_type === 2 ? 6 : item.value_type,
                                    "length": item.length === 0 ? 10 : item.length,
                                    "is_unique": item.is_unique ? 1 : 0,
                                    "is_required": item.must_input ? 1 : 0,
                                    "is_mask": item.is_mark ? 1 : 0
                                });
                                if (item.col_type === 2) {
                                    has_options = item.option;
                                    $("#down_options").empty();
                                    Object.keys(item.option).forEach((k) => {
                                        $("#down_options").append(`<option value="${k}">${item.option[k]}</option>`);
                                    });
                                }
                                form.render("select", "column");
                            }
                        });
                    }
                }
            });
            form.on("select(hasColumn)", (data) => {
                if ($("input[name='mode']:checked").val() === "alter") {
                    let value = data.value;
                    header.forEach((item) => {
                        if (item.field === value) {
                            form.val("column", {
                                "col_name": item.title,
                                "col_name_en": item.field,
                                "data_type": item.col_type === 2 ? 6 : item.value_type,
                                "length": item.length === 0 ? 10 : item.length,
                                "is_unique": item.is_unique ? 1 : 0,
                                "is_required": item.must_input ? 1 : 0,
                                "is_mask": item.is_mark ? 1 : 0
                            });
                            if (item.col_type === 2) {
                                has_options = item.option;
                                $("#down_options").empty();
                                Object.keys(item.option).forEach((k) => {
                                    $("#down_options").append(`<option value="${k}">${item.option[k]}</option>`);
                                });
                            }
                            form.render("select", "column");
                        }
                    })
                }
            });
            form.on("submit(addNewCol)", (data) => {
                let field = data.field;
                let loadIndex = "";
                // 校验数据
                let curr_type = field.data_type;
                if (curr_type === "2") {
                    // 校验长度设置
                    let curr_length = field.length;
                    if (parseInt(curr_length) > 50 || parseInt(curr_length) < 1) {
                        layer.msg("长度取值范围是1-50", { icon: 2 });
                        return false;
                    }
                } else if (curr_type === "6") {
                    if (has_options.length === 0) {
                        layer.msg("请添加下拉选项", { icon: 2 });
                        return false;
                    }
                }
                $.ajax({
                    url: "/crm/api/v1/manage/add_or_alter_column",
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        "mode": $("input[name='mode']:checked").val(),
                        "table_uuid": table_id,
                        "col_name": field.col_name,
                        "col_alias": field.col_name_en,
                        "type": field.data_type,
                        "options": Object.keys(has_options).map((k) => {return {"name": has_options[k], "value": k}}),
                        "must_input": field.is_required,
                        "is_desence": field.is_mask,
                        "is_unique": field.is_unique,
                        "length": field.length
                    }),
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index);
                            layer.msg("成功", { icon: 1 });
                            // 刷新界面
                            let win = window.frames["crm_manage"];
                            win.contentWindow.loadManageTable(table_id);
                        } else if (res.code === 302) {
                            window.location.href = res.message;
                        } else {
                            layer.msg(`失败: ${res.message}`, { icon: 2 });
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
            })
        }
    })
}

/**
 * 查看任务详情
 * @param {String} id 表id 
 * @param {String} task_id 任务id
 */
function showTaskDeail (id, task_id) {
    let win = window.frames["crm_manage"];
    let echarts = win.contentWindow.getEchartMethod();
    layer.open({
        type: 1,
        title: "任务详情",
        area: ["540px", "550px"],
        shade: 0.8,
        shadeClose: false,
        resize: false,
        move: false,
        maxmin: false,
        content: `<div style="padding: 10px;">
                    <div style="width: 100%; height: 200px;">
                        <div id="detail_pie" style="width: 100%;height: 100%;"></div>
                    </div>
                    <table class="layui-hide" id="detail" lay-filter="detail"></table>  
                  </div>`,
        success: () => {
            table.render({
                elem: "#detail",
                url: `/crm/api/v1/manage/ping?id=${id}&task_id=${task_id}`,
                parseData: (res) => {
                    if (res.code === 302) {
                         window.location.href = res.message;
                         return false;
                    }
                    return {
                        "code": res.code,
                        "msg": res.code === 0 ? "" : res.message,
                        "count": res.message.total,
                        "data": res.message.data,
                        "echart": res.message.echart
                    };
                },
                page: {
                    groups: 3
                },
                limit: 5,
                limits: [5],
                cols: [[
                    { field: "ip", title: "IP地址", width: 140 },
                    { field: "status", title: "状态", width: 110, templet: (d) => {
                        return d.status === 1 ? `<span class="layui-badge layui-bg-green">在线</span>`: `<span class="layui-badge">离线</span>`;
                    } },
                    { field: "reason", title: "原因", width: 255 }
                ]],
                done: (res) => {
                    if (res.code === 0) {
                        // 渲染饼图图表
                        echarts.init(document.getElementById("detail_pie")).setOption({
                            title: {
                                text: "任务信息",
                                left: "center"
                            },
                            tooltip: {
                                trigger: "item"
                            },
                            legend: {
                                orient: "vertical",
                                left: "left"
                            },
                            toolbox: {
                                feature: {
                                    saveAsImage: {}
                                }
                            },
                            series: [{
                                name: "状态",
                                type: "pie",
                                radius: "50%",
                                data: res.echart,
                                emphasis: {
                                    itemStyle: {
                                        shadowBlur: 10,
                                        shadowOffsetX: 0,
                                        shadowColor: "rgba(0, 0, 0, 0.5)"
                                    }
                                }
                            }]
                        });
                    }
                },
            });
        }
    })

}

window.showTaskDeail = window.showTaskDeail || showTaskDeail;

/**
 * @description 批量检测
 */ 
var mulitDetect = () => {
    let table_id = localStorage.getItem("tableUid");
    let header = JSON.parse(localStorage.getItem("header"))[table_id];
    let option_template = "";
    header.forEach((item) => {
        if (item.col_type !== 2 && item.value_type !== 4 && item.value_type !== 5) {
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
                    <div class="layui-tab layui-tab-card" lay-filter="pingTask" style="margin-top: 0px;border-bottom-style: none;box-shadow: none;">
                        <ul class="layui-tab-title">
                            <li class="layui-this">创建任务</li>
                            <li>历史任务</li>
                        </ul>
                        <div>
                            <div class="layui-tab-content">
                                <div class="layui-tab-item layui-show" id="showTask">
                                    <form class="layui-form" id="showTaskForm" lay-filter="taskForm">
                                        <div class="layui-form-item">
                                            <label class="layui-form-label">任务名称</label>
                                            <div class="layui-input-inline">
                                                <input type="text" name="task_name" lay-verify="required" autocomplete="off" placeholder="请输入任务名称" class="layui-input">
                                            </div>
                                        </div>
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
                                            <button type="button" class="layui-btn" lay-submit lay-filter="createTask" style="margin-left: 200px;margin-top: 8px;">创建任务</button>
                                        </div>
                                    </form>
                                </div>
                                <div class="layui-tab-item" id="showHistory">
                                    <table class="layui-hide" id="historyTask" lay-filter="historyTask"></table>
                                </div>
                            </div>
                        </div>
                    </div>
                  </div>`,
        success: (_, index) => {
            element.on("tab(pingTask)", (data) => {
                if (data.index === 0) {
                    $("#showHistory").hide();
                    $("#showTask").show();
                    $("#showTaskForm").show();
                } else {
                    $("#showTaskForm").hide();
                    $("#showTask").hide();
                    $("#showHistory").show();
                    table.render({
                        elem: "#historyTask",
                        id: "historyTask",
                        url: `/crm/api/v1/manage/ping?id=${table_id}`,
                        page: true,
                        limit: 2,
                        limits: [2],
                        text: {none: "暂无数据,请先创建任务"},
                        parseData: (res) => {
                            if (res.code === 302) {
                                window.location.href = res.message;
                                return false;
                            }
                            return {
                                "code": res.code,
                                "msg": res.code === 0 ? "" : res.message,
                                "count": res.message.total,
                                "data": res.message.data
                            };
                        },
                        cols:[[
                            { fidle: "id", title: "任务ID", hide: true },
                            { field: "name", title: "任务名称", width: 120 },
                            { field: "create_time", title: "创建时间", width: 160 },
                            { field: "status", title: "状态", width: 80, templet: (d) => {
                                if (d.status === 0) return `<span class="layui-badge-rim">排队中</span>`;
                                if (d.status === 1) return `<span class="layui-badge layui-bg-blue">执行中</span>`;
                                if (d.status === 2) return `<span class="layui-badge layui-bg-green">成功</span>`;
                                if (d.status === 3) return `<span class="layui-badge">失败</span>`;
                            } },
                            { field: "result", title: "结果", width: 100, templet: (d) => {
                                if (d.status === 1) return `<button class="layui-btn layui-btn-xs" onclick="showProgress('${d.id}')">查看进度</button>`;
                                if (d.status === 2) return `<button class="layui-btn layui-btn-xs" onclick="showTaskDeail('${table_id}','${d.id}')">查看详情</button>`;
                            } }
                        ]]
                    });
                }
            });
            form.render(null, "taskForm");
            form.on("submit(createTask)", (data) => {
                let field = data.field;
                if (!$("#ip_col").val()) {
                    layer.msg("请选择IP列", { icon: 2 });
                    return false;
                }
                $.ajax({
                    url: `/crm/api/v1/manage/ping?id=${table_id}`,
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        "id": table_id,
                        "name": field.task_name,
                        "column": $("#ip_col").val()
                    }),
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index);
                            layer.msg("创建成功", { icon: 1 });
                        } else if (res.code === 302) {
                            window.location.href = res.message;
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
        }
    });
}

/**
 * @description 启动或停止通知
 * @param {String} mode 启动或者停止
 * @param {String} task_id 任务id
 */
function startOrStopNotify (mode, task_id) {
    let loadIndex = "";
    $.ajax({
        url: "/crm/api/v1/manage/notify",
        type: "POST",
        contentType: "application/json;charset=utf-8",
        data: JSON.stringify({
            "operate": mode,
            "task_id": task_id
        }),
        beforeSend: () => {
            loadIndex = layer.load(2);
        },
        success: (res) => {
            layer.close(loadIndex);
            if (res.code === 0) {
                layer.msg("操作成功", { icon: 1 });
                table.reloadData("historyNotify");
            } else if (res.code === 302) {
                window.location.href = res.message;
            } else {
                layer.msg(`操作失败: ${res.message}`, { icon: 2 });
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
}

window.startOrStopNotify = window.startOrStopNotify || startOrStopNotify;

/**
 * @description 新建到期通知
 */
var createNotify = () => {
    let table_id = localStorage.getItem("tableUid");
    let header = JSON.parse(localStorage.getItem("header"))[table_id];
    let option_template = "";
    let key2Word = new Object();
    header.forEach((item) => {  // 判断header中是否有date、datetime属性列
        if (item.value_type == 4 || item.value_type == 5) {
            option_template += `<option value="${item.field}">${item.title}</option>`;
        }
        key2Word[item.field] = item.title;
    });
    layer.open({
        type: 1,
        title: "到期提醒任务",
        area: ["500px", "300px"],
        shade: 0.6,
        shadeClose: false,
        resize: false,
        move: false,
        maxmin: false,
        content: `<div class="layui-tab layui-tab-card" lay-filter="notify" style="margin-top: 0px;border-bottom-style: none;box-shadow: none;">
                    <ul class="layui-tab-title">
                        <li class="layui-this">创建任务</li>
                        <li>历史任务</li>
                    </ul>
                    <div>
                        <div class="layui-tab-content">
                            <div class="layui-tab-item" id="showAddTask">
                                <form class="layui-form" lay-filter="notifyForm">
                                    <div class="layui-form-item">
                                        <label class="layui-form-label">任务名称</label>
                                        <div class="layui-input-inline">
                                            <input type="text" name="taskName" id="taskName" lay-verify="required" placeholder="请输入任务名称" autocomplete="off" class="layui-input">
                                        </div>
                                    </div>
                                    <div class="layui-form-item">
                                        <label class="layui-form-label">时间列</label>
                                        <div class="layui-input-inline">
                                            <select name="date_col" id="date_col" lay-verify="required">
                                                <option value="">请选择</option>
                                                ${option_template}
                                            </select>
                                        </div>
                                    </div>
                                    <div class="layui-form-item" style="margin-left: 180px;margin-top: 20px;">
                                        <button type="button" class="layui-btn" lay-submit lay-filter="add" id="addTask">创建任务</button>
                                    </div>
                                </form>
                            </div>
                            <div class="layui-tab-item" id="showHistory">
                                <table class="layui-hide" id="historyNotify" lay-filter="historyNotify"></table>
                            </div>
                        </div>
                    </div>
                </div>`,
        success: (_, index) => {
            $("#showAddTask").show();
            element.on("tab(notify)", (data) => {
                if (data.index === 0) {
                    $("#showHistory").hide();
                    $("#showAddTask").show();
                } else if (data.index === 1) {
                    $("#showAddTask").hide();
                    $("#showHistory").show();
                    table.render({
                        elem: "#historyNotify",
                        id: "historyNotify",
                        url: `/crm/api/v1/manage/notify?id=${table_id}`,
                        page: true,
                        limit: 2,
                        limits: [2],
                        text: {none: "暂无数据,请先创建任务"},
                        parseData: (res) => {
                            if (res.code === 302) {
                                window.location.href = res.message;
                                return false;
                            }
                            return {
                                "code": res.code,
                                "msg": res.code === 0 ? "" : res.message,
                                "count": res.message.total,
                                "data": res.message.data
                            }
                        },
                        cols: [[
                            { field: "id", title: "任务ID", hide: true },
                            { field: "name", title: "任务名称", width: 125 },
                            { field: "keyword", title: "字段", width: 120, templet: (d) => {
                                return key2Word[d.keyword];
                            } },
                            { field: "create_time", title: "创建时间", width: 160 },
                            { field: "status", title: "操作", width: 80, templet: (d) => {
                                return d.status === 0 ? `<button type="button" class="layui-btn layui-btn-sm" onclick="startOrStopNotify('start', '${d.id}')">启动</button>` : `<button type="button" class="layui-btn layui-btn-sm layui-bg-red" onclick="startOrStopNotify('stop', '${d.id}')">停止</button>`;
                            } }
                        ]]
                    });
                }
            });
            form.render(null, "notifyForm");
            if (option_template === "") {
                $("#addTask").text("暂无时间列可选");
                $("#addTask").addClass("layui-btn-disabled");
                return false;
            }
            form.on("submit(add)", (data) => {
                let field = data.field;
                let loadIndex = "";
                $.ajax({
                    url: "/crm/api/v1/manage/notify",
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        "operate": "add",
                        "id": table_id,
                        "name": field.taskName,
                        "keyword": field.date_col
                    }),
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index);
                            layer.msg("任务创建成功", { icon: 1 });
                        } else if (res.code === 302) {
                            window.location.href = res.message;
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
            })
        }
    });
}

/**
 * @description 显示历史记录
 */
var showHistory = () => {
    let table_id = localStorage.getItem("tableUid");
    layer.open({
        type: 1,
        area: ["620px", "410px"],
        title: "显示详情",
        shade: 0.6,
        shadeClose: false,
        resize: false,
        move: false,
        maxmin: false,
        content: `<div>
                    <div class="layui-tab layui-tab-card" lay-filter="history" style="margin-top: 0px;border-bottom-style: none;box-shadow: none;">
                        <ul class="layui-tab-title">
                            <li class="layui-this">导入记录</li>
                            <li>导出记录</li>
                        </ul>
                        <div>
                            <div class="layui-tab-content">
                                <div class="layui-tab-item layui-show">
                                    <table class="layui-hide" id="historyTable" lay-filter="historyTable"></table>
                                </div>
                            </div>
                        </div>
                    </div>
                  </div>`,
        success: () => {
            table.render({
                elem: "#historyTable",
                id: "historyTable",
                url: `/crm/api/v1/manage/history?type=1&id=${table_id}`,
                page: true,
                limit: 5,
                limits: [5],
                parseData: (res) => {
                    if (res.code === 302) {
                        window.location.href = res.message;
                        return false;
                    }
                    return {
                        "code": res.code,
                        "msg": res.code === 0 ? "" : res.message,
                        "count": res.message.total,
                        "data": res.message.data
                    }
                },
                cols: [[
                    { field: "id", title: "ID", hide: true },
                    { field: "file", title: "文件", width: 120, templet: (d) => {
                        if (!d.file) {
                            return "";
                        }
                        return `<a href="/crm/api/v1/file/${d.file}" style="color: blue;">点此下载文件</a>`;
                    } },
                    { field: "create_user", title: "创建者", width: 120 },
                    { field: "create_time", title: "创建时间", width: 170 },
                    { field: "status", title: "状态", width: 80, templet: (d) => {
                        if (d.status === 1) return `<span class="layui-badge layui-bg-blue">执行中</span>`;
                        if (d.status === 0) return `<span class="layui-badge-rim">排队中</span>`;
                        if (d.status === 2) return `<span class="layui-badge layui-bg-green">成功</span>`;
                        if (d.status === 3) return `<span class="layui-badge">失败</span>`;
                    } },
                    { field: "error", title: "错误", width: 120, templet: (d) => {
                        if (!d.error) {
                            return "";
                        }
                        return `<a href="/crm/api/v1/file/${d.error}" style="color: blue;">下载错误文件</a>`;
                    } }
                ]]
            });
            element.on("tab(history)", (data) => {
                if (data.index === 0) {
                    table.reloadData("historyTable", {
                        url: `/crm/api/v1/manage/history?type=1&id=${table_id}`
                    }); 
                } else {
                    table.reloadData("historyTable", {
                        url: `/crm/api/v1/manage/history?type=2&id=${table_id}`
                    }); 
                }
            });
        } 
    });
}

/**
 * @description 导出表格数据
 */
var exportTableData = () => {
    let table_id = localStorage.getItem("tableUid");
    layer.open({
        type: 1,
        title: "是否加密表格",
        area: ["500px", "250px"],
        shade: 0.6,
        shadeClose: false,
        move: false,
        resize: false,
        maxmin: false,
        content: `<div class="layui-form" lay-filter="exportForm" style="padding: 20px 0 0 20px;">
                    <div class="layui-form-item">
                        <div class="layui-input-inline">
                            <input type="radio" name="is_set" value="0" title="否,直接导出" checked>
                        </div>
                    </div>
                    <div class="layui-form-item">
                        <div class="layui-input-inline" style="width: 100%;">
                            <input type="radio" name="is_set" value="1" title="是,请设置密码">
                            <div style="width: 180px;display: inline-block;">
                                <input type="password" name="passwd" maxlength="10" autocomplete="off" lay-affix="eye" class="layui-input">
                            </div>
                        </div>
                    </div>
                    <div class="layui-form-item" style="margin-top: 20px;">
                        <button type="button" class="layui-btn" lay-submit lay-filter="export" style="margin-left: 90px;">导出</button>
                        <button type="button" class="layui-btn layui-btn-primary layui-border" lay-submit lay-filter="cancel" style="margin-left: 100px;">取消</button>
                    </div>
                  </div>`,
        success: (_, index) => {
            form.render(null, "exportForm");  // 渲染表单
            form.on("submit(export)", (data) => {
                let field = data.field;
                let loadIndex = "";
                if (field.is_set === "1") {
                    if (field.passwd.length < 6) {
                        layer.msg("密码长度不能小于6位", { icon: 2 });
                        return false;
                    }
                }
                $.ajax({
                    url: `/crm/api/v1/manage/export?id=${table_id}${field.is_set === "1" ? `&passwd=${field.passwd}` : ""}${localStorage.getItem("condition") ? `&filter='${localStorage.getItem("condition")}'` : ""}`,
                    type: "GET",
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index);
                            showProgress(res.message, () => {
                                let target = document.createElement("a");
                                target.href = `/crm/api/v1/file/${res.message}`;
                                target.download = "资产表导出文件.xlsx";
                                document.body.appendChild(target);
                                target.click();
                                document.body.removeChild(target);
                            });
                        } else if (res.code === 302) {
                            window.location.href = res.message;
                        } else {
                            layer.msg(`导出错误: ${res.message}`, { icon: 2 });
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
    });
}

/** 
 * @description 显示任务进度
 * @param {String} task_id  任务id
 * @param {Function} callback  回调函数
*/
var showProgress = (task_id, callback) => {
    layer.open({
        type: 1,
        title: false,
        area: ["300px", "20px"],
        shade: 0.6,
        shadeClose: true,
        move: false,
        resize: false,
        maxmin: false,
        closeBtn: 0,
        skin: "layui-layer-opacity",
        content: `<div style="width: 300px;">
                    <div class="layui-progress layui-progress-big" lay-showPercent="true" lay-filter="progress">
                        <div class="layui-progress-bar" lay-percent="0%"></div>
                    </div>
                  </div>`,
        success: (_, index) => {
            element.render("progress", "progress");
            // sse推送进度
            let eventSource = new EventSource(`/crm/api/v1/manage/process/${task_id}`);
            eventSource.onmessage = (e) => {
                let data = JSON.parse(e.data);
                element.progress("progress", `${data.speed}%`);  // 渲染进度
                if (data.speed === 100) {
                    eventSource.close();  // 关闭连接
                    if (data.error) {
                        layer.msg(`失败: ${data.error}`, { icon: 2 });
                    } else {
                        setTimeout(() => {
                            layer.close(index);
                            if (callback) {
                                callback();
                            }
                        }, 1000);
                    }
                }
            };
            eventSource.onerror = () => {
                eventSource.close();
            };
        }
    });
}

/**
 * @description 绑定IP列
 */
var bindIP = () => {
    let checkIPCol = JSON.parse(localStorage.getItem("ip_col")) || {};
    let table_id = localStorage.getItem("tableUid");
    let header = JSON.parse(localStorage.getItem("header"))[table_id];
    let option_obj = new Object();
    let option_templ = "";
    header.forEach((item) => {
        if (item.col_type !== 2 && item.value_type !== 4 && item.value_type !== 5) {
            if (checkIPCol && item.field === checkIPCol["field"]) {
                option_templ += `<option value="${item.field}" selected>${item.title}</option>`;
            } else {
                option_templ += `<option value="${item.field}">${item.title}</option>`;
            }
            option_obj[item.field] = item.title;
        }
    });
    layer.open({
        type: 1,
        title: "绑定IP列",
        area: ["360px", "200px"],
        shade: 0.6,
        shadeClose: false,
        move: false,
        resize: false,
        maxmin: false,
        content: `<div class="layui-form" lay-filter="bindIpForm">
                    <div class="layui-form-item" id="tableForIp" style="margin-top: 5px;">
                        <label class="layui-form-label">IP列</label>
                        <div class="layui-input-block" style="width: 200px;">
                            <select name="ip_column" lay-verify="required">
                                <option value="">请选择IP列</option>
                                ${option_templ}
                            </select>
                        </div>
                    </div>
                    <div class="layui-form-item">
                        <button class="layui-btn" style="margin-left: 140px;margin-top: 10px;" lay-submit lay-filter="bindIp">绑定</button>
                    </div>
                  </div>`,
        success: (_, index) => {
            let loadIndex = "";
            form.render(null, "bindIpForm");
            form.on("submit(bindIp)", (data) => {
                $.ajax({
                    url: "/crm/api/v1/manage/bind",
                    type: "POST",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({
                        "table_id": table_id,
                        "ip_col": data.field.ip_column
                    }),
                    beforeSend: () => {
                        loadIndex = layer.load(2);
                    },
                    success: (res) => {
                        layer.close(loadIndex);
                        if (res.code === 0) {
                            layer.close(index)
                            layer.msg("绑定成功", { icon: 1 });
                        } else if (res.code === 302) {
                            window.location.href = res.message;
                        } else {
                            layer.msg(`绑定失败: ${res.message}`, { icon: 2 });
                        }
                        return false;
                    },
                    error: (err) => {
                        layer.close(loadIndex);
                        let errMsg = err.responseJSON || JSON.parse(err.responseText);
                        layer.msg(errMsg.message, { icon: 2 });
                        return false;
                    }
                })
                localStorage.setItem("ip_col", JSON.stringify({"field": data.field.ip_column, "title": option_obj[data.field.ip_column]}));
            });
        }
    });
}
