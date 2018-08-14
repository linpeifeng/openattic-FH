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

export default {
  "deep-flatten": {
    desc: "Deep flatten（快照扁平化操作）",
    helpText: "",
    requires: null,
    excludes: null,
    isSupportedISCSI: false,
    isDisplayed: true
  },
  "layering": {
    desc: "Layering（分层）",
    helpText: "",
    requires: null,
    excludes: null,
    isSupportedISCSI: true,
    isDisplayed: true
  },
  "stripingv2": {
    desc: "Striping（条带化）",
    helperTemplate: "components/ceph-rbd/ceph-rbd-form/ceph-rbd-form-helper-striping.html",
    requires: null,
    excludes: null,
    isSupportedISCSI: false,
    isDisplayed: true
  },
  "exclusive-lock": {
    desc: "Exclusive lock（独占锁）",
    helpText: "",
    requires: null,
    excludes: null,
    isSupportedISCSI: false,
    isDisplayed: true
  },
  "object-map": {
    desc: "Object map（对象映射）（需独占锁）",
    helpText: "",
    requires: "exclusive-lock",
    excludes: null,
    isSupportedISCSI: false,
    isDisplayed: true
  },
  "journaling": {
    desc: "Journaling（记录IO操作）（需独占锁）",
    helpText: "",
    requires: "exclusive-lock",
    excludes: null,
    isSupportedISCSI: false,
    isDisplayed: true
  },
  "fast-diff": {
    desc: "Fast diff（快速计算差异）（需对象映射）",
    helperTemplate: "components/ceph-rbd/ceph-rbd-form/ceph-rbd-form-helper-fast-diff.html",
    requires: "object-map",
    excludes: null,
    isSupportedISCSI: false,
    isDisplayed: true
  },
  "data-pool": {
    desc: "Data pool（数据池）",
    helpText: "",
    requires: null,
    excludes: null,
    isSupportedISCSI: true,
    isDisplayed: false
  }
};
