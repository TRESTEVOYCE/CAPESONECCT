# CAPESONECCT

CAPESONECCT is a Django-based employment and public employment service platform. It provides separate workflows for jobseekers (applicants), employers, PESO/MSWDO staff, and administrators, plus a protected REST API for special employment-program records.

This document describes the system **as implemented in the current repository**. Where behavior differs from the apparent intended role design, the difference is called out in the "Implementation Notes" section.

---

## Table of Contents

- [1. System Overview](#1-system-overview)
- [2. Technology Stack](#2-technology-stack)
- [3. Application Structure](#3-application-structure)
- [4. Roles and Responsibilities](#4-roles-and-responsibilities)
- [5. Authentication and Security](#5-authentication-and-security)
- [6. Main User Workflows](#6-main-user-workflows)
- [7. Applicant Workflow](#7-applicant-workflow)
- [8. Employer Workflow](#8-employer-workflow)
- [9. Admin and PESO Operations](#9-admin-and-peso-operations)
- [10. Job Matching](#10-job-matching)
- [11. REST API](#11-rest-api)
- [12. API Data Models](#12-api-data-models)
- [13. API Examples](#13-api-examples)
- [14. Web Routes](#14-web-routes)
- [15. Local Development Setup](#15-local-development-setup)
- [16. Environment Variables](#16-environment-variables)
- [17. Management Commands](#17-management-commands)
- [18. Deployment](#18-deployment)
- [19. Troubleshooting](#19-troubleshooting)
- [20. Implementation Notes and Known Gaps](#20-implementation-notes-and-known-gaps)
- [21. Developer Quick Reference](#21-developer-quick-reference)

---

## 1. System Overview

CAPESONECCT is organized around four major areas:

1. **Applicant side** — applicant registration, profile completion, job discovery, job saving, applications, and application tracking.
2. **Employer side** — employer/company registration, verification documents, job posting, applicant review, and application-status updates.
3. **Admin/PESO side** — administration of jobs, applicant/employer verification, PESO referrals, special-program beneficiaries, reports, and account administration.
4. **MSWD/PESO REST API** — authenticated, read-only endpoints for SPES, GIP, TUPAD, DILP, and Career Guidance beneficiary data.

The Django project is mounted through:

```text
config/
├── settings.py
├── urls.py
├── asgi.py
└── wsgi.py
```

The custom authentication model is:

```text
AdminSide.User
```

The configured user identifier for normal authentication is the user's **email address**.

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| Backend | Django 6.0.6 |
| API | Django REST Framework 3.17.1 |
| API authentication | Simple JWT |
| Database | SQLite by default; database URL can configure PostgreSQL/other supported DBs |
| Filtering | django-filter |
| Static files | WhiteNoise |
| Media/file storage | Cloudinary |
| Email | SMTP / Gmail configuration |
| Login protection | django-axes |
| Form anti-bot protection | django-honeypot |
| Job matching | ChromaDB + Sentence Transformers (`all-MiniLM-L6-v2`) |
| Reporting/export | Django views + openpyxl |
| Python | See project environment; dependencies are pinned in `requirements.txt` |

---

## 3. Application Structure

```text
CAPESONECCT-testing-branch/
│
├── manage.py
├── requirements.txt
├── build.sh
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── AdminSide/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── permissions.py
│   ├── service.py
│   ├── tokens.py
│   ├── services/
│   ├── management/commands/
│   └── templates/
│
├── ApplicantSide/
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/
│
├── EmployerSide/
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/
│
├── LandingPage/
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/
│
├── MSWDAPI/
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
└── JobMatchingEngine/
    ├── config.py
    └── database.py
```

### Responsibilities

#### `AdminSide`

Contains the central domain models and administrative workflows.

Important models include:

- `User`
- `ApplicantProfile`
- `EmployerProfile`
- `Jobs`
- `ApplicantSkills`
- `ApplicantWorkExperience`
- `AppliedJobs`
- `OfferedJobs`
- `SavedJobs`
- SPES/GIP/TUPAD/DILP/Career Guidance beneficiary models
- `PESOActivities`
- `AuditLog`

#### `ApplicantSide`

Provides the jobseeker-facing portal.

#### `EmployerSide`

Provides employer/company-facing functionality.

#### `LandingPage`

Handles:

- Landing page
- Registration
- Email verification
- Login
- Password reset
- Terms and privacy pages

#### `MSWDAPI`

Provides the REST API for special-program beneficiary records.

#### `JobMatchingEngine`

Builds applicant/job text representations and stores/searches job embeddings using ChromaDB.

---

## 4. Roles and Responsibilities

The custom `User.role` field supports these values:

| Role | Purpose | Main access |
|---|---|---|
| `admin` | System administrator | Admin dashboard and administrative operations; API role is also accepted |
| `applicant` | Jobseeker | Applicant profile, jobs, saved jobs, applications |
| `employer` | Employer/recruiter | Company profile, job postings, applicants, application statuses |
| `peso` | PESO staff | Protected MSWD/PESO API access; intended for PESO operational use |
| `mswdo` | MSWDO staff | Protected MSWD/PESO API access |

### 4.1 Applicant

An applicant can:

- Register an account.
- Verify their email.
- Complete their personal profile.
- Add address, education, training, preferences, work experience, and skills.
- Upload resume/CV/supporting documents.
- Browse active jobs.
- Search jobs by keyword/location.
- Filter jobs by nature of work.
- Save jobs.
- Apply to jobs.
- View submitted applications and their statuses.
- Receive job recommendations from the matching engine.

### 4.2 Employer

An employer can:

- Register an account.
- Create/update company information.
- Upload verification documents.
- Wait for employer verification.
- Create job vacancies.
- Edit/delete their own job postings when verified.
- View applicants for their jobs when verified.
- Update application status.

Employer verification is important: several employer functions explicitly require:

```text
verification_status == "verified"
```

### 4.3 Admin

The administrative portal is intended for a Django superuser/PESO administrator.

Admin capabilities include:

- Dashboard metrics.
- Job vacancy management.
- Applicant verification.
- Employer verification.
- Referral management.
- Special-program beneficiary management.
- PESO monthly reports.
- Excel report export.
- Account settings.
- Help.

### 4.4 PESO

The `peso` role is explicitly recognized by the API permission class.

A user with role `peso` can access the protected MSWD API endpoints when authenticated.

### 4.5 MSWDO

The `mswdo` role is explicitly recognized by the API permission class.

A user with role `mswdo` can access the protected MSWD API endpoints when authenticated.

---

## 5. Authentication and Security

There are two authentication mechanisms in the project.

### 5.1 Web application authentication

The browser-facing application uses Django sessions.

Normal user login:

```text
POST /login/
```

The login form authenticates using:

```text
email + password
```

After successful login:

- applicant → `/applicant/`
- employer → `/employer/home/`

Email verification is required before a normal applicant/employer account can sign in.

### 5.2 Email verification

During applicant/employer registration:

1. The account is created with `email_verified = False`.
2. A verification token is generated.
3. A verification email is sent.
4. The user opens the activation URL.
5. The account becomes verified.
6. The user is logged in and redirected to the appropriate dashboard.

The email says the verification link expires after 24 hours.

The repository also contains:

```bash
python manage.py delete_unverified_users
```

which removes users whose verification has remained incomplete for more than 24 hours.

### 5.3 Password reset

The public application supports:

```text
/forgot-password/
/password-reset/sent/
/password-reset/<uidb64>/<token>/
/password-reset/complete/
```

### 5.4 API authentication

The REST API uses Simple JWT.

Token endpoints:

```text
POST /api/token/
POST /api/token/refresh/
```

The REST framework configuration requires authentication globally:

```python
DEFAULT_AUTHENTICATION_CLASSES = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
]
```

The API views additionally require:

```text
MSWDO OR ADMIN OR PESO
```

through `MSWDRolePermission`.

### 5.5 Login attack protection

`django-axes` is configured with:

- Failure limit: 5
- Cool-off: 30 seconds
- Lockout parameters: username + IP address
- Reset on successful authentication

### 5.6 Session behavior

The web session is configured for:

- 30-minute cookie age
- Save every request
- Expire when browser closes

When `DEBUG=False`, secure cookies and HTTPS-related security settings are enabled.

### 5.7 Honeypot protection

Registration/login views are protected with `django-honeypot`.

---

# 6. Main User Workflows

## 6.1 Applicant lifecycle

```text
Register
   │
   ▼
Email verification
   │
   ▼
Complete applicant profile
   │
   ▼
Admin reviews applicant
   │
   ├── rejected ──► cannot apply
   │
   └── approved ─► browse/apply
                       │
                       ▼
                 Employer reviews
                       │
                       ▼
              Application status changes
                       │
                       ▼
                     Hired
```

## 6.2 Employer lifecycle

```text
Register
   │
   ▼
Email verification
   │
   ▼
Complete company profile
   │
   ▼
Upload verification documents
   │
   ▼
Admin verifies employer
   │
   ├── rejected
   │
   └── verified
          │
          ▼
      Post jobs
          │
          ▼
     Receive applications
          │
          ▼
   Update applicant status
```

## 6.3 PESO referral lifecycle

```text
Applicant / job records
        │
        ▼
PESO/Admin selects applicant + job
        │
        ▼
Create OfferedJobs referral
        │
        ▼
Employer/application workflow
        │
        ▼
Status → interview / hired / rejected
        │
        ▼
Reports and placement metrics
```

---

# 7. Applicant Workflow

## 7.1 Registration

Applicant registration uses two steps:

```text
/register/jobseeker/
/register/jobseeker/account/
```

The first step collects basic applicant information and temporarily stores it in the session.

The second step creates the user:

```python
user.role = "applicant"
user.email_verified = False
```

and creates an `ApplicantProfile`.

## 7.2 Profile completion

The profile is divided into several sections:

```text
/applicant/personal_info/
/applicant/address/
/applicant/education/
/applicant/training/
/applicant/preferred_job/
/applicant/work_experience/
/applicant/skills/
/applicant/documents/
```

The applicant can also manage:

```text
/applicant/my_profile/
/applicant/personal_info/profile/
/applicant/personal_info/edit_profile_picture/
```

## 7.3 Finding jobs

Applicants can browse:

```text
GET /applicant/jobs/
```

Search:

```text
GET /applicant/search_jobs/?q=developer
```

Location filter:

```text
GET /applicant/jobs/?location=Cebu
```

Nature-of-work filter:

```text
GET /applicant/jobs/?job_type=permanent
```

The active job list searches:

- job title
- job description
- employer business name
- place of work
- nature of work

## 7.4 Saving a job

```text
POST /applicant/jobs/<job_id>/save/
```

Saved jobs are available at:

```text
/applicant/saved-jobs/
```

## 7.5 Applying

```text
POST /applicant/jobs/<job_id>/apply/
```

The code enforces:

1. Applicant must have a profile.
2. Applicant profile must have `status == "approved"`.
3. Job must be active.
4. Applicant cannot apply to the same job twice.

The application is stored as an `AppliedJobs` record with initial status:

```text
pending
```

## 7.6 Application statuses

`AppliedJobs` supports:

```text
pending
reviewed
for interview
hired
rejected
```

The dashboard also contains logic for `near_hire` and `withdrawn`; those values are referenced by the UI/reporting logic even though they are not present in the current `AppliedJobs.APPLICATION_STATUS` choices. See [Implementation Notes](#20-implementation-notes-and-known-gaps).

---

# 8. Employer Workflow

## 8.1 Registration

Employer registration uses:

```text
/register/employer/
/register/employer/account/
```

The account is created with:

```python
user.role = "employer"
user.email_verified = False
```

and an `EmployerProfile`.

## 8.2 Company profile

Main company profile route:

```text
/employer/company_profile/
```

The profile includes:

- Business name
- Trade name
- Acronym
- Office type
- TIN
- Employer type
- Workforce size
- Line of business
- Address
- Authorized representative
- Contact details
- Verification documents

## 8.3 Employer verification

Employer profiles have:

```text
pending
verified
rejected
```

An employer should reach:

```text
verification_status = verified
```

before using verified-only functionality.

## 8.4 Creating a job

```text
/employer/jobs/create/
```

A job contains:

- Job title
- Job description
- Nature of work
- Place of work
- Salary
- Vacancy count
- Experience requirement
- Qualifications
- PWD eligibility
- OFW eligibility
- Education
- Course/strand
- License
- Eligibility
- Certification
- Languages
- Application quota
- Posting expiry

After a job is created, the job is also inserted/updated in the ChromaDB job-matching collection.

## 8.5 Job lifecycle

Jobs support:

```text
Active
Filled
Closed
```

A job can also automatically become closed when:

- the application quota is reached, or
- the expiry date is reached.

The `Jobs.check_and_close()` method performs this check.

## 8.6 Managing applicants

Employer applicant routes include:

```text
/employer/applicants/
/employer/applicants/<id>/
/employer/applicants/<id>/job-status/
/employer/applicants/<id>/job-status/update/
```

Employer applicant lists are restricted to applications belonging to that employer.

---

# 9. Admin and PESO Operations

Admin-side base path:

```text
/admin-side/
```

## 9.1 Admin login

```text
GET/POST /admin-side/login/
```

The admin login view authenticates with:

```text
username + password
```

and requires:

```text
user.is_superuser == True
```

This differs from the normal `/login/` flow, which uses email + password.

## 9.2 Dashboard

```text
/admin-side/
```

The dashboard provides metrics such as:

- Registered applicants
- Registered employers
- Active jobs
- Referrals
- Placements
- Placement rate
- Recent referrals
- Pending approvals
- Monthly activity
- Job-type placement breakdowns

## 9.3 Job management

```text
/admin-side/jobs/
/admin-side/jobs/create/
/admin-side/jobs/<job_uuid>/
```

## 9.4 Applicant verification

```text
/admin-side/applicants/
/admin-side/applicants/<uuid>/verify/
```

Applicant profiles use:

```text
pending
approved
rejected
```

Applicants must be approved before applying to jobs.

## 9.5 Employer verification

```text
/admin-side/employers/
/admin-side/employers/<uuid>/verify/
```

Employer profiles use:

```text
pending
verified
rejected
```

## 9.6 Referrals

Referral listing:

```text
/admin-side/referrals/
```

Referral creation:

```text
/admin-side/referrals/create/
```

Referrals are represented by `OfferedJobs`.

Important fields include:

- applicant
- offered job
- referred by
- date offered
- status
- remarks

## 9.7 Special employment programs

The system manages:

- SPES
- GIP
- TUPAD
- DILP
- Career Guidance

Main route:

```text
/admin-side/special-programs/
```

Enrollment/editing:

```text
/admin-side/special-programs/enroll/
```

The program is selected using:

```text
?program=spes
?program=gip
?program=tupad
?program=dilp
?program=career_guidance
```

## 9.8 PESO reports

HTML report:

```text
/admin-side/reports/
```

Excel export:

```text
/admin-side/reports/excel/
```

The report logic aggregates employment and special-program statistics by month.

---

# 10. Job Matching

CAPESONECCT contains a semantic job-matching engine under:

```text
JobMatchingEngine/
```

## 10.1 Technology

The matching engine uses:

```text
ChromaDB
Sentence Transformers
all-MiniLM-L6-v2
```

The ChromaDB data path is:

```text
<project-root>/chroma_data/
```

## 10.2 Job representation

A job is converted into searchable text containing:

- Job title
- Job description
- Nature of work
- Location
- Salary
- Vacancies
- Education
- Course/strand
- License
- Eligibility
- Certification
- Languages
- Experience
- Qualifications
- PWD support
- OFW support
- Employer
- Industry
- Municipality
- Province

## 10.3 Applicant representation

An applicant is converted into searchable text containing:

- Education
- School
- Course
- Graduation year
- Employment status
- Active job-seeking state
- Expected salary
- Skills
- Preferred jobs
- Municipality
- Province
- OFW state
- 4Ps beneficiary state

## 10.4 Matching process

When an employer creates a job:

```text
JobsForm
   │
   ▼
Jobs object saved
   │
   ▼
upsert_job_vector(job)
   │
   ▼
ChromaDB collection: job_postings
```

When an applicant opens the dashboard:

```text
ApplicantProfile
   │
   ▼
build_applicant_profile_text()
   │
   ▼
ChromaDB query
   │
   ▼
top 10 matching jobs
   │
   ▼
filter Django jobs to Active
```

If matching jobs are found, they are shown as recommended jobs.

If no matching jobs are found, the dashboard falls back to all active jobs.

## 10.5 ChromaDB collection

The collection name is:

```text
job_postings
```

Each job uses its UUID as the ChromaDB document ID.

---

# 11. REST API

## 11.1 Base path

The API is mounted under:

```text
/api/
```

Therefore the actual endpoints are:

```text
/api/token/
/api/token/refresh/
/api/special-programs/
/api/government-internships/
/api/tupad-beneficiaries/
/api/displaced-informal-labor-programs/
/api/career-guidance-beneficiaries/
```

> The older repository README documents these without `/api/`. The Django root URL configuration shows that `/api/` is the actual prefix.

## 11.2 Authentication

All API endpoints require a valid JWT.

First obtain tokens:

```http
POST /api/token/
Content-Type: application/json
```

Body:

```json
{
  "email": "your-email@example.com",
  "password": "your-password"
}
```

Response contains:

```json
{
  "refresh": "<refresh-token>",
  "access": "<access-token>"
}
```

Use the access token:

```http
Authorization: Bearer <access-token>
```

## 11.3 API role requirement

The API requires:

```text
authenticated user
+
role in:
  - mswdo
  - admin
  - peso
```

Applicants and employers are not authorized to access these API resources.

## 11.4 API endpoint summary

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/token/` | Public login endpoint | Obtain JWT access/refresh tokens |
| POST | `/api/token/refresh/` | Refresh token | Obtain a new access token |
| GET | `/api/special-programs/` | JWT + MSWDO/Admin/PESO | List SPES beneficiaries |
| GET | `/api/special-programs/<uuid>/` | JWT + MSWDO/Admin/PESO | Get one SPES beneficiary |
| GET | `/api/government-internships/` | JWT + MSWDO/Admin/PESO | List GIP beneficiaries |
| GET | `/api/government-internships/<uuid>/` | JWT + MSWDO/Admin/PESO | Get one GIP beneficiary |
| GET | `/api/tupad-beneficiaries/` | JWT + MSWDO/Admin/PESO | List TUPAD beneficiaries |
| GET | `/api/tupad-beneficiaries/<uuid>/` | JWT + MSWDO/Admin/PESO | Get one TUPAD beneficiary |
| GET | `/api/displaced-informal-labor-programs/` | JWT + MSWDO/Admin/PESO | List DILP beneficiaries |
| GET | `/api/displaced-informal-labor-programs/<uuid>/` | JWT + MSWDO/Admin/PESO | Get one DILP beneficiary |
| GET | `/api/career-guidance-beneficiaries/` | JWT + MSWDO/Admin/PESO | List Career Guidance beneficiaries |
| GET | `/api/career-guidance-beneficiaries/<uuid>/` | JWT + MSWDO/Admin/PESO | Get one Career Guidance beneficiary |

The API serializers use:

```python
fields = "__all__"
```

so all model fields are returned.

---

# 12. API Data Models

All five beneficiary API models inherit common beneficiary fields.

## 12.1 Common beneficiary fields

| Field | Type | Description |
|---|---|---|
| `id` | integer | Database primary key |
| `uuid` | UUID | Public unique identifier |
| `first_name` | string | First name |
| `middle_name` | string/null | Middle name |
| `last_name` | string | Last name |
| `sex` | string | `M` or `F` |
| `date_of_birth` | date | Date of birth |
| `phone_number` | string | Contact number |
| `barangay` | string | Barangay |
| `municipality` | string | Municipality |
| `province` | string | Province |
| `region` | string | Region |
| `zip_code` | string | ZIP code |
| `daily_salary` | decimal | Daily salary |
| `start_date` | date | Program/employment start |
| `end_date` | date | Program/employment end |
| `is_done` | boolean | Whether the activity/employment is completed |
| `created_at` | datetime | Record creation timestamp |
| `updated_at` | datetime | Last update timestamp |

## 12.2 SPES

Endpoint:

```text
/api/special-programs/
```

Additional fields:

| Field | Type |
|---|---|
| `education_level` | string |
| `is_out_of_school_youth` | boolean |
| `has_graduated` | boolean |
| `has_nc_certification` | boolean |
| `is_absorbed_by_employer` | boolean |
| `school_name` | string/null |
| `college_program` | string/null |

Education values:

```text
elementary
juniors_hs
senior_hs
college
tech_voc
```

## 12.3 GIP

Endpoint:

```text
/api/government-internships/
```

Additional fields:

| Field | Type |
|---|---|
| `education_level` | string |
| `has_nc_certification` | boolean |
| `is_absorbed_by_agency` | boolean |

Education values:

```text
als
juniors_hs
senior_hs
tech_voc
college
```

## 12.4 TUPAD

Endpoint:

```text
/api/tupad-beneficiaries/
```

Additional fields:

| Field | Type |
|---|---|
| `project_type` | string |
| `project_name` | string/null |

Project type values:

```text
short
long
```

Meaning:

```text
short = Short-term (10-30 days)
long  = Long-term (31-90 days)
```

## 12.5 DILP

Endpoint:

```text
/api/displaced-informal-labor-programs/
```

Additional fields:

| Field | Type |
|---|---|
| `project_category` | string |
| `project_classification` | string |

Project category:

```text
individual
group
```

Project classification:

```text
formation
enhancement
restoration
```

## 12.6 Career Guidance

Endpoint:

```text
/api/career-guidance-beneficiaries/
```

Additional fields:

| Field | Type |
|---|---|
| `participant_category` | string |
| `activity_type` | string |
| `school_or_institution` | string/null |
| `preferred_curriculum_exit` | string |
| `conducted_date` | date/null |
| `has_received_lmi_materials` | boolean |

Participant category:

```text
juniors_hs
senior_hs
college
tech_voc
osy
jobseeker
```

Activity type:

```text
orientation
coaching
lmi_briefing
pre_employment
```

Curriculum exit:

```text
higher_ed
employment
entrepreneurship
skills_dev
undecided
```

---

# 13. API Examples

## 13.1 Get a JWT

```bash
curl -X POST "https://YOUR-DOMAIN/api/token/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "peso@example.com",
    "password": "YOUR_PASSWORD"
  }'
```

Save the returned `access` token.

## 13.2 List SPES records

```bash
curl "https://YOUR-DOMAIN/api/special-programs/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## 13.3 Get one SPES record

```bash
curl "https://YOUR-DOMAIN/api/special-programs/YOUR_UUID/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## 13.4 Refresh the access token

```bash
curl -X POST "https://YOUR-DOMAIN/api/token/refresh/" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

## 13.5 JavaScript client

```javascript
const BASE_URL = "https://YOUR-DOMAIN";

async function getAccessToken(email, password) {
  const response = await fetch(`${BASE_URL}/api/token/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(`Token request failed: ${response.status}`);
  }

  return response.json();
}

async function apiGet(path, accessToken) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

// Example:
const tokens = await getAccessToken(
  "peso@example.com",
  "YOUR_PASSWORD"
);

const spes = await apiGet(
  "/api/special-programs/",
  tokens.access
);

console.log(spes);
```

## 13.6 Pagination

The REST framework configuration uses:

```text
LimitOffsetPagination
PAGE_SIZE = 10
```

List responses therefore use the normal DRF paginated structure:

```json
{
  "count": 42,
  "next": "https://YOUR-DOMAIN/api/special-programs/?limit=10&offset=10",
  "previous": null,
  "results": [
    {}
  ]
}
```

Example:

```text
/api/special-programs/?limit=10&offset=20
```

## 13.7 Filtering

The list API views enable `django-filter` with:

```python
filterset_fields = "__all__"
```

This means model fields can be used as query filters.

Examples:

```text
/api/special-programs/?sex=F
/api/special-programs/?education_level=college
/api/tupad-beneficiaries/?project_type=short
/api/career-guidance-beneficiaries/?activity_type=coaching
```

Use only fields that exist on the particular model.

---

# 14. Web Routes

## 14.1 Public routes

| Route | Purpose |
|---|---|
| `/` | Landing page |
| `/login/` | Normal user login |
| `/register/` | Registration selection |
| `/register/jobseeker/` | Applicant registration step 1 |
| `/register/jobseeker/account/` | Applicant account creation |
| `/register/employer/` | Employer registration step 1 |
| `/register/employer/account/` | Employer account creation |
| `/activate/<uidb64>/<token>/` | Email activation |
| `/verify-email/` | Verification page |
| `/forgot-password/` | Password reset request |
| `/password-reset/sent/` | Password reset sent page |
| `/password-reset/<uidb64>/<token>/` | Set new password |
| `/password-reset/complete/` | Password reset complete |
| `/terms-and-conditions/` | Applicant/general terms |
| `/privacy-policy/` | Applicant/general privacy |
| `/employer-terms-and-condition/` | Employer terms |
| `/employer-privacy-policy/` | Employer privacy |

## 14.2 Applicant routes

Prefix:

```text
/applicant/
```

| Route | Purpose |
|---|---|
| `/applicant/` | Dashboard |
| `/applicant/my_profile/` | Profile |
| `/applicant/personal_info/` | Personal information |
| `/applicant/address/` | Address |
| `/applicant/education/` | Education |
| `/applicant/training/` | Training |
| `/applicant/preferred_job/` | Job preferences |
| `/applicant/work_experience/` | Work experience |
| `/applicant/skills/` | Skills |
| `/applicant/documents/` | Documents |
| `/applicant/jobs/` | Active jobs |
| `/applicant/jobs/<id>/` | Job details |
| `/applicant/jobs/<id>/apply/` | Apply |
| `/applicant/jobs/<id>/save/` | Save job |
| `/applicant/saved-jobs/` | Saved jobs |
| `/applicant/saved-jobs/<id>/unsave/` | Remove saved job |
| `/applicant/applied_jobs/` | Applications |
| `/applicant/search_jobs/` | Search jobs |
| `/applicant/jobs/sort/` | Sort jobs |
| `/applicant/logout/` | Logout |

## 14.3 Employer routes

Prefix:

```text
/employer/
```

| Route | Purpose |
|---|---|
| `/employer/home/` | Employer dashboard |
| `/employer/company_profile/` | Company profile |
| `/employer/employer-profile/create/` | Create/update employer profile |
| `/employer/employer-profile/picture/` | Employer profile picture |
| `/employer/jobs/create/` | Create job |
| `/employer/jobs_posted/` | Posted jobs |
| `/employer/jobs/<id>/` | Job details |
| `/employer/jobs/<id>/update/` | Update job |
| `/employer/jobs/<id>/delete/` | Delete job |
| `/employer/applicants/` | Applicants |
| `/employer/applicants/<id>/` | Applicant detail |
| `/employer/applicants/<id>/job-status/` | Update application status |
| `/employer/account/delete/` | Delete employer account |
| `/employer/logout/` | Logout |

## 14.4 Admin routes

Prefix:

```text
/admin-side/
```

| Route | Purpose |
|---|---|
| `/admin-side/login/` | Admin login |
| `/admin-side/logout/` | Admin logout |
| `/admin-side/` | Admin dashboard |
| `/admin-side/jobs/` | Job postings |
| `/admin-side/jobs/create/` | Create job |
| `/admin-side/jobs/<uuid>/` | Job detail |
| `/admin-side/applicants/` | Applicant list |
| `/admin-side/applicants/<uuid>/verify/` | Applicant verification |
| `/admin-side/employers/` | Employer list |
| `/admin-side/employers/<uuid>/verify/` | Employer verification |
| `/admin-side/referrals/` | Referral list |
| `/admin-side/referrals/create/` | Create referral |
| `/admin-side/special-programs/` | Special-program records |
| `/admin-side/special-programs/enroll/` | Enroll/edit beneficiary |
| `/admin-side/special-programs/<program_type>/` | Filtered special-program view |
| `/admin-side/reports/` | PESO report |
| `/admin-side/reports/excel/` | Excel report |
| `/admin-side/account/settings/` | Account settings |
| `/admin-side/account/help/` | Help |

---

# 15. Local Development Setup

## 15.1 Clone/extract the project

```bash
cd CAPESONECCT-testing-branch
```

## 15.2 Create a virtual environment

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

## 15.3 Install dependencies

```bash
pip install -r requirements.txt
```

### Important dependency check

The current code imports packages that are not all explicitly pinned in the checked-in `requirements.txt`.

In particular, verify that the environment has the packages needed by:

```text
whitenoise
chromadb
sentence-transformers
```

The job-matching engine also expects the `all-MiniLM-L6-v2` Sentence Transformer model to be available locally because the code uses:

```python
local_files_only=True
```

Do not assume a fresh machine can download the model automatically.

## 15.4 Configure environment variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

For production, use real secret values stored in the hosting provider's secret/environment configuration rather than committing them to Git.

## 15.5 Run migrations

```bash
python manage.py migrate
```

## 15.6 Create an administrator

The repository includes:

```bash
python manage.py seed_admin
```

The command reads:

```text
SEED_ADMIN_USER
SEED_ADMIN_EMAIL
SEED_ADMIN_PASSWORD
```

or falls back to the defaults coded in the command.

For safety, always set your own values:

```bash
export SEED_ADMIN_USER="peso_admin"
export SEED_ADMIN_EMAIL="admin@example.com"
export SEED_ADMIN_PASSWORD="CHANGE_THIS"
python manage.py seed_admin
```

On Windows PowerShell:

```powershell
$env:SEED_ADMIN_USER="peso_admin"
$env:SEED_ADMIN_EMAIL="admin@example.com"
$env:SEED_ADMIN_PASSWORD="CHANGE_THIS"
python manage.py seed_admin
```

## 15.7 Start the server

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

Admin:

```text
http://127.0.0.1:8000/admin-side/login/
```

API token endpoint:

```text
http://127.0.0.1:8000/api/token/
```

---

# 16. Environment Variables

The settings code expects/uses the following environment values.

| Variable | Required/Conditional | Purpose |
|---|---|---|
| `SECRET_KEY` | Required | Django secret key |
| `DEBUG` | Recommended | Enables/disables debug mode |
| `ALLOWED_HOSTS` | Production | Comma-separated allowed hosts |
| `RENDER_EXTERNAL_HOSTNAME` | Render deployment | Adds Render hostname and CSRF trusted origin |
| `CLOUDINARY_CLOUD_NAME` | Media storage | Cloudinary cloud |
| `CLOUDINARY_API_KEY` | Media storage | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Media storage | Cloudinary API secret |
| `EMAIL_HOST_USER` | Email | SMTP username |
| `EMAIL_HOST_PASSWORD` | Email | SMTP password/app password |
| `SEED_ADMIN_USER` | Seed command | Admin username |
| `SEED_ADMIN_EMAIL` | Seed command | Admin email |
| `SEED_ADMIN_PASSWORD` | Seed command | Admin password |

Database configuration is controlled through `dj_database_url`.

If no database URL is supplied, the project falls back to:

```text
sqlite:///db.sqlite3
```

---

# 17. Management Commands

## 17.1 Seed administrator

```bash
python manage.py seed_admin
```

Creates a Django superuser if the configured username does not already exist.

## 17.2 Seed PESO program data

```bash
python manage.py seed_peso <count>
```

Creates generated records for PESO-related beneficiary/activity models.

Example:

```bash
python manage.py seed_peso 10
```

## 17.3 Seed applicants/employers/jobs

```bash
python manage.py seed_beneficiaries <count>
```

Optional:

```bash
python manage.py seed_beneficiaries 10 --with-images
```

This generates sample applicants, employers, jobs, applications, and offers.

## 17.4 Seed offered jobs/referrals

```bash
python manage.py seed_offered_jobs
```

Optional count:

```bash
python manage.py seed_offered_jobs --count 25
```

## 17.5 Generate broader PESO test data

```bash
python manage.py peso_seed_data
```

Optional multiplier:

```bash
python manage.py peso_seed_data --count 20
```

## 17.6 Delete unverified accounts

```bash
python manage.py delete_unverified_users
```

This removes users who:

```text
email_verified = False
```

and whose verification timestamp is more than 24 hours old.

---

# 18. Deployment

The repository includes:

```text
build.sh
```

The build script performs:

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

The settings are prepared for deployment using:

- PostgreSQL or another database URL
- Render hostname support
- Cloudinary media storage
- WhiteNoise static files
- HTTPS/security settings when `DEBUG=False`

## Production checklist

Before deployment:

- [ ] Set a strong `SECRET_KEY`.
- [ ] Set `DEBUG=False`.
- [ ] Configure `ALLOWED_HOSTS`.
- [ ] Configure production database.
- [ ] Configure Cloudinary.
- [ ] Configure SMTP email.
- [ ] Configure a real admin password.
- [ ] Verify the Sentence Transformer model is available locally if matching is enabled.
- [ ] Ensure ChromaDB storage is persistent if recommendations must survive restarts.
- [ ] Run migrations.
- [ ] Run `collectstatic`.
- [ ] Test email verification.
- [ ] Test password reset.
- [ ] Test applicant approval.
- [ ] Test employer verification.
- [ ] Test job creation and matching.
- [ ] Test JWT authentication and API role restrictions.

---

# 19. Troubleshooting

## "Please verify your email before signing in"

The account exists but:

```text
email_verified = False
```

Use the verification email or investigate SMTP configuration.

## Applicant cannot apply

The applicant must have:

```text
ApplicantProfile.status = approved
```

The application view also requires the job to be:

```text
status = Active
```

and prevents duplicate applications.

## Employer cannot see applicants

The employer must have:

```text
verification_status = verified
```

and the applications must belong to that employer.

## API returns 401

Check:

```http
Authorization: Bearer <access-token>
```

Also verify that the access token is valid and has not expired.

## API returns 403

The JWT may be valid, but the authenticated user's role is not one of:

```text
mswdo
admin
peso
```

## Job recommendations are empty

Check:

1. ChromaDB is available.
2. The `chroma_data/` directory can be written.
3. The `all-MiniLM-L6-v2` model is available locally.
4. Jobs have been indexed.
5. Jobs are still `Active`.

## Static files are missing

Run:

```bash
python manage.py collectstatic --no-input
```

and verify WhiteNoise/static configuration.

## Database connection issues

If no external database URL is supplied, Django falls back to SQLite.

For production, verify the database URL passed to `dj_database_url`.

---

# 20. Implementation Notes and Known Gaps

This section is intentionally included because the README is based on the source code rather than only the UI.

## 20.1 Existing README API paths are outdated

The repository's previous README lists endpoints such as:

```text
/special-programs/
```

but `config/urls.py` mounts `MSWDAPI.urls` under:

```text
/api/
```

The correct application routes are therefore:

```text
/api/special-programs/
/api/government-internships/
/api/tupad-beneficiaries/
/api/displaced-informal-labor-programs/
/api/career-guidance-beneficiaries/
```

## 20.2 API is read-only

The API currently exposes:

- JWT token creation
- JWT refresh
- GET list
- GET detail

There are no POST/PUT/PATCH/DELETE beneficiary API views in `MSWDAPI`.

Beneficiary creation/editing is performed through the web/admin side.

## 20.3 API role enforcement is explicit

`MSWDRolePermission` accepts:

```python
['mswdo', 'admin', 'peso']
```

Applicants and employers cannot use the MSWD API.

## 20.4 Admin portal uses superuser status in several places

The dedicated admin login requires:

```python
request.user.is_superuser
```

The `SuperuserRequiredMixin` does the same.

This means the administrative portal is not simply controlled by:

```text
role == "admin"
```

A Django superuser is the important administrative credential.

## 20.5 Seeded admin role/API access should be verified

`seed_admin` creates a Django superuser but does not explicitly set:

```text
role = "admin"
```

The `User` model defaults `role` to:

```text
applicant
```

Therefore, after running `seed_admin`, verify the user's role if that account also needs API access. The API requires the `admin` role, while the admin web portal checks `is_superuser`.

## 20.6 Some admin-side views only check authentication

Several admin-side views inherit `LoginRequiredMixin` without also inheriting `SuperuserRequiredMixin`.

If strict administrative isolation is required, those views should be reviewed and consistently protected by the intended role/superuser permission.

## 20.7 Employer creation vs verification

The employer job creation view checks that the user is an employer, but the job update/delete/detail views explicitly require a verified employer.

This means the intended business rule appears to be "verified employers manage jobs", but the current create path does not enforce verification as strictly as update/delete/detail.

Review this if unverified employers must never create postings.

## 20.8 Applicant status choices vs dashboard/reporting

`ApplicantProfile.status` uses:

```text
pending
approved
rejected
```

`AppliedJobs.status` defines:

```text
pending
reviewed
for interview
hired
rejected
```

Some dashboard/reporting code also checks:

```text
near_hire
withdrawn
```

Those values are not present in the current `AppliedJobs.APPLICATION_STATUS` choices.

If those states are intended to be supported, they should be added consistently to the model/form/UI/reporting layer.

## 20.9 Job matching dependencies

The source imports ChromaDB and uses Sentence Transformers, but those dependencies are not all explicitly present in the current `requirements.txt`.

Before deploying from a clean environment, verify/install the packages required by:

```text
JobMatchingEngine/config.py
```

and ensure the local embedding model exists.

## 20.10 Job matching persistence

ChromaDB is configured with:

```text
<project-root>/chroma_data
```

For a platform where the filesystem is ephemeral, job embeddings can disappear after a restart unless this directory is stored on persistent storage or the vectors are rebuilt.

## 20.11 Model naming

The model called `ApplicantProfile` contains both the modern structured fields and a large set of NSRP-style fields, including training, preferences, skills, documents, and contact information.

When extending the application, prefer using the existing model rather than creating a second applicant profile model without a migration/design reason.

---

# 21. Developer Quick Reference

## Start locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Create admin

```bash
python manage.py seed_admin
```

## Main URLs

```text
Web:
http://127.0.0.1:8000/

Normal login:
http://127.0.0.1:8000/login/

Admin:
http://127.0.0.1:8000/admin-side/login/

Applicant:
http://127.0.0.1:8000/applicant/

Employer:
http://127.0.0.1:8000/employer/

API:
http://127.0.0.1:8000/api/
```

## JWT

```text
POST /api/token/
POST /api/token/refresh/
```

## Special-program API

```text
GET /api/special-programs/
GET /api/special-programs/<uuid>/

GET /api/government-internships/
GET /api/government-internships/<uuid>/

GET /api/tupad-beneficiaries/
GET /api/tupad-beneficiaries/<uuid>/

GET /api/displaced-informal-labor-programs/
GET /api/displaced-informal-labor-programs/<uuid>/

GET /api/career-guidance-beneficiaries/
GET /api/career-guidance-beneficiaries/<uuid>/
```

## Important model relationships

```text
User
├── ApplicantProfile
│   ├── ApplicantSkills
│   ├── ApplicantWorkExperience
│   ├── AppliedJobs
│   ├── SavedJobs
│   └── OfferedJobs
│
└── EmployerProfile
    └── Jobs
         ├── AppliedJobs
         ├── SavedJobs
         └── OfferedJobs
```

## Core status values

Applicant:

```text
pending
approved
rejected
```

Employer:

```text
pending
verified
rejected
```

Job:

```text
Active
Filled
Closed
```

Application/referral:

```text
pending
reviewed
for interview
hired
rejected
```

---

## License / Project Ownership

No explicit open-source license was identified in the reviewed repository. Add the project's official license/ownership statement here if one exists.

---

## Documentation Scope

This README was generated from inspection of the current source tree, including:

- Django URL configurations
- settings
- models
- forms
- views
- API serializers/views
- permission classes
- job-matching engine
- management commands
- deployment script
- existing project README

When behavior in the UI and code differs, treat the source code as the authoritative implementation until the code is changed.
