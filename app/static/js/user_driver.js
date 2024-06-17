// user_driver module
// 普通用户的引导模块

function user_driver($, fn) {
    'use strict'
    const driver = window.driver.js.driver;
    const driverObj = driver({
            showProcess: true,
            allowClose: false,
            disableActiveInteraction: true,
            nextBtnText: "下一步",
            prevBtnText: "上一步",
            doneBtnText: "我知道啦",
            onHighlightStarted: () => {
                $(".guide").show();
            },
            onDestroyed: () => {
                $(".guide").hide();
                $(".layui-layout-right .layui-nav-item .layui-nav-child").removeClass("layui-show");  // 移除样式
                fn();
                $.ajax({
                    url: "/crm/api/v1/user/first",
                    type: "get"
                });
            },
            steps: [
                {
                    element: ".guide",
                    popover: {
                        title: "新手引导",
                        description: "欢迎使用新手引导",
                        onNextClick: () => {
                            driverObj.moveNext();
                            $(".guide").hide();
                        }
                    }
                },
                {
                    element: ".manual",
                    popover: {
                        title: "使用手册",
                        description: "下载使用手册查看如何使用本系统",
                        onPrevClick: () => {
                            driverObj.movePrevious();
                            $(".guide").show();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").removeClass("layui-show");
                        },
                        onNextClick: () => {
                            driverObj.moveNext();
                            $(".guide").hide();
                        }
                    }
                },
                {
                    element: ".layui-layout-right .layui-nav-item",
                    popover: {
                        title: "用户信息",
                        description: "展示用户头像和用户名",
                        onPrevClick: () => {
                            driverObj.movePrevious();
                            $(".guide").hide();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").removeClass("layui-show");
                        },
                        onNextClick: () => {
                            driverObj.moveNext();
                            $(".guide").hide();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").addClass("layui-show");
                        }
                    }
                },
                {
                    element: "#information",
                    popover: {
                        title: "用户资料",
                        description: "查看和修改用户的资料",
                        onPrevClick: () => {
                            driverObj.movePrevious();
                            $(".guide").hide();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").removeClass("layui-show");
                        },
                        onNextClick: () => {
                            driverObj.moveNext();
                            $(".guide").hide();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").addClass("layui-show");
                        }
                    }
                },
                {
                    element: "#setPassword",
                    popover: {
                        title: "修改密码",
                        description: "用户修改密码",
                        onPrevClick: () => {
                            driverObj.movePrevious();
                            $(".guide").hide();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").addClass("layui-show");
                        },
                        onNextClick: () => {
                            driverObj.moveNext();
                            $(".guide").hide();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").addClass("layui-show");
                        }
                    }
                },
                {
                    element: "#quit",
                    popover: {
                        title: "退出登录",
                        description: "用户退出登录",
                        onPrevClick: () => {
                            driverObj.movePrevious();
                            $(".guide").hide();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").addClass("layui-show");
                        },
                        onNextClick: () => {
                            driverObj.moveNext();
                            $(".guide").hide();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").removeClass("layui-show");
                        }
                    }
                },
                {
                    element: ".layui-side .layui-nav-item:nth-child(1)",
                    popover: {
                        title: "资产管理",
                        description: "资产管理菜单选择",
                        onPrevClick: () => {
                            driverObj.movePrevious();
                            $(".guide").hide();
                            $(".layui-layout-right .layui-nav-item .layui-nav-child").addClass("layui-show");
                        },
                    }
                }
            ]
    });
    driverObj.drive();
}

