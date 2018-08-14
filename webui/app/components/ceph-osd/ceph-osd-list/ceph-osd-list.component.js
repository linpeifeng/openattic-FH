/**
 *
 * @source: http://bitbucket.org/openattic/openattic
 *
 * @licstart  The following is the entire license notice for the
 *  JavaScript code in this page.
 *
 * Copyright (C) 2011-2016, it-novum GmbH <community@openattic.org>
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
import globalConfig from "globalConfig";

class CephOsdList {
  constructor ($state, $filter, $uibModal, cephOsdService, registryService, $resource,
      oaTabSetService, $timeout) {
    this.$timeout = $timeout;
    this.$state = $state;
    this.$filter = $filter;
    this.$uibModal = $uibModal;
    this.cephOsdService = cephOsdService;
    this.registryService = registryService;
    this.DRsuccess = false;
    this.DRerror = false;
    this.DRwait = false;

    this.registry = registryService;
    this.$resource = $resource;
    this.cluster = undefined;
    this.oaTabSetService = oaTabSetService;
    this.osd = {};
    this.selection = {};
    this.tabData = {
      active: 0,
      tabs: {
        status: {
          show: () => _.isObjectLike(this.selection.item),
          state: "cephOsds.detail.details",
          class: "tc_statusTab",
          name: "Status"
        },
        statistics: {
          show: () => _.isObjectLike(this.selection.item),
          state: "cephOsds.detail.statistics",
          class: "tc_statisticsTab",
          name: "Statistics"
        }
      }
    };
    this.tabConfig = {
      type: "cephOsds",
      linkedBy: "id",
      jumpTo: "more"
    };

    this.filterConfig = {
      page     : 0,
      entries  : 10,
      search   : "",
      sortfield: null,
      sortorder: null
    };

    this.res = $resource(globalConfig.API.URL + "disk_roam", {
      name: "@name",
      hostname:"@hostname"
    }, {
      postOsd: {
        method: "POST",
        headers:{
          "Content-Type": "application/json;  charset=UTF-8"
        },
        interceptor: {
          response: function (response) {
            var result = response.resource;
            result.$status = response.status;
            return result;
          }
        }
      }
    });
  }

  onClusterLoad (cluster) {
    this.cluster = cluster;
  }

  getOsdList () {
    if (_.isObjectLike(this.cluster) && this.cluster.results &&
      this.cluster.results.length > 0 && this.registry.selectedCluster) {
      let obj = this.$filter("filter")(this.cluster.results, {
        fsid: this.registry.selectedCluster.fsid
      }, true);
      if (obj.length === 0) {
        this.registry.selectedCluster = this.cluster.results[0];
      }
      this.osd = {};
      this.error = false;
      this.cephOsdService
        .get({
          fsid: this.registry.selectedCluster.fsid,
          page: this.filterConfig.page + 1,
          pageSize: this.filterConfig.entries,
          search: this.filterConfig.search,
          ordering: (this.filterConfig.sortorder === "ASC" ? "" : "-") + this.filterConfig.sortfield
        })
        .$promise
        .then((res) => {
          this.osd = res;
        })
        .catch((error) => {
          this.error = error;
        });
    }
  }

  onSelectionChange (selection) {
    if (selection.item) {
      this.$resource(globalConfig.API.URL + "disk_info/" + selection.item.name)
        .get({})
        .$promise
        .then(response => {
          console.log(response);
          this.selection.info = response;
          this.selection.info.otherinfo =
            this.selection.info.otherinfo === "null" || !this.selection.info.otherinfo ?
              "-" :
              this.selection.info.otherinfo;
          this.selection.StatusError = false;
          this.selection.StatusSuccess = true;
        })
        .catch(error => {
          console.log(error);
          this.selection.StatusSuccess = false;
          this.selection.StatusError = true;
          return false;
          return;
        });
    } else {
      return;
    }
    this.selection = selection;
    let item = selection.item;
    let items = selection.items;

    this.multiSelection = Boolean(items) && items.length > 1;
    this.hasSelection = Boolean(item);

    if (!items || items.length !== 1) {
      this.$state.go("cephOsds");
      return;
    }
    if (this.$state.current.name === "cephOsds") {
      this.oaTabSetService.changeTab("cephOsds.detail.details", this.tabData,
        this.tabConfig, selection);
    } else {
      this.oaTabSetService.changeTab(this.$state.current.name, this.tabData,
        this.tabConfig, selection);
    }
  }

  configureClusterAction () {
    this.$uibModal.open({
      windowTemplate: require("../../../templates/messagebox.html"),
      component: "cephClusterSettingsModal",
      resolve: {
        fsid: () => {
          return this.registry.selectedCluster.fsid;
        }
      }
    });
  }

  DiskRoamingSetAction () {
    this.res.postOsd({
      name: this.selection.item.name,
      hostname: this.selection.item.hostname
    }).$promise
      .then((response) => {
        console.log(response);
        if (response.$status === 200) {
          this.DRwait = true;
          this.$timeout(() => {
            this.DRwait = false;
            this.DRsuccess = true;
          }, 1000);
          this.$timeout(() => {
            this.DRsuccess = false;
          }, 2000);
        } else {
          this.DRwait = true;
          this.$timeout(() => {
            this.DRwait = false;
            this.DRerror = true;
          }, 1000);
          this.$timeout(() => {
            this.DRerror = false;
          }, 2000);
        }
      })
      .catch(() => {
        this.DRwait = true;
        this.$timeout(() => {
          this.DRwait = false;
          this.DRerror = true;
        }, 1000);
        this.$timeout(() => {
          this.DRerror = false;
        }, 2000);
      });
  }
  scrubAction (deep) {
    if (!this.hasSelection) {
      return;
    }
    let modalInstance = this.$uibModal.open({
      windowTemplate: require("../../../templates/messagebox.html"),
      component: "cephOsdScrubModal",
      resolve: {
        osd: () => {
          return this.selection.item;
        },
        deep: () => {
          return deep;
        }
      }
    });
    modalInstance.result.then(() => {
      this.filterConfig.refresh = new Date();
    });
  }
}

export default {
  template: require("./ceph-osd-list.component.html"),
  controller: CephOsdList
};
