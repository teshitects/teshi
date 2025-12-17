# User Login Function Test

## Preconditions
1. System is running normally
2. Test user account exists in database
3. User is not logged in

## Operation Steps
1. Open login page
2. Enter correct username
3. Enter correct password
4. Click login button
5. Wait for system response

## Expected Results
1. Login successful
2. Page redirects to main page
3. Display user information
4. System has no error prompts

## Notes
This is a basic user login test case, covering the normal login process.

---

# User Login Failure Test

## Preconditions
1. System is running normally
2. Test user account exists in database
3. User is not logged in

## Operation Steps
1. Open login page
2. Enter correct username
3. Enter incorrect password
4. Click login button
5. Wait for system response

## Expected Results
1. Login failed
2. Page stays on login page
3. Display "Username or password error" prompt message
4. Password input box is cleared

## Notes
Test password error scenario, verify system's error handling mechanism.

---

# User Registration Function Test

## Preconditions
1. System is running normally
2. User is not logged in
3. Prepare new user registration information

## Operation Steps
1. Open registration page
2. Enter new username
3. Enter password
4. Confirm password
5. Enter email address
6. Click registration button

## Expected Results
1. Registration successful
2. Page redirects to login page
3. Display "Registration successful" prompt message
4. New user information saved to database

## Notes
Need to verify username uniqueness check and password strength validation.