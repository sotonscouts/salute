# Permissions

Generally, users can be assigned a role for either the district, or for a specific group. A user may also have a superuser permission.

## Default permissions

By default, a user can:

* View all groups
* View all sections
* Can see own person, including PII
* View all teams
* View own roles
* View own accreditations

## District Roles

As there is only one district in a deployment of Salute, a user can have exactly one of the following:

* District Admin
    * View all people including PII
* District Manager
    * View all people, excluding PII
    * View all roles
    * View all accreditations


## Group Roles

!!! note

    Group roles are planned for Salute Phase II.

A user can be assigned different roles for different groups (i.e Bob is MANAGER for 2nd):

* Group Manager
    * View all people in Group, excluding PII
        * Cannot view roles that a person has elsewhere
        * Must be accessed from the role edge?
    * View all roles in Group
    * View all sections in Group
    * View all accreditations in Group

## Determining user roles

It is possible to query the roles that the current user possesses:

```graphql
{
  currentUser {
    userRoles {
      __typename
      ... on UserDistrictRole {
        level
      }
    }
  }
}
```

`roles` will return a list of role types, each of which may have different properties, so a group role would contain an edge to the group that the user has access to.

Default permissions do not yield a role, but may require the user to be linked to an active person.

```json
{
  "data": {
    "currentUser": {
      "roles": [
        {
          "__typename": "UserDistrictRole",
          "level": "MANAGER"
        }
      ]
    }
  }
}
```