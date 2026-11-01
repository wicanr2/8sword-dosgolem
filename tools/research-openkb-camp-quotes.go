// Disposable quote probe. No guest execution, game memory or save writes.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
)

func main() {
	input := flag.String("input", "", "proposal JSON")
	out := flag.String("out", "", "new quote JSON")
	flag.Parse()
	must := func(e error) {
		if e != nil {
			panic(e)
		}
	}
	raw, e := os.ReadFile(*input)
	must(e)
	var d struct {
		Camps []struct {
			ID    string `json:"id"`
			Stock uint32 `json:"stock"`
			Gold  uint64 `json:"gold"`
		}
		Units []UnitProfile `json:"units"`
	}
	must(json.Unmarshal(raw, &d))
	catRaw, e := os.ReadFile("inputs/army-catalog.json")
	must(e)
	var c ArmyCatalog
	must(json.Unmarshal(catRaw, &c))
	var rows []any
	for _, camp := range d.Camps {
		for _, u := range d.Units {
			stock := uint32(uint64(camp.Stock) * camp.Gold / u.Gold)
			for _, rank := range []uint32{1, 5} {
				a := OwnedArmy{Gold: 5000, Leadership: 1000, RecruitRank: rank, Rules: "tactics", Slots: [6]ArmyStack{{Unit: "native:01", Count: 30}}, Offers: map[string]ArmyOffer{"proposal": {Unit: u.ID, Stock: stock}}}
				q, e := a.quote(c, "proposal")
				must(e)
				rows = append(rows, map[string]any{"camp": camp.ID, "unit": u.ID, "rank": rank, "candidate_stock": stock, "maximum": q.Maximum, "reason": q.Reason})
			}
		}
	}
	b, e := json.MarshalIndent(map[string]any{"status": "passed-disposable-camp-quotes", "rows": rows, "guest_execution": false, "save_writes": false, "decision_pending": true}, "", "  ")
	must(e)
	f, e := os.OpenFile(*out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	must(e)
	_, e = f.Write(append(b, '\n'))
	must(e)
	must(f.Close())
	fmt.Println("quote samples", len(rows))
}
