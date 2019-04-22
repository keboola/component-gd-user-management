## Input mapping

The application accepts 4 parameters and a table of users. In addition to the 4 parameters, the component automatically uses [Storage API Token](https://help.keboola.com/management/project/tokens/) to access available GoodData projects within the project. A sample configuration can be found [in the repository](https://bitbucket.org/kds_consulting_team/kds-team.app-gd-user-management/src/4ec16093a0bbd39c2d4784d19eee17776ae6f968/component_config/sample-config/?at=master).

### Parameters

Following 4 parameters are accepted: `GD Login`, `GD Password`, `GD Project ID` and `GD Custom Domain`. More detailed description of all parameters is provided in the upcoming subsections.

#### GD Login

The login email to the GoodData portal. Requirements for the used login are:

* must have access to the project
* must be admin of the project
* must not have any data permissions assigned to them.

Failure to comply with any of the above requirements will raise an error.

#### GD Password

The password to `GD Login` used to log in to GoodData portal.

#### GD Project ID

The ID of a project, for which the changes are to be made. The ID is compared to a list of available project IDs in the Keboola project. If the GD PID is not in the list of available PIDs, i.e. the writer is not located in the same project as the application, an error is raised. This behavior is enforced by the application to prevent somebody changing users across projects without knowing about it.

Follow [the link](https://help.gooddata.com/display/doc/Find+the+Project+ID) to get more information on how to find your project ID.

#### GD Custom Domain

In case, the destination GoodData project is white labelled, it is required to provide the white label domain in the following format: `https://subdomain.domain.com` or whatever the equivalent is. This domain will be used for all GoodData related API calls,
hence the incorrect format or domain will result in application failure.
If the GoodData project is not white labeled, the field should be left blank and the component will use the base URL based on project location.

### User table

The user table **must** contain following columns: `login`, `action`, `role`, `muf`, `first_name` and `last_name`. If any of the column is missing, the application will fail. Below is the detailed description of each column.

#### login

The email of the user, for whom the action is to be executed. If the user does not exist in the organization, an attempt will be made to register the user under Keboola organization with this email.

#### action

The action, which is to be done for the user. Must be one of the following: `DISABLE`, `ENABLE` or `INVITE`.

##### `DISABLE`

**Disables the user** in the project. This process skips all data permission processes and automatically disables the user. If the user is not in the project or is already disabled, the user is skipped.

##### `ENABLE`

If the **user** is **already in the project**, they will be disabled. Data permissions processed follow, after which the user **will be re-enabled**.

If the **user** is **not in the project**, they will be automatically enabled provided that data permission processes execute successfully.

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

In the above example, two data permission filters are provided. Each JSON object must contain key `attribute`, `value` and `operator`. 

If the user should be able to acccess all the data, the `muf` expression should be provided as an empty list, i.e.

```
[]
```

##### `attribute`

The attribute must be a string expression, identifying the attribute within the project. In general, attributes sourcing from Keboola writers are quite easy to determine. For example, column `city` from table `in.c-test.sales` would become `attr.inctestsales.city` in GoodData, not the `attr` in the beginning of the identifier and missing punctuation from table name, i.e. all dosts and dashes from Keboola table path were replaced.
If unsure what is the attribute identifier, it's possible to obtain the full list of attributes within the project [in the following guide](https://help.gooddata.com/display/doc/Determine+the+Attribute+Value+ID).

##### `value`

The key value must be a list of values for which the expression must be determined. The application always assumes primary  label for the attribute, i.e. any custom labels for the attribute are ignored. You can obtain a list of available valuesfor   attribute by following [this guide](https://help.gooddata.com/display/doc/Determine+the+Attribute+Value+ID).

##### `operator`

Operator must be one of `=`, `<>`, `IN` or `NOT IN`. At the moment, the only unsupported operator is `AND`. See more about operators [here](https://help.gooddata.com/display/doc/Data+Permissions#DataPermissions-CreateanExpressionStatementforaDataPermission).

##### Note on .csv files

Note that json-files have keys enclosed in double quotes, which, conincidentally, is a commonly used character in quoting CSV files as well. This may lead to bad parsing of the `muf` expression, if it's not quoted properly. It is therefore recommended to follow standard CSV file procedures, specifically double all double quotes. As an example, below is the correct way the `muf` expression should be inputted in the CSV file

```
"[{""attribute"":""attr.inctestsales.city"",""value"":[""NYC"",""VAN"",""PRG""],""operator"":""NOT IN""}]"
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

##### first_name

First name of the user. The name will be used if the user must be created in the Keboola domain.

##### last_name

Last name of the user. The usage is same as `first_name`.