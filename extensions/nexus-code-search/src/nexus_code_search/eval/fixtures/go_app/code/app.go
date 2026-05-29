package main

import "fmt"

type Greeter struct {
	name string
}

type Speaker interface {
	Speak() string
}

func (g Greeter) Speak() string {
	return g.name
}

func NewGreeter(n string) Greeter {
	return Greeter{name: n}
}

func main() {
	g := NewGreeter("hi")
	fmt.Println(g.Speak())
}
