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

import _ from "lodash";

class CephSNMPModal {

  constructor (cephSNMPService) {
    this.cephSNMPService = cephSNMPService;
    this.snmp = {
      snmp_serverport: 162,
      snmp_version: "0",
      authmeth: "noAuthNoPriv",
      authprotocol: "MD5",
      privprotocol: "DES"
    };
  }

  $onInit () {
    this.cephSNMPService.get()
      .$promise
      .then((res) => {
        res.results.forEach((value) => {
          if (value.enabled) {
            if (value.snmp_serverip === "null") {
              value.snmp_serverip = "";
            }
            if (value.community_str === "null") {
              value.community_str = "";
            }
            if (value.engineid === "null") {
              value.engineid = "";
            }
            if (value.authuser === "null") {
              value.authuser = "";
            }
            if (value.authpasswd === "null") {
              value.authpasswd = "";
            }
            if (value.privpasswd === "null") {
              value.privpasswd = "";
            }
            this.snmp = value;
            return false;
          }
        });
      })
      .catch((error) => {
        this.error = error;
      });
  }

  submitAction (snmpForm) {
    let requestModel = _.cloneDeep(this.snmp);
    var instance = null;
    if (requestModel.id) {
      instance = this.cephSNMPService.update(requestModel);
    } else {
      instance = this.cephSNMPService.save(requestModel);
    }
    instance
      .$promise
      .then(() => {
        this.modalInstance.dismiss("cancel");
      }, () => {
        snmpForm.$submitted = false;
      });
  }

  cancel () {
    this.modalInstance.dismiss("cancel");
  }
}

export default {
  template: require("./ceph-snmp-modal.component.html"),
  bindings: {
    modalInstance: "<",
    resolve: "<"
  },
  controller: CephSNMPModal
};

