# Vertex Search Config (Recommended for Legal/Patent)

Use sentence-aware chunking with 20-25% overlap to preserve claim context and
avoid mid-sentence cuts.

Recommended settings:
- Chunk size: 700-900 tokens (target 800)
- Overlap: 20-25%
- Enable table + image annotation
- Use OCR parsing for scanned PDFs/images

Example (Document Processing Config):

```json
{
  "documentProcessingConfig": {
    "defaultParsingConfig": {
      "layoutParsingConfig": {
        "enableTableAnnotation": true,
        "enableImageAnnotation": true
      }
    },
    "parsingConfigOverrides": {
      "pdf": { "ocrParsingConfig": {} }
    },
    "chunkingConfig": {
      "layoutBasedChunkingConfig": {
        "chunkSize": 800,
        "overlapSize": 200
      }
    }
  }
}
```

Notes:
- `chunkSize` and `overlapSize` are token-ish; adjust for average section size.
- If claims are still splitting, reduce chunk size or increase overlap.
