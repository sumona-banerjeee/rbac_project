# Role-Based Access Control (RBAC) System - Buy & Sell Platform
## Project Objective
Build a **secure RBAC web system** using FastAPI, PostgreSQL, and HTML/CSS where:
•	Users can register and request access.
•	Superadmin reviews and onboards users as an `Admin` or `User`.
•	Admins can **list, update, delete** their own products.
•	Users can **browse and buy** products.
•	Superadmin will monitor everything and **analytics**.
## Roles & Permissions
Roles       |	Permissions
Super-admin	| View pending users, approve/deny, assign roles, view analytics, delete the user details or can edit.
Admin	    | Create, Read, Edit, Delete own products 
User	    | Read and buy products


Permissions include: `read`, `write`, `edit`, ‘assign_roles’(only for superadmin).
READ: The user can see only the preface. In this site, the user can view our products and cannot change any specifications.
WRITE: The user can purchase products, and the administrator can make changes. The full user type can also make certain commitments, but only partially.
EDIT: This user can add products, delete their own product, and edit their product.
## Tech Stack
- **Backend:** FastAPI
- **Frontend:**  HTML + CSS
- **Database:** PostgreSQL
- **Authentication:** JWT + HTTPOnly Cookies
- **ORM:** SQLAlchemy
- **Password Security:** bcrypt
-**Login with Google & Forget password: ** Oauth 2.0 : Future Scope
## How it Works?
### 1. Signup/Login
•	Any visitor can sign up with **name, email, password**
•	The user is **not approved** yet and cannot log in
### 2. Superadmin Dashboard
•	Superadmin logs in at `/login` using:
•	Email: `sumobanerjee2000@gmail.com`
•	Default password: admin123
•	Sees all **pending users**
•	Can **approve** and assign:
•	Role: Admin/User
•	Permissions: read/write/edit
•	Can also **deny** unqualified users
•	Superadmin can view analytics dashboard like Most sold products, Active users, Payment stats (UPI, cash, card) : Future Scope
### 3. Admin Dashboard
After approval, admin logs in and goes to the different page and can
•	Add products with `name`, `price`, `description`, `category`
•	View only their own listed products
•	Edit or delete those products
•	Logout securely
### 4. User Dashboard
Approved users can
•	View all available products
•	Buy (write), View (read) products
•	Cannot see delete/edit options
## Login Details (for testing)
Role	    | Email	                        | Password
Super-admin	| sumobanerjee2000@gmail.com	| Pre-set
Admin	    | Post-approval	                | Chosen by the users
User	    | Post-approval	                | Chosen by the users
## Future Enhancements
•	Add email notifications to Super-admin on user signup
•	Email notification for the approval for the user and admin
•	Enable product image uploads
•	Super-admin can view analytics dashboard like Most sold products, Active users, Payment stats (UPI, cash, card) 
•	Can also **deny** after approval the users and might see as a unqualified users
•	Login with the google
•	Forgot password features
