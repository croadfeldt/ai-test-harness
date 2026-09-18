```go
package harnesstest

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
)

// TestNewCallbackCreatesEmptyCallback asserts that NewCallback with no options returns a non-nil Callback.
func TestNewCallbackCreatesEmptyCallback(t *testing.T) {
	cb := openapi3.NewCallback()
	if cb == nil {
		t.Fatalf("expected non-nil Callback, got nil")
	}
}

// TestWithCallbackAddsPathItem asserts that WithCallback option adds a path item to the callback.
func TestWithCallbackAddsPathItem(t *testing.T) {
	pathItem := &openapi3.PathItem{}
	cb := openapi3.NewCallback(openapi3.WithCallback("/test", path7))
	if len(*cb) != 1 {
		t.Fatalf("expected 1 path item, got %d", len(*cb))
	}
	if _, exists := (*cb)["/test"]; !exists {
		t.Errorf("expected path '/test' to exist in callback, but it does not")
	}
}

// TestComponentsNewCreatesEmptyComponents asserts that NewComponents returns a Components with zero maps.
func TestComponentsNewCreatesEmptyComponents(t *testing.T) {
	components := openapi3.NewComponents()
	if components.Schemas == nil {
		t.Errorf("expected Schemas map to be initialized, got nil")
	}
	if components.Parameters == nil {
		t.Errorf("expected Parameters map to be initialized, got nil")
	}
	if components.Headers == nil {
		t.Errorf("expected Headers map to be initialized, got nil")
	}
}

// TestComponentsValidateEmptyIsSuccessful asserts that an empty Components object passes validation.
func TestComponentsValidateEmptyIsSuccessful(t *testing.T) {
	components := openapi3.NewComponents()
	ctx := context.Background()
	if err := components.Validate(ctx); err != nil {
		t.Errorf("expected no validation error for empty components, got %v", err)
	}
}

// TestContentGetReturnsMediaType asserts that Content.Get returns the correct media type by MIME type.
func TestContentGetReturnsMediaType(t *testing.T) {
	content := openapi3.NewContentWithJSONSchema(&openapi3.Schema{Type: "string"})
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatalf("expected non-nil media type for application/json, got nil")
	}
	if mediaType.Schema == nil {
		t.Fatalf("expected schema to be set, got nil")
	}
	if mediaType.Schema.Value.Type != "string" {
		t.Errorf("expected schema type 'string', got %s", mediaType.Schema.Value.Type)
	}
}

// TestContactUnmarshalJSONParsesName asserts that Contact.UnmarshalJSON correctly parses the name field.
func TestContactUnmarshalJSONParsesName(t *testing.T) {
	data := []byte(`{"name": "API Support"}`)
	var contact openapi3.Contact
	if err := contact.UnmarshalJSON(data); err != nil {
		t.Fatalf("unexpected error during UnmarshalJSON: %v", err)
	}
	if contact.Name != "API Support" {
		t.Errorf("expected name 'API Support', got %s", contact.Name)
	}
}

// TestCallbackUnmarshalJSONSetsData asserts that Callbacks.UnmarshalJSON sets the map with correct key.
func TestCallbackUnmarshalJSONSetsData(t *testing.T) {
	data := []byte(`{"my-callback": {"$ref": "#/components/callbacks/test"}}`)
	var callbacks openapi3.Callbacks
	if err := callbacks.UnmarshalJSON(data); err != nil {
		t.Fatalf("unexpected error during UnmarshalJSON: %v", err)
	}
	if _, exists := callbacks["my-callback"]; !exists {
		t.Errorf("expected key 'my-callback' to exist in callbacks map")
	}
}

// TestMultiErrorImplementsError asserts that MultiError returns a non-empty string for Error().
func TestMultiErrorImplementsError(t *testing.T) {
	merr := openapi3.MultiError{json.UnmarshalTypeError{Value: "number", Type: &struct{}{}}}
	errStr := merr.Error()
	if errStr == "" {
		t.Errorf("expected MultiError.Error() to return non-empty string")
	}
}

// TestExampleNewCreatesExample asserts that NewExample creates an Example with the provided value.
func TestExampleNewCreatesExample(t *testing.T) {
	value := "test example"
	example := openapi3.NewExample(value)
	if example == nil {
		t.Fatalf("expected non-nil Example, got nil")
	}
	if example.Value != value {
		t.Errorf("expected Value to be '%s', got '%v'", value, example.Value)
	}
}

// TestEncodingWithHeaderAddsHeader asserts that Encoding.WithHeader adds a header to the encoding.
func TestEncodingWithHeaderAddsHeader(t *testing.T) {
	encoding := openapi3.NewEncoding()
	header := &openapi3.Header{Description: "Test Header"}
	encoding = encoding.WithHeader("X-Test", header)
	if encoding.Headers == nil {
		t.Fatalf("expected Headers map to be initialized, got nil")
	}
	if h, exists := encoding.Headers["X-Test"]; !exists || h.Value.Description != "Test Header" {
		t.Errorf("expected header 'X-Test' with description 'Test Header', not found or mismatched")
	}
}
```