##### Note

A more detailed documentation is available in [component's repository](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/master/README.md).

## Input mapping

The application accepts 4 parameters and a table of users. In addition to the 4 parameters, the component automatically uses [Storage API Token](https://help.keboola.com/management/project/tokens/) to access available GoodData projects within the project and provision users. A sample configuration can be found [in the repository](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/master/component_config/sample-config/).

### 1 Parameters

Following 4 parameters are accepted: `GD Login`, `GD Password`, `GD Project ID` and `GD Custom Domain`. More detailed description of all parameters is provided in the upcoming subsections.

A sample of the configuration file can be [found here](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/master/component_config/sample-config/config.json).

#### 1.1 GD Login

The login email to the GoodData portal. Requirements for the used login are:

* must have access to the project
* must be admin of the project
* must not have any data permissions assigned to them.

Failure to comply with any of the above requirements will raise an error.

#### 1.2 GD Password

The password to `GD Login` used to log in to GoodData portal.

#### 1.3 GD Project ID

The ID of a project, for which the changes are to be made. The ID is compared to a list of available project IDs in the Keboola project. If the GD PID is not in the list of available PIDs, i.e. the writer is not located in the same project as the application, an error is raised. This behavior is enforced by the application to prevent changing users across projects without having knowledge about it.

Follow [the link](https://help.gooddata.com/display/doc/Find+the+Project+ID) to get more information on how to find your project ID.

#### 1.4 GD Custom Domain

In case, the destination GoodData project is white labelled, it is required to provide the white label domain in the following format: `https://subdomain.domain.com` or whatever the equivalent is. This domain will be used for all GoodData related API calls,
hence the incorrect format or domain will result in application failure.
If the GoodData project is not white labeled, the field should be left blank and the component will use the base URL based on project location (`keboola.eu.gooddata.com` for EU location, `secure.gooddata.com` for US location).

### 2 User table

The user table **must** contain following columns: `login`, `action`, `role`, `muf`, `first_name` and `last_name`. If any of the columns is missing, the application will fail. Sample of the table can be [found here](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/master/component_config/sample-config/in/tables/test.csv).

Below is the detailed description of each column.

#### 2.1 login

The email of the user, for whom the action is to be executed. If the user does not exist in the organization, an attempt will be made to register the user under Keboola organization with this email.

#### 2.2 action

The action, which is to be done for the user. Must be one of the following: `DISABLE`, `ENABLE` or `INVITE`.

##### 2.2.a `DISABLE`

**Disables the user** in the project. This process skips all data permission processes and automatically disables the user. If the user is not in the project or is already disabled, the user is skipped.

##### 2.2.b `ENABLE`

If the **user** is **already in the project**, they will be disabled. Data permissions processes follow, after which the user **will be re-enabled**.

If the **user** is **not in the project**, they will be automatically enabled, provided that data permission processes execute successfully.

In the special case, that **user** is **not part of the project nor Keboola organization**, there are not enough privileges for the user to be automatically added to the project. This action will be demoted to `INVITE`.

##### 2.2.c `INVITE`

If the **user** is **already in the project**, no invite is generated. Standard `DISABLE - MUF - ENABLE` process is followed instead.

If the **user** is **not in the project**, an invite is generated for the user. The invite is sent to user's `login` mail and the user is assigned data permissions prior to invite being sent out.

#### 2.3 role

Role of the user to be had in the project. Must be one of `admin`, `dashboardOnly`, `editor`, `editorInvite`, `editorUserAdmin`, `explorer`, `explorerOnly`, `keboolaEditorPlus`, `readOnlyUser` or `readOnlyNoExport`. If a role is not assigned properly, the error is recorded in the status file.

#### 2.4 muf

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

##### 2.4.a `attribute`

The attribute must be a string expression, identifying the attribute within the project. In general, attributes sourcing from Keboola writers are quite easy to determine. For example, column `city` from table `in.c-test.sales` would become `attr.inctestsales.city` in GoodData. Note the `attr` in the beginning of the identifier and missing punctuation from table name, i.e. all dots and dashes from Keboola table path were replaced.
If unsure what is the correct attribute identifier, it is possible to obtain the full list of attributes within the project [in the following guide](https://help.gooddata.com/display/doc/Determine+the+Attribute+Value+ID).

##### 2.4.b `value`

The key value must be a list of values for which the expression must be determined. The application always assumes primary label for the attribute, i.e. any custom labels for the attribute are ignored. You can obtain a list of available values for attribute by following [this guide](https://help.gooddata.com/display/doc/Determine+the+Attribute+Value+ID).

##### 2.4.c `operator`

Operator must be one of `=`, `<>`, `IN` or `NOT IN`. At the moment, the only unsupported operator is `AND`. See more about operators [here](https://help.gooddata.com/display/doc/Data+Permissions#DataPermissions-CreateanExpressionStatementforaDataPermission).

##### 2.4.d Note on .csv files

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

#### 2.5 first_name

First name of the user. The name will be used if the user must be created in the Keboola domain.

#### 2.6 last_name

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

See [documentaion](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/master/README.md) for more detailed information about execution plans and output mapping.

## 4 See also

The following two API references might be handy when working with the application:

* [Keboola GoodData Provisioning API](https://keboolagooddataprovisioning.docs.apiary.io/)
* [GoodData API Reference](https://help.gooddata.com/display/API/API+Reference)