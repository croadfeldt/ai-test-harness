```go
package harnesstest

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
)

// TestNewComponentsReturnsEmptyMaps ensures NewComponents initializes all map fields as empty.
func TestNewComponentsReturnsEmptyMaps(t *testing.T) {
	components := openapi3.NewComponents()
	if components.Schemas == nil {
		t.Fatalf("expected Schemas to be initialized, got nil")
	}
	if components.Parameters == nil {
		t.Fatalf("expected Parameters to be initialized, got nil")
	}
	if components.Headers == nil {
		t.Fatalf("expected Headers to be initialized, got nil")
	}
	if components.RequestBodies == nil {
		t.Fatalf("expected RequestBodies to be initialized, got nil")
	}
	if components.Responses == nil {
		t.Fatalf("expected Responses to be initialized, got nil")
	}
	if components.SecuritySchemes == nil {
		t.Fatalf("expected SecuritySchemes to be initialized, got nil")
	}
	if components.Examples == nil {
		t.Fatalf("expected Examples to be initialized, got nil")
	}
	if components.Links == nil {
		t.Fatalf("expected Links to be initialized, got nil")
	}
	if components.Callbacks == nil {
		t.Fatalf("expected Callbacks to be initialized, got nil")
	}
}

// TestComponentsValidatePassesOnEmpty checks that an empty Components object is valid.
func TestComponentsValidatePassesOnEmpty(t *testing.T) {
	components := openapi3.NewComponents()
	if err := components.Validate(context.Background()); err != nil {
		t.Fatalf("expected no validation error for empty components, got %v", err)
	}
}

// TestContactUnmarshalJSONSetsName verifies unmarshaling JSON sets the Name field.
func TestContactUnmarshalJSONSetsName(t *testing.T) {
	data := `{"name": "API Support"}`
	var contact openapi3.Contact
	if err := json.Unmarshal([]byte(data), &contact); err != nil {
		t.Fatalf("unexpected error during UnmarshalJSON: %v", err)
	}
	if contact.Name != "API Support" {
		t.Errorf("expected Name to be 'API Support', got %q", contact.Name)
	}
}

// TestContactMarshalJSONProducesName verifies marshaling includes the Name field.
func TestContactMarshalJSONProducesName(t *testing.T) {
	contact := &openapi3.Contact{Name: "API Team"}
	data, err := json.Marshal(contact)
	if err != nil {
		t.Fatalf("unexpected error during MarshalJSON: %v", err)
	}
	expected := `{"name":"API Team"}`
	if string(data) != expected {
		t.Errorf("expected JSON %q, got %q", expected, string(data))
	}
}

// TestNewContentWithJSONSchemaCreatesApplicationJSONEntry checks that NewContentWithJSONSchema adds application/json.
func TestNewContentWithJSONSchemaCreatesApplicationJSONEntry(t *testing.T) {
	schema := &openapi3.Schema{Type: "string"}
	content := openapi3.NewContentWithJSONSchema(schema)
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatalf("expected content to have application/json entry")
	}
	if mediaType.Schema == nil {
		t.Fatalf("expected schema in media type, got nil")
	}
	if mediaType.Schema.Value.Type != "string" {
		t.Errorf("expected schema type string, got %q", mediaType.Schema.Value.Type)
	}
}

// TestContentUnmarshalJSONParsesApplicationJSON verifies unmarshaling content with application/json.
func TestContentUnmarshalJSONParsesApplicationJSON(t *testing.T) {
	data := `{"application/json":{"schema":{"type":"integer"}}}`
	var content openapi3.Content
	if err := json.Unmarshal([]byte(data), &content); err != nil {
		t.Fatalf("unexpected error during UnmarshalJSON: %v", err)
	}
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatalf("expected application/json in content")
	}
	if mediaType.Schema == nil {
		t.Fatalf("expected schema, got nil")
	}
	if mediaType.Schema.Value.Type != "integer" {
		t.Errorf("expected schema type integer, got %q", mediaType.Schema.Value.Type)
	}
}

// TestNewCallbackWithOptionCreatesEntry checks WithCallback adds a path item under a key.
func TestNewCallbackWithOptionCreatesEntry(t *testing.T) {
	pathItem := &openapi3.PathItem{}
	cb := openapi3.NewCallback(openapi3.WithCallback("/onSuccess", pathItem))
	if len(cb.Paths) != 1 {
		t.Fatalf("expected one path entry, got %d", len(cb.Paths))
	}
	if _, exists := cb.Paths["/onSuccess"]; !exists {
		t.Errorf("expected path key /onSuccess to exist")
	}
}

// TestCallbackUnmarshalJSONCopiesData ensures UnmarshalJSON copies data into Callbacks.
func TestCallbackUnmarshalJSONCopiesData(t *testing.T) {
	data := `{"myCallback":{"$ref":"#/components/callbacks/generic"}}`
	var callbacks openapi3.Callbacks
	if err := callbacks.UnmarshalJSON([]byte(data)); err != nil {
		t.Fatalf("unexpected error during UnmarshalJSON: %v", err)
	}
	if len(callbacks) != 1 {
		t.Fatalf("expected one callback, got %d", len(callbacks))
	}
	if _, exists := callbacks["myCallback"]; !exists {
		t.Errorf("expected key 'myCallback' to exist")
	}
}

// TestNewExampleSetsValue checks NewExample initializes Example with given value.
func TestNewExampleSetsValue(t *testing.T) {
	value := "sample text"
	example := openapi3.NewExample(value)
	if example.Value != value {
		t.Errorf("expected Value to be %q, got %q", value, example.Value)
	}
}

// TestExampleUnmarshalJSONSetsSummary verifies unmarshaling sets the Summary field.
func TestExampleUnmarshalJSONSetsSummary(t *testing.T) {
	data := `{"summary":"A sample","value":"test"}`
	var example openapi3.Example
	if err := json.Unmarshal([]byte(data), &example); err != nil {
		t.Fatalf("unexpected error during UnmarshalJSON: %v", err)
	}
	if example.Summary != "A sample" {
		t.Errorf("expected Summary to be 'A sample', got %q", example.Summary)
	}
}
```