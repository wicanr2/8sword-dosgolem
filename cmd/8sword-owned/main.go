// Command 8sword-owned runs the Go-owned army adapter with HD presentation.
package main

import (
	"fmt"
	"os"

	"github.com/wicanr2/8sword-dosgolem/internal/ownedworld"
)

func main() {
	if err := ownedworld.Run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
