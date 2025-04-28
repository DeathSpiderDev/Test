import os
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class WorkflowGenerator:
    def __init__(self, workflow_dir: str = ".github/workflows", max_workflows: int = 10):
        self.workflow_dir = workflow_dir
        self.max_workflows = max_workflows
        os.makedirs(self.workflow_dir, exist_ok=True)

    def _enforce_limits(self):
        """Ensure we don't exceed max workflow limit by deleting oldest ones"""
        workflows = sorted(
            [f for f in os.listdir(self.workflow_dir) if f.endswith('.yml') or f.endswith('.yaml')],
            key=lambda x: os.path.getmtime(os.path.join(self.workflow_dir, x))
        
        while len(workflows) >= self.max_workflows:
            oldest = workflows.pop(0)
            os.remove(os.path.join(self.workflow_dir, oldest))
            print(f"Deleted old workflow: {oldest} to maintain limit")

    def _generate_filename(self, workflow_name: str) -> str:
        """Generate a unique filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = workflow_name.lower().replace(' ', '_')
        return f"{clean_name}_{timestamp}.yml"

    def _validate_workflow(self, workflow: Dict) -> bool:
        """Basic validation of workflow structure"""
        required = ['name', 'on', 'jobs']
        return all(key in workflow for key in required)

    def _workflow_exists(self, workflow: Dict) -> bool:
        """Check if similar workflow already exists"""
        existing = [f for f in os.listdir(self.workflow_dir) 
                   if f.endswith('.yml') or f.endswith('.yaml')]
        
        for filename in existing:
            with open(os.path.join(self.workflow_dir, filename)) as f:
                existing_workflow = yaml.safe_load(f)
                if (existing_workflow['name'] == workflow['name'] and
                    existing_workflow['on'] == workflow['on']):
                    return True
        return False

    def create_workflow(self, workflow: Dict, force: bool = False) -> bool:
        """
        Create a new GitHub workflow with limits and validation
        
        Args:
            workflow: Dictionary containing workflow definition
            force: Create even if similar workflow exists
            
        Returns:
            bool: True if workflow was created, False otherwise
        """
        if not self._validate_workflow(workflow):
            print("Invalid workflow structure. Must contain 'name', 'on', and 'jobs'")
            return False
            
        if self._workflow_exists(workflow) and not force:
            print(f"Similar workflow already exists: {workflow['name']}")
            return False
            
        self._enforce_limits()
        
        filename = self._generate_filename(workflow['name'])
        filepath = os.path.join(self.workflow_dir, filename)
        
        with open(filepath, 'w') as f:
            yaml.dump(workflow, f, sort_keys=False)
            
        print(f"Created new workflow: {filename}")
        return True

    def create_from_template(self, template_name: str, **kwargs) -> bool:
        """Create workflow from a predefined template"""
        templates = {
            'python-ci': {
                'name': 'Python CI',
                'on': {'push': {'branches': ['main', 'master']}, 
                      'pull_request': {'branches': ['main', 'master']}},
                'jobs': {
                    'build': {
                        'runs-on': 'ubuntu-latest',
                        'steps': [
                            {'uses': 'actions/checkout@v4'},
                            {'uses': 'actions/setup-python@v4', 
                             'with': {'python-version': kwargs.get('python_version', '3.10')}},
                            {'run': 'pip install -r requirements.txt'},
                            {'run': 'pytest'}
                        ]
                    }
                }
            },
            'node-ci': {
                'name': 'Node.js CI',
                'on': {'push': {'branches': ['main', 'master']}},
                'jobs': {
                    'build': {
                        'runs-on': 'ubuntu-latest',
                        'steps': [
                            {'uses': 'actions/checkout@v4'},
                            {'uses': 'actions/setup-node@v3',
                             'with': {'node-version': kwargs.get('node_version', '16')}},
                            {'run': 'npm ci'},
                            {'run': 'npm test'}
                        ]
                    }
                }
            }
        }
        
        if template_name not in templates:
            print(f"Unknown template: {template_name}. Available: {list(templates.keys())}")
            return False
            
        return self.create_workflow(templates[template_name])

    def cleanup_old_workflows(self, days: int = 30):
        """Delete workflows older than X days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(self.workflow_dir):
            if filename.endswith('.yml') or filename.endswith('.yaml'):
                filepath = os.path.join(self.workflow_dir, filename)
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    os.remove(filepath)
                    print(f"Deleted old workflow: {filename} (last modified {mtime})")


# Example Usage
if __name__ == "__main__":
    generator = WorkflowGenerator(max_workflows=5)
    
    # Create from template
    generator.create_from_template('python-ci', python_version='3.11')
    generator.create_from_template('node-ci', node_version='18')
    
    # Create custom workflow
    custom_workflow = {
        'name': 'Custom Deployment',
        'on': {'workflow_dispatch': {}},
        'jobs': {
            'deploy': {
                'runs-on': 'ubuntu-latest',
                'steps': [
                    {'uses': 'actions/checkout@v4'},
                    {'name': 'Deploy to production',
                     'run': './deploy.sh production'}
                ]
            }
        }
    }
    generator.create_workflow(custom_workflow)
    
    # Cleanup old workflows
    generator.cleanup_old_workflows(days=7)
