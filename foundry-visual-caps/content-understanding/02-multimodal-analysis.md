## Architectural Foundation and Environments

Azure Content Understanding centralizes multimodal content processing under a unified development model deployed via Microsoft Foundry.

### Resource and Tooling Ecosystem
- **Microsoft Foundry Resource:** The foundational Azure resource required to host Content Understanding projects, manage endpoints, handle billing, and secure API keys.
- **Development Interfaces:**
  - **Microsoft Foundry Portal:** General resource management, credential retrieval, and consumption of selected prebuilt models.
  - **Content Understanding Studio:** Dedicated visual GUI for creating end-to-end custom analyzer projects, authoring schemas, testing, and managing versions.
  - **REST API / Client SDKs:** Programmatic interface for defining, building, and invoking analyzers at scale.
- **Automatically Provisioned Infrastructure:** Creating a project in Content Understanding Studio automatically provisions dependent Azure assets:
  - Azure Storage (sample and working data).
  - Azure Key Vault (secure management of secrets and API keys).

### Bring Your Own Model (BYOM)
- Allows connection of custom generative AI model deployments hosted in Microsoft Foundry directly to custom analyzers.
- Enables granular trade-offs between extraction accuracy, latency, and operational cost.

---

## Multimodal Analysis Domains

Content Understanding uses a standardized pipeline to extract structured fields across four core content categories:

| Content Modality | Primary Extraction and Processing Capabilities | Common Scenarios |
|---|---|---|
| **Documents and Forms** | Field extraction, tabular data, layout analysis, plus optional advanced extraction (barcodes, mathematical formulas). | Invoice automation, claims processing, contract extraction. |
| **Images** | Object/person detection, visual defect detection, chart and diagram interpretation. | Quality inspection, inventory auditing, asset monitoring. |
| **Audio** | Speech-to-text processing, sentiment determination, key metadata extraction. | Conference call summarization, contact center analytics, voicemail processing. |
| **Video** | Activity and anomaly detection, key-point extraction, visual and audio event tracking. | Security footage review, presentation indexing, meeting summaries. |

---

## Analyzer Creation Lifecycle

Custom analyzers follow a sequential build and release cycle inside Content Understanding Studio:

```
[Provision Foundry Resource]
             │
             ▼
[Define Schema from Sample + Template]
             │
             ▼
[Iterative Testing & Optional Labeling]
             │
             ▼
[Build Analyzer] ──► [Deploy to Foundry Endpoint as Named Version]
```

1. **Schema Definition by Example:** Minimal training data is needed. The underlying generative models automatically infer mappings between sample content values and target schema elements.
2. **Explicit Labeling (Optional):** Manual annotation on sample documents can be used when higher precision is required.
3. **Analyzer Templates:** Domain- and media-specific starter schemas that dictate supported field types based on input modality.
4. **Testing and Validation:** Visual runs return both extracted field values and raw JSON payloads before compilation.
5. **Compilation and Versioning:** Building the analyzer publishes it to the Foundry resource endpoint and allows named versioning for iterative updates.

---

## REST API Integration Patterns

The Content Understanding API implements an asynchronous polling model for processing workloads.

### Authentication
- **API Key:** Passed via HTTP request headers (`Ocp-Apim-Subscription-Key` or equivalent).
- **Microsoft Entra ID:** Token-based identity authentication using Azure AD credentials.

### Ingestion Endpoints
- **URL-based Content:** Submitted via HTTP POST to the standard analyze route:
  ```http
  POST {endpoint}/contentunderstanding/analyzers/{analyzer}:analyze?api-version=2025-11-01
  ```
  Payload structure:
  ```json
  {
    "inputs": [
      { "url": "https://host.com/doc.pdf" }
    ]
  }
  ```
- **Raw Binary Content:** Directly uploaded via the dedicated `analyzeBinary` operation.

### Asynchronous Execution and Polling Workflow
1. **Job Submission:** The client issues the POST request to initiate processing.
2. **Initial Response (`202 Accepted`):**
   - Returns an `Operation-Id` tracking token.
   - Supplies an `Operation-Location` header containing the polling URL.
   - Initial JSON status payload (e.g., `"status": "NotStarted"` or `"Running"`).
3. **Status Polling:** The client periodically issues an HTTP GET against the results endpoint:
   ```http
   GET {endpoint}/contentunderstanding/analyzerResults/{operationId}?api-version=2025-11-01
   ```
4. **Payload Retrieval:** Once `"status": "Succeeded"`, the response contains the final extracted fields in JSON format.
5. **Optional Telemetry:** Setting `estimateFieldSourceAndConfidence` to `true` enriches the returned JSON with confidence scores ($0.0 - 1.0$) and coordinate-based source grounding.