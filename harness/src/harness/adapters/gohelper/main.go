// gohelper: the Go half of the Go adapter. It uses go/parser and go/ast to answer two questions the
// harness asks of every ecosystem with tools, never with a model:
//   api   <dir>            exported declarations (functions, methods, types, consts, vars) as JSON
//   sites <dir> <module>   every reference from first-party code to a package of <module>, as JSON
// Built with `go run` at call time from the harness's own source, so the Go toolchain on the runner is
// the only requirement. Output is one JSON document on stdout.
package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strings"
)

type Symbol struct {
	Module    string `json:"module"`
	Qualname  string `json:"qualname"`
	Kind      string `json:"kind"`
	Signature string `json:"signature"`
	Doc       string `json:"doc"`
	File      string `json:"file"`
	Line      int    `json:"line"`
}

type Site struct {
	Symbol  string `json:"symbol"`
	File    string `json:"file"`
	Line    int    `json:"line"`
	InTest  bool   `json:"in_test"`
	Context string `json:"context"`
}

func firstLine(d *ast.CommentGroup) string {
	if d == nil {
		return ""
	}
	t := strings.TrimSpace(d.Text())
	if i := strings.IndexByte(t, '\n'); i >= 0 {
		t = t[:i]
	}
	if len(t) > 160 {
		t = t[:160]
	}
	return t
}

func exprString(fset *token.FileSet, e ast.Expr) string {
	if e == nil {
		return ""
	}
	var b strings.Builder
	printExpr(&b, e)
	return b.String()
}

func printExpr(b *strings.Builder, e ast.Expr) {
	switch x := e.(type) {
	case *ast.Ident:
		b.WriteString(x.Name)
	case *ast.SelectorExpr:
		printExpr(b, x.X)
		b.WriteString(".")
		b.WriteString(x.Sel.Name)
	case *ast.StarExpr:
		b.WriteString("*")
		printExpr(b, x.X)
	case *ast.ArrayType:
		b.WriteString("[]")
		printExpr(b, x.Elt)
	case *ast.MapType:
		b.WriteString("map[")
		printExpr(b, x.Key)
		b.WriteString("]")
		printExpr(b, x.Value)
	case *ast.Ellipsis:
		b.WriteString("...")
		printExpr(b, x.Elt)
	case *ast.FuncType:
		b.WriteString("func(")
		b.WriteString(fieldList(x.Params))
		b.WriteString(")")
		if x.Results != nil {
			b.WriteString(" ")
			b.WriteString(fieldList(x.Results))
		}
	case *ast.InterfaceType:
		b.WriteString("interface{...}")
	case *ast.StructType:
		b.WriteString("struct{...}")
	case *ast.ChanType:
		b.WriteString("chan ")
		printExpr(b, x.Value)
	case *ast.IndexExpr:
		printExpr(b, x.X)
		b.WriteString("[")
		printExpr(b, x.Index)
		b.WriteString("]")
	default:
		b.WriteString("?")
	}
}

func fieldList(fl *ast.FieldList) string {
	if fl == nil {
		return ""
	}
	var parts []string
	for _, f := range fl.List {
		t := exprString(nil, f.Type)
		if len(f.Names) == 0 {
			parts = append(parts, t)
			continue
		}
		for _, n := range f.Names {
			parts = append(parts, n.Name+" "+t)
		}
	}
	return strings.Join(parts, ", ")
}

func isTestFile(rel string) bool {
	return strings.HasSuffix(rel, "_test.go") || strings.Contains(rel, "/testdata/")
}

func apiCmd(dir string) {
	fset := token.NewFileSet()
	var out []Symbol
	filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(path, ".go") {
			return nil
		}
		rel, _ := filepath.Rel(dir, path)
		if isTestFile(rel) || strings.HasPrefix(rel, "internal/") || strings.Contains(rel, "/internal/") || strings.HasPrefix(rel, "vendor/") {
			return nil
		}
		f, err := parser.ParseFile(fset, path, nil, parser.ParseComments)
		if err != nil {
			return nil
		}
		pkgDir := filepath.Dir(rel)
		if pkgDir == "." {
			pkgDir = ""
		}
		module := strings.TrimSuffix(strings.ReplaceAll(pkgDir, string(filepath.Separator), "/"), "/")
		for _, d := range f.Decls {
			switch x := d.(type) {
			case *ast.FuncDecl:
				if !x.Name.IsExported() {
					continue
				}
				name := x.Name.Name
				kind := "function"
				if x.Recv != nil && len(x.Recv.List) > 0 {
					recv := exprString(fset, x.Recv.List[0].Type)
					recv = strings.TrimPrefix(recv, "*")
					name = recv + "." + name
					kind = "method"
				}
				sig := "(" + fieldList(x.Type.Params) + ")"
				if x.Type.Results != nil {
					sig += " " + fieldList(x.Type.Results)
				}
				out = append(out, Symbol{module, joinQ(module, name), kind, sig, firstLine(x.Doc), rel, fset.Position(x.Pos()).Line})
			case *ast.GenDecl:
				for _, s := range x.Specs {
					switch sp := s.(type) {
					case *ast.TypeSpec:
						if sp.Name.IsExported() {
							k := "type"
							if _, ok := sp.Type.(*ast.InterfaceType); ok {
								k = "interface"
							} else if _, ok := sp.Type.(*ast.StructType); ok {
								k = "struct"
							}
							out = append(out, Symbol{module, joinQ(module, sp.Name.Name), k, exprString(fset, sp.Type), firstLine(x.Doc), rel, fset.Position(sp.Pos()).Line})
						}
					case *ast.ValueSpec:
						for _, n := range sp.Names {
							if n.IsExported() {
								k := "var"
								if x.Tok == token.CONST {
									k = "constant"
								}
								out = append(out, Symbol{module, joinQ(module, n.Name), k, exprString(fset, sp.Type), firstLine(x.Doc), rel, fset.Position(n.Pos()).Line})
							}
						}
					}
				}
			}
		}
		return nil
	})
	json.NewEncoder(os.Stdout).Encode(map[string]any{"symbols": out})
}

func joinQ(module, name string) string {
	if module == "" {
		return name
	}
	return module + "." + name
}

func sitesCmd(dir, module string) {
	fset := token.NewFileSet()
	var out []Site
	filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(path, ".go") {
			return nil
		}
		rel, _ := filepath.Rel(dir, path)
		if strings.HasPrefix(rel, "vendor/") {
			return nil
		}
		src, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		f, err := parser.ParseFile(fset, path, src, parser.ParseComments)
		if err != nil {
			return nil
		}
		lines := strings.Split(string(src), "\n")
		alias := map[string]string{}
		for _, imp := range f.Imports {
			p := strings.Trim(imp.Path.Value, `"`)
			if p == module || strings.HasPrefix(p, module+"/") {
				name := p[strings.LastIndex(p, "/")+1:]
				if imp.Name != nil {
					name = imp.Name.Name
				}
				alias[name] = p
				out = append(out, Site{p, rel, fset.Position(imp.Pos()).Line, isTestFile(rel), strings.TrimSpace(lines[fset.Position(imp.Pos()).Line-1])})
			}
		}
		if len(alias) == 0 {
			return nil
		}
		ast.Inspect(f, func(n ast.Node) bool {
			sel, ok := n.(*ast.SelectorExpr)
			if !ok {
				return true
			}
			id, ok := sel.X.(*ast.Ident)
			if !ok {
				return true
			}
			if p, ok := alias[id.Name]; ok {
				ln := fset.Position(sel.Pos()).Line
				ctx := ""
				if ln-1 < len(lines) {
					ctx = strings.TrimSpace(lines[ln-1])
					if len(ctx) > 160 {
						ctx = ctx[:160]
					}
				}
				out = append(out, Site{p + "." + sel.Sel.Name, rel, ln, isTestFile(rel), ctx})
			}
			return true
		})
		return nil
	})
	json.NewEncoder(os.Stdout).Encode(map[string]any{"sites": out})
}

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintln(os.Stderr, "usage: gohelper api <dir> | sites <dir> <module>")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "api":
		apiCmd(os.Args[2])
	case "sites":
		if len(os.Args) < 4 {
			os.Exit(2)
		}
		sitesCmd(os.Args[2], os.Args[3])
	default:
		os.Exit(2)
	}
}
