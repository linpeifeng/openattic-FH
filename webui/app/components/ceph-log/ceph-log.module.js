"use strict";

// angular.module("openattic.cephLog", []);

// requireAll(require.context("./", true, /^(?!.*\.spec\.js$).*\.js$/));

// function requireAll (require) {
//   require.keys().forEach(require);
// }
import cephLogList from "./ceph-log-list/ceph-log-list.component";
import cephLogTypeFilter from "./shared/ceph-log-type.filter";

let app = angular.module("openattic.cephLog", []);

require("./ceph-log.route");
require("./services/ceph-log.service");

app.component("cephLogList", cephLogList)
  .filter("cephLogTypeFilter", cephLogTypeFilter);
