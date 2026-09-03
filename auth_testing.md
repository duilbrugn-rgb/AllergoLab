# AllergoLab Auth Testing Playbook

This app supports TWO auth methods that coexist:
1. Custom email/password (JWT, httpOnly cookies)
2. Emergent-managed Google login (session_token cookie)

## Custom Email/Password (JWT)

Step 1: MongoDB Verification
```
mongosh
use <database_name>
db.users.find({role: "admin"}).pretty()
```
Verify bcrypt hash starts with `$2b$`; unique index on users.email.

Step 2: API Testing
```
curl -c cookies.txt -X POST $BACKEND/api/auth/login -H "Content-Type: application/json" -d '{"email":"duilbrugn@gmail.com","password":"<admin_password>"}'
curl -b cookies.txt $BACKEND/api/auth/me
```
Login returns the user object and sets `access_token` + `refresh_token` cookies. `/me` returns the same user.

## Emergent Google Auth

Step 1: Create Test User & Session
```
mongosh --eval "
use('<database_name>');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({user_id: userId, email: 'test.user.'+Date.now()+'@example.com', name: 'Test User', role:'user', created_at: new Date()});
db.user_sessions.insertOne({user_id: userId, session_token: sessionToken, expires_at: new Date(Date.now()+7*24*60*60*1000), created_at: new Date()});
print('Session token: ' + sessionToken);
"
```

Step 2: Browser Testing — set cookie `session_token` (httpOnly, secure, sameSite None) then navigate to app.

Notes:
- `get_current_user` checks JWT `access_token` cookie / Bearer first, then falls back to Emergent `session_token` cookie.
- All queries exclude Mongo `_id` where returning user data.
