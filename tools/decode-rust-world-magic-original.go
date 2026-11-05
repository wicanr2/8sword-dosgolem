//go:build ignore

// Extract inherited dosgolem receipt RAM. No guest execution and no game helper.
package main

import (
 "compress/gzip"
 "encoding/binary"
 "encoding/gob"
 "fmt"
 "io"
 "os"
)
func main() {
 if os.Getuid()!=1000 {panic("UID")};if _,e:=os.Stat("/.dockerenv");e!=nil {panic(e)}
 if len(os.Args)!=3 {panic("input output")}
 f,e:=os.Open(os.Args[1]);if e!=nil {panic(e)};defer f.Close()
 z,e:=gzip.NewReader(f);if e!=nil {panic(e)};defer z.Close()
 var n uint64;if e=binary.Read(z,binary.LittleEndian,&n);e!=nil {panic(e)};if n==0||n>4<<20 {panic("section length")}
 var s struct{Magic string;Version int;Mem []byte;Seg [4]uint16}
 if e=gob.NewDecoder(io.LimitReader(z,int64(n))).Decode(&s);e!=nil {panic(e)}
 if s.Magic!="DOSGOLEM-M" || s.Version<2 || s.Version>3 || len(s.Mem)<1048576 {panic("state identity")}
 if e=os.WriteFile(os.Args[2],s.Mem,0644);e!=nil {panic(e)};fmt.Println(len(s.Mem),s.Seg)
}
