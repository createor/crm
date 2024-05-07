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
            title: "完成",
            code: "03"
        }
    ];
    stepprogress.render({
        elem: "#stepProgressBar",
        stepItems: stepItems,
        position: 0  // 起始位置0
    });
}

var addNewTable = function () {
    // 新建资产表 
    layer.open({
        type: 1,
        area: ["500px", "300px"],
        title: "新建资产表",
        shade: 0.6,
        shadeClose: true,
        content: `<div class="layui-container" style="width: 100%;height: 100%;padding-top: 10px;">
                    <div id="stepProgressBar"></div>
                    <div class="stepContent layui-form" style="padding-top: 10px;text-align: left;">
                        <div class="layui-form-item">
                            <div class="layui-inline">
                                <label class="layui-form-label">表名(必填)</label>
                                <div class="layui-input-inline">
                                    <input type="text" name="mangeName" id="manageName" autocomplete="off" lay-verify="required" placeholder="" class="layui-input">
                                </div>
                            </div>
                        </div>
                        <div class="layui-form-item">
                            <div class="layui-inline">
                                <label class="layui-form-label">表别名(必填)</label>
                                <div class="layui-input-inline">
                                    <input type="text" name="emanegName" id="emanegName" autocomplete="off" lay-verify="required|isEnglish" placeholder="仅支持英文组成" class="layui-input">  
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="stepContent layui-form">
                        <div style="padding: 10px 0;">
                            <span>表格导入数据(可选)</span>
                        </div>
                        <div class="layui-upload-drag" style="display: block;width: 50%;height: 30%;margin-left: 19%;padding-top: 15px;" id="uploadExcel">
                            <i class="layui-icon layui-icon-upload"></i> 
                            <div>点击上传，或将文件拖拽到此处</div>
                        </div>
                    </div>
                    <div class="stepContent layui-form">
                       <div style="padding: 15px 0;margin-left: -10px;">
                            <i class="layui-icon layui-icon-loading layui-anim layui-anim-rotate layui-anim-loop" style="font-size: 60px;"></i>
                       </div>
                       <span style='margin-left: -10px;'>创建中</span>
                    </div>
                    <div class="layui-btn-container">
                        <div style="text-align: center;margin-top: 10px;">
	                        <button type="button" id="pre" class="layui-btn layui-btn-sm" style="margin: 0 20px;">上一步</button>
	                        <button type="button" id="next" class="layui-btn layui-btn-sm" style="margin: 0 20px;">下一步</button>
                            <button type="button" id="rightUse" class="layui-btn layui-btn-sm" style="display: none;">立即使用</button>
                        </div>
                    </div> 
                  </div>`,
        success: function () {
            form.render();
            form.verify({
                isEnglish: function(value) {
                    if (!value) return;
                    if (!(/^[A-Za-z]+$/.test(value))) {
                        return "只能由英文组成";
                    }
                }
            });
            let currIndex = 0;
            $("#pre").hide();
            $(".stepContent").eq(0).show();
            renderStepProgress();
            $("#next").click(function(){
                if (currIndex === 0) {
                    let isEmpty = form.validate("#manageName");
                    let isValid = form.validate("#emanegName");
                    if (!isEmpty) {
                        return false;
                    }
                    if (!isValid) {
                        return false;
                    }
                }
                currIndex += 1;
		        stepprogress.next('stepProgressBar');
	        });
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
                    $("#pre").hide();
                    $("#next").show();
                    return false;
                }
                if (options.position == 1) {
                    $(".stepContent").eq(0).hide();
                    $(".stepContent").eq(1).show();
                    $(".stepContent").eq(2).hide();
                    $("#pre").show();
                    $("#next").show();
                    return false;
                }
                if (options.position == 2) {
                    $(".stepContent").eq(0).hide();
                    $(".stepContent").eq(1).hide();
                    $(".stepContent").eq(2).show();
                    $("#pre").hide();
                    $("#next").hide();
                    $.ajax({
                        url: "/crm/api/v1/manage/add",
                        type: "post",
                        success: function (data) {
                            if (data.code === 0) {
                                // 将load换成打勾表示完成
                                $(".stepContent").eq(2).html("<div style='padding: 15px 0;margin-left: -10px;'> \
                                    <i class='layui-icon layui-icon-success' style='font-size: 60px;color: green;'></i> \
                                    </div> \
                                    <span style='margin-left: -10px;'>完 成</span>");
                                stepprogress.next('stepProgressBar');
                                $("#rightUse").show();
                            } else {
                                $(".stepContent").eq(2).html("<div style='padding: 15px 0;margin-left: -10px;'> \
                                    <i class='layui-icon layui-icon-error' style='font-size: 60px;color: red;'></i> \
                                    </div> \
                                    <span style='margin-left: -10px;'>失 败</span>");
                            }
                        }
                    });
                    return false;
                }
            });
        }
    });
    return false;
}
