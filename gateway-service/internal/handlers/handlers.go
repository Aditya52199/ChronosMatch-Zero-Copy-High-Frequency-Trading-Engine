package handlers
import (
 "encoding/json"
 "fmt"
 "net/http"
 "sync/atomic"
 "time"
)
type market struct { Symbol string `json:"symbol"`; Price float64 `json:"price"`; Change float64 `json:"change"` }
type orderRequest struct { Symbol string `json:"symbol"`; Side string `json:"side"`; Quantity float64 `json:"quantity"`; Type string `json:"type"`; LimitPrice float64 `json:"limitPrice,omitempty"` }
var orderID atomic.Uint64
func Health(w http.ResponseWriter,r *http.Request) { writeJSON(w,http.StatusOK,map[string]string{"status":"ok","time":time.Now().UTC().Format(time.RFC3339)}) }
func Markets(w http.ResponseWriter,r *http.Request) {
 if r.Method != http.MethodGet { http.Error(w,"method not allowed",http.StatusMethodNotAllowed); return }
 writeJSON(w,http.StatusOK,[]market{{"BTC-USD",67250.12,1.8},{"ETH-USD",3520.42,-0.6},{"SOL-USD",148.30,2.4}})
}
func Orders(w http.ResponseWriter,r *http.Request) {
 if r.Method != http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed); return }
 var req orderRequest
 if err:=json.NewDecoder(http.MaxBytesReader(w,r.Body,1<<20)).Decode(&req); err!=nil { http.Error(w,"invalid JSON",http.StatusBadRequest); return }
 if req.Symbol=="" || (req.Side!="buy" && req.Side!="sell") || req.Quantity<=0 || (req.Type!="market" && req.Type!="limit") { http.Error(w,"invalid order fields",http.StatusBadRequest); return }
 if req.Type=="limit" && req.LimitPrice<=0 { http.Error(w,"limitPrice must be positive",http.StatusBadRequest); return }
 id:=orderID.Add(1)
 writeJSON(w,http.StatusAccepted,map[string]any{"id":fmt.Sprintf("paper-%d",id),"status":"accepted","received":req,"note":"Demo acknowledgement only; no real trade executed."})
}
func writeJSON(w http.ResponseWriter,status int,v any) { w.Header().Set("Content-Type","application/json"); w.WriteHeader(status); _=json.NewEncoder(w).Encode(v) }
