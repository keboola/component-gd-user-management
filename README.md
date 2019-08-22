# GoodData User Management Application

This application allows user of the component to manage users in the GoodData project, invite new users to the project, change roles and assign data permissions for each user.

## 1 Overview

The application, as aforementioned, allows users to maintain access to a GoodData project and or manage users' access to certain data. The application uses GoodData API to assign [Data Permissions](https://help.gooddata.com/display/doc/Data+Permissions) to desired users, that automatically pre-filter available data to end-user.

### 1.1 Prerequisities

**The following requirements are needed for successful conifguration of the application:**

* a GoodData project
* an admin account to the GoodData project

### 1.2 Status file

All actions performed by the application are automatically recorded to a status file. The file is incrementally auto-saved to `out.c-GDUserManagement.status` table. All actions contain information on whether said action was successful and any additional information, which are the result of taking the action.

### 1.3 Process overview

The application automatically determines what actions need to be taken for each user based on the table of users (see *input mapping* section). The process is ran row-by-row, i.e. all users are processed sequentially, to avoid any confusion in the process. For each user, the application determines whether the user is already in the organization and/or project and acts accordingly on that, i.e. creates the user if necessary. To prevent any possible failure, all users are first disabled in the project, before assigning data permissions and re-enabling them again. If it's necessary, the application generates an invitation, which is delivered to the user on the provided e-mail address.

### 1.4 Process detail

Below is a more detailed description of the process.

1. User and all their data is read from the table.
2. User's login is compared to the list of users in GD project and list of users provisioned by Keboola.
    1. If the user is in both organization and project, they are disabled or removed.
    2. If the user is in the organization but not in the project, nothing is done.
    3. If the user is not in the organization but is in the project, they are disabled.
    4. If the user is not in the organization nor the project, an attempt is made to create them in Keboola organization. If the       attemp fails, the user is already part of another organization and will not be maintained in Keboola domain.
3. For each user, their `Mandatory User Filter (MUF)` expression is read and parsed into URI format. The URI format is a format, where all attribute names, labels and values are transformed to their URI counterparts. If the attribute, label or value does not exist, the URI expression is not created and an error is recorded in the status file.
4. The URI expression is posted to GoodData and the user filter is created. Each user filter is assigned unique ID, which is then passed on to users as an attribute.
5. The following action occurs once the user filter was created (follow-up to point 2):
    1. User is assigned the user filter and is re-enabled in the project.
    2. User is assigned the user filter and is added to the project.
    3. User is assigned the user fitler and is re-enabled in the project.
    4. User is assigned the user filter and is enabled/invited to the project.
6. Process ends.

## 2 Input mapping

The application accepts 4 parameters and a table of users. In addition to the 4 parameters, the component automatically uses [Storage API Token](https://help.keboola.com/management/project/tokens/) to access available GoodData projects within the project and provision users. A sample configuration can be found [in the repository](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/master/component_config/sample-config/).

### 2.1 Parameters

Following 4 parameters are accepted: `GD Login`, `GD Password`, `GD Project ID` and `GD Custom Domain`. More detailed description of all parameters is provided in the upcoming subsections.

A sample of the configuration file can be [found here](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/master/component_config/sample-config/config.json).

#### 2.1.1 GD Login

The login email to the GoodData portal. Requirements for the used login are:

* must have access to the project
* must be admin of the project
* must not have any data permissions assigned to them.

Failure to comply with any of the above requirements will raise an error.

You can either use an already existing login (e.g. a personal account with admin privileges) or you can use Keboola's GoodData Provisioning API to [create a new login](https://keboolagooddataprovisioning.docs.apiary.io/#reference/0/kbc-access/get-user-credentials-to-project) and use those credentials.

#### 2.1.2 GD Password

The password to `GD Login` used to log in to GoodData portal.

#### 2.1.3 GD Project ID

The ID of a project, for which the changes are to be made. The ID is compared to a list of available project IDs in the Keboola project. If the GD PID is not in the list of available PIDs, i.e. the writer is not located in the same project as the application, an error is raised. This behavior is enforced by the application to prevent changing users across projects without having knowledge about it.

Follow [the link](https://help.gooddata.com/display/doc/Find+the+Project+ID) to get more information on how to find your project ID.

#### 2.1.4 GD Custom Domain

In case, the destination GoodData project is white labelled, it is required to provide the white label domain in the following format: `https://subdomain.domain.com` or whatever the equivalent is. This domain will be used for all GoodData related API calls,
hence the incorrect format or domain will result in application failure.
If the GoodData project is not white labeled, the field should be left blank and the component will use the base URL based on project location (`https://keboola.eu.gooddata.com` for EU location, `https://secure.gooddata.com` for US location).

### 2.2 User table

The user table **must** contain following columns: `login`, `action`, `role`, `muf`, `first_name` and `last_name`. If any of the columns is missing, the application will fail. Sample of the table can be [found here](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/master/component_config/sample-config/in/tables/test.csv).

Below is the detailed description of each column.

#### 2.2.1 login

The email of the user, for whom the action is to be executed. If the user does not exist in the organization, an attempt will be made to register the user under Keboola organization with this email.

#### 2.2.2 action

The action, which is to be done for the user. Must be one of the following: `DISABLE`, `ENABLE`, `INVITE` or `REMOVE`.

##### 2.2.2.a `DISABLE`

**Disables the user** in the project. This process skips all data permission processes and automatically disables the user. If the user is not in the project or is already disabled, the user is skipped.

##### 2.2.2.b `ENABLE`

If the **user** is **already in the project**, they will be disabled. Data permissions processes follow, after which the user **will be re-enabled**.

If the **user** is **not in the project**, they will be automatically enabled, provided that data permission processes execute successfully.

In the special case, that **user** is **not part of the project nor Keboola organization**, there are not enough privileges for the user to be automatically added to the project. This action will be demoted to `INVITE`.

##### 2.2.2.c `INVITE`

If the **user** is **already in the project**, no invite is generated. Standard `DISABLE - MUF - ENABLE` process is followed instead.

If the **user** is **not in the project**, an invite is generated for the user. The invite is sent to user's `login` mail and the user is assigned data permissions prior to invite being sent out.

##### 2.2.2.d `REMOVE`

If the **user** is in the project, in disabled or enabled state, and their email address is not identical to `GD login` parameter, the user is removed using process `GD_REMOVE`. If the **user** is in the project and their login is identical to `GD login` parameter, or they are not present in the project, `SKIP_NO_REMOVE` or `SKIP` process is used, respectively.

#### 2.2.3 role

Role of the user to be had in the project. Must be one of `admin`, `dashboardOnly`, `editor`, `editorInvite`, `editorUserAdmin`, `explorer`, `explorerOnly`, `keboolaEditorPlus`, `readOnlyUser` or `readOnlyNoExport`. If a role is not assigned properly, the error is recorded in the status file.

#### 2.2.4 muf

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

##### 2.2.4.a `attribute`

The attribute must be a string expression, identifying the attribute within the project. In general, attributes sourcing from Keboola writers are quite easy to determine. For example, column `city` from table `in.c-test.sales` would become `attr.inctestsales.city` in GoodData. Note the `attr` in the beginning of the identifier and missing punctuation from table name, i.e. all dots and dashes from Keboola table path were replaced.
If unsure what is the correct attribute identifier, it is possible to obtain the full list of attributes within the project [in the following guide](https://help.gooddata.com/display/doc/Determine+the+Attribute+Value+ID).

##### 2.2.4.b `value`

The key value must be a list of values for which the expression must be determined. The application always assumes primary label for the attribute, i.e. any custom labels for the attribute are ignored. You can obtain a list of available values for attribute by following [this guide](https://help.gooddata.com/display/doc/Determine+the+Attribute+Value+ID).

##### 2.2.4.c `operator`

Operator must be one of `=`, `<>`, `IN` or `NOT IN`. At the moment, the only unsupported operator is `AND`. See more about operators [here](https://help.gooddata.com/display/doc/Data+Permissions#DataPermissions-CreateanExpressionStatementforaDataPermission).

##### 2.2.4.d Note on .csv files

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

#### 2.2.5 first_name

First name of the user. The name will be used if the user must be created in the Keboola domain.

#### 2.2.6 last_name

Last name of the user. The usage is same as `first_name`.

## 3 Output mapping

The output of the application is the status file, which is loaded incrementally to `out.c-GDUserManagement.status` table automatically. Sample of the status file can be [found here](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/master/component_config/sample-config/out/tables/test.csv).

The file contains following columns:

* `user` - user, for which the action was executed. `admin` records are required calls by application at initialization.
* `action` - describes action type
* `status` - marks, whether the action was a success
* `timestamp` - UTC timestamp of the event
* `role` - user role
* `details` - any additional details related to the action
* `muf` - muf assigned to the user from the table

### 3.1 user

The user column contains the information about the login, for which the action was performed. For each login, there's a set of actions that are executed in order to make sure that each user is safely added to a project and in case of fail does not have access to information they should not have access to.

### 3.2 action

The column represents the action that is executed. Detailed information about all of the actions can be found in the `details` column. There are currently 4 admin actions, executed at the very beginning of the process and 8 user actions, executed on the user level. In the following subsections, each of the actions will be briefly discussed in order of their usual execution.

#### 3.2.1 `GET_ATTRIBUTES`

An admin action that obtains the list of all attributes in the GoodData project, which is then used to create MUF expressions and MUFs. When a user specified attribute is missing in the list of attributes returned by this action, the MUF fails and user is not enabled in the project.

#### 3.2.2 `GET_GD_USERS` and `GET_KBC_USERS`

Both of these admin actions download a list of users from the GoodData project or its assigned Keboola domain respectively. The list of users is then used when assigning necessary actions to each user (see seciont 3.2.4 `ASSIGN_ACTION`).

#### 3.2.3 `MAP_ROLES`

The admin action creates a map of roles beteen GoodData and Keboola. As the roles can have slightly different names, this action is necessary to assign correct role to users.

#### 3.2.4 `ASSIGN_ACTION`

A user action, which determines the required steps needed for each user. The backbone of the action is comparing a user against the list of users obtained in 3.2.2. Arbitrary actions, such as disabling a user that is not part of the project, are skipped. See section for 4 for detailed execution plan and description of each assigned action.

#### 3.2.5 `USER_CREATE`

A user action performed, when user is not in the GoodData project nor part of the user list in Keboola domain. The action creates a user in the Keboola domain and allows them to be provisioned and managed further using Keboola GoodData Provisioning API.

#### 3.2.6 `DISABLE_IN_PRJ`

A user action that disables a user in the project. The action is only executed, if a user is already present in the project, either in disabled or enabled state.

#### 3.2.7 `CREATE_MUF_EXPR`

An action performed on user level, that converts each of the json MUF objects to be represented by their unique URI identifiers. The action uses output of `GET_ATTRIBUTES` action, obtains the values for attributes used in the json structure and maps accordingly. If the action is successful, the resulting URI representation can be seen in `details` column. If the action fails, the reason is recorded in the `details` column.

#### 3.2.8 `CREATE_MUF`

A user level action, that registers the MUF expression obtained in step 3.2.7, pushes it to GoodData and returns unique URI for the filter. If filter is a list with lenght more than 1 (multiple filters) a list of URIs is returned.

#### 3.2.9 `ASSIGN_MUF`

A user action, which assigns the filters obtained in step 3.2.8 to user. The filters are tied to user's profile in the project.

#### 3.2.10 `INVITE_TO_PRJ`

A user action that invites user to the project and assigns MUF at the same time. The filter is sent together with the invitation and the filter becomes active once the user accepts the invitation. The action is executed only if all the preceeding steps were completed successfully to make sure users do not have access to data, they're not supposed to have.

#### 3.2.11 `ENABLE_IN_PRJ`

A user action, that enables user in the project. The action is executed only if all the preceeding steps were completed successfully to prevent access to data, user should not see.

#### 3.2.12 `REMOVE_FROM_PRJ`

A user action, that removes a user from the project. The action is executed straight away with no preceeding steps.

### 3.3 status

One of `SUCCESS` or `ERROR`. Marks whether the respective action was successful.

### 3.4 timestamp

A time when the action was perfomed. The time is provided in `YYYY-MM-DD HH:MI:SS.F` format and UTC timezone.

### 3.5 role

A role assigned to the user.

### 3.6 details

Additional details available to each action. The value in the column varies from the action performed.

### 3.7 muf

Original MUF expression assigned to the user in the input mapping.

## 4 Execution plan

As was mentioned in section 3.2.4, each user has a unique list of actions which are performed based on his membership in the project or organization. In this section, each of the execution plans from `ASSIGN_ACTION` step will be discussed in detail to provide more clarity.

### 4.1 `GD_DISABLE`

This action performs only one step:

```
DISABLE_IN_PRJ
```

and is performed only on users, that should be disabled and are already present in the project. Other users, who are assigned this action but are not members of the project are skipped.

### 4.2 `GD_REMOVE`

This action only performs one step:

```
REMOVE_FROM_PRJ
```

and removes user completely from the project. No data filters or role changes are applied.

### 4.3 `GD_DISABLE MUF GD_ENABLE`

This action is performed on all of the users, that are already in the project (enabled or disabled state) and should be enabled after the result is finished. The execution plan is following:

```
DISABLE_IN_PRJ > CREATE_MUF_EXPR > CREATE_MUG > ASSIGN_MUG > ENABLE_IN_PRJ
```

If any of the steps before the `ENABLE_IN_PRJ` action fails, the user stays in disabled state.

### 4.4 `MUF GD_INVITE`

The action is performed, when users should be invited to the project instead of adding them directly to the project. In this case, an email invitation will be sent and user will have the MUF assigned once he activates his account automatically. There's no need to re-run the component to activate the filter once the user accepts the invitation. The execution plan for the process is following:

```
CREATE_MUF_EXPR > CREATE_MUF > INVITE_TO_PRJ
```

and as was mentioned, the invitation contains the MUF so the `ASSIGN_MUF` step is omitted. If any of the intermediary step fail, the invitation is not sent out. It's also important to mention, that invitation is not sent to users, that are already in the project in enabled state.

### 4.5 `MUF KB_ENABLE`

The action happens when user is present in Keboola organization but not a member of the GoodData project. The action uses Keboola endpoint to add user directly to the project. The execution plan is following:

```
CREATE_MUF_EXPR > CREATE_MUF > ASSIGN_MUF > ENABLE_IN_PRJ
```

and as is the case with previous action steps, the user is not enabled in the project if any of the preceeding actions fail.

### 4.6 `TRY_KB_CREATE MUF ENABLE_OR_INVITE`

If a user is not a member of the project nor the organization, the component will try to create the user in Keboola organization. However, it might happen that some users are already part of different organization. In that case, the user can't be created in the organization and his unique identifier is not known since he's not part of a project. The only remaining thing is to invite user to the project, which component does automatically with added MUF. If the user is created successfully in Keboola organization, the user will then follow the same process as `MUF KB_ENABLE` action. Therefore, there are two possible execution steps based on whether `USER_CREATE` action succeds or not.

If `USER_CREATE` succeeds, the following execution plan is executed:

```
USER_CREATE > CREATE_MUF_EXPR > CREATE_MUF > ASSIGN_MUF > ENABLE_IN_PRJ
```

else the plan below is executed:

```
USER_CREATE > CREATE_MUF_EXPR > CREATE_MUF > INVITE_TO_PRJ
```

## 5 Development

To run the image locally, use `docker-compose.yml` to define environment, mainly `KBC_TOKEN`, which is used as storage API token for Keboola Provisioning API. Then run following commands:

```
docker-compose build
docker-compose run --rm dev
```

## 6 See also

The following two API references might be handy when working with the application:

* [Keboola GoodData Provisioning API](https://keboolagooddataprovisioning.docs.apiary.io/)
* [GoodData API Reference](https://help.gooddata.com/display/API/API+Reference)