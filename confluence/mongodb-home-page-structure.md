# Proposed MongoDB Confluence Page Structure

## Purpose

Use the MongoDB home page as a navigation and ownership page. Store detailed content in categorized child pages rather than keeping every document directly below the home page.

Confluence uses a page hierarchy rather than filesystem folders. Keep the hierarchy to approximately three or four levels so pages remain easy to find.

## Proposed Page Hierarchy

```text
MongoDB Home Page
│
├── 1. Architecture and Environments
│   ├── MongoDB Architectural Diagrams
│   ├── Cluster and Database Inventory
│   │   └── Production Databases by Cluster
│   └── Collection Index Inventory by Environment
│
├── 2. Standards and Governance
│   ├── MongoDB Naming Conventions
│   ├── Development and Deployment Standards
│   └── MongoDB Backlog and Roadmap
│
├── 3. Access and Security
│   ├── MongoDB User Account Creation
│   ├── MongoDB User Access Privileges
│   └── MongoDB OIDC
│       ├── OIDC Configuration
│       └── OIDC Support and Troubleshooting
│
├── 4. Operations and Automation
│   ├── MongoDB Useful Scripts
│   ├── Index Management
│   ├── CI/CD Deployment
│   └── Operational Runbooks
│
├── 5. Capacity and Performance
│   ├── MongoDB Cluster Sizing
│   ├── Application Sizing Questionnaire
│   └── Performance and Capacity Reviews
│
├── 6. Migrations and Modernization
│   └── Oracle to MongoDB
│       ├── Migration Overview
│       ├── Oracle to MongoDB Migration Checklist
│       ├── Relational Migrator
│       │   ├── Relational Migrator Learning Labs
│       │   │   ├── Lab 1 – One Table to One Collection
│       │   │   ├── Lab 2 – Two Referenced Collections
│       │   │   └── Lab 3 – Embedded Child Array
│       │   ├── Permissions and Connections
│       │   ├── Snapshot Migration
│       │   └── CDC, AMP, and Troubleshooting
│       └── Migration Validation and Reconciliation
│
└── 7. Support and Troubleshooting
    ├── Common MongoDB Issues
    ├── Connection Problems
    └── Escalation and Support Contacts
```

## Relational Migrator Lab Placement

Place the Relational Migrator teaching document at:

```text
MongoDB Home Page
└── Migrations and Modernization
    └── Oracle to MongoDB
        └── Relational Migrator
            └── Relational Migrator Learning Labs
```

Initially, keep all three labs in one page:

1. One Oracle table to one MongoDB collection.
2. Two related tables as separate referenced collections.
3. Two related tables with the child rows embedded in the parent.

Create separate child pages for the labs only when they become large enough to require independent ownership, revision history, or review.

## Existing Page Placement

| Existing content | Proposed parent |
|---|---|
| Architectural diagrams | Architecture and Environments |
| Production databases by cluster | Architecture and Environments → Cluster and Database Inventory |
| Collection indexes by environment | Architecture and Environments |
| Naming conventions | Standards and Governance |
| Backlog activities | Standards and Governance → MongoDB Backlog and Roadmap |
| User account creation | Access and Security |
| User access privileges | Access and Security |
| OIDC configuration and support | Access and Security → MongoDB OIDC |
| Useful scripts | Operations and Automation |
| Cluster sizing | Capacity and Performance |
| Oracle-to-MongoDB checklist | Migrations and Modernization → Oracle to MongoDB |
| Relational Migrator labs | Migrations and Modernization → Oracle to MongoDB → Relational Migrator |

## Home Page Content

The MongoDB home page should contain:

- A short description of the team's MongoDB responsibilities.
- Links to the seven top-level categories.
- Service ownership and support-contact information.
- Links to commonly used operational runbooks.
- A recently updated section.
- A page-tree or children-display macro.

Do not place credentials, internal connection strings, hostnames, or production data on the home page.

## Content Ownership

Use each platform for its intended purpose:

| Content | System of record |
|---|---|
| Operational procedures and internal environment information | Confluence |
| Executable scripts and deployment configuration | Internal GitLab |
| Work requests, approvals, and implementation tracking | Jira |
| Sanitized reusable templates and teaching examples | Public GitHub repository |

