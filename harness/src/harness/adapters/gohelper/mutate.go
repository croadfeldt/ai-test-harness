// Mutation operators on go/ast, the Go half of stage 4's mutation step (stages/mutate.py).
//
//	mutsites <file> [line,line,...]   candidate mutation sites, restricted to the given lines, as JSON
//	mutate <file> <op> <line> <col>   the file with that one site mutated, on stdout
//
// The operators mirror the Python mutator's: compare-swap, boolop-swap, const-int, const-bool,
// not-drop, plus two Go has and Python does not need: cond-negate (if x -> if !x) and incdec-swap.
package main

import (
	"bytes"
	"encoding/json"
	"go/ast"
	"go/format"
	"go/parser"
	"go/token"
	"os"
	"reflect"
	"strconv"
	"strings"
)

type MutSite struct {
	Op   string `json:"op"`
	Line int    `json:"line"`
	Col  int    `json:"col"`
	Text string `json:"text"`
}

var compareSwap = map[token.Token]token.Token{
	token.EQL: token.NEQ, token.NEQ: token.EQL, token.LSS: token.LEQ, token.LEQ: token.LSS, token.GTR: token.GEQ, token.GEQ: token.GTR,
}

func parseLines(spec string) map[int]bool {
	if spec == "" {
		return nil
	}
	out := map[int]bool{}
	for _, s := range strings.Split(spec, ",") {
		if n, err := strconv.Atoi(strings.TrimSpace(s)); err == nil {
			out[n] = true
		}
	}
	return out
}

// on reports whether a node's line is one the tests executed (or all lines when no restriction).
func on(fset *token.FileSet, n ast.Node, lines map[int]bool) bool {
	return lines == nil || lines[fset.Position(n.Pos()).Line]
}

func mutsitesCmd(file, lineSpec string) {
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, file, nil, parser.ParseComments)
	if err != nil {
		os.Stderr.WriteString(err.Error())
		os.Exit(1)
	}
	lines := parseLines(lineSpec)
	sites := []MutSite{}
	add := func(op string, n ast.Node, text string) {
		p := fset.Position(n.Pos())
		sites = append(sites, MutSite{op, p.Line, p.Column, text})
	}
	ast.Inspect(f, func(n ast.Node) bool {
		if n == nil || !on(fset, n, lines) {
			return true
		}
		switch x := n.(type) {
		case *ast.BinaryExpr:
			if _, ok := compareSwap[x.Op]; ok {
				add("compare-swap", x, x.Op.String())
			} else if x.Op == token.LAND || x.Op == token.LOR {
				add("boolop-swap", x, x.Op.String())
			}
		case *ast.BasicLit:
			if x.Kind == token.INT && len(x.Value) < 10 && !strings.HasPrefix(x.Value, "0") {
				add("const-int", x, x.Value)
			}
		case *ast.Ident:
			if (x.Name == "true" || x.Name == "false") && x.Obj == nil {
				add("const-bool", x, x.Name)
			}
		case *ast.UnaryExpr:
			if x.Op == token.NOT {
				add("not-drop", x, "!")
			}
		case *ast.IfStmt:
			if x.Cond != nil {
				add("cond-negate", x.Cond, "if")
			}
		case *ast.IncDecStmt:
			add("incdec-swap", x, x.Tok.String())
		}
		return true
	})
	json.NewEncoder(os.Stdout).Encode(map[string]any{"sites": sites})
}

// replaceChild swaps one child expression of a parent node for another, whatever field or slice
// element holds it. go/ast has no generic replace; reflection over the parent's struct does it.
func replaceChild(parent ast.Node, old, repl ast.Expr) bool {
	v := reflect.ValueOf(parent).Elem()
	for i := 0; i < v.NumField(); i++ {
		fld := v.Field(i)
		switch fld.Kind() {
		case reflect.Interface:
			if fld.CanSet() && fld.Interface() == ast.Node(old) {
				fld.Set(reflect.ValueOf(repl))
				return true
			}
		case reflect.Slice:
			for j := 0; j < fld.Len(); j++ {
				el := fld.Index(j)
				if el.Kind() == reflect.Interface && el.Interface() == ast.Node(old) {
					el.Set(reflect.ValueOf(repl))
					return true
				}
			}
		}
	}
	return false
}

func mutateCmd(file, op string, line, col int) {
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, file, nil, parser.ParseComments)
	if err != nil {
		os.Stderr.WriteString(err.Error())
		os.Exit(1)
	}
	done := false
	var stack []ast.Node
	at := func(n ast.Node) bool {
		p := fset.Position(n.Pos())
		return p.Line == line && p.Column == col
	}
	// cond-negate is applied on the IfStmt whose Cond starts at the site; the others on the node itself.
	ast.Inspect(f, func(n ast.Node) bool {
		if n == nil {
			if len(stack) > 0 {
				stack = stack[:len(stack)-1]
			}
			return true
		}
		if done {
			return false
		}
		parent := ast.Node(nil)
		if len(stack) > 0 {
			parent = stack[len(stack)-1]
		}
		stack = append(stack, n)
		switch x := n.(type) {
		case *ast.BinaryExpr:
			if at(x) {
				if op == "compare-swap" {
					if t, ok := compareSwap[x.Op]; ok {
						x.Op = t
						done = true
					}
				} else if op == "boolop-swap" && (x.Op == token.LAND || x.Op == token.LOR) {
					if x.Op == token.LAND {
						x.Op = token.LOR
					} else {
						x.Op = token.LAND
					}
					done = true
				}
			}
		case *ast.BasicLit:
			if op == "const-int" && at(x) && x.Kind == token.INT {
				if v, err := strconv.Atoi(x.Value); err == nil {
					x.Value = strconv.Itoa(v + 1)
					done = true
				}
			}
		case *ast.Ident:
			if op == "const-bool" && at(x) {
				if x.Name == "true" {
					x.Name = "false"
					done = true
				} else if x.Name == "false" {
					x.Name = "true"
					done = true
				}
			}
		case *ast.UnaryExpr:
			if op == "not-drop" && at(x) && x.Op == token.NOT && parent != nil {
				// `!x` becomes `x`: the operand takes the node's place in the parent.
				done = replaceChild(parent, x, x.X)
			}
		case *ast.IfStmt:
			if op == "cond-negate" && x.Cond != nil && at(x.Cond) {
				x.Cond = &ast.UnaryExpr{OpPos: x.Cond.Pos(), Op: token.NOT, X: &ast.ParenExpr{Lparen: x.Cond.Pos(), X: x.Cond, Rparen: x.Cond.End()}}
				done = true
			}
		case *ast.IncDecStmt:
			if op == "incdec-swap" && at(x) {
				if x.Tok == token.INC {
					x.Tok = token.DEC
				} else {
					x.Tok = token.INC
				}
				done = true
			}
		}
		return true
	})
	if !done {
		os.Stderr.WriteString("no such site")
		os.Exit(3)
	}
	var buf bytes.Buffer
	if err := format.Node(&buf, fset, f); err != nil {
		os.Stderr.WriteString(err.Error())
		os.Exit(1)
	}
	os.Stdout.Write(buf.Bytes())
}
