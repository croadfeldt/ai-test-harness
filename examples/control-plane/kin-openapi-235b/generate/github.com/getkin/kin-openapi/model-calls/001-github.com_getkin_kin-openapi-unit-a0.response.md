```go
package harnesstest

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/getkin/kin-openapi/openapi3filter"
)

// TestNewLoader creates a loader and checks it initializes correctly.
func TestNewLoader(t *testing.T) {
	loader := openapi3.NewLoader()
	if loader == nil {
		t.Fatalf("NewLoader returned nil")
	}
	if loader.ReadFromURIFunc == nil {
		t.Errorf("expected ReadFromURIFunc to be non-nil by default")
	}
}

// TestLoaderReadFromURIFuncAllowsCustomization sets a custom ReadFromURIFunc and checks it is stored.
func TestLoaderReadFromURIFuncAllowsCustomization(t *testing.T) {
	loader := openapi3.NewLoader()
	customFunc := func(*openapi3.Loader, *openapi3.URI) ([]byte, error) {
		return []byte("test"), nil
	}
	loader.ReadFromURIFunc = customFunc
	if loader.ReadFromURIFunc == nil {
		t.Fatalf("ReadFromURIFunc was not set")
	}
}

// TestNewCallbackBuildsWithEmptyOptions creates a callback with no options and checks it is non-nil.
func TestNewCallbackBuildsWithEmptyOptions(t *testing.T) {
	cb := openapi3.NewCallback()
	if cb == nil {
		t.Fatalf("NewCallback returned nil with no options")
	}
}

// TestWithCallbackReturnsOption checks that WithCallback returns a valid option function.
func TestWithCallbackReturnsOption(t *testing.T) {
	pathItem := &openapi3.PathItem{}
	opt := openapi3.WithCallback("/test", path7)
	if opt == nil {
		t.Fatalf("WithCallback returned nil option")
	}
	// Apply the option to verify it doesn't panic
	cb := &openapi3.Callback{}
	opt(cb)
	if len(*cb) != 1 {
		t.Errorf("expected callback to have 1 path item after applying option")
	}
}

// TestComponentsNewCreatesEmptyMap checks that NewComponents returns a Components with empty maps.
func TestComponentsNewCreatesEmptyMap(t *testing.T) {
	components := openapi3.NewComponents()
	if components.Schemas == nil {
		t.Errorf("expected Schemas to be initialized")
	}
	if len(components.Schemas) != 0 {
		t.Errorf("expected Schemas to be empty")
	}
}

// TestComponentsValidateOnEmptySucceeds validates an empty Components and expects no error.
func TestComponentsValidateOnEmptySucceeds(t *testing.T) {
	components := openapi3.NewComponents()
	err := components.Validate(context.Background())
	if err != nil {
		t.Errorf("expected no validation error for empty components, got %v", err)
	}
}

// TestContentGetReturnsNilForMissingMime checks Get returns nil when mime type is not present.
func TestContentGetReturnsNilForMissingMime(t *testing.T) {
	content := openapi3.NewContent()
	result := content.Get("application/json")
	if result != nil {
		t.Errorf("expected Get to return nil for missing mime, got %v", result)
	}
}

// TestNewContentWithJSONSchemaCreatesContent checks it creates content with application/json schema.
func TestNewContentWithJSONSchemaCreatesContent(t *testing.T) {
	schema := &openapi3.Schema{Type: "string"}
	content := openapi3.NewContentWithJSONSchema(schema)
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatalf("expected application/json MediaType to be set")
	}
	if mediaType.Schema == nil || mediaType.Schema.Value.Type != "string" {
		t.Errorf("expected schema type string, got %v", mediaType.Schema)
	}
}

// TestMultiErrorImplementsError checks MultiError returns a non-empty string for Error().
func TestMultiErrorImplementsError(t *testing.T) {
	merr := openapi3.MultiError{json.UnmarshalTypeError{Value: "x", Type: &struct{}{}}}
	msg := merr.Error()
	if msg == "" {
		t.Errorf("expected MultiError.Error() to return non-empty string")
	}
}

// TestMultiErrorIsAllowsComparison uses errors.Is pattern to check Is method works.
func TestMultiErrorIsAllowsComparison(t *testing.T) {
	cause := &json.UnmarshalTypeError{Value: "bool", Type: &struct{}{}}
	merr := openapi3.MultiError{cause}
	var target *json.UnmarshalTypeError
	if !merr.Is(target) {
		t.Errorf("expected MultiError.Is to recognize underlying UnmarshalTypeError")
	}
}
```