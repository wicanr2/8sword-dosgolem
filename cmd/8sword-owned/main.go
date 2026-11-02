// Command 8sword-owned imports native progress while the original battlefield bridge is pending.
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
