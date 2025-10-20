"""Test project creation."""

import sys
sys.path.insert(0, '.')

from src.database.connection import get_db
from src.database.repository import ProjectRepository

try:
    print("Testing project creation...")
    with get_db() as db:
        project = ProjectRepository.create_project(
            db,
            name="Test Project",
            description="This is a test project"
        )
        print(f"✅ Project created successfully!")
        print(f"   ID: {project.project_id}")
        print(f"   Name: {project.name}")
        print(f"   Description: {project.description}")
        print(f"\n   to_dict(): {project.to_dict()}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
