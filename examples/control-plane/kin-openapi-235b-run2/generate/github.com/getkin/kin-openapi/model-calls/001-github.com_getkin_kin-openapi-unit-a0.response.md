```go
package harnesstest

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
)

// TestNewLoaderCreatesValidLoader checks that NewLoader returns a non-nil Loader with default settings.
func TestNewLoaderCreatesValidLoader(t *testing.T) {
	loader := openapi3.NewLoader()
	if loader == nil {
		t.Fatalf("expected non-nil loader, got nil")
	}
	if loader.ReadFromURIFunc == nil {
		t.Errorf("expected ReadFromURIFunc to be initialized, got nil")
	}
}

// TestLoaderReadFromURIDefaultBehavior ensures the default ReadFromURIFunc returns an error for unsupported URIs.
func TestLoaderReadFromURIDefaultBehavior(t *testing.T) {
	loader := openapi3.NewLoader()
	_, err := loader.ReadFromURIFunc(loader, nil)
	if err == nil {
		t.Fatalf("expected error from ReadFromURIFunc, got nil")
	}
}

// TestNewComponentsReturnsEmptyComponents verifies NewComponents returns an empty Components struct.
func TestNewComponentsReturnsEmptyComponents(t *testing.T) {
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

// TestComponentsValidateEmpty succeeds when Components is empty and valid.
func TestComponentsValidateEmpty(t *testing.T) {
	components := openapi3.NewComponents()
	err := components.Validate(context.Background())
	if err != nil {
		t.Fatalf("expected no validation error for empty components, got %v", err)
	}
}

// TestNewCallbackWithoutOptions creates a Callback without options and checks it's non-nil.
func TestNewCallbackWithoutOptions(t *testing.T) {
	cb := openapi3.NewCallback()
	if cb == nil {
		t.Fatalf("expected non-nil callback, got nil")
	}
	if len(*cb) != 0 {
		t.Errorf("expected empty callback map, got %d entries", len(*cb))
	}
}

// TestWithCallbackOption adds a callback via WithCallback and checks it's stored correctly.
func TestWithCallbackOption(t *testing.T) {
	pathItem := &openapi3.PathItem{}
	option := openapi3.WithCallback("/test", pathItem)
	cb := openapi3.NewCallback(option)
	if len(*cb) != 1 {
		t.Fatalf("expected 1 callback entry, got %d", len(*cb))
	}
	if _, exists := (*cb)["/test"]; !exists {
		t.Errorf("expected callback key '/test' to exist")
	}
}

// TestNewContentReturnsEmptyContent checks NewContent returns a non-nil empty Content map.
func TestNewContentReturnsEmptyContent(t *testing.T) {
	content := openapi3.NewContent()
	if content == nil {
		t.Fatalf("expected non-nil content, got nil")
	}
	if len(content) != 0 {
		t.Errorf("expected empty content map, got %d entries", len(content))
	}
}

// TestNewContentWithJSONSchema creates Content with JSON schema and checks application/json key exists.
func TestNewContentWithJSONSchema(t *testing.T) {
	schema := &openapi3.Schema{Type: "string"}
	content := openapi3.NewContentWithJSONSchema(schema)
	if mt := content.Get("application/json"); mt == nil {
		t.Fatalf("expected MediaType for application/json, got nil")
	} else {
		if mt.Schema == nil {
			t.Errorf("expected schema to be set, got nil")
		} else if mt.Schema.Value.Type != "string" {
			t.Errorf("expected schema type string, got %s", mt.Schema.Value.Type)
		}
	}
}

// TestContactUnmarshalJSON parses a valid JSON contact and populates the struct fields.
func TestContactUnmarshalJSON(t *testing.T) {
	data := `{"name":"test","email":"test@example.com","url":"https://example.com"}`
	var contact openapi3.Contact
	err := json.Unmarshal([]byte(data), &contact)
	if err != nil {
		t.Fatalf("unexpected error during UnmarshalJSON: %v", err)
	}
	if contact.Name != "test" {
		t.Errorf("expected Name=test, got %s", contact.Name)
	}
	if contact.Email != "test@example.com" {
		t.Errorf("expected Email=test@example.com, got %s", contact.Email)
	}
	if contact.URL == nil || *contact.URL != "https://example.com" {
		t.Errorf("expected URL=https://example.com, got %v", contact.URL)
	}
}

// TestContactValidateValid succeeds when Contact has valid fields.
func TestContactValidateValid(t *testing.T) {
	contact := &openapi3.Contact{
		Name:  "test",
		Email: "test@example.com",
	}
	err := contact.Validate(context.Background())
	if err != nil {
		t.Fatalf("expected no validation error, got %v", err)
	}
}
```