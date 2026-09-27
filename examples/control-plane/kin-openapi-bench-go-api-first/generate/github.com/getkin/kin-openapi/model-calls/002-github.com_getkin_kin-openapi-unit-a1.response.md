```go
package harnesstest

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/stretchr/testify/assert"
)

// TestNewLoader ensures that NewLoader returns a non-nil Loader with ReadFromURIFunc set to a non-nil function.
func TestNewLoader(t *testing.T) {
	loader := openapi3.NewLoader()
	assert.NotNil(t, loader)
	assert.NotNil(t, loader.ReadFromURIFunc, "ReadFromURIFunc should not be nil after NewLoader")
}

// TestLoaderReadFromURIFuncDefault checks that the default ReadFromURIFunc can be called without panic.
func TestLoaderReadFromURIFuncDefault(t *testing.T) {
	loader := openapi3.NewLoader()
	assert.NotNil(t, loader.ReadFromURIFunc, "ReadFromURIFunc should not be nil")

	// Try calling it with minimal data to ensure it doesn't panic (even if result is error)
	_, err := loader.ReadFromURIFunc(nil, nil)
	assert.Error(t, err) // Expected to fail due to nil inputs, but not panic
}

// TestTStructZeroValue checks the zero value marshaling behavior of openapi3.T.
func TestTStructZeroValue(t *testing.T) {
	var spec openapi3.T
	data, err := json.Marshal(&spec)
	assert.NoError(t, err)
	assert.JSONEq(t, `{"info":null,"openapi":"","paths":null}`, string(data))
}

// TestTValidateEmptySpec checks validation behavior of an empty spec.
func TestTValidateEmptySpec(t *testing.T) {
	var spec openapi3.T
	ctx := context.Background()
	err := spec.Validate(ctx)
	assert.Error(t, err)
	// Validate should return a RequiredFieldError for "info" when validating empty spec
	assert.Contains(t, err.Error(), "info")
}

// TestNewComponents checks that NewComponents initializes all map fields.
func TestNewComponents(t *testing.T) {
	components := openapi3.NewComponents()
	assert.NotNil(t, components.Schemas)
	assert.NotNil(t, components.RequestBodies)
	assert.NotNil(t, components.Parameters)
	assert.NotNil(t, components.Headers)
	assert.NotNil(t, components.SecuritySchemes)
	assert.NotNil(t, components.Responses)
	assert.NotNil(t, components.Examples)
	assert.NotNil(t, components.Links)
	assert.NotNil(t, components.Callbacks)
}

// TestComponentsValidate checks that an empty Components passes validation.
func TestComponentsValidate(t *testing.T) {
	components := openapi3.NewComponents()
	ctx := context.Background()
	err := components.Validate(ctx)
	assert.NoError(t, err)
}

// TestNewContent checks that NewContent returns a non-nil map.
func TestNewContent(t *testing.T) {
	content := openapi3.NewContent()
	assert.NotNil(t, content)
	assert.IsType(t, openapi3.Content{}, content)
	assert.Empty(t, content)
}

// TestNewContentWithJSONSchema creates a schema and uses it in NewContentWithJSONSchema.
func TestNewContentWithJSONSchema(t *testing.T) {
	schema := openapi3.NewSchema()
	content := openapi3.NewContentWithJSONSchema(schema)
	assert.NotNil(t, content)
	assert.Equal(t, 1, len(content))
	mediaType, exists := content["application/json"]
	assert.True(t, exists)
	assert.NotNil(t, mediaType)
	assert.Same(t, schema, mediaType.Schema)
}

// TestNewCallback checks that NewCallback with WithCallback option correctly sets up a callback.
func TestNewCallback(t *testing.T) {
	pathItem := openapi3.NewPathItem()
	cb := openapi3.NewCallback(openapi3.WithCallback("/callback", pathItem))
	assert.NotNil(t, cb)
	assert.Equal(t, 1, len(cb))
	ref, exists := cb["/callback"]
	assert.True(t, exists)
	assert.Same(t, pathItem, ref.Value)
}

// TestMultiErrorIs checks that MultiError implements errors.Is correctly.
func TestMultiErrorIs(t *testing.T) {
	err1 := assert.AnError
	err2 := openapi3.MultiError{err1}
	assert.ErrorIs(t, err2, err1)
}
```