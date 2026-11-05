## Core Definition and Architecture

Azure Content Understanding is an Azure AI Foundry tool designed to ingest unstructured multimodal inputs and convert them into structured, actionable outputs for analytical and automation pipelines.

- **Multimodal Inputs:** Native processing support for documents, images, video, and audio.
- **Processing Stages:**
  - **Inputs:** Raw data ingestion.
  - **Analyzer:** Central configuration engine containing extraction parameters and the target schema.
  - **Content Extraction:** Normalization layer turning unstructured media into text and layout metadata via OCR, speech-to-text, and layout analysis.
  - **Field Extraction:** Generates targeted key-value pairs matching the predefined schema.
  - **Confidence Scores:** Numerical metrics ($0.0$ to $1.0$) indicating the reliability of extracted fields.
  - **Grounding:** Precise region coordinates (bounding boxes/source references) locating where each value resides in the source.
  - **Structured Output:** Delivered as JSON for system automation or Markdown for search/RAG architectures.

---

## Analyzers and Schema Configuration

Analyzers dictate how generative AI models interpret and process ingested content.

### Types of Analyzers
- **Prebuilt Analyzers:** Off-the-shelf, specialized templates for common patterns:
  - `prebuilt-image`: Baseline image processing and figure description.
  - `prebuilt-receipt`: Extraction of vendors, totals, dates, and line items.
  - `prebuilt-invoice`: Invoice details and billing lines.
  - `prebuilt-idDocument`: Structured extraction of identity cards, driver's licenses, and passports.
- **Custom Analyzers:** Tailored processing pipelines where developers configure custom base types, underlying models, segmentation options, and schema definitions.

### Field Extraction Methods
When constructing a custom field schema, each defined property uses one of three extraction paradigms:

| Method | Operational Function | Typical Scenario |
|---|---|---|
| **extract** | Pulls exact textual/data values verbatim from the input. | Reading raw serial numbers, names, or prices. |
| **classify** | Maps input properties into a predefined `enum` list. | Categorizing condition (`new`, `used`, `damaged`). |
| **generate** | Synthesizes descriptive or narrative content based on model analysis. | Producing natural language scene captions or summaries. |

---

## Operational Features and Capabilities

Key mechanics enable both straight-through automated processing and risk management.

- **Confidence Score Thresholds:**
  - **High ($\ge 0.9$):** Suitable for straight-through automation without manual intervention.
  - **Medium ($0.7 - 0.9$):** Recommended for conditional human review in mission-critical environments.
  - **Low ($< 0.7$):** Routed to manual verification queues.
- **Input Image Specifications:** Supports formats including JPEG, PNG, BMP, TIFF, HEIF, and multi-page/single-page PDF files containing images.
- **Target Use Cases:**
  - **Intelligent Document Processing (IDP):** Claims, receipts, contracts, and invoices.
  - **Search and RAG:** Ingesting multimodal content with rich visual descriptions into vector/search indexes.
  - **Agentic Workflows:** Standardizing unstructured files into predictable schemas for autonomous AI agents.
  - **Analytics & BI:** Tabular conversion for reporting dashboards.
- **Responsible AI and Content Safeguards:**
  - Built-in integration with **Azure AI Content Safety** for automatic filtering of hate speech, violence, and exploitation.
  - Facial attribute identification in visual streams.
  - Regulatory compliance mechanisms requiring consent for biometric operations.
