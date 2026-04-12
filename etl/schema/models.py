"""
Pydantic models representing inferred dataset schemas.

These models are the standardised output of the schema identification
step.  They can be serialised to JSON for persistence, comparison
between pipeline runs (drift detection), and logging.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class InferredType(str, Enum):
    """Canonical data types the schema identifier can detect."""
    INTEGER   = "integer"
    FLOAT     = "float"
    STRING    = "string"
    BOOLEAN   = "boolean"
    DATETIME  = "datetime"
    DATE      = "date"
    JSON      = "json"       # stringified JSON / nested dict
    LIST      = "list"       # array / list column
    MIXED     = "mixed"      # column has multiple incompatible types
    UNKNOWN   = "unknown"


class IssueSeverity(str, Enum):
    INFO     = "info"
    WARNING  = "warning"
    CRITICAL = "critical"


class SchemaIssue(BaseModel):
    """A single issue detected during schema identification."""
    field: Optional[str] = None
    severity: IssueSeverity
    message: str


class FieldSchema(BaseModel):
    """Schema description for a single field (column)."""
    name: str
    inferred_type: InferredType
    original_dtype: str               # pandas dtype as string
    nullable: bool
    null_count: int                   = 0
    null_percentage: float            = 0.0
    unique_count: int                 = 0
    cardinality_ratio: float          = 0.0   # unique / total
    min_value: Optional[Any]          = None
    max_value: Optional[Any]          = None
    sample_values: List[Any]          = Field(default_factory=list)
    is_nested: bool                   = False
    nested_keys: Optional[List[str]]  = None  # keys found inside JSON fields
    detected_pattern: Optional[str]   = None  # e.g. "ISO-8601", "UUID", "email"


class DatasetSchema(BaseModel):
    """
    Full schema description for a dataset.

    This is the primary output of ``identify_schema()`` and the input
    to the transform / validation steps.
    """
    source_name: str
    source_type: str                  = "unknown"
    record_count: int
    field_count: int
    fields: Dict[str, FieldSchema]
    inferred_at: datetime             = Field(default_factory=datetime.utcnow)
    issues: List[SchemaIssue]         = Field(default_factory=list)
    version: int                      = 1

    # ── helpers ─────────────────────────────────────────────────────

    def field_names(self) -> List[str]:
        return list(self.fields.keys())

    def nullable_fields(self) -> List[str]:
        return [n for n, f in self.fields.items() if f.nullable]

    def nested_fields(self) -> List[str]:
        return [n for n, f in self.fields.items() if f.is_nested]

    def has_critical_issues(self) -> bool:
        return any(i.severity == IssueSeverity.CRITICAL for i in self.issues)

    def summary(self) -> str:
        """Human-readable one-liner."""
        return (
            f"Schema[{self.source_name}]: {self.record_count} rows, "
            f"{self.field_count} fields, {len(self.issues)} issue(s)"
        )


class SchemaDriftReport(BaseModel):
    """Result of comparing two DatasetSchema objects."""
    previous_version: int
    current_version: int
    added_fields: List[str]           = Field(default_factory=list)
    removed_fields: List[str]         = Field(default_factory=list)
    type_changes: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    nullability_changes: Dict[str, Dict[str, bool]] = Field(default_factory=dict)
    has_breaking_changes: bool        = False
    details: List[str]                = Field(default_factory=list)
