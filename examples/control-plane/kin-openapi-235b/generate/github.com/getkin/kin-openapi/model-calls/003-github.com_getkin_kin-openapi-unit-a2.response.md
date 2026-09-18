```go
package harnesstest

import (
	"context"
	"encoding/json"
	"fmt"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
)

// TestNewCallbackWithOption ensures NewCallback with WithCallback option correctly sets the callback path.
func TestNewCallbackWithOption(t *testing.T) {
	pathItem := &openapi3.PathItem{}
	cb := openapi3.NewCallback(openapi3.WithCallback("/test", pathItem))
	if len(cb) != 1 {
		t.Fatalf("expected callback map length 1, got %d", len(cb))
	}
	if _, exists := cb["/test"]; !exists {
		t.Errorf("expected callback key '/test' to exist")
	}
}

// TestCallbackValidateNilContext ensures Callback.Validate returns no error when context is nil.
func TestCallbackValidateNilContext(t *testing.T) {
	cb := openapi3.NewCallback()
	err := cb.Validate(nil)
	if err != nil {
		t.Errorf("Callback.Validate with nil context failed: %v", err)
	}
}

// TestCallbacksUnmarshalJSON ensures Callbacks.UnmarshalJSON correctly parses a JSON map.
func TestCallbacksUnmarshalJSON(t *testing.T) {
	data := []byte(`{"cb1": {"$ref": "#/components/callbacks/cb1"}}`)
	var callbacks openapi3.Callbacks
	err := callbacks.UnmarshalJSON(data)
	if err != nil {
		t.Fatalf("Callbacks.UnmarshalJSON failed: %v", err)
	}
	if len(callbacks) != 1 {
		t.Errorf("expected 1 callback, got %d", len(callbacks))
	}
	if _, exists := callbacks["cb1"]; !exists {
		t.Errorf("expected callback 'cb1' to exist")
	}
}

// TestNewComponentsReturnsEmptyStruct ensures NewComponents returns an empty Components struct.
func TestNewComponentsReturnsEmptyStruct(t *testing.T) {
	components := openapi3.NewComponents()
	if components.Schemas == nil {
		t.Error("expected Schemas map to be initialized")
	}
	if components.Parameters == nil {
		t.Error("expected Parameters map to be initialized")
	}
	if components.RequestBodies == nil {
		t.Error("expected RequestBodies map to be initialized")
	}
}

// TestComponentsValidateNilContext ensures Components.Validate returns no error with nil context.
func TestComponentsValidateNilContext(t *testing.T) {
	components := openapi3.NewComponents()
	err := components.Validate(nil)
	if err != nil {
		t.Errorf("Components.Validate with nil context failed: %v", err)
	}
}

// TestNewContentWithJSONSchema creates content with a JSON schema and checks MIME type.
func TestNewContentWithJSONSchema(t *testing.T) {
	schema := &openapi3.Schema{Type: "string"}
	content := openapi3.NewContentWithJSONSchema(schema)
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatal("expected application/json MediaType to exist")
	}
	if mediaType.Schema == nil {
		t.Fatal("expected MediaType.Schema to be set")
	}
	if mediaType.Schema.Value.Type != "string" {
		t.Errorf("expected schema type 'string', got '%s'", mediaType.Schema.Value.Type)
	}
}

// TestContentUnmarshalJSON ensures Content.UnmarshalJSON correctly parses JSON content.
func TestContentUnmarshalJSON(t *testing.T) {
	data := []byte(`{"text/plain": {"schema": {"type": "string"}}}`)
	var content openapi3.Content
	err := content.UnmarshalJSON(data)
	if err != nil {
		t.Fatalf("Content.UnmarshalJSON failed: %v", err)
	}
	mediaType := content.Get("text/plain")
	if mediaType == nil {
		t.Fatal("expected text/plain MediaType to exist")
	}
	if mediaType.Schema.Value.Type != "string" {
		t.Errorf("expected schema type 'string', got '%s'", mediaType.Schema.Value.Type)
	}
}

// TestExampleUnmarshalJSON ensures Example.UnmarshalJSON correctly parses JSON example data.
func TestExampleUnmarshalJSON(t *testing.T) {
	data := []byte(`{"value": "test", "summary": "a test"}`)
	example := &openapi3.Example{}
	err := example.UnmarshalJSON(data)
	if err != nil {
		t.Fatalf("Example.UnmarshalJSON failed: %v", err)
	}
	if example.Value != "test" {
		t.Errorf("expected Value 'test', got '%v'", example.Value)
	}
	if example.Summary != "a test" {
		t.Errorf("expected Summary 'a test', got '%s'", example.Summary)
	}
}

// TestExampleValidateNilContext ensures Example.Validate returns no error with nil context.
func TestExampleValidateNilContext(t *testing.T) {
	example := openapi3.NewExample("test")
	err := example.Validate(nil)
	if err != nil {
		t.Errorf("Example.Validate with nil context failed: %v", err)
	}
}

// TestMultiErrorIs checks that MultiError correctly implements errors.Is.
func TestMultiErrorIs(t *testing.T) {
	err1 := fmt.Errorf("first error")
	err2 := fmt.Errorf("second error")
	multiErr := openapi3.MultiError{err1, err2}
	if !multiErr.Is(err1) {
		t.Error("expected MultiError to contain err1 via Is")
	}
	if !multiErr.Is(err2) {
		t.Error("expected MultiError to contain err2 via Is")
	}
}
```