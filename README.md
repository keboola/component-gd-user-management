# GoodData User Management Application

This application allows user of the component to manage users in the GoodData project, invite new users to the project, change roles and assign data permissions for each user.

## Overview

The application, as aforementioned, allows users to maintain access to a GoodData project and or manage users' access to certain data. The application uses GoodData API to assign [Data Permissions](https://help.gooddata.com/display/doc/Data+Permissions) to desired users, that automatically pre-filter available data to end-user.

### Prerequisities

**The following requirements are needed for successful conifguration of the application:**

* a GoodData project
* an admin account to the GoodData project

### Status file

All actions performed by the application are automatically recorded to a status file. The file is incrementally auto-saved to `out.c-GDUserManagement.status` table. All actions contain information on whether said action was successful and any additional information, which are the result of taking the action.

### Process overview

The application automatically determines what actions need to be taken for each user based on the table of users (see *input mapping* section). The process is ran row-by-row, i.e. all users are processed sequentially, to avoid any confusion in the process. For each user, the application determines whether the user is already in the organization and/or project and acts accordingly on that, i.e. creates the user if necessary. To prevent any possible failure, all users are first disabled in the project, before assigning data permissions and re-enabling them again. If it's necessary, the application generates an invitation, which is delivered to the user on the provided e-mail address.

### Process detail

Below is a more detailed description of the process.

1. User and all their data is read from the table.
2. User's login is compared to the list of users in GD project and list of users provisioned by Keboola.
   1. If the user is in both organization and project, they are disabled.
   2. If the user is in the organization but not in the project, nothing is done.
   3. If the user is not in the organization but is in the project, they are disabled.
   4. If the user is not in the organization nor the project, an attempt is made to create them in Keboola organization. If the attemp fails, the user is already part of another organization and will not be maintained in Keboola domain.
3. For each user, their `Mandatory User Filter (MUF)` expression is read and parsed into URI format. The URI format is a format, where all attribute names, labels and values are transformed to their URI counterparts. If the attribute, label or value does not exist, the URI expression is not created and an error is recorded in the status file.
4. The URI expression is posted to GoodData and the user filter is created. Each user filter is assigned unique ID, which is then passed on to users as an attribute.
5. The following action occurs once the user filter was created (follow-up to point 2):
   1. User is assigned the user filter and is re-enabled in the project.
   2. User is assigned the user filter and is added to the project.
   3. User is assigned the user fitler and is re-enabled to the project.
   4. User is assigned the user filter and is enabled/invited to the project.
6. Process ends.

## Input mapping

The application accepts 4 parameters and a table of users. In addition to the 4 parameters, the component automatically uses [Storage API Token](https://help.keboola.com/management/project/tokens/) to access available GoodData projects within the project and provision users. A sample configuration can be found [in the repository](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/4ec16093a0bbd39c2d4784d19eee17776ae6f968/component_config/sample-config/?at=master).

### Parameters

Following 4 parameters are accepted: `GD Login`, `GD Password`, `GD Project ID` and `GD Custom Domain`. More detailed description of all parameters is provided in the upcoming subsections.

A sample of the configuration file can be [found here](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/4ec16093a0bbd39c2d4784d19eee17776ae6f968/component_config/sample-config/config.json?at=master&fileviewer=file-view-default).

#### GD Login

The login email to the GoodData portal. Requirements for the used login are:

* must have access to the project
* must be admin of the project
* must not have any data permissions assigned to them.

Failure to comply with any of the above requirements will raise an error.

#### GD Password

The password to `GD Login` used to log in to GoodData portal.

#### GD Project ID

The ID of a project, for which the changes are to be made. The ID is compared to a list of available project IDs in the Keboola project. If the GD PID is not in the list of available PIDs, i.e. the writer is not located in the same project as the application, an error is raised. This behavior is enforced by the application to prevent changing users across projects without having knowledge about it.

Follow [the link](https://help.gooddata.com/display/doc/Find+the+Project+ID) to get more information on how to find your project ID.

#### GD Custom Domain

In case, the destination GoodData project is white labelled, it is required to provide the white label domain in the following format: `https://subdomain.domain.com` or whatever the equivalent is. This domain will be used for all GoodData related API calls,
hence the incorrect format or domain will result in application failure.
If the GoodData project is not white labeled, the field should be left blank and the component will use the base URL based on project location (`keboola.eu.gooddata.com` for EU location, `secure.gooddata.com` for US location).

### User table

The user table **must** contain following columns: `login`, `action`, `role`, `muf`, `first_name` and `last_name`. If any of the columns is missing, the application will fail. Sample of the table can be [found here](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/4ec16093a0bbd39c2d4784d19eee17776ae6f968/component_config/sample-config/in/tables/test.csv?at=master&fileviewer=file-view-default).

Below is the detailed description of each column.

#### login

The email of the user, for whom the action is to be executed. If the user does not exist in the organization, an attempt will be made to register the user under Keboola organization with this email.

#### action

The action, which is to be done for the user. Must be one of the following: `DISABLE`, `ENABLE` or `INVITE`.

##### `DISABLE`

**Disables the user** in the project. This process skips all data permission processes and automatically disables the user. If the user is not in the project or is already disabled, the user is skipped.

##### `ENABLE`

If the **user** is **already in the project**, they will be disabled. Data permissions processes follow, after which the user **will be re-enabled**.

If the **user** is **not in the project**, they will be automatically enabled, provided that data permission processes execute successfully.

In the special case, that **user** is **not part of the project nor Keboola organization**, there are not enough privileges for the user to be automatically added to the project. This action will be demoted to `INVITE`.

##### `INVITE`

If the **user** is **already in the project**, no invite is generated. Standard `DISABLE - MUF - ENABLE` process is followed instead.

If the **user** is **not in the project**, an invite is generated for the user. The invite is sent to user's `login` mail and the user is assigned data permissions prior to invite being sent out.

#### role

Role of the user to be had in the project. Must be one of `admin`, `editor`, `readOnly`, `dashboardOnly`, `keboolaEditorPlus`. If a role is not assigned properly, the error is recorded in the status file.

#### muf

A list of json-like objects, from which data permissions are created. An example list might have the following form:

```
[
    {
        "attribute": "attr.inctestsales.city",
        "value": ["NYC", "VAN", "PRG"],
        "operator": "IN"
    },
    {
        "attribute": "attr.inctestsales.sales_person",
        "value": ["Sales_1"],
        "operator": "="
    }
]
```

In the above example, two data permission filters are provided. Each JSON object must contain keys `attribute`, `value` and `operator`. 

If the user should be able to acccess all the data, the `muf` expression should be provided as an empty list, i.e.

```
[]
```

##### `attribute`

The attribute must be a string expression, identifying the attribute within the project. In general, attributes sourcing from Keboola writers are quite easy to determine. For example, column `city` from table `in.c-test.sales` would become `attr.inctestsales.city` in GoodData. Note the `attr` in the beginning of the identifier and missing punctuation from table name, i.e. all dots and dashes from Keboola table path were replaced.
If unsure what is the correct attribute identifier, it is possible to obtain the full list of attributes within the project [in the following guide](https://help.gooddata.com/display/doc/Determine+the+Attribute+Value+ID).

##### `value`

The key value must be a list of values for which the expression must be determined. The application always assumes primary label for the attribute, i.e. any custom labels for the attribute are ignored. You can obtain a list of available values for attribute by following [this guide](https://help.gooddata.com/display/doc/Determine+the+Attribute+Value+ID).

##### `operator`

Operator must be one of `=`, `<>`, `IN` or `NOT IN`. At the moment, the only unsupported operator is `AND`. See more about operators [here](https://help.gooddata.com/display/doc/Data+Permissions#DataPermissions-CreateanExpressionStatementforaDataPermission).

##### Note on .csv files

Note that json-files have keys enclosed in double quotes, which, conincidentally, is a commonly used character in quoting CSV files as well. This may lead to bad parsing of the `muf` expression, if it's not quoted properly. It is therefore recommended to follow standard CSV file procedures, specifically double all double quotes. As an example, below is the correct way the `muf` expression should be inputted in the CSV file

```
"[{""attribute"":""attr.inctestsales.city"",""value"":[""NYC"",""VAN"",""PRG""],""operator"":""NOT IN""}]"
```

and

```
"[]"
```

which will then be parsed as

```
[
    {
        "attribute": "attr.inctestsales.city",
        "value": ["NYC","VAN","PRG"],
        "operator": "NOT IN"
    }
]
```

and 

```
[]
```

##### first_name

First name of the user. The name will be used if the user must be created in the Keboola domain.

##### last_name

Last name of the user. The usage is same as `first_name`.

## Output mapping

The output of the application is the status file, which is loaded incrementally to `out.c-GDUserManagement.status` table automatically. Sample of the status file can be [found here](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/4ec16093a0bbd39c2d4784d19eee17776ae6f968/component_config/sample-config/out/tables/test.csv?at=master&fileviewer=file-view-default).

The file contains following columns:

* `user` - user, for which the action was executed. `admin` records are required calls by application at initialization.
* `action` - describes action type
* `status` - marks, whether the action was a success
* `timestamp` - UTC timestamp of the event
* `role` - user role
* `details` - any additional details related to the action
* `muf` - muf assigned to the user from the table

## Development

To run the image locally, use `docker-compose.yml` to define environment, mainly `KBC_TOKEN`, which is used as storage API token for Keboola Provisioning API. Then run following commands:

```
docker-compose build
docker-compose run -rm dev
```

## See also

The following two API references might be handy when working with the application:

* [Keboola GoodData Provisioning API](https://keboolagooddataprovisioning.docs.apiary.io/)
* [GoodData API Reference](https://help.gooddata.com/display/API/API+Reference)