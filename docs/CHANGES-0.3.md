# GAS HUNAR 0.3 — local sign-up and login

The startup screen has separate Login and Sign up tabs, translated into Kurdish Sorani, Arabic and English. Sign up accepts full name, username, password and confirmation. Passwords are masked with an optional visibility toggle. Validation and success messages appear inline. A successful registration switches to Login and prefills only the username; the user must enter the password to sign in.

The first account is the restaurant administrator. Later self-registered accounts are active cashiers with only POS and customer permissions. Registration never accepts a requested role. Existing administrators, employee accounts, passwords and restaurant data are not modified. Admins can continue creating privileged employees through Employees. The inactivity/unlock dialog offers Login only.

Registration is a reserved SQLite write transaction. Duplicate usernames fail without a partial user/employee/audit record, and concurrent first registrations cannot create two administrators. Passwords use Argon2id and the existing 10–256 character policy. UI password input is validated rather than silently truncated. No internet, email verification, cloud login, third-party account or default production password is introduced.

Automated test source covers first/subsequent registration, restart/login, restricted permissions, Unicode names, duplicate/invalid data, concurrent registration, complete native GUI flow, masked input and localization. The packaged EXE self-check exercises registration and login and captures both screens. Windows CI must pass before the new EXE is presented as verified.

Existing database schema remains version 1; no schema migration or data replacement is needed.
