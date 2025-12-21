import re
from typing import List, Set

def mergeJavaFiles(javaFiles: List[str]) -> str:
    """
    Merges multiple Java file contents into a single file with:
    - All unique package declarations
    - Deduplicated imports
    - All public classes preserved separately
    
    Args:
        javaFiles: List of Java file contents as strings
    
    Returns:
        Merged Java file content as a string
    """
    packages = set()
    imports = set()
    classes = []
    
    for content in javaFiles:
        # Extract package (collect all unique)
        pkg = extractPackagesFromJavaFile(content)
        if pkg:
            packages.add(pkg)

        # Extract imports (collect all unique)
        imports.update(extractImportsFromJavaFile(content))
        
        # Extract complete class definition
        classDefinition = extractClassDefinitionFromJavaFile(content)
        if classDefinition:
            classes.append(classDefinition)    

    # Build merged file
    mergedJavaContent = createMergedJavaFile(
        packages,
        imports,
        classes
    )
    
    return mergedJavaContent


def extractPackagesFromJavaFile(content: str) -> str:
    match = re.search(r'^package\s+[\w.]+;', content, re.MULTILINE)
    return match.group(0) if match else None

def extractImportsFromJavaFile(content: str) -> Set[str]:
    imports = set()
    pattern = r'^import\s+(?:static\s+)?[\w.*]+;'
    matches = re.finditer(pattern, content, re.MULTILINE)
    for match in matches:
        imports.add(match.group(0))
    return imports

def extractClassDefinitionFromJavaFile(content: str) -> str:
    # Find the class declaration
    classMatch = re.search(r'public\s+class\s+\w+\s*{', content)
    if not classMatch:
        return None
    
    # Get content starting from class declaration
    classStart = classMatch.start()
    classContent = content[classStart:]
    
    # Find the matching closing brace for the class
    braceCount = 0
    classEnd = 0
    
    for i, char in enumerate(classContent):
        if char == '{':
            braceCount += 1
        elif char == '}':
            braceCount -= 1
            if braceCount == 0:
                classEnd = i + 1
                break
    
    return classContent[:classEnd].strip()


def createMergedJavaFile(packages: Set[str], imports: Set[str], 
                                   classes: List[str]) -> str:
    lines = []
    
    # Add all packages (sorted for consistency)
    sortedPackages = sorted(packages)
    lines.extend(sortedPackages)
    
    if sortedPackages:
        lines.append('')
    
    # Add imports (sorted for consistency)
    sortedImports = sorted(imports)
    lines.extend(sortedImports)
    
    if sortedImports:
        lines.append('')
    
    # Add all classes
    for i, classDefinition in enumerate(classes):
        lines.append(classDefinition)
        # Add blank line between classes (but not after the last one)
        if i < len(classes) - 1:
            lines.append('')
    
    return '\n'.join(lines)


def extractClassNameFromJavaFile(content: str) -> str:
    """
    Extract the class name from Java file.
    
    Args:
        content: Java file content as string
    
    Returns:
        Class name as string, or None if not found
    """
    match = re.search(r'public\s+class\s+(\w+)', content)
    return match.group(1) if match else None

def extractIndividualMembers(classBody: str) -> List[str]:
    """
    Splits class body into individual members (methods, fields, etc.)
    """
    members = []
    lines = classBody.split('\n')
    currentMember = []
    braceCount = 0
    inMember = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines between members
        if not stripped and not inMember:
            continue
        
        # Check if this line starts a new member
        if not inMember and stripped:
            inMember = True
        
        if inMember:
            currentMember.append(line)
            
            # Count braces
            for char in line:
                if char == '{':
                    braceCount += 1
                elif char == '}':
                    braceCount -= 1
            
            # Check if we've completed a member
            # Field declarations end with semicolon at brace level 0
            # Methods/constructors end when braces return to 0
            if braceCount == 0 and (stripped.endswith(';') or stripped.endswith('}')):
                memberText = '\n'.join(currentMember).strip()
                if memberText:
                    members.append(memberText)
                currentMember = []
                inMember = False
    
    # Handle any remaining content
    if currentMember:
        memberText = '\n'.join(currentMember).strip()
        if memberText:
            members.append(memberText)
    
    return members

def mergeJavaFilesWithSingleClass(javaFiles: List[str], mergedClassName: str = None) -> str:
    """
    Merges multiple Java file contents into a single file with one class.
    Deduplicates field initializations and static variables, keeping only unique ones at the top.
    
    Args:
        javaFiles: List of Java file contents as strings
        mergedClassName: Name for the merged class (uses first class name if None)
    
    Returns:
        Merged Java file content as a string with single class
    """
    packages = set()
    imports = set()
    fields = {}  # Dict to deduplicate fields by their declaration
    methods = []  # All methods
    className = mergedClassName
    
    for content in javaFiles:
        # Extract package
        pkg = extractPackagesFromJavaFile(content)
        if pkg:
            packages.add(pkg)

        # Extract imports
        imports.update(extractImportsFromJavaFile(content))
        
        # Extract class name if not set
        if not className:
            className = extractClassNameFromJavaFile(content)
        
        # Extract and separate fields vs methods
        classFields, classMethods = extractFieldsAndMethodsFromJavaFile(content)
        
        # Deduplicate fields by their normalized form
        for field in classFields:
            fieldKey = normalizeFieldDeclaration(field)
            if fieldKey not in fields:
                fields[fieldKey] = field
        
        # Add all methods
        methods.extend(classMethods)
    
    # Use first class name if none provided
    if not className:
        className = "MergedClass"
    
    # Build merged file with single class
    mergedJavaContent = createMergedJavaFileWithSingleClass(
        packages,
        imports,
        className,
        list(fields.values()),
        methods
    )
    
    return mergedJavaContent


def normalizeFieldDeclaration(field: str) -> str:
    """
    Normalizes a field declaration for comparison.
    Extracts the core declaration pattern (type + variable name).
    """
    # Remove extra whitespace and newlines
    normalized = ' '.join(field.split())
    
    # Extract the pattern: modifiers type variableName
    # Examples:
    # "ApiClient apiClient = new ApiClient();" -> "ApiClient apiClient"
    # "static Logger logger = LogManager.getLogger(...);" -> "static Logger logger"
    # "static String orderId;" -> "static String orderId"
    
    match = re.match(r'((?:public|private|protected|static|final|\s)+)([\w<>.,\s]+?)\s+(\w+)\s*[=;]', normalized)
    if match:
        modifiers = ' '.join(match.group(1).split())  # Normalize modifiers
        fieldType = match.group(2).strip()
        fieldName = match.group(3)
        return f"{modifiers} {fieldType} {fieldName}"
    
    return normalized


def extractFieldsAndMethodsFromJavaFile(content: str) -> tuple:
    """
    Extracts fields and methods separately from a Java class.
    Returns: (fields_list, methods_list)
    """
    classMatch = re.search(r'public\s+class\s+\w+[^{]*{', content)
    if not classMatch:
        return ([], [])
    
    classStart = classMatch.end()
    classContent = content[classStart:]
    
    # Find the matching closing brace
    braceCount = 1
    classEnd = 0
    
    for i, char in enumerate(classContent):
        if char == '{':
            braceCount += 1
        elif char == '}':
            braceCount -= 1
            if braceCount == 0:
                classEnd = i
                break
    
    classBody = classContent[:classEnd].strip()
    
    if not classBody:
        return ([], [])
    
    # Separate fields and methods
    fields = []
    methods = []
    
    members = extractIndividualMembers(classBody)
    
    for member in members:
        if isFieldDeclaration(member):
            fields.append(member)
        else:
            methods.append(member)
    
    return (fields, methods)


def isFieldDeclaration(member: str) -> bool:
    """
    Determines if a member is a field declaration vs a method.
    Fields typically:
    - Don't have parentheses for method calls (except in initialization)
    - End with semicolon at the top level
    - Don't have method-like structure (returnType methodName(...) {...})
    """
    memberStripped = member.strip()
    
    # Check if it's a method declaration pattern
    # Methods have: [modifiers] returnType methodName(params) { or @Annotation
    if re.match(r'@\w+', memberStripped):  # Starts with annotation (likely method)
        return False
    
    if re.search(r'\b\w+\s+\w+\s*\([^)]*\)\s*{', memberStripped):  # Method signature pattern
        return False
    
    # Check if it ends with semicolon (field) vs ends with closing brace (method)
    lines = memberStripped.split('\n')
    lastLine = lines[-1].strip()
    
    if lastLine.endswith(';'):
        return True
    if lastLine.endswith('}'):
        return False
    
    # Default: if it has an opening brace, it's likely a method
    if '{' in memberStripped:
        return False
    
    return True


def createMergedJavaFileWithSingleClass(packages: Set[str], imports: Set[str],
                                        className: str, fields: List[str],
                                        methods: List[str]) -> str:
    """Creates a single merged Java file with deduplicated fields at top"""
    lines = []
    
    # Add package
    if packages:
        sortedPackages = sorted(packages)
        lines.append(sortedPackages[0])
        lines.append('')
    
    # Add imports
    sortedImports = sorted(imports)
    lines.extend(sortedImports)
    
    if sortedImports:
        lines.append('')
    
    # Add class declaration
    lines.append(f'public class {className} {{')
    lines.append('')
    
    # Add all FIELDS first (deduplicated)
    if fields:
        for field in fields:
            indentedField = '\n'.join('    ' + line if line.strip() else '' 
                                      for line in field.split('\n'))
            lines.append(indentedField)
        lines.append('')
    
    # Add all METHODS
    for i, method in enumerate(methods):
        indentedMethod = '\n'.join('    ' + line if line.strip() else '' 
                                   for line in method.split('\n'))
        lines.append(indentedMethod)
        
        if i < len(methods) - 1:
            lines.append('')
    
    # Close class
    lines.append('}')
    
    return '\n'.join(lines)