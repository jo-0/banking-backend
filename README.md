Create a Django project displaying a user balance computed from a list of transactions.
Users should be able to transfer funds to each other.

A staff member should be able to consult a user balance using a custom action in the admin panel (no UI work needed from you).

Example:
1. User Foo is credited with €10,000. User Bar is credited with €15,000
2. Balance should display €10,000 for user Foo, and €15,000 for user Bar
3. User Foo sends €5,000 to user Bar.
4. Balance should display €5,000 for user Foo, and €20,000 for user Bar
5. User Bar withdraws €10,000
6. Balance should display €5,000 for user Foo, and €10,000 for user Bar

A few notes:
- One currency (EUR) is good enough, however you are free to allow more
Deposits/Withdrawals (credit & debit) should be implemented (a staff member in the admin should be able to create those)
- An API Endpoint should return a given user balance (the simplest authentication is fine)
- An admin should be able to check the list of transactions
- We will not pay much attention to the UI, you can use the admin for the entirety of the project
- As a bonus, an admin should be able to check the balance of a user at a given time (what was
Foo's balance vesterday at 04:00 UTC?)
- As a bonus, you can start thinking about performance and scalability. What would be the most efficient way to retrieve the balance if there are millions of transactions and/or if there are 1,000 transactions/s?
As a bonus, you can use AWS-cli to create a simple stack for the deployment
