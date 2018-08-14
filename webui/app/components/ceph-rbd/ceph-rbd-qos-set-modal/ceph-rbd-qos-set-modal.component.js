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
 * redistribute it and/or modify it under th7e terms of the GNU
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
import globalConfig from "globalConfig";

class cephRbdQosSetActionModal {

  constructor ($scope, $http, $resource, $rootScope) {
    this.$scope = $scope;
    this.$http = $http;
    this.$rootScope = $rootScope;
    this.selectedData = this.resolve.selectedData;
    this.success = false;
    this.faild = false;
    this.$scope.placeholder = {
      ReadLimit: this.selectedData.length === 1 ? this.selectedData[0].name : 0,
      WriteLimit: this.selectedData.length === 1 ? this.selectedData[0].name : 0
    };
    this.poolidArray = [];
    this.res = $resource(globalConfig.API.URL + "test", {
      poolid: "@poolid",
      iopsqosread: "@iopsqosread",
      iopsqoswrite:"@iopsqoswrite"
    }, {
      postForm: {method:"POST"}
    });
  }
  $onInit () {
    console.log("13:27");
  }
  poolidName () {
    for (let x of this.selectedData) {
      this.poolidArray.push(x.name);
    }
    return this.poolidArray;
  }
  minus ($event) {
    let keyCode = $event.which || $event.keyCode;
    if (keyCode === 189) {
      console.log(keyCode);
      return false;
    }
  }
  submitForm () {
    if (this.$scope.Limit.ReadLimit === undefined || this.$scope.Limit.WriteLimit === undefined) {
      return;
    }
    this.res.postForm({
      poolid:this.poolidName(),
      iopsqosread:this.$scope.Limit.ReadLimit,
      iopsqoswrite:this.$scope.Limit.WriteLimit
    }).$promise
      .then((res) => {
        console.log(res);
        this.success = true;
        setTimeout(() => {
          this.closeQos();
        }, 2000);
      })
      .catch((req) => {
        console.log(req);
        this.faild = true;
        this.poolidArray = [];
        setTimeout(() => {
          this.faild = false;
        }, 2000);
      });
  }
  closeQos () {
    this.modalInstance.dismiss("cancel");
  }
}

export default {
  template: require("./ceph-rbd-qos-set-modal.component.html"),
  bindings: {
    modalInstance: "<",
    resolve: "<"
  },
  controller: cephRbdQosSetActionModal
};
