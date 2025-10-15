#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check database contents"""

from src.database.connection import get_db
from src.database.models import Project, Scan, Endpoint, Vulnerability

def check_database():
    with get_db() as db:
        projects = db.query(Project).count()
        scans = db.query(Scan).count()
        endpoints = db.query(Endpoint).count()
        vulnerabilities = db.query(Vulnerability).count()

        print("=" * 50)
        print("Database Status")
        print("=" * 50)
        print(f"Projects: {projects}")
        print(f"Scans: {scans}")
        print(f"Endpoints: {endpoints}")
        print(f"Vulnerabilities: {vulnerabilities}")
        print("=" * 50)

        if projects == 0 and scans == 0:
            print("[OK] Database is empty and ready to use")
        else:
            print("[INFO] Database contains data")

if __name__ == "__main__":
    check_database()
