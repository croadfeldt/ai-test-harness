```go
package harnesstest

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
)

// TestNewLoaderReturnsNonNil ensures NewLoader returns a non-nil Loader instance.
func TestNewLoaderReturnsNonNil(t *testing.T) {
	loader := openapi3.NewLoader()
	if loader == nil {
		t.Fatalf("expected non-nil loader, got nil")
	}
}

// TestLoaderReadFromURIFuncIsAssignable verifies that a function can be assigned to ReadFromURIFunc.
func TestLoaderReadFromURIFuncIsAssignable(t *testing.T) {
	loader := openapi3.NewLoader()
	fakeFunc := func(loader *openapi3.Loader, url string) ([]byte, error) {
		return nil, nil
	}
	// Assign a mock function to ensure the field exists and is assignable
	loader.ReadFromURIFunc = func(loader *openapi3.Loader, url string) ([]byte, error) {
		return fakeFunc(loader, url)
	}
	if loader.ReadFromURIFunc == nil {
		t.Fatal("expected ReadFromURIFunc to be set, but it is nil")
	}
}

// TestTStructExists ensures the T struct can be instantiated directly.
func TestTStructExists(t *testing.T) {
	var spec openapi3.T
	if &spec == nil {
		t.Fatal("expected T struct to exist, got nil")
	}
}

// TestNewComponentsReturnsEmptyComponents checks that NewComponents returns an empty Components value.
func TestNewComponentsReturnsEmptyComponents(t *testing.T) {
	components := openapi3.NewComponents()
	if components.Schemas == nil {
		t.Error("expected Schemas map to be initialized")
	}
	if components.Parameters == nil {
		t.Error("expected Parameters map to be initialized")
	}
	if components.Headers == nil {
		t.Error("expected Headers map to be initialized")
	}
}

// TestComponentsValidateWithEmptyContext checks validation does not panic with empty context.
func TestComponentsValidateWithEmptyContext(t *testing.T) {
	components := openapi3.NewComponents()
	err := components.Validate(context.Background())
	if err != nil {
		t.Errorf("expected no validation error for empty components, got %v", err)
	}
}

// TestNewContentReturnsEmptyContent verifies NewContent returns a non-nil map.
func TestNewContentReturnsEmptyContent(t *testing.T) {
	content := openapi3.NewContent()
	if content == nil {
		t.Fatal("expected NewContent to return non-nil map")
	}
	if len(content) != 0 {
		t.Errorf("expected empty content map, got %d entries", len(content))
	}
}

// TestNewContentWithJSONSchemaCreatesApplicationJsonEntry checks that schema is set under application/json.
func TestNewContentWithJSONSchemaCreatesApplicationJsonEntry(t *testing.T) {
	schema := &openapi3.Schema{Type: "string"}
	content := openapi3.NewContentWithJSONSchema(schema)
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatal("expected application/json MediaType to be set")
	}
	if mediaType.Schema == nil {
		t.Fatal("expected schema to be set in MediaType")
	}
	if mediaType.Schema.Value.Type != "string" {
		t.Errorf("expected schema type string, got %s", mediaType.Schema.Value.Type)
	}
}

// TestContentUnmarshalJSONParsesSimpleSchema ensures unmarshaling JSON into Content works.
func TestContentUnmarshalJSONParsesSimpleSchema(t *testing.T) {
	data := `{"application/json":{"schema":{"type":"integer"}}}`
	var content openapi3.Content
	err := json.Unmarshal([]byte(data), &content)
	if err != nil {
		t.Fatalf("unexpected error during UnmarshalJSON: %v", err)
	}
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatal("expected application/json MediaType after unmarshaling")
	}
	if mediaType.Schema == nil || mediaType.Schema.Value.Type != "integer" {
		t.Errorf("expected schema type integer, got %+v", mediaType.Schema)
	}
}

// TestContactUnmarshalJSONSetsName verifies unmarshaling contact JSON sets the Name field.
func TestContactUnmarshalJSONSetsName(t *testing.T) {
	data := `{"name":"API Support"}`
	var contact openapi3.Contact
	err := json.Unmarshal([]byte(data), &contact)
	if err != nil {
		t.Fatalf("unexpected error during Contact UnmarshalJSON: %v", err)
	}
	if contact.Name != "API Support" {
		t.Errorf("expected Name 'API Support', got '%s'", contact.Name)
	}
}

// TestNewCallbackCreatesValidCallback checks that NewCallback with option sets callback path.
func TestNewCallbackCreatesValidCallback(t *testing.T) {
	pathItem := &openapi3.PathItem{Summary: "test"}
	cb := openapi3.NewCallback(openapi3.WithCallback("/event", pathItem))
	if len(cb.Paths) != 1 {
		t.Fatalf("expected 1 path in callback, got %d", len(cb.Paths))
	}
	if _, exists := cb.Paths["/event"]; !exists {
		t.Errorf("expected path /event to exist in callback")
	}
}
```