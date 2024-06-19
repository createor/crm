// user_iframe.js
// iframe调用父页面方法

// 绑定进度条步骤
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

// 文本输入长度
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
        content: `<div class="layui-container" style="width: 100%;height: 100%;padding-top: 10px;">
                    <div id="stepProgressBar"></div>
                    <div class="stepContent layui-form" style="padding-top: 10px;text-align: left;">
                        <div class="layui-form-item">
                            <div class="layui-inline">
                                <label class="layui-form-label" style="width: 100px;">表名(必填)</label>
                                <div class="layui-input-inline" style="width: 250px;">
                                    <input type="text" name="mangeName" id="manageName" autocomplete="off" lay-verify="required" placeholder="请输入中文名称" class="layui-input">
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
                acceptMime: "application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                exts: "xlsx|xls",
                choose: function (obj) {
                    obj.preview(function(_,file) {
                        uploadFilename = file.name;
                    });
                },
                before: function () {
                    layerIndex = layer.load();
                },
                done: function (data) {
                    layer.close(layerIndex);
                    if (data.code === 0) {
                        // 写入filename
                        $("input[name='filename']").val(data.message);
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
                            "table_name": $("input[name='emanegName']").val(),
                            "mode": $("input[name='mode']:checked").val(),
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
                                    <span style='margin-left: -10px;font-size: 20px;'>创建失败</span>");
                            }
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

// 新增图表规则
var addNewRule = function (tableId) {
    $.ajax({
        url: "/crm/api/v1/manage/header",   // 获取资产表字段
        type: "get",
        success: function (data) {
            let option_template = "";
            data.message.forEach(item => {
                option_template += `<option value="${item.id}">${item.name}</option>`;
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
                                            <div class="layui-input-inline" style="width:100%;">
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
                                            <div class="layui-input-inline" style="width:100%;">
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
                                            <div class="layui-input-inline" style="width:100%;">
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
                    element.on("tab(ruleTab)", function(data) {
                        $(".layui-tab-content .layui-tab-item").each(function(){
                            $(this).removeClass("layui-show");
                        });
                        $(".layui-tab-content .layui-tab-item").eq(data.index).addClass("layui-show");
                    });
                    form.on('submit(updateChart)', function(data) {
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
    })
}

// 手动录入数据
var addNewData = function (tableId, header) {
    layer.open({
        type: 1,
        title: "新增数据",
        area: ["500px", "300px"],
        content: `<div>
                    <form class="layui-form">
                        <div class="layui-form-item"></div>
                        <div class="layui-form-item"></div>
                    </form>
                  </div>`,
        success: function () {
            form.render();
        }
    });
}

// 修改列
var alterCol = function (tableId) {
}

// 新增列
var addNewCol = function (tableId) {
    layer.open({
        type: 1,
        title: "新增列",
        area: ["500px", "400px"],
        content: `<div>
                    <form class="layui-form" style="margin-top: 10px;">
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 85px;">列名</label>
                            <div class="layui-input-block">
                                <input type="text" name="col_name" lay-verify="required" autocomplete="off" class="layui-input" style="width: 200px;">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 85px;">列名</label>
                            <div class="layui-input-block">
                                <input type="text" name="col_name_en" lay-verify="required" autocomplete="off" class="layui-input" style="width: 200px;">
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <label class="layui-form-label" style="width: 85px;">数据类型</label>
                            <div class="layui-input-block">
                                <input type="radio" name="data_type" value="1" title="文本" checked>
                                <input type="radio" name="data_type" value="2" title="日期">
                                <input type="radio" name="data_type" value="3" title="下拉列表">
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
            form.on("submit(addNewCol)", function (){
                let field = data.field;
                $.ajax({
                    url: "",
                    type: "post",
                    data: field,
                    success: function (res) {
                        if (res.code === 200) {
                            layer.msg(res.msg, {icon: 1, time: 1000}, function () {
                                layer.closeAll();
                                window.location.reload();
                            });
                        } else {
                            layer.msg(res.msg, {icon: 2, time: 1000});
                        }
                    }
                });
            })
        }
    })
}

// 
var mulitDetect = function (tableId) {
    $.ajax({
        url: `/crm/api/v1/manage/${tableId}/head?type=1`,
        type: "get",
        success: function (data) {
            if (data.code === 0) {
                if (data.message.length === 0) {
                    layer.msg("未找到相关字段", {icon: 3});
                    return false;
                } else {
                    let option_template = "";
                    layer.open({
                        type: 1,
                        title: "Ping探测任务",
                        area: ["500px", "300px"],
                        content: `<div>
                                    <form class="layui-form">
                                        <div class="layui-form-item">
                                            <label class="layui-form-label">IP列</label>
                                            <div class="layui-input-inline">
                                                <select name="ip_col" lay-verify="required">
                                                    <option value="">请选择IP列</option>
                                                    ${option_template}
                                                </select>
                                            </div>
                                        </div>
                                        <div class="layui-form-item">
                                            <button class="layui-btn" lay-submit lay-filter="createTask">创建任务</button>
                                        </div>
                                    </form>
                                  </div>`,
                        success: function () {
                            form.render();
                            if (!$().val()) {
                                layer.msg("请选择IP列", { icon: 2 });
                                return false;
                            }
                            form.on("submit(createTask)", function() {

                                return false;
                            });
                        }
                    });
                }
            }
        },
        error: function (err) {
            let errMsg = err.responseJSON || JSON.parse(err.responseText);
            layer.msg(errMsg.message, {icon: 2});
            return false;
        }
    });
}

//
var createNotify = function (tableId) {
    $.ajax({
        url: "/crm/api/v1/manage/",
        type: "get",
        success: function (data) {
            let option_template = "";
            layer.open({
                type: 1,
                title: "到期提醒任务",
                area: ["500px", "300px"],
                content: `<div>
                            <form class="layui-form">
                                <div class="layui-form-item">
                                    <label class="layui-form-label">时间列</label>
                                </div>
                                <div class="layui-form-item">
                                    <button class="layui-btn">创建任务</button>
                                </div>
                            </form>
                          </div>`,
                success: function () {}
            });
        }
    });
}
