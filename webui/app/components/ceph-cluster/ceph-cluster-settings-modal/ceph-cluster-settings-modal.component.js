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

class cephClusterSettingsModal {

  constructor (cephClusterService) {
    this.cephClusterService = cephClusterService;

    this.model = undefined;
    this.data = {
      osd_flags: {
        "noin": {
          name: "离线",
          value: false,
          description: "OSD节点在服务启动时会被标记为离线"
        },
        "noout": {
          name: "强制在线",
          value: false,
          description: "不检查OSD节点磁盘状态，标记为在线"
        },
        "noup": {
          name: "暂停",
          value: false,
          description: "暂停OSD节点的服务"
        },
        "nodown": {
          name: "故障忽略",
          value: false,
          description: "忽略OSD产生的故障报告，标记OSD服务状态正常"
        },
        "pause": {
          name: "暂停读写",
          value: false,
          description: "暂停该OSD节点读写"
        },
        "noscrub": {
          name: "禁用洗刷（Scrub）",
          value: false,
          description: "禁用洗刷"
        },
        "nodeep-scrub": {
          name: "禁用深层洗刷（Deep Scrub）",
          value: false,
          description: "禁用深层洗刷"
        },
        "nobackfill": {
          name: "暂停回填",
          value: false,
          description: "暂停OSD节点中PG数据变化的回填"
        },
        "norecover": {
          name: "暂停数据平衡",
          value: false,
          description: "暂停OSD节点中PG数据副本异常的数据平衡"
        }
      }
    };
  }

  $onInit () {
    this.cephClusterService.get({
      fsid: this.resolve.fsid
    })
      .$promise
      .then((res) => {
        this.model = res;

        res.osd_flags.forEach((value) => {
          if (this.data.osd_flags[value]) {
            this.data.osd_flags[value].value = true;
          }
        });
      })
      .catch((error) => {
        this.error = error;
      });
  }

  submitAction () {
    let requestModel = _.cloneDeep(this.model);
    let allFlags = Object.keys(this.data.osd_flags);
    requestModel.osd_flags =
      requestModel.osd_flags.filter(flag => !allFlags.includes(flag));

    _.forIn(this.data.osd_flags, (flag, key) => {
      if (flag.value) {
        requestModel.osd_flags.push(key);
      }
    });

    this.cephClusterService.update(requestModel)
      .$promise
      .then(() => {
        this.modalInstance.dismiss("cancel");
      }, () => {
        this.clusterForm.$submitted = false;
      });
  }

  cancel () {
    this.modalInstance.dismiss("cancel");
  }
}

export default {
  template: require("./ceph-cluster-settings-modal.component.html"),
  bindings: {
    modalInstance: "<",
    resolve: "<"
  },
  controller: cephClusterSettingsModal
};

