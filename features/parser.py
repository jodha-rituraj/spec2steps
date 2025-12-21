from typing import List

def extractScenarioOulines(featureText):
    """
    Parses a Gherkin feature text and extracts individual Scenario Outline blocks.
    Args:
        featureText (str): The raw content of the feature file.
    Returns:
        list: A list of strings, where each string is a complete Scenario Outline block.
    """
    scenarios = []
    currentBlock = []
    
    # Split the text into lines to process them one by one
    lines = featureText.splitlines()

    for line in lines:
        strippedLine = line.strip()

        if strippedLine.startswith("Scenario Outline:"):
            # If we were already building a block, save it to the list
            if currentBlock:
                scenarios.append("\n".join(currentBlock))
                currentBlock = [] # Reset for the new block
            
            currentBlock.append(line)
            
        # If we are currently inside a block (i.e., we have found the first Scenario Outline)
        elif currentBlock:
            currentBlock.append(line)

    # Append the very last block after the loop finishes
    if currentBlock:
        scenarios.append("\n".join(currentBlock))

    return scenarios

class GherkinScenarioParser:
    """
    A class to parse and extract Scenario Outlines from Gherkin feature files.
    """
    
    def __init__(self):
        """Initialize the GherkinScenarioParser."""
        self.scenarios = []
        self.current_block = []
    
    def parse(self, feature_text: str) -> List[str]:
        """
        Parses a Gherkin feature text and extracts individual Scenario Outline blocks.
        
        Args:
            feature_text: The raw content of the feature file.
        
        Returns:
            List of strings, where each string is a complete Scenario Outline block.
        """
        self._reset()
        lines = feature_text.splitlines()
        
        for line in lines:
            self._process_line(line)
        
        # Append the last block
        self._save_current_block()
        
        return self.scenarios
    
    def _reset(self):
        """Reset internal state for a new parse operation."""
        self.scenarios = []
        self.current_block = []
    
    def _process_line(self, line: str):
        """Process a single line of the feature file."""
        stripped_line = line.strip()
        
        if stripped_line.startswith("Scenario Outline:"):
            # Save previous block if it exists
            self._save_current_block()
            # Start new block
            self.current_block = [line]
        elif self.current_block:
            # Add line to current block
            self.current_block.append(line)
    
    def _save_current_block(self):
        """Save the current block to scenarios list if not empty."""
        if self.current_block:
            self.scenarios.append("\n".join(self.current_block))
            self.current_block = []
    
    def extract_scenario_outlines(self, feature_text: str) -> List[str]:
        """
        Alias for parse() method for backward compatibility.
        
        Args:
            feature_text: The raw content of the feature file.
        
        Returns:
            List of strings, where each string is a complete Scenario Outline block.
        """
        return self.parse(feature_text)


if __name__ == "__main__":
    feature_content = """
    Feature: Test Feature
    
    Scenario Outline: First scenario
        Given I have <item>
        When I do something
        Then result is <result>
        
        Examples:
        | item | result |
        | A    | Pass   |
    
    Scenario Outline: Second scenario
        Given I have <value>
        When I process it
        Then output is <output>
        
        Examples:
        | value | output |
        | 1     | OK     |
    """
    
    parser = GherkinScenarioParser()
    scenarios = parser.parse(feature_content)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"=== Scenario {i} ===")
        print(scenario)
        print()