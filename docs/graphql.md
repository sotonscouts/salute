# GraphQL API

Salute exposes a GraphQL API for querying and mutating data. The API is designed to be used by the frontend, but can also be used by other services.

The API is exposed at `/graphql/`.

A GraphQL Playground is available at `/graphql/`, which allows you to explore the schema and run queries. This is only available in development environments, and query introspection is disabled in production.

## Example Queries

### Get the current user, their user roles, and their person details

```graphql
query {
    currentUser {
        email
        lastLogin
        userRoles {
            __typename
            ... on UserDistrictRole {
                level
            }
        }
        person {
            firstName
            displayName
            formattedMembershipNumber
            contactEmail
        }
    }
    }
```

### Get the district, and explorer sections

```graphql
query DistrictWithExplorerSections {
    district {
        shortcode
        sections(filters: {sectionType: "EXPLORERS"}) {
            edges {
                node {
                    displayName
                    sectionType
                }
            }
            totalCount
        }
    }
}
```