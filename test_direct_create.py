"""Direct test of project creation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing project creation directly...\n")

try:
    from src.database.connection import get_db
    from src.database.repository import ProjectRepository
    
    print("✅ Imports successful")
    
    with get_db() as db:
        print("✅ Database connection successful")
        
        project = ProjectRepository.create_project(
            db,
            name="Test Project",
            description="This is a test"
        )
        print(f"✅ Project created: {project.project_id}")
        
        # Test to_dict()
        project_dict = project.to_dict()
        print(f"✅ to_dict() successful: {project_dict}")
        
        # Try to serialize to JSON
        import json
        json_str = json.dumps(project_dict, indent=2)
        print(f"\n✅ JSON serialization successful:\n{json_str}")
        
except Exception as e:
    print(f"\n❌ Error occurred: {e}")
    import traceback
    traceback.print_exc()
