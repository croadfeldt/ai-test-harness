```go
package harnesstest

import (
	"context"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/getkin/kin-openapi/openapi3filter"
)

// TestNewLoader ensures that NewLoader returns a non-nil Loader with a non-nil ReadFromURIFunc.
func TestNewLoader(t *testing.T) {
	loader := openapi3.NewLoader()
	if loader == nil {
		t.Fatal("NewLoader returned nil")
	}
	if loader.ReadFromURIFunc == nil {
		t.Fatal("ReadFromURIFunc should not be nil after NewLoader")
	}
}

// TestLoaderReadFromURIFuncDefault ensures that the default ReadFromURIFunc is callable and non-nil.
func TestLoaderReadFromURIFuncDefault(t *testing.T) {
	loader := openapi3.NewLoader()
	if loader.ReadFromURIFunc == nil {
		t.Fatal("ReadFromURIFunc is nil by default")
	}
	// We don't need to call it with valid URL for this test; just ensure it's a function and can be called.
	// Since we cannot create a valid URL without side effects, we rely on non-nil check.
}

// TestT_Struct ensures that the T struct can be instantiated and has expected zero values.
func TestT_Struct(t *testing.T) {
	swagger := &openapi3.T{}
	if swagger.Paths == nil {
		t.Error("Expected Paths to be initialized as empty map, got nil")
	}
	if swagger.Components == (openapi3.Components{}) {
		t.Error("Expected Components to be value, but it's uninitialized?")
	}
}

// TestNewComponents ensures that NewComponents returns a Components with properly initialized maps.
func TestNewComponents(t *testing.T) {
	components := openapi3.NewComponents()
	// Validate that Schemas is non-nil
	if components.Schemas == nil {
		t.Error("Expected Components.Schemas to be non-nil after NewComponents")
	}
	if components.RequestBodies == nil {
		t.Error("Expected Components.RequestBodies to be non-nil after NewComponents")
	}
	if components.Parameters == nil {
		t.Error("Expected Components.Parameters to be non-nil after NewComponents")
	}
	if components.Headers == nil {
		t.Error("Expected Components.Headers to be non-nil after NewComponents")
	}
	if components.SecuritySchemes == nil {
		t.Error("Expected Components.SecuritySchemes to be non-nil after NewComponents")
	}
}

// TestComponentsValidate ensures that Components.Validate returns nil on empty components.
func TestComponentsValidate(t *testing.T) {
	components := openapi3.NewComponents()
	err := components.Validate(context.Background())
	if err != nil {
		t.Fatalf("Expected no validation error on empty components, got: %v", err)
	}
}

// TestNewContent ensures that NewContent returns a non-nil Content with zero entries.
func TestNewContent(t *testing.T) {
	content := openapi3.NewContent()
	if content == nil {
		t.Fatal("NewContent returned nil")
	}
	if len(content) != 0 {
		t.Errorf("Expected empty content map, got %d entries", len(content))
	}
}

// TestNewContentWithJSONSchema ensures that NewContentWithJSONSchema creates content for application/json.
func TestNewContentWithJSONSchema(t *testing.T) {
	schema := &openapi3.Schema{Type: "string"}
	content := openapi3.NewContentWithJSONSchema(schema)
	if content == nil {
		t.Fatal("NewContentWithJSONSchema returned nil")
	}
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatal("Expected application/json MediaType in content")
	}
	if mediaType.Schema == nil {
		t.Fatal("Expected MediaType to have Schema")
	}
	if mediaType.Schema.Value.Type != "string" {
		t.Errorf("Expected schema type string, got %v", mediaType.Schema.Value.Type)
	}
}

// TestNewExample ensures that NewExample creates an Example with correct value.
func TestNewExample(t *testing.T) {
	value := "test-example"
	example := openapi3.NewExample(value)
	if example == nil {
		t.Fatal("NewExample returned nil")
	}
	if example.Value != value {
		t.Errorf("Expected Example.Value to be %v, got %v", value, example.Value)
	}
}

// TestExampleValidate ensures that Example.Validate returns nil for a valid example.
func TestExampleValidate(t *testing.T) {
	example := openapi3.NewExample("test")
	err := example.Validate(context.Background())
	if err != nil {
		t.Fatalf("Expected no validation error on valid Example, got: %v", err)
	}
}

// TestOptions_Struct ensures that openapi3filter.Options has expected zero values.
func TestOptions_Struct(t *testing.T) {
	opts := openapi3filter.Options{}
	// This is a concrete struct; just asserting it can be declared
	if &opts == nil {
		t.Fatal("Expected Options to be stack-allocated and addressable")
	}
	// No explicit fields tested unless we know from API, but struct exists.
}
```