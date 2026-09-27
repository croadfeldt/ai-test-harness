```go
package harnesstest

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/getkin/kin-openapi/openapi3filter"
)

// TestNewLoaderCreatesNonNilInstance ensures NewLoader returns a non-nil Loader.
func TestNewLoaderCreatesNonNilInstance(t *testing.T) {
	loader := openapi3.NewLoader()
	if loader == nil {
		t.Fatalf("expected non-nil loader, got nil")
	}
}

// TestLoaderReadFromURIFuncIsSettable verifies that ReadFromURIFunc field can be assigned.
func TestLoaderReadFromURIFuncIsSettable(t *testing.T) {
	loader := openapi3.NewLoader()
	original := loader.ReadFromURIFunc
	loader.ReadFromURIFunc = func(loader *openapi3.Loader, url string) ([]byte, error) {
		return nil, nil
	}
	if loader.ReadFromURIFunc == original {
		t.Errorf("expected ReadFromURIFunc to be modifiable")
	}
}

// TestTStructExists ensures the T struct (Swagger specification) can be instantiated.
func TestTStructExists(t *testing.T) {
	var spec openapi3.T
	if spec.Info != nil {
		t.Errorf("expected zero value of T to have nil Info, got non-nil")
	}
}

// TestNewComponentsReturnsEmptyMap ensures NewComponents returns a Components with initialized maps.
func TestNewComponentsReturnsEmptyMap(t *testing.T) {
	components := openapi3.NewComponents()
	if components.Schemas == nil {
		t.Errorf("expected Schemas to be initialized, got nil")
	}
	if components.Parameters == nil {
		t.Errorf("expected Parameters to be initialized, got nil")
	}
	if components.Headers == nil {
		t.Errorf("expected Headers to be initialized, got nil")
	}
	if components.RequestBodies == nil {
		t.Errorf("expected RequestBodies to be initialized, got nil")
	}
}

// TestComponentsValidateOnEmpty succeeds when Validate is called on empty Components.
func TestComponentsValidateOnEmpty(t *testing.T) {
	components := openapi3.NewComponents()
	err := components.Validate(context.Background())
	if err != nil {
		t.Errorf("expected no validation error on empty components, got %v", err)
	}
}

// TestNewContentCreatesEmptyMap ensures NewContent returns an initialized Content map.
func TestNewContentCreatesEmptyMap(t *testing.T) {
	content := openapi3.NewContent()
	if content == nil {
		t.Fatalf("expected non-nil content, got nil")
	}
}

// TestNewContentWithJSONSchemaRefSetsApplicationJSON ensures schema ref is set under application/json.
func TestNewContentWithJSONSchemaRefSetsApplicationJSON(t *testing.T) {
	schemaRef := &openapi3.SchemaRef{Value: &openapi3.Schema{Type: "string"}}
	content := openapi3.NewContentWithJSONSchemaRef(schemaRef)
	mediaType := content.Get("application/json")
	if mediaType == nil {
		t.Fatalf("expected application/json media type to be set")
	}
	if mediaType.Schema != schemaRef {
		t.Errorf("expected schema ref to match, but got mismatch")
	}
}

// TestContactUnmarshalJSONParsesName ensures unmarshaling JSON sets the Name field.
func TestContactUnmarshalJSONParsesName(t *testing.T) {
	data := `{"name": "API Support"}`
	var contact openapi3.Contact
	err := contact.UnmarshalJSON([]byte(data))
	if err != nil {
		t.Fatalf("unexpected error on unmarshal: %v", err)
	}
	if contact.Name != "API Support" {
		t.Errorf("expected Name to be 'API Support', got '%s'", contact.Name)
	}
}

// TestContactValidateFailsOnInvalidEmail ensures validation fails when email is invalid.
func TestContactValidateFailsOnInvalidEmail(t *testing.T) {
	contact := &openapi3.Contact{
		Email: "invalid-email",
	}
	err := contact.Validate(context.Background())
	if err == nil {
		t.Errorf("expected validation error for invalid email, got nil")
	}
}

// TestAuthenticationInputIsUsable verifies AuthenticationInput can be instantiated and used.
func TestAuthenticationInputIsUsable(t *testing.T) {
	input := &openapi3filter.AuthenticationInput{
		Scopes: []string{"read"},
	}
	if len(input.Scopes) != 1 || input.Scopes[0] != "read" {
		t.Errorf("expected scopes to be preserved")
	}
}
```