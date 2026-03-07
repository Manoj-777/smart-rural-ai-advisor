import os
import re


def _template_text():
    test_dir = os.path.dirname(__file__)
    template_path = os.path.join(test_dir, '..', '..', 'infrastructure', 'template.yaml')
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def test_globals_timeout_is_30_seconds():
    text = _template_text()

    assert re.search(r'Globals:\s*\n\s*Function:\s*\n\s*Timeout:\s*30\b', text)


def test_agent_orchestrator_does_not_override_timeout():
    text = _template_text()

    block_match = re.search(
        r'AgentOrchestratorFunction:\s*\n\s*Type:\s*AWS::Serverless::Function\s*\n\s*Properties:\s*\n(.*?)(?:\n\s{2}[A-Za-z0-9_]+Function:|\nOutputs:|\Z)',
        text,
        re.DOTALL,
    )
    assert block_match, 'AgentOrchestratorFunction block not found'

    block = block_match.group(1)
    assert not re.search(r'^\s*Timeout:\s*\d+\b', block, re.MULTILINE)
