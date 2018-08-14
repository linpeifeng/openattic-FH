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

export default ($stateProvider) => {
  $stateProvider
    .state("cephOsds", {
      url: "/ceph/osds",
      views: {
        "main": {
          component: "cephOsdList"
        }
      },
      ncyBreadcrumb: {
        label: "Ceph OSD"
      }
    })
    .state("cephOsds.detail", {
      views: {
        "tab": {
          component: "oaTabSet"
        }
      },
      ncyBreadcrumb: {
        skip: true
      }
    })
    .state("cephOsds.detail.details", {
      url: "/details",
      views: {
        "tab-content": {
          template: require("./ceph-osd-detail/ceph-osd-detail.component.html")
        }
      },
      ncyBreadcrumb: {
        label: "{{$ctrl.selection.item.name}} details"
      }
    })
    .state("cephOsds.detail.statistics", {
      url: "/statistics",
      views: {
        "tab-content": {
          template: require("./ceph-osd-statistics/ceph-osd-statistics.component.html")
        }
      },
      ncyBreadcrumb: {
        label: "{{$ctrl.selection.item.name}} statistics"
      }
    });
};
