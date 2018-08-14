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

export default ($stateProvider) => {
  $stateProvider
    .state("ceph-rgw", {
      url: "/ceph/rgw",
      ncyBreadcrumb: {
        label: "Object Gateway"
      }
    })
    .state("ceph-rgw-users", {
      url: "/ceph/rgw/users",
      views: {
        "main": {
          component: "cephRgwUserList"
        }
      },
      ncyBreadcrumb: {
        label: "对象网关用户"
      }
    })
    .state("ceph-rgw-users.detail", {
      views: {
        "tab": {
          component: "oaTabSet"
        }
      },
      ncyBreadcrumb: {
        skip: true
      }
    })
    .state("ceph-rgw-users.detail.details", {
      url: "/details",
      views: {
        "tab-content": {
          component: "cephRgwUserDetail"
        }
      },
      ncyBreadcrumb: {
        label: "{{selection.item.user_id}} 详情"
      }
    })
    .state("ceph-rgw-users.detail.statistics", {
      url: "/statistics",
      views: {
        "tab-content": {
          component: "cephRgwUserStatistics"
        }
      },
      ncyBreadcrumb: {
        label: "{{selection.item.user_id}} 统计"
      }
    })
    .state("ceph-rgw-user-add", {
      url: "/ceph/rgw/users/add",
      views: {
        "main": {
          component: "cephRgwUserForm"
        }
      },
      ncyBreadcrumb: {
        parent: "ceph-rgw-users",
        label: "添加"
      }
    })
    .state("ceph-rgw-user-edit", {
      url: "/ceph/rgw/users/edit/:user_id",
      views: {
        "main": {
          component: "cephRgwUserForm"
        }
      },
      ncyBreadcrumb: {
        parent: "ceph-rgw-users",
        label: "编辑 {{user.user_id}}"
      }
    })
    .state("ceph-rgw-buckets", {
      url: "/ceph/rgw/buckets",
      params: {
        page: undefined,
        entries: undefined,
        search: undefined,
        sortfield: undefined,
        sortorder: undefined
      },
      views: {
        "main": {
          component: "cephRgwBucketList"
        }
      },
      ncyBreadcrumb: {
        label: "对象网关bucket"
      }
    })
    .state("ceph-rgw-buckets.detail", {
      views: {
        "tab": {
          component: "oaTabSet"
        }
      },
      ncyBreadcrumb: {
        skip: true
      }
    })
    .state("ceph-rgw-buckets.detail.details", {
      url: "/details",
      views: {
        "tab-content": {
          component: "cephRgwBucketDetail"
        }
      },
      ncyBreadcrumb: {
        label: "{{selection.item.bucket}} 详情"
      }
    })
    .state("ceph-rgw-bucket-add", {
      url: "/ceph/rgw/buckets/add",
      views: {
        "main": {
          component: "cephRgwBucketForm"
        }
      },
      ncyBreadcrumb: {
        parent: "ceph-rgw-buckets",
        label: "添加"
      }
    })
    .state("ceph-rgw-bucket-edit", {
      url: "/ceph/rgw/buckets/edit/:bucket",
      views: {
        "main": {
          component: "cephRgwBucketForm"
        }
      },
      ncyBreadcrumb: {
        parent: "ceph-rgw-buckets",
        label: "编辑 {{bucket.bucket}}"
      }
    });
};
