/**
 * 
 * @source: http://bitbucket.org/openattic/openattic
 * 
 * @licstart The following is the entire license notice for the JavaScript code
 *           in this page.
 * 
 * Copyright (c) 2017 SUSE LLC
 * 
 * 
 * The JavaScript code in this page is free software: you can redistribute it
 * and/or modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; version 2.
 * 
 * This package is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details.
 * 
 * As additional permission under GNU GPL version 2 section 3, you may
 * distribute non-source (e.g., minimized or compacted) forms of that code
 * without the copy of the GNU GPL normally required by section 1, provided you
 * include this license notice and a URL through which recipients can access the
 * Corresponding Source.
 * 
 * @licend The above is the entire license notice for the JavaScript code in
 *         this page.
 * 
 */
"use strict";

// import _ from "lodash";

class CephAlertsList {

  constructor (
      $filter,
      $state,
      $uibModal,
      cephAlertsService,
      $scope,
      $interval) {
    this.$filter = $filter;
    this.$state = $state;
    this.$uibModal = $uibModal;
    this.interval = $interval;
    this.cephAlertsService = cephAlertsService;
    this.selection = {};
    /**
	 * 响应体，包含至少count（未分页的数量）和results属性
	 */
    this.alerts = {};
    /**
	 * 处理分页、搜索与排序
	 */
    this.filterConfig = {
      page     : 0,
      entries  : 10,
      search   : "",
      sortfield: null,
      sortorder: null
    };

    var instance = this;
    var pollPromise = $interval(function () {
      instance.getAlertsList();
    }, 2000);
    $scope.$on("$destroy", function () {
      $interval.cancel(pollPromise);
    });
  }

  /**
	 * 获取报警列表
	 */
  getAlertsList () {
    this.cephAlertsService
      .get({
        page: this.filterConfig.page + 1,
        pageSize: this.filterConfig.entries,
        search: this.filterConfig.search,
        ordering: (this.filterConfig.sortorder === "ASC" ? "" : "-") + this.filterConfig.sortfield
      }).$promise.then((res) => {
        this.alerts = res;
      }).catch((error) => {
        error.ignoreStatusCode(404);
      });
  }

  snmpAction () {
    this.$uibModal.open({
      windowTemplate: require("../../../templates/messagebox.html"),
      component: "cephSNMPModal"
    });
  }

}

export default {
  template: require("./ceph-alerts-list.component.html"),
  controller: CephAlertsList
};
