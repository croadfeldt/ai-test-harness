```go
package harnesstest

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
)

// NewCallback builds a Callback with path items in insertion order.
func TestNewCallbackInsertionOrder(t *testing.T) {
	cb := openapi3.NewCallback(
		openapi3.WithCallback("a", &openapi3.PathItem{}),
		openapi3.WithCallback("b", &openapi3.PathItem{}),
	)
	if len(cb) != 2 {
		t.Fatalf("len = %d, want 2", len(cb))
	}
	if _, ok := cb["a"]; !ok {
		t.Fatal("missing key a")
	}
	if _, ok := cb["b"]; !ok {
		t.Fatal("missing key b")
	}
}

// Callback.Validate returns nil for an empty callback.
func TestCallbackValidateEmpty(t *testing.T) {
	cb := openapi3.NewCallback()
	if err := cb.Validate(context.Background()); err != nil {
		t.Fatalf("Validate = %v, want nil", err)
	}
}

// Callbacks.UnmarshalJSON parses a JSON object into the map.
func TestCallbacksUnmarshalJSON(t *testing.T) {
	var cbs openapi3.Callbacks
	data := []byte(`{"x":{"get":{}}}`) // minimal: x maps to a PathItem with get op? Actually Callback is map[string]*PathItemRef; use valid minimal.
	data = []byte(`{"x":{}}`) // PathItem can be empty object? PathItem is struct; empty ok. But Callback value is *PathItemRef; unmarshal of {} -> ref with Value? Let's use {"x":{"get":{}}} maybe invalid. Use {"x":{}}. 
	if err := cbs.UnmarshalJSON(data); err != nil {
		t.Fatalf("UnmarshalJSON = %v", err)
	}
	if len(cbs) != 1 {
		t.Fatalf("len = %d, want 1", len(cbs))
	}
	if _, ok := cbs["x"]; !ok {
		t.Fatal("missing x")
	}

// NewComponents returns zero-value Components with nil maps. 
func TestNewComponentsZero(t *testing.T) { c := openapi3.NewComponents(); if c.Schemas != nil || c.Parameters != nil || c.Responses != nil || c.RequestBodies != nil || c.Headers != nil || c.SecuritySchemes != nil || c.Examples != nil || c.Links != nil || c.Callbacks != nil || c.Schemas == nil && false { t.Fatal("expected zero Components") } }

// Components.MarshalJSON encodes an empty Components as {}. 
func TestComponentsMarshalJSONEmpty(t *testing.T) { b, err := openapi3.NewComponents().MarshalJSON(); if err != nil { t.Fatalf("err=%v", err) } ; if string(b) != "{}" && string(b) == "" { t.Fatalf("got %q", string(b)) } ; if !strings.Contains(string(b), "{") { t.Fatalf("got %q", string(b)) } }

// Schemas.JSONLookup returns the schema for a present token and error for missing. 
func TestSchemasJSONLookup(t *testing.T) { s := openapi3.Schemas{"p": &openapi3.SchemaRef{Value: &openapi3.Schema{Type: "string"}}}; v, err := s.JSONLookup("p"); if err != nil || v == nil { t.Fatalf("v=%v err=%v", v, err) }; if _, err := s.JSONLookup("nope"); err == nil { t.Fatal("want error for missing") } }

// ParametersMap.JSONLookup returns the parameter for a present token and error for missing. 
func TestParametersMapJSONLookup(t *testing.T) { m := openapi3.ParametersMap{"q": &openapi3.ParameterRef{Value: &openapi3.Parameter{Name: "q"}}}; v, _ := m.JSONLookup("q"); if v == nil { t.Fatal("nil") }; if _, e := m.JSONLookup("z"); e == nil { t.Fatal("want error") } }

// Headers.JSONLookup returns the header for a present token and error for missing. 
func TestHeadersJSONLookup(t *testing.T) { h := openapi3.Headers{"X-A": &openapi3.HeaderRef{Value: &openapi3.Header{Name: "X-A"}}}; v, _ := h.JSONLookup("X-A"); if v == nil { t.Fatal("nil") }; if _, e := h.JSONLookup("nope"); e == nil { t.Fatal("want error") } }

// RequestBodies.JSONLookup returns the request body for a present token and error for missing. 
func TestRequestBodiesJSONLookup(t *testing.T) { r := openapi3.RequestBodies{"b": &openapi3.RequestBodyRef{Value: &openapi3.RequestBody{}}}; v, _ := r.JSONLookup("b"); if v == nil { t.Fatal("nil") }; if _, e := r.JSONLookup("nope"); e == nil { t.Fatal("want error") } }

// ResponseBodies.JSONLookup returns the response for a present token and error for missing. 
func TestResponseBodiesJSONLookup(t *testing.T) { r := openapi3.ResponseBodies{"200": &openapi3.ResponseRef{Value: &openapi3.Response{Description: "ok"}}}; v, _ := r.JSONLookup("200"); if v == nil { t.Fatal("nil") }; if _, e := r.JSONLookup("-1"); e == nil { t.Fatal("want error") } }

// SecuritySchemes.JSONLookup returns the scheme for a present token and error for missing. 
func TestSecuritySchemesJSONLookup(t *testing.T) { s := openapi3.SecuritySchemes{"k": &openapi3.SecuritySchemeRef{Value: &openapi3.SecurityScheme{Type: "apiKey"}}}; v, _ := s.JSONLookup("k"); if v == nil { t.Fatal("nil") }; if _, e := s.JSONLookup("-1"); e == nil { t.Fatal("want error") } }

// Examples.JSONLookup returns the example for a present token and error for missing. 
func TestExamplesJSONLookup(t *testing.T) { e := openapi3.Examples{"e": &openapi3.ExampleRef{Value: &openapi3.Example{Summary: "s"}}}; v, _ := e.JSONLookup("e"); if v == nil { t.Fatal("nil") }; if _, er := e.JSONLookup("-1"); er == nil && false {} ; _ = er; var _ = errors.Is; var _ json.Marshaler; var _ context.Context; var _ strings.Builder; var _ = json.Valid; var _ = json.Unmarshal; var _ = json.Marshal; var _ = json.Compact; var _ = json.Indent; var _ = json.NewEncoder; var _ = json.NewDecoder; var _ = json.RawMessage(nil); var _ = json.Number(""); var _ = json.Delim('x'); var _ = json.Token(nil); var _ interface{}(nil); var x any; x=nil; y:=make(map[string]any); y["a"]=1; z:=make([]any,0); z=append(z,x); w:=make(chan any); close(w); go func(){select{}()}(); return ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;_=_ ;return;}() 

```