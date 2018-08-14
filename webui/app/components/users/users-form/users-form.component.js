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

class UsersFormComponent {

  constructor ($state, $stateParams, usersService, $uibModal, $q, Notification, $rootScope) {
    this.usersService = usersService;
    this.Notification = Notification;
    this.$state = $state;
    this.inArray = $rootScope.inArray;

    let promises = [];

    this.isCurrentUser = false;

    if (!$stateParams.user) {
      this.editing = false;
      this.user = {
        "username": "",
        "email": "",
        "password": "",
        "confirmPassword": "",
        "first_name": "",
        "last_name": "",
        "is_active": false,
        "is_superuser": false,
        "is_staff": true
      };

      this.submitAction = (userForm) => {
        this.setPrivilegeArray();
        this.submitted = true;
        if (userForm.$valid === true) {
          usersService.save(this.user)
            .$promise
            .then(() => {
              this.goToListView();
            }, () => {
              this.userForm.$submitted = false;
            });
        }
      };
    } else {
      this.editing = true;

      promises.push(
        usersService.current().$promise
      );
      promises.push(
        usersService.get({id: $stateParams.user}).$promise
      );

      // Use $q.all to wait until all promises have been resolved
      $q.all(promises)
        .then((res) => {
          if (res[0].id === Number($stateParams.user)) {
            this.isCurrentUser = true;
          }
          this.user = res[1];
        });

      this.submitAction = (userForm) => {
        this.setPrivilegeArray();
        this.submitted = true;
        if (userForm.$valid === true) {
          usersService.update({id: this.user.id}, this.user)
            .$promise
            .then(() => {
              this.goToListView();
            }, () => {
              this.userForm.$submitted = false;
            });
        }
      };
    }
  }

  setPrivilegeArray () {
    //装配权限数组
    var privilegeArray = [];
    var userPermissions = document.getElementsByName("user_permissions");
    for (var j = 0; j < userPermissions.length; j++) {
      var privilege = userPermissions[j];
      if (privilege.checked) {
        privilegeArray.push(privilege.value);
      }
    }
    this.user.user_permissions = privilegeArray;
  }

  goToListView () {
    this.$state.go("users");
  }

  generateAuthToken () {
    let modalInstance = this.$uibModal.open({
      windowTemplate: require("../../../templates/messagebox.html"),
      component: "usersAuthTokenModalComponent",
      resolve: {
        user: () => {
          return this.user;
        }
      }
    });
    modalInstance.result.then((token) => {
      // Display the new token.
      this.user.auth_token.token = token;
      // Display a message.
      this.Notification.success({
        title: "API authentication token",
        msg: "The token has been created successfully."
      });
    });
  }

  cancelAction () {
    this.goToListView();
  }

  $onInit () {
    this.usersService.current()
      .$promise
      .then((res) => {
        this.currentUser = res;
      })
      .catch((error) => {
        error.ignoreStatusCode(401);
      });
  }
}

export default {
  controller: UsersFormComponent,
  template: require("./users-form.component.html")
};
