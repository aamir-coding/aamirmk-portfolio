---
id: "proj-secure-auction-overview"
type: "project"
title: "Secure Online Auction System — Overview"
source_section: "J1, J2, J3, J4 (Project E)"
tags: ["auction", "django", "postgresql", "rbac", "security", "learning-project"]
draft: true
private: false
---

The Secure Online Auction System is a security-focused online auction web application designed around authentication, role-based access control (RBAC), and protected auction/bidding workflows. It is intended to let sellers list auction items, bidders participate, and administrators manage the platform while protecting account and auction-related actions.

The project stack includes Python, Django, PostgreSQL, cryptography utilities, role-based access, password hashing (Argon2 was referenced), email verification, and JWT/OAuth-related authentication design. The intended final direction was server-rendered HTML Django views rather than a JSON-only Django REST Framework API.

Django handles routing and HTML templates for registration, login, verification, auctions, bidding, profile, and administration. PostgreSQL stores application data. Authentication and authorisation checks protect views and actions.

Note: This is a learning project. Exact organisation, dates, team status, personal contribution, implemented vs. planned features, specific incidents, and test results require verification. No verified production usage or quantified security/performance results are available.

---
id: "proj-secure-auction-status"
type: "project"
title: "Secure Online Auction System — Status"
source_section: "J10, J11, V7 (Project E)"
tags: ["auction", "status", "learning-project"]
draft: true
private: false
---

The Secure Online Auction System is not live and has no clean repository present. It should be presented as a learning/project system, not a production financial platform. No repository link, live app URL, demo, or screenshots are currently available.
