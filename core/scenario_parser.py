from typing import List

SCENARIO_PREFIXES = ("Scenario Outline:", "Scenario:")


class GherkinScenarioParser:
    """Splits a feature file into one text block per Scenario / Scenario Outline."""

    def parse(self, feature_text: str) -> List[str]:
        scenarios, block = [], []
        for line in feature_text.splitlines():
            if line.strip().startswith(SCENARIO_PREFIXES):
                if block:
                    scenarios.append("\n".join(block))
                block = [line]
            elif block:
                block.append(line)
        if block:
            scenarios.append("\n".join(block))
        return scenarios
