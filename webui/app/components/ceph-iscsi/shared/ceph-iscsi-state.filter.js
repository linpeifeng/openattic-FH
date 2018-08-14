/**
 *
 * @source: http://bitbucket.org/openattic/openattic
 *
 * @licstart  The following is the entire license notice for the
 *  JavaScript code in this page.
 *
 * Copyright (c) 2017 SUSE LLC
 *
 *
 * The JavaScript code in this page is free software: you can
 * redistribute it and/or modify it under the terms of the GNU
 * General Public License as published by the Free Software
 * Foundation; version 2.
 *
 * This package is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * As additional permission under GNU GPL version 2 section 3, you
 * may distribute non-source (e.g., minimized or compacted) forms of
 * that code without the copy of the GNU GPL normally required by
 * section 1, provided you include this license notice and a URL
 * through which recipients can access the Corresponding Source.
 *
 * @licend  The above is the entire license notice
 * for the JavaScript code in this page.
 *
 */
"use strict";

export default () => {
  return (value) => {
    switch (value) {
      case "启动中":
        return "<i class=\"fa fa-spinner fa-spin fa-fw\"></i><span> 启用中...</span>";
      case "停止中":
        return "<i class=\"fa fa-spinner fa-spin fa-fw\"></i><span> 停止中...</span>";
      case "运行中":
        return "<span> 已启用</span>";
      case "告警":
        return "<i class=\"fa fa-exclamation-triangle icon-warning\"></i><span> 已启用</span>";
      case "已停止":
        return "<i class=\"fa fa-angle-double-down fa-lg icon-danger\"></i><span> 未启用</span>";
      case "加载中":
        return "<i class=\"fa fa-spinner fa-spin fa-fw\"></i><span> 加载中...</span>";
      default:
        return "<span>未知</span>";
    }
  };
};
