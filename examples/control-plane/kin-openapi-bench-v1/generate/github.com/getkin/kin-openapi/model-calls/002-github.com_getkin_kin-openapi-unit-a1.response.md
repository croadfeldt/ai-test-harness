```go
package harnesstest

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
)

// TestNewComponentsReturnsEmptyMaps initializes Components and checks that all map fields are non-nil.
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
	if components.ResponseBodies == nil {
		t.Fatalf("expected ResponseBodies to be initialized, got nil")
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

// TestContactValidateFailsOnInvalidEmail checks that Contact.Validate returns an error for invalid email.
func TestContactValidateFailsOnInvalidEmail(t *testing.T) {
	contact := &openapi3.Contact{
		Email: "invalid-email",
	}
	err := contact.Validate(context.Background())
	if err == nil {
		t.Fatalf("expected validation error for invalid email, got nil")
	}
}

// TestContactValidatePassesOnValidEmail checks that Contact.Validate passes for a valid email.
func TestContactValidatePassesOnValidEmail(t *testing.T) {
	contact := &openapi3.Contact{
		Email: "user@example.com",
	}
	err := contact.Validate(context.Background())
	if err != nil {
		t.Fatalf("expected no validation error for valid email, got %v", err)
	}
}

// TestNewContentWithJSONSchemaCreatesApplicationJsonEntry checks that NewContentWithJSONSchema adds application/json media type.
func TestNewContentWithJSONSchemaCreatesApplicationJsonEntry(t *testing.T) {
	schema := &openapi3.Schema{Type: "string"}
	content := openapi3.NewContentWithJSONSchema(schema)
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatalf("expected application/json MediaType to be set")
	}
	if mediaType.Schema == nil {
		t.Fatalf("expected schema to be set in application/json MediaType")
	}
	if mediaType.Schema.Value.Type != "string" {
		t.Errorf("expected schema type 'string', got %s", mediaType.Schema.Value.Type)
	}
}

// TestComponentsUnmarshalJSONPopulatesSchemas checks that Components.UnmarshalJSON correctly parses JSON into Schemas.
func TestComponentsUnmarshalJSONPopulatesSchemas(t *testing.T) {
	data := `{"schemas":{"User":{"type":"object","properties":{"name":{"type":"string"}}}}}`
	var components openapi3.Components
	err := components.UnmarshalJSON([]byte(data))
	if err != nil {
		t.Fatalf("unexpected error during UnmarshalJSON: %v", err)
	}
	schemaRef, exists := components.Schemas["User"]
	if !exists {
		t.Fatalf("expected schema 'User' to exist")
	}
	if schemaRef.Value.Type != "object" {
		t.Errorf("expected schema type 'object', got %s", schemaRef.Value.Type)
	}
}

// TestComponentsValidateFailsOnInvalidSchema checks that Components.Validate returns an error when a schema has invalid property.
func TestComponentsValidateFailsOnInvalidSchema(t *testing.T) {
	components := openapi3.NewComponents()
	invalidSchema := &openapi3.Schema{Type: "object", Properties: map[string]*openapi3.SchemaRef{"": {Value: &openapi3.Schema{Type: "string"}}}}
	components.Schemas["Invalid"] = &openapi3.SchemaRef{Value: invalidSchema}
	err := components.Validate(context.Background())
	if err == nil {
		t.Fatalf("expected validation error for empty property name, got nil")
	}
}

// TestNewCallbackBuildsWithOption checks that NewCallback with WithCallback option sets the path item correctly.
func TestNewCallbackBuildsWithOption(t *testing.T) {
	pathItem := &openapi3.PathItem{}
	cb := openapi3.NewCallback(openapi3.WithCallback("/event", pathItem))
	if len(cb.PathItems) != 1 {
		t.Fatalf("expected one path item, got %d", len(cb.PathItems))
	}
	retrieved, exists := cb.PathItems["/event"]
	if !exists {
		t.Fatalf("expected path item '/event' to exist")
	}
	if retrieved.Value != pathItem {
		t.Errorf("expected retrieved path item to match input")
	}
}

// TestCallbackValidateFailsOnInvalidPath checks that Callback.Validate fails when path starts with invalid character.
func TestCallbackValidateFailsOnInvalidPath(t *testing.T) {
	pathItem := &openapi3.PathItem{}
	cb := openapi3.NewCallback(openapi3.WithCallback("invalid-path", pathItem))
	err := cb.Validate(context.Background())
	if err == nil {
		t.Fatalf("expected validation error for invalid path key, got nil")
	}
}

// TestNewExampleCreatesWithGivenValue checks that NewExample sets the Value field correctly.
func TestNewExampleCreatesWithGivenValue(t *testing.T) {
	value := "test-example"
	example := openapi3.NewExample(value)
	if example.Value != value {
		t.Errorf("expected Value %v, got %v", value, example.Value)
	}
}

// TestExampleMarshalJSONProducesExpectedFormat checks that Example.MarshalJSON produces correct JSON output.
func TestExampleMarshalJSONProducesExpectedFormat(t *testing.T) {
	example := &openapi3.Example{
		Summary: "Test example",
		Value:   "example-value",
	}
	data, err := example.MarshalJSON()
	if err != nil {
		t.Fatalf("unexpected error during MarshalJSON: %v", err)
	}
	var result map[string]json.RawMessage
	err = json.Unmarshal(data, &result)
	if err != nil {
		t.Fatalf("invalid JSON produced: %v", err)
	}
	if string(result["value"]) != `"example-value"` {
		t.Errorf("expected value to be serialized as \"example-value\", got %s", result["value"])
	}
	if string(result["summary"]) != `"Test example"` {
		t.Errorf("expected summary to be serialized as \"Test example\", got %s", result["summary"])
	}
}
```