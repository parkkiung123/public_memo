@echo off
chcp 65001 > nul

set PGPASSWORD=xxx
set PGCLIENTENCODING=UTF8

psql -d testDB -U postgres -Atc "SELECT schemaname||'.'||tablename FROM pg_tables WHERE schemaname='public'" > tables.txt

for /f %%t in (tables.txt) do (
  echo ----- %%t ----- >> dump.sql
  psql -d testDB -U postgres -P pager=off -c "\d+ %%t" | python psql_to_ddl.py >> dump.sql
)

del tables.txt