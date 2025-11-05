#!/bin/bash
# Healthcheck script for SQL Server
# This script is used by the database container healthcheck

# Use the MSSQL_SA_PASSWORD from environment
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q 'SELECT 1' -b -o /dev/null

