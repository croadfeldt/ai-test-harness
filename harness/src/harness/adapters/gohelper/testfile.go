// The test-file half of gohelper: what the generation gates need to know about one Go test file,
// answered with go/ast rather than regular expressions.
//
//	inspect <file>              parse errors, Test* functions, imports, weak tests, symbol references, skips
//	strip <file> <name>...      the file without the named functions, and without imports they alone used
package main

import (
	"bytes"
	"encoding/json"
	"go/ast"
	"go/format"
	"go/parser"
	"go/token"
	"os"
	"strings"
)

type Inspection struct {
	Error   string              `json:"error"`
	Package string              `json:"package"`
	Tests   []string            `json:"tests"`
	Imports []string            `json:"imports"`
	Weak    []string            `json:"weak"`
	Skipped []string            `json:"skipped"`
	Refs    map[string][]string `json:"refs"`
}

var failCalls = map[string]bool{"Error": true, "Errorf": true, "Fatal": true, "Fatalf": true, "Fail": true, "FailNow": true}

func isTestFunc(fd *ast.FuncDecl) bool {
	if fd.Recv != nil || !strings.HasPrefix(fd.Name.Name, "Test") || fd.Type.Params == nil || len(fd.Type.Params.List) != 1 {
		return false
	}
	star, ok := fd.Type.Params.List[0].Type.(*ast.StarExpr)
	if !ok {
		return false
	}
	sel, ok := star.X.(*ast.SelectorExpr)
	return ok && sel.Sel.Name == "T"
}

// weak: no t.Error/Fatal/Fail call, no helper call that receives t, no assertion library. Such a
// test cannot fail on its own; a panic would fail it, which is not an assertion.
func isWeak(fd *ast.FuncDecl, tName string) bool {
	canFail := false
	ast.Inspect(fd.Body, func(n ast.Node) bool {
		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}
		if sel, ok := call.Fun.(*ast.SelectorExpr); ok {
			if id, ok := sel.X.(*ast.Ident); ok && id.Name == tName && failCalls[sel.Sel.Name] {
				canFail = true
			}
		}
		for _, a := range call.Args {
			if id, ok := a.(*ast.Ident); ok && id.Name == tName {
				canFail = true
			}
		}
		return true
	})
	return !canFail
}

func hasSkip(fd *ast.FuncDecl, tName string) bool {
	found := false
	ast.Inspect(fd.Body, func(n ast.Node) bool {
		if call, ok := n.(*ast.CallExpr); ok {
			if sel, ok := call.Fun.(*ast.SelectorExpr); ok {
				if id, ok := sel.X.(*ast.Ident); ok && id.Name == tName && strings.HasPrefix(sel.Sel.Name, "Skip") {
					found = true
				}
			}
		}
		return true
	})
	return found
}

func inspectCmd(file string) {
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, file, nil, parser.ParseComments)
	out := Inspection{Tests: []string{}, Imports: []string{}, Weak: []string{}, Skipped: []string{}, Refs: map[string][]string{}}
	if err != nil {
		out.Error = err.Error()
		json.NewEncoder(os.Stdout).Encode(out)
		return
	}
	out.Package = f.Name.Name
	alias := map[string]string{}
	for _, imp := range f.Imports {
		p := strings.Trim(imp.Path.Value, `"`)
		out.Imports = append(out.Imports, p)
		name := p[strings.LastIndex(p, "/")+1:]
		if imp.Name != nil {
			name = imp.Name.Name
		}
		alias[name] = p
	}
	for _, d := range f.Decls {
		fd, ok := d.(*ast.FuncDecl)
		if !ok || !isTestFunc(fd) {
			continue
		}
		out.Tests = append(out.Tests, fd.Name.Name)
		tName := "t"
		if len(fd.Type.Params.List[0].Names) > 0 {
			tName = fd.Type.Params.List[0].Names[0].Name
		}
		if isWeak(fd, tName) {
			out.Weak = append(out.Weak, fd.Name.Name)
		}
		if hasSkip(fd, tName) {
			out.Skipped = append(out.Skipped, fd.Name.Name)
		}
		refs := map[string]bool{}
		ast.Inspect(fd.Body, func(n ast.Node) bool {
			if sel, ok := n.(*ast.SelectorExpr); ok {
				if id, ok := sel.X.(*ast.Ident); ok {
					if p, ok := alias[id.Name]; ok {
						refs[p+"."+sel.Sel.Name] = true
					}
				}
			}
			return true
		})
		list := []string{}
		for r := range refs {
			list = append(list, r)
		}
		out.Refs[fd.Name.Name] = list
	}
	json.NewEncoder(os.Stdout).Encode(out)
}

func stripCmd(file string, names []string) {
	drop := map[string]bool{}
	for _, n := range names {
		drop[n] = true
	}
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, file, nil, parser.ParseComments)
	if err != nil {
		os.Stderr.WriteString(err.Error())
		os.Exit(1)
	}
	var kept []ast.Decl
	for _, d := range f.Decls {
		if fd, ok := d.(*ast.FuncDecl); ok && fd.Recv == nil && drop[fd.Name.Name] {
			continue
		}
		kept = append(kept, d)
	}
	f.Decls = kept
	// Imports no remaining declaration uses go too, or the file would not compile.
	used := map[string]bool{}
	for _, d := range f.Decls {
		if _, ok := d.(*ast.GenDecl); ok {
			if g := d.(*ast.GenDecl); g.Tok == token.IMPORT {
				continue
			}
		}
		ast.Inspect(d, func(n ast.Node) bool {
			if sel, ok := n.(*ast.SelectorExpr); ok {
				if id, ok := sel.X.(*ast.Ident); ok {
					used[id.Name] = true
				}
			}
			return true
		})
	}
	for _, d := range f.Decls {
		g, ok := d.(*ast.GenDecl)
		if !ok || g.Tok != token.IMPORT {
			continue
		}
		var specs []ast.Spec
		for _, s := range g.Specs {
			imp := s.(*ast.ImportSpec)
			p := strings.Trim(imp.Path.Value, `"`)
			name := p[strings.LastIndex(p, "/")+1:]
			if imp.Name != nil {
				name = imp.Name.Name
			}
			if name == "_" || name == "." || used[name] {
				specs = append(specs, s)
			}
		}
		g.Specs = specs
	}
	var decls []ast.Decl
	for _, d := range f.Decls {
		if g, ok := d.(*ast.GenDecl); ok && g.Tok == token.IMPORT && len(g.Specs) == 0 {
			continue
		}
		decls = append(decls, d)
	}
	f.Decls = decls
	f.Comments = nil // comments anchored to removed declarations would float; the header comment is re-added by the harness
	var buf bytes.Buffer
	if err := format.Node(&buf, fset, f); err != nil {
		os.Stderr.WriteString(err.Error())
		os.Exit(1)
	}
	os.Stdout.Write(buf.Bytes())
}
