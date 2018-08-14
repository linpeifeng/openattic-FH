"use strict";

export default () => {
  return (value) => {

    if (value === "POST") {
      return "创建";
    }
    if (value === "DELETE") {
      return "删除";
    }
    if (value === "PUT") {
      return "变更";
    }
    if (value === "INFO") {
      return "成功";
    }
    if (value === "ERROR") {
      return "失败";
    }
    if (value === "LOGIN") {
      return "登录";
    }
    if (value === "LOGOUT") {
      return "注销";
    }
    return "";
  };
};
