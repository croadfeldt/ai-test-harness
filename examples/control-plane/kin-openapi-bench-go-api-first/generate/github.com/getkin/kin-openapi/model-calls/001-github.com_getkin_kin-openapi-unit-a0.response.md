```go
package harnesstest

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/getkin/kin-openapi/openapi3filter"
)

// TestNewLoader creates a new Loader and checks its default configuration.
func TestNewLoader(t *testing.T) {
	loader := openapi3.NewLoader()
	if loader == nil {
		t.Fatal("expected NewLoader to return a non-nil Loader")
	}
	if loader.ReadFromURIFunc == nil {
		t.Error("expected ReadFromURIFunc to be initialized, but it was nil")
	}
	if loader.IsExternalRefsAllowed != false {
		t.Errorf("expected IsExternalRefsAllowed to be false by default, got %v", loader.IsExternalRefsAllowed)
	}
	if loader.Context == nil {
		t.Error("expected Context to be initialized, but it was nil")
	}
}

// TestLoaderReadFromURIFuncDefault ensures the default ReadFromURIFunc is set.
func TestLoaderReadFromURIFuncDefault(t *testing.T) {
	loader := openapi3.NewLoader()
	if loader.ReadFromURIFunc == nil {
		t.Fatal("ReadFromURIFunc should not be nil by default")
	}
	// Just check it's callable (without triggering actual fetch)
	// We can't test full behavior without a real URI, but we expect no panic.
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("ReadFromURIFunc panicked unexpectedly: %v", r)
		}
	}()
	// This will fail logically (nil URL), but should not panic
	_, _ = loader.ReadFromURIFunc(loader, nil)
}

// TestTStructZeroValue validates zero value of T struct and its round-trip JSON.
func TestTStructZeroValue(t *testing.T) {
	swagger := &openapi3.T{}
	data, err := json.Marshal(swagger)
	if err != nil {
		t.Fatalf("json.Marshal failed on zero-value T: %v", err)
	}
	expected := `{}` // empty object
	if string(data) != expected {
		t.Errorf("expected JSON %q, got %q", expected, string(data))
	}
}

// TestTUnmarshalJSONEmptyObject ensures unmarshaling empty JSON into T works.
func TestTUnmarshalJSONEmptyObject(t *testing.T) {
	var swagger openapi3.T
	err := json.Unmarshal([]byte("{}"), &swagger)
	if err != nil {
		t.Fatalf("json.Unmarshal failed: %v", err)
	}
	// Ensure basic fields are zero but not nil where relevant
	if swagger.Components != nil {
		t.Errorf("expected Components to be nil in empty T, got %+v", swagger.Components)
	}
	if swagger.Paths != nil {
		t.Errorf("expected Paths to be nil, got %+v", swagger.Paths)
	}
	if swagger.Servers != nil {
		t.Errorf("expected Servers to be nil, got %+v", swagger.Servers)
	}
}

// TestTValidateEmptySpec checks that an empty spec fails validation.
func TestTValidateEmptySpec(t *testing.T) {
	swagger := &openapi3.T{}
	ctx := context.Background()
	err := swagger.Validate(ctx)
	if err == nil {
		t.Fatal("expected Validate to return an error for empty T, but got nil")
	}
	// It should be a MultiError or at least contain specific validation failures
	if _, ok := err.(openapi3.MultiError); !ok {
		t.Errorf("expected MultiError, got %T", err)
	}
}

// TestNewComponents returns a Components with initialized maps.
func TestNewComponents(t *testing.T) {
	components := openapi3.NewComponents()
	// Check that all map fields are non-nil after NewComponents
	if components.Schemas == nil {
		t.Error("expected Schemas to be initialized by NewComponents, but it was nil")
	}
	if components.RequestBodies == nil {
		t.Error("expected RequestBodies to be initialized, but it was nil")
	}
	if components.Parameters == nil {
		t.Error("expected Parameters to be initialized, but it was nil")
	}
	if components.Headers == nil {
		t.Error("expected Headers to be initialized, but it was nil")
	}
	if components.SecuritySchemes == nil {
		t.Error("expected SecuritySchemes to be initialized, but it was nil")
	}
	if components.Callbacks == nil {
		t.Error("expected Callbacks to be initialized, but it was nil")
	}
	if components.Examples == nil {
		t.Error("expected Examples to be initialized, but it was nil")
	}
	if components.Links == nil {
		t.Error("expected Links to be initialized, but it was nil")
	}
}

// TestComponentsValidateEmpty ensures empty Components passes validation.
func TestComponentsValidateEmpty(t *testing.T) {
	components := openapi3.NewComponents()
	ctx := context.Background()
	err := components.Validate(ctx)
	if err != nil {
		t.Fatalf("expected empty Components to be valid, but Validate returned: %v", err)
	}
}

// TestNewExample creates an example with a value and checks its export field.
func TestNewExample(t *testing.T) {
	value := "test-value"
	example := openapi3.NewExample(value)
	if example == nil {
		t.Fatal("NewExample returned nil")
	}
	if example.Value != value {
		t.Errorf("expected Value %v, got %v", value, example.Value)
	}
	if example.Summary != "" {
		t.Errorf("expected Summary to be empty by default, got %q", example.Summary)
	}
	if example.Description != "" {
		t.Errorf("expected Description to be empty, got %q", example.Description)
	}
	if example.ExternalValue != "" {
		t.Errorf("expected ExternalValue to be empty, got %q", example.ExternalValue)
	}
}

// TestExampleValidate checks that a valid Example passes validation.
func TestExampleValidate(t *testing.T) {
	example := openapi3.NewExample("valid-example")
	ctx := context.Background()
	err := example.Validate(ctx)
	if err != nil {
		t.Fatalf("expected valid Example to pass Validate, but got: %v", err)
	}
}

// TestOptionsInOpenapi3filter ensures Options struct can be instantiated.
func TestOptionsInOpenapi3filter(t *testing.T) {
	opts := openapi3filter.Options{
		ExcludeReadOnly:    false,
		IncludeReadOnly:    true,
		AuthenticationFunc: nil, // valid to be nil
	}
	// Just ensure it's constructable and has expected fields
	if opts.IncludeReadOnly != true {
		t.Errorf("expected IncludeReadOnly to be true, got %v", opts.IncludeReadOnly)
	}
	if opts.AuthenticationFunc != nil {
		t.Errorf("expected AuthenticationFunc to be nil, got %v", opts.AuthenticationFunc)
	}
}
```