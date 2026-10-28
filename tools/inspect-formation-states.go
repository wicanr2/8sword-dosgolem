// Standalone gob reader. machineState types are copied from the fixed state schema.
package main

import (
 "bytes"
 "compress/gzip"
 "crypto/sha256"
 "encoding/binary"
 "encoding/gob"
 "encoding/json"
 "flag"
 "fmt"
 "io"
 "os"
 "path/filepath"
 "strings"
)
func check(e error){if e!=nil{panic(e)}}
func sum(b []byte)string{return fmt.Sprintf("%x",sha256.Sum256(b))}
func main(){
 calls:=flag.String("calls","","original saved states");out:=flag.String("out","","new decoding output");flag.Parse();check(os.Mkdir(*out,0755));rows:=map[string]any{}
 check(filepath.WalkDir(*calls,func(p string,d os.DirEntry,e error)error{
  check(e);if d.IsDir()||!strings.HasSuffix(p,".state"){return nil}
  f,e:=os.Open(p);check(e);z,e:=gzip.NewReader(f);check(e);raw,e:=io.ReadAll(io.LimitReader(z,64<<20));check(e);check(z.Close());check(f.Close())
  n:=int(binary.LittleEndian.Uint64(raw));if n<0||n+16>len(raw){panic("state section bound")};machineBytes:=raw[8:8+n];dosAt:=8+n;dosN:=int(binary.LittleEndian.Uint64(raw[dosAt:]));if dosAt+8+dosN!=len(raw){panic("DOS section bound")}
  var s machineState;check(gob.NewDecoder(bytes.NewReader(machineBytes)).Decode(&s));if s.Magic!="DOSGOLEM-M"||s.Version!=3{panic("state schema")}
  memSHA:=sum(s.Mem);target:=filepath.Join(*out,memSHA+".ram.gz")
  if _,e:=os.Stat(target);os.IsNotExist(e){f,e:=os.OpenFile(target,os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);check(e);zw:=gzip.NewWriter(f);_,e=zw.Write(s.Mem);check(e);check(zw.Close());check(f.Close())}
  regs:=s.R;s.R[0]=0;normalized,e:=json.Marshal(s);check(e);name,e:=filepath.Rel(*calls,p);check(e)
  rows[name]=map[string]any{"registers":regs,"segments":s.Seg,"ip":s.IP,"flags":s.Flags,"steps":s.Steps,"memory_sha256":memSHA,"normalized_except_ax_sha256":sum(normalized),"dos_sha256":sum(raw[dosAt+8:])}
  return nil
 }))
 b,e:=json.MarshalIndent(rows,"","  ");check(e);check(os.WriteFile(filepath.Join(*out,"index.json"),append(b,'\n'),0644));fmt.Printf("independently decoded %d states\n",len(rows))
}
