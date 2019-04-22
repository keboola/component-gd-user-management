# GoodData User Management Application

This application allows user of the component to manage users in the GoodData project, invite new users to the project, change roles and assign data permissions for each user.

## Overview

The application, as aforementioned, allows users to maintain access to a GoodData project and or manage users' access to certain data. The application uses GoodData API to assign [Data Permissions](https://help.gooddata.com/display/doc/Data+Permissions) to desired users, that automatically pre-filter available data to end-user.

### Prerequisities

**The following requirements are needed for successful conifguration of the application:**

* a GoodData project
* an admin account to the GoodData project

### Process overview

The application automatically determines what actions need to be taken for each user based on the table of users (see *input mapping* section). The process is ran row-by-row, i.e. all users are process sequentially, to avoid any confusion in the process. For each user, the application determines whether the user is already in the organization and/or project and acts accordingly on that, i.e. creates the user if necessary. To prevent any possible failure, all users are first disabled in the project, before assigning data permissions and re-enabling them again. If it's necessary, the application generates an invitation, which is delivered to the user.

### Process detail

Below is the more detailed description of the process.

1. User and all their data is read from the table.
2. User's login is compared to the list of users in GD project and list of users provisioned by Keboola.
   1. If the user is in both organization and project, they are disabled.
   2. If the user is in the organization but not in the project, nothing is done.
   3. If the user is not in the organization but is in the project, they are disabled.
   4. If the user is not in the organization nor the project, an attempt is made to create them in Keboola organization is made. If the attemp fails, the user is already part of another organization and will not be maintained in Keboola domain.
3. For each user, their `Mandatory User Filter (MUF)` expression is read and parsed into URI format. The URI format is a format, where all attribute names, labels and values are transformed to their URI counterparts. If the attribute, label or value does not exist, the URI expression is not created and an error is recorded in the status file.
4. The URI expression is posted to GoodData and the user filter is created. Each user filter is assigned unique ID, which is then passed on to users as an attribute.
5. The following action occurs once the user filter was created (follow-up to point 2):
   1. User is assigned the user filter and is re-enabled in the project.
   2. User is assigned the user filter and is added to the project.
   3. User is assigned the user fitler and is re-enabled in the project.
   4. User is assigned the user filter and is enabled/invited to the project.
6. Process ends.

## See also

The following two API references might be handy when working with the application:

* [Keboola GoodData Provisioning API](https://keboolagooddataprovisioning.docs.apiary.io/)
* [GoodData API Reference](https://help.gooddata.com/display/API/API+Reference)