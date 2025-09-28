#!/usr/bin/env python3
"""
CDP Ninja Documentation Extractor
Extracts JSDoc-style API documentation from Python route files
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class JSDocExtractor:
    """Extract JSDoc-style documentation from Python functions"""

    def __init__(self, routes_dir: str = "cdp_ninja/routes"):
        self.routes_dir = Path(routes_dir)
        self.extracted_docs = {}

    def extract_function_docs(self, file_path: Path) -> List[Dict]:
        """Extract JSDoc documentation from a Python file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        docs = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.body:
                # Check if first statement is a docstring
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    docstring = first.value.value
                    if isinstance(docstring, str) and '@route' in docstring:
                        docs.append(self.parse_jsdoc(node.name, docstring))

        return docs

    def parse_jsdoc(self, func_name: str, docstring: str) -> Dict:
        """Parse JSDoc-style annotations from docstring"""
        doc = {
            'function_name': func_name,
            'description': '',
            'route': '',
            'params': [],
            'returns': '',
            'examples': []
        }

        lines = docstring.split('\n')
        current_section = 'description'
        example_lines = []

        for line in lines:
            line = line.strip()

            if line.startswith('@route'):
                doc['route'] = line.replace('@route', '').strip()
                current_section = 'route'
            elif line.startswith('@param'):
                # Parse @param {type} name - description
                param_match = re.match(r'@param\s+\{([^}]+)\}\s+(\[?[^-\]]+\]?)\s*-?\s*(.*)', line)
                if param_match:
                    param_type, param_name, param_desc = param_match.groups()
                    doc['params'].append({
                        'type': param_type,
                        'name': param_name.strip('[]'),
                        'optional': param_name.startswith('['),
                        'description': param_desc
                    })
                current_section = 'params'
            elif line.startswith('@returns'):
                doc['returns'] = line.replace('@returns', '').strip()
                current_section = 'returns'
            elif line.startswith('@example'):
                current_section = 'example'
                example_lines = []
            elif current_section == 'example' and line:
                example_lines.append(line)
            elif current_section == 'description' and line and not line.startswith('@'):
                if doc['description']:
                    doc['description'] += ' '
                doc['description'] += line

        if example_lines:
            doc['examples'] = example_lines

        return doc

    def extract_all_docs(self) -> Dict[str, List[Dict]]:
        """Extract documentation from all route files"""
        docs_by_file = {}

        for py_file in self.routes_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                try:
                    docs = self.extract_function_docs(py_file)
                    if docs:
                        docs_by_file[py_file.stem] = docs
                        print(f"✅ Extracted {len(docs)} endpoints from {py_file.name}")
                except Exception as e:
                    print(f"❌ Error processing {py_file.name}: {e}")

        return docs_by_file

    def generate_markdown_docs(self, docs_by_file: Dict) -> None:
        """Generate markdown documentation files by domain"""

        # Domain mapping
        domain_mapping = {
            'system': 'System Commands',
            'browser': 'Browser Interaction',
            'performance': 'Performance & Memory',
            'security': 'Security Testing',
            'network_intelligence': 'Network Monitoring',
            'stress_testing': 'Stress Testing',
            'stress_testing_advanced': 'Advanced Stress Testing',
            'accessibility': 'Accessibility',
            'error_handling': 'Error Handling',
            'navigation': 'Page Navigation',
            'dom': 'DOM Operations',
            'dom_advanced': 'Advanced DOM',
            'debugging': 'Debugging',
            'js_debugging': 'JavaScript Debugging'
        }

        docs_dir = Path("docs/usage")
        docs_dir.mkdir(exist_ok=True)

        total_endpoints = 0

        for file_stem, docs in docs_by_file.items():
            domain_name = domain_mapping.get(file_stem, file_stem.replace('_', ' ').title())

            # Generate markdown content
            md_content = f"# {domain_name} API\n\n"
            md_content += f"*Auto-generated from {file_stem}.py JSDoc comments*\n\n"

            for doc in docs:
                total_endpoints += 1
                md_content += f"## {doc['route']}\n\n"
                md_content += f"**Function:** `{doc['function_name']}()`\n\n"

                if doc['description']:
                    md_content += f"{doc['description']}\n\n"

                if doc['params']:
                    md_content += "**Parameters:**\n"
                    for param in doc['params']:
                        optional = " *(optional)*" if param['optional'] else ""
                        md_content += f"- `{param['name']}` *({param['type']})*{optional}: {param['description']}\n"
                    md_content += "\n"

                if doc['returns']:
                    md_content += f"**Returns:** {doc['returns']}\n\n"

                if doc['examples']:
                    md_content += "**Examples:**\n```javascript\n"
                    md_content += '\n'.join(doc['examples'])
                    md_content += "\n```\n\n"

                md_content += "---\n\n"

            # Write to file
            output_file = docs_dir / f"{file_stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)

            print(f"📝 Generated {output_file} with {len(docs)} endpoints")

        print(f"\n🎉 Generated documentation for {total_endpoints} total endpoints")


def main():
    """Main execution"""
    print("🥷 CDP Ninja Documentation Extractor")
    print("=" * 40)

    extractor = JSDocExtractor()
    docs_by_file = extractor.extract_all_docs()

    if docs_by_file:
        extractor.generate_markdown_docs(docs_by_file)

        # Generate summary
        total_files = len(docs_by_file)
        total_endpoints = sum(len(docs) for docs in docs_by_file.values())

        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"   • Files processed: {total_files}")
        print(f"   • Total endpoints: {total_endpoints}")
        print(f"   • Documentation files: docs/usage/")
    else:
        print("❌ No JSDoc documentation found")


if __name__ == "__main__":
    main()