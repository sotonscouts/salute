# Auth0 Authentication

## Authentication Methods

The application uses Auth0 as its authentication provider, supporting the following authentication methods:

1. **Bearer Token Authentication**: The primary method for API access, where clients include a JWT token in the `Authorization` header with the format `Bearer <token>`.

2. **Google OAuth Integration**: Users can authenticate using their Google accounts. The system links Google identities to existing user records based on email or Google user ID.

## User Matching Process

When a user authenticates via Auth0, the following matching process occurs:

1. The Auth0 token is validated to ensure:
   - It has a valid signature
   - It hasn't expired
   - It contains required claims (subject, scope, etc.)
   - It includes the `salute:user` scope permission

2. The system attempts to find an existing user by the `auth0_sub` claim:
   - For direct Auth0 users, this is in the format `auth0|user-id`
   - For Google users, this is in the format `google-oauth2|google-user-id`

3. If a user is found, additional validation occurs:
   - User must be active (`is_active=True`)
   - User must be linked to a `Person` record
   - The linked `Person` must not be suspended (`is_suspended=False`)

## Account Linking for New Users

If no existing user matches the `auth0_sub` claim but the token is from a Google account, the system attempts to link the account:

1. For Google accounts, the system extracts the Google UID from the token's `sub` claim
2. The system searches for a `Person` record with:
   - A matching Google UID
   - OR a matching email address (if available in the token)
   - No existing User association
   - Not suspended

3. If a matching `Person` is found, a new `User` record is created with:
   - Email from the token or the Person record
   - `auth0_sub` set to the token's subject claim
   - Association with the found Person record
   - Active status (`is_active=True`)

4. If no matching `Person` is found, authentication fails with an error message indicating no matching account was found.

## Development Override

For development and testing purposes, you can manually set the Auth0 user identifier:

1. Access the Django admin interface
2. Navigate to the Users section
3. Select the user you want to modify
4. Set the `auth0_sub` field to the appropriate value:
   - For direct Auth0 users: `auth0|user-id`
   - For Google users: `google-oauth2|google-user-id`
5. Save the changes

This allows you to test different authentication scenarios without needing to create actual Auth0 tokens.

## Important Notes

- The system requires the `salute:user` scope in the token for API access
- Users without an associated `Person` record cannot authenticate
- `Person` records that are suspended prevent authentication
- Only Google OAuth accounts can be automatically linked to existing records
- Direct Auth0 accounts cannot be automatically linked and must be explicitly associated
