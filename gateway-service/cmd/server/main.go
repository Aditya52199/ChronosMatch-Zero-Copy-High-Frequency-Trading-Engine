package main

import (
  "encoding/json"
  "log"
  "net/http"
  "os"
  "time"
  "trading-platform/gateway-service/internal/handlers"
  "trading-platform/gateway-service/internal/router"
)
func main() {
  mux := router.New()
  mux.HandleFunc("/health", handlers.Health)
  mux.HandleFunc("/api/markets", handlers.Markets)
  mux.HandleFunc("/api/orders", handlers.Orders)
  addr := os.Getenv("ADDR")
  if addr == "" { addr = ":8080" }
  server := &http.Server{Addr: addr, Handler: cors(mux), ReadHeaderTimeout: 5*time.Second}
  log.Printf("gateway listening on %s", addr)
  log.Fatal(server.ListenAndServe())
}
func cors(next http.Handler) http.Handler {
 return http.HandlerFunc(func(w http.ResponseWriter,r *http.Request) {
  w.Header().Set("Access-Control-Allow-Origin","http://localhost:5173")
  w.Header().Set("Access-Control-Allow-Headers","Content-Type, Authorization")
  w.Header().Set("Access-Control-Allow-Methods","GET, POST, OPTIONS")
  if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
  next.ServeHTTP(w,r)
 })
}
var _ = json.NewEncoder
