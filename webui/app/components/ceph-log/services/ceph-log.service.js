"use strict";

import globalConfig from "globalConfig";

var app = angular.module("openattic.cephLog");

app.factory("cephLogService", function ($resource) {
  const debug = false;
  return $resource(debug ? "/mock-data/mock-log.json" : globalConfig.API.URL + "logging?format=json");
});
