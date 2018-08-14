"use strict";

import "./ceph-log-list.component.css";

class cephLogListController {

  constructor (cephLogService) {
    this.cephLogService = cephLogService;
    this.data = {};
  }

  $onInit () {
    this.getLogList();
  }

  getLogList () {
    this.cephLogService.get({
      search: this.searchValue
    })
      .$promise
      .then((res) => {
        console.log(res);
        this.data = res;
      })
      .catch((error) => {
        this.error = error;
      });
  }
}

export default {
  template: require("./ceph-log-list.component.html"),
  controller: cephLogListController
};