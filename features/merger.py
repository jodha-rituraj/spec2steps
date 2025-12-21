import re
from typing import List, Set, Tuple


class JavaFileMerger:
    """
    A class to merge multiple Java files into a single file with:
    - Deduplicated field declarations at the top
    - All methods combined below
    - Single class definition
    """
    
    def __init__(self, merged_class_name: str = None):
        """
        Initialize the JavaFileMerger.
        
        Args:
            merged_class_name: Name for the merged class (uses first class name if None)
        """
        self.merged_class_name = merged_class_name
        self.packages = set()
        self.imports = set()
        self.fields = {}  # Dict to deduplicate fields
        self.methods = []
        self.class_name = merged_class_name
    
    def merge(self, java_files: List[str]) -> str:
        """
        Merges multiple Java file contents into a single file.
        
        Args:
            java_files: List of Java file contents as strings
        
        Returns:
            Merged Java file content as a string
        """
        self._reset()
        
        for content in java_files:
            self._process_file(content)
        
        # Use default class name if none found
        if not self.class_name:
            self.class_name = "MergedClass"
        
        return self._build_merged_file()
    
    def _reset(self):
        """Reset internal state for a new merge operation."""
        self.packages = set()
        self.imports = set()
        self.fields = {}
        self.methods = []
        if not self.merged_class_name:
            self.class_name = None
        else:
            self.class_name = self.merged_class_name
    
    def _process_file(self, content: str):
        """Process a single Java file and extract its components."""
        # Extract package
        pkg = self._extract_package(content)
        if pkg:
            self.packages.add(pkg)
        
        # Extract imports
        self.imports.update(self._extract_imports(content))
        
        # Extract class name if not set
        if not self.class_name:
            self.class_name = self._extract_class_name(content)
        
        # Extract and separate fields vs methods
        class_fields, class_methods = self._extract_fields_and_methods(content)
        
        # Deduplicate fields
        for field in class_fields:
            field_key = self._normalize_field_declaration(field)
            if field_key not in self.fields:
                self.fields[field_key] = field
        
        # Add all methods
        self.methods.extend(class_methods)
    
    def _extract_package(self, content: str) -> str:
        """Extract package declaration from Java file."""
        match = re.search(r'^package\s+[\w.]+;', content, re.MULTILINE)
        return match.group(0) if match else None
    
    def _extract_imports(self, content: str) -> Set[str]:
        """Extract all import statements from Java file."""
        imports = set()
        pattern = r'^import\s+(?:static\s+)?[\w.*]+;'
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            imports.add(match.group(0))
        return imports
    
    def _extract_class_name(self, content: str) -> str:
        """Extract the class name from Java file."""
        match = re.search(r'public\s+class\s+(\w+)', content)
        return match.group(1) if match else None
    
    def _extract_fields_and_methods(self, content: str) -> Tuple[List[str], List[str]]:
        """
        Extract fields and methods separately from a Java class.
        
        Returns:
            Tuple of (fields_list, methods_list)
        """
        class_match = re.search(r'public\s+class\s+\w+[^{]*{', content)
        if not class_match:
            return ([], [])
        
        class_start = class_match.end()
        class_content = content[class_start:]
        
        # Find the matching closing brace
        brace_count = 1
        class_end = 0
        
        for i, char in enumerate(class_content):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    class_end = i
                    break
        
        class_body = class_content[:class_end].strip()
        
        if not class_body:
            return ([], [])
        
        # Separate fields and methods
        fields = []
        methods = []
        
        members = self._extract_individual_members(class_body)
        
        for member in members:
            if self._is_field_declaration(member):
                fields.append(member)
            else:
                methods.append(member)
        
        return (fields, methods)
    
    def _extract_individual_members(self, class_body: str) -> List[str]:
        """Split class body into individual members (methods, fields, etc.)"""
        members = []
        lines = class_body.split('\n')
        current_member = []
        brace_count = 0
        in_member = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines between members
            if not stripped and not in_member:
                continue
            
            # Check if this line starts a new member
            if not in_member and stripped:
                in_member = True
            
            if in_member:
                current_member.append(line)
                
                # Count braces
                for char in line:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                
                # Check if we've completed a member
                if brace_count == 0 and (stripped.endswith(';') or stripped.endswith('}')):
                    member_text = '\n'.join(current_member).strip()
                    if member_text:
                        members.append(member_text)
                    current_member = []
                    in_member = False
        
        # Handle any remaining content
        if current_member:
            member_text = '\n'.join(current_member).strip()
            if member_text:
                members.append(member_text)
        
        return members
    
    def _is_field_declaration(self, member: str) -> bool:
        """Determine if a member is a field declaration vs a method."""
        member_stripped = member.strip()
        
        # Check if it's a method declaration pattern
        if re.match(r'@\w+', member_stripped):  # Starts with annotation
            return False
        
        if re.search(r'\b\w+\s+\w+\s*\([^)]*\)\s*{', member_stripped):  # Method signature
            return False
        
        # Check ending
        lines = member_stripped.split('\n')
        last_line = lines[-1].strip()
        
        if last_line.endswith(';'):
            return True
        if last_line.endswith('}'):
            return False
        
        # Default: if it has an opening brace, it's likely a method
        if '{' in member_stripped:
            return False
        
        return True
    
    def _normalize_field_declaration(self, field: str) -> str:
        """
        Normalize a field declaration for comparison.
        Extracts the core declaration pattern (modifiers + type + variable name).
        """
        # Remove extra whitespace and newlines
        normalized = ' '.join(field.split())
        
        # Extract pattern: modifiers type variableName
        match = re.match(r'((?:public|private|protected|static|final|\s)+)([\w<>.,\s]+?)\s+(\w+)\s*[=;]', normalized)
        if match:
            modifiers = ' '.join(match.group(1).split())
            field_type = match.group(2).strip()
            field_name = match.group(3)
            return f"{modifiers} {field_type} {field_name}"
        
        return normalized
    
    def _build_merged_file(self) -> str:
        """Build the final merged Java file content."""
        lines = []
        
        # Add package
        if self.packages:
            sorted_packages = sorted(self.packages)
            lines.append(sorted_packages[0])
            lines.append('')
        
        # Add imports
        sorted_imports = sorted(self.imports)
        lines.extend(sorted_imports)
        
        if sorted_imports:
            lines.append('')
        
        # Add class declaration
        lines.append(f'public class {self.class_name} {{')
        lines.append('')
        
        # Add all FIELDS first (deduplicated)
        if self.fields:
            for field in self.fields.values():
                indented_field = '\n'.join('    ' + line if line.strip() else '' 
                                          for line in field.split('\n'))
                lines.append(indented_field)
            lines.append('')
        
        # Add all METHODS
        for i, method in enumerate(self.methods):
            indented_method = '\n'.join('    ' + line if line.strip() else '' 
                                       for line in method.split('\n'))
            lines.append(indented_method)
            
            if i < len(self.methods) - 1:
                lines.append('')
        
        # Close class
        lines.append('}')
        
        return '\n'.join(lines)


if __name__ == "__main__":
    file1 = """
    package com.example.test;
    
    import org.junit.Test;
    
    public class Test1 {
        ApiClient apiClient = new ApiClient();
        static Logger logger = LogManager.getLogger(Test1.class);
        
        @Given("something")
        public void testMethod1() {
            System.out.println("Test 1");
        }
    }
    """
    
    file2 = """
    package com.example.test;
    
    import org.junit.Test;
    
    public class Test2 {
        ApiClient apiClient = new ApiClient();
        static String orderId;
        
        @When("something else")
        public void testMethod2() {
            System.out.println("Test 2");
        }
    }
    """
    
    # Create merger and merge files
    merger = JavaFileMerger(merged_class_name = "MergedTestClass")
    merged_content = merger.merge([file1, file2])
    
    print(merged_content)