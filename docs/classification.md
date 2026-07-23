# Classification & evaluation

Once an incident is stored, AgentWatch classifies it with a **pluggable provider** and
an **abstain-capable taxonomy**, and measures how well it does with a **labelled
evaluation set** guarded by a **regression test**.

## The taxonomy

Every classification assigns:

- **relevance** — `relevant`, `not_relevant`, or `insufficient_evidence`
- **incident_type** — one of ten categories: `unauthorized_action`,
  `resistance_to_correction`, `deception`, `goal_persistence`, `privilege_escalation`,
  `sandbox_escape`, `destructive_action`, `resource_acquisition`,
  `harmless_malfunction`, or `insufficient_evidence`
- **severity** (1–5), **evidence_quality**, **autonomy_level**, **confidence**, and a
  one-line **reasoning_summary**

The key design point is the explicit **abstain / insufficient_evidence** outcome. A
monitoring system must distinguish *"this is not an incident"* from *"there isn't
enough information to decide"* — conflating the two either hides real signals or
invents false ones.

## Providers

All providers implement one interface:

```python
class LLMProvider(Protocol):
    name: str
    def generate(self, system: str, user: str) -> LLMResult: ...
```

| Provider | Dependencies | Use |
|---|---|---|
| **baseline** | none | Deterministic keyword classifier. The default, so the whole pipeline — including evaluation — runs with no model server or network. Also used in tests and CI for reproducibility. |
| **ollama** | a running [Ollama](https://ollama.com) | Local open-weight models (e.g. Qwen, Llama). Requests JSON-formatted output. No API cost. |
| **anthropic** | `pip install -e ".[anthropic]"` + API key | Optional hosted model, with per-token cost accounting. |

Because the interface is uniform, the **same evaluation** can be run against any
provider to compare them on identical data.

## How a classification is produced

```text
incident text
      │
      ▼
build versioned prompt (prompt_version)
      │
      ▼
provider.generate(system, user)  →  JSON text
      │
      ▼
validate against the schema
   ├─ valid   → ClassificationResult
   └─ invalid → retry once → still invalid → ABSTAIN
      │
      ▼
persist a Classification row (model_name, prompt_version, cost, latency, abstained…)
```

Recording `model_name` and `prompt_version` on every row means any result can be
reproduced and that different models/prompts can be compared over time.

## Evaluation

`agentwatch eval` runs the classifier over a labelled dataset
(`agentwatch/eval/dataset.json`) and reports:

- **precision, recall, F1** per incident type, and **macro-F1** overall
- a **confusion matrix**
- **abstention rate**
- **total cost** and **average latency**

```bash
agentwatch eval --provider baseline
agentwatch eval --provider ollama     # compare a real model on the same data
```

### The regression gate

`tests/test_eval.py` runs the evaluation with the deterministic baseline and asserts
macro-F1 stays above a committed floor. Because the baseline and dataset are fixed,
this is a stable guard: a change to the prompt, taxonomy, or classifier logic that
regresses quality on the labelled set **fails the test suite**. Real-model numbers
(from Ollama or Anthropic) are produced with the same `agentwatch eval` command and
can be recorded alongside a release.
