\# Production Migration Runbook



\## Purpose



This document defines the controlled procedure for applying database migrations to a production environment.



The objective is to ensure that schema changes are applied safely, consistently, and with a clear rollback strategy.



\---



\## 1. Preconditions



Before running any production migration:



1\. Confirm the correct Git branch and commit.

2\. Confirm the production environment variables are configured.

3\. Confirm the database connection points to the intended production database.

4\. Confirm the current Alembic revision.

5\. Confirm the target Alembic revision exists in the deployed code.

6\. Create a database backup before applying the migration.



\---



\## 2. Verify Application Version



From the deployed application directory:



```powershell

git status

git log -1 --oneline

